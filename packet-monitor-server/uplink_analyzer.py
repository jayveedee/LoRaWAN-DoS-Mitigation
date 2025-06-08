import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional

from device_state import DeviceState


class UplinkAnalyzer:
    """Light but opinionated LoRaWAN uplink sanity checker."""

    # ── tune these to taste ────────────────────────────────────────────────
    EXPECTED_INTERVAL = 10          # s, what “normal” looks like
    MAX_TIME_GAP      = 20          # s, beyond this = “long delay”
    MAX_FCNT_GAP      = 10
    FCNT_HISTORY_SIZE = 10

    RSSI_THRESHOLD = -115
    RSSI_BAD       = -120
    RSSI_GOOD      = -100
    SNR_THRESHOLD  = -10
    SNR_BAD        = -15
    SNR_GOOD       = -5
    # ───────────────────────────────────────────────────────────────────────

    def __init__(self, logger: logging.Logger) -> None:
        self._log      = logger.getChild("analyzer")
        self._devices: Dict[str, DeviceState] = {}

    # ------------------------------------------------------------------ API
    def analyze_uplink(self, data: Dict[str, Any]) -> Dict[str, Any]:
        dev_eui = data.get("end_device_ids", {}).get("dev_eui", "unknown")
        fcnt    = data.get("uplink_message", {}).get("f_cnt")
        payload = data.get("uplink_message", {}).get("frm_payload", "")
        ttn_ts  = data.get("uplink_message", {}).get("received_at")

        # primary gateway’s RF
        meta        = (data.get("uplink_message", {})
                           .get("rx_metadata", [{}]))[0]
        rssi, snr   = meta.get("rssi", -999), meta.get("snr", -999)

        ts, time_alert = self._parse_timestamp(ttn_ts)
        alerts: List[str] = time_alert

        state = self._devices.setdefault(dev_eui, DeviceState(dev_eui))

        alerts += self._analyze_fcnt(state, fcnt)
        alerts += self._analyze_timing(state, ts)
        alerts += self._analyze_rf_quality(state, rssi, snr)
        alerts += self._analyze_payload(state, payload, fcnt)

        # ----- state mutate & history -------------------------------------
        state.last_fcnt = fcnt if isinstance(fcnt, int) else state.last_fcnt
        state.last_time = ts
        state.last_rssi = rssi
        state.last_snr  = snr

        # ----- logging -----------------------------------------------------
        self._log.info(
            "DevEUI=%s │ FCnt=%s │ Δt=%s s │ RSSI=%s dBm │ SNR=%s dB",
            dev_eui,
            fcnt,
            (None if state.last_time is None
             else round((ts - state.last_time).total_seconds(), 1)),
            rssi,
            snr,
        )
        for a in alerts:
            self._log.warning("  %s", a)

        return {
            "status":      "ok",
            "device_eui":  dev_eui,
            "fcnt":        fcnt,
            "alerts":      alerts,
            "received_at": ts.isoformat(),
            "rssi":        rssi,
            "snr":         snr,
        }

    # ---------------------------------------------------------------- helpers
    def _parse_timestamp(self, raw: str) -> Tuple[datetime, List[str]]:
        if not raw:
            return datetime.now(timezone.utc), ["⚠️ Missing timestamp"]

        try:
            ts = datetime.fromisoformat(raw.rstrip("Z")).replace(tzinfo=timezone.utc)
            return ts, []
        except Exception:
            return datetime.now(timezone.utc), [f"⚠️ Bad timestamp: {raw!r}"]

    # .......................................... FCnt
    def _analyze_fcnt(self, s: DeviceState, fcnt: Any) -> List[str]:
        a: List[str] = []
        if not isinstance(fcnt, int):
            a.append("⚠️ Invalid or missing FCnt")
            return a

        if fcnt > 65535:
            a.append("⚠️ FCnt > 16-bit limit")

        if s.last_fcnt is None:
            return a

        if fcnt < s.last_fcnt <= 65535 and s.last_fcnt > 60000:
            a.append("ℹ️ FCnt rollover detected")
        elif fcnt == s.last_fcnt:
            a.append(f"⚠️ Duplicate FCnt {fcnt}")
        elif fcnt < s.last_fcnt:
            a.append(f"⚠️ FCnt went backwards ({s.last_fcnt}→{fcnt})")
        else:
            gap = fcnt - s.last_fcnt
            if gap > 1:
                a.append(f"⚠️ FCnt gap of {gap}")
                if gap > self.MAX_FCNT_GAP:
                    a.append("⚠️ Large FCnt gap – potential loss")

        # short history for quick inspection
        s.fcnt_sequence.append(fcnt)
        if len(s.fcnt_sequence) > self.FCNT_HISTORY_SIZE:
            s.fcnt_sequence.pop(0)

        return a

    # .......................................... Timing
    def _analyze_timing(self, s: DeviceState, ts: datetime) -> List[str]:
        if s.last_time is None:
            return []

        dt = (ts - s.last_time).total_seconds()
        if dt < 1:
            return [f"⚠️ Too fast ({dt:.2f}s) – duplicates?"]
        if dt > self.MAX_TIME_GAP:
            return [f"⚠️ Long delay ({dt:.1f}s) – expected {self.EXPECTED_INTERVAL}s"]

        # a mild nudge if just slightly off
        if abs(dt - self.EXPECTED_INTERVAL) > 2:
            return [f"ℹ️ Interval {dt:.1f}s (nominal {self.EXPECTED_INTERVAL}s)"]
        return []

    # .......................................... RF
    def _analyze_rf_quality(self, s: DeviceState, rssi: float, snr: float) -> List[str]:
        a: List[str] = []
        # keep last 100 samples for crude averages
        if rssi != -999:
            s.rssi_history.append(rssi)
            if len(s.rssi_history) > 100:
                s.rssi_history.pop(0)
        if snr != -999:
            s.snr_history.append(snr)
            if len(s.snr_history) > 100:
                s.snr_history.pop(0)

        if rssi < self.RSSI_BAD or snr < self.SNR_BAD:
            a.append(f"⚠️ Very poor RF (RSSI {rssi} / SNR {snr})")
        elif rssi < self.RSSI_THRESHOLD or snr < self.SNR_THRESHOLD:
            a.append(f"⚠️ Low RF (RSSI {rssi} / SNR {snr})")
        elif rssi > self.RSSI_GOOD and snr > self.SNR_GOOD:
            a.append(f"ℹ️ Good RF (RSSI {rssi} / SNR {snr})")
        return a

    # .......................................... Payload
    def _decode_payload(
        self, b64: str
    ) -> Tuple[str, Optional[int], List[str]]:
        if not b64:
            return "", None, ["⚠️ Empty payload"]

        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception:
            return "<base64-err>", None, ["⚠️ Bad base64"]

        if len(raw) == 0:
            return "", None, ["⚠️ Zero-length payload"]

        if len(raw) > 1:
            text = raw[:-1].decode("utf-8", errors="replace").strip()
            cnt  = raw[-1]
        else:
            text = raw.decode("utf-8", errors="replace").strip()
            cnt  = None

        return text, cnt, []

    def _analyze_payload(self, s: DeviceState, b64: str, fcnt: Any) -> List[str]:
        text, cnt, errs = self._decode_payload(b64)
        a: List[str] = errs

        # equality checks
        if text == s.last_string and cnt == s.last_count:
            if fcnt == s.last_fcnt:
                a.append("⚠️ Exact duplicate payload & FCnt")
            else:
                a.append("⚠️ Payload+count repeated with new FCnt")

        # counter progression
        if cnt is not None and s.last_count is not None:
            if cnt == s.last_count:
                a.append("⚠️ Payload counter unchanged")
            elif cnt < s.last_count:
                a.append("⚠️ Payload counter decreased")

        # minimal content
        if not text:
            a.append("⚠️ Empty decoded string")
        elif len(text) < 3:
            a.append("⚠️ Very short payload")

        # store
        s.last_string, s.last_count = text, cnt
        return a
