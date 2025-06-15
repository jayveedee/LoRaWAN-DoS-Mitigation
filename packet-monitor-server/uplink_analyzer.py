"""
UplinkAnalyzer: A simple LoRaWAN uplink sanity checker.
"""
import logging, base64, csv, os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional
from device_state import DeviceState, WindowStats

class UplinkAnalyzer:
    # ── statistics ─────────────────────────────────────────────────────────
    WINDOW = 50
    CSV_DIR = "stats"

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
        os.makedirs(self.CSV_DIR, exist_ok=True)

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

        delta_seconds = None
        if state.last_time:
            delta_seconds = round((ts - state.last_time).total_seconds(), 1)

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
            delta_seconds if delta_seconds is not None else "0",
            rssi,
            snr,
        )

        self._log.info(
            "  Payload='%s' │ Counter=%s",
            state.last_string,
            state.last_count,
        )

        for a in alerts:
            self._log.warning("  %s", a)

        # ----- save statistics ----------------------------------------------
        self._update_window(state, alerts, rssi, snr, ts)   
        self.export_window_state(dev_eui, force=False)                 

        return {
            "status":      "ok",
            "device_eui":  dev_eui,
            "fcnt":        fcnt,
            "alerts":      alerts,
            "received_at": ts.isoformat(),
            "rssi":        rssi,
            "snr":         snr,
        }

    def export_window_state(self, dev_eui: str, force: bool = False) -> None:
        state = self._devices.get(dev_eui)
        if state is None:
            self._log.warning(f"No state found for {dev_eui}")
            return  # or raise an exception
        
        if force or state.window.msgs >= self.WINDOW:
            self._export_window_csv(dev_eui, state)
            state.window = WindowStats()    

    # ---------------------------------------------------------------- helpers
    def _parse_timestamp(self, raw: str) -> Tuple[datetime, List[str]]:
        if not raw:
            return datetime.now(timezone.utc), ["⚠️ Missing timestamp"]
        try:
            # Strip trailing 'Z'
            if raw.endswith("Z"):
                raw = raw[:-1]

            # Split date/time and fractional seconds if present
            if '.' in raw:
                date_part, frac = raw.split('.', 1)
                # Truncate fractional part to max 6 digits (microseconds)
                # Pad with zeros if less than 6 digits
                frac = (frac + "000000")[:6]
                raw_fixed = f"{date_part}.{frac}"
                ts = datetime.fromisoformat(raw_fixed).replace(tzinfo=timezone.utc)
            else:
                ts = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)

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

    def _update_window(self, s, alerts, rssi, snr, ts):
        """Increment counters used for the 50-message roll-up."""
        w = s.window
        w.msgs += 1

        if any("Duplicate FCnt" in al for al in alerts):
            w.dup_fcnt += 1
        if any("FCnt gap" in al for al in alerts):
            w.fcnt_gap += 1
        if any("Long delay" in al for al in alerts):
            w.long_delay += 1

        # delay stats
        if s.last_time:
            w.total_delay += (ts - s.last_time).total_seconds()

        # RF quality
        if rssi < self.RSSI_THRESHOLD or snr < self.SNR_THRESHOLD:
            w.poor_rf += 1
        elif rssi > self.RSSI_GOOD and snr > self.SNR_GOOD:
            w.good_rf += 1

        # payload quirks
        if any("Payload+count repeated" in al for al in alerts):
            w.same_payload += 1
        if any("counter decreased" in al for al in alerts):
            w.counter_decrease += 1

    # ......................................... CSV serializer
    def _export_window_csv(self, dev_eui: str, s: DeviceState):
        os.makedirs(self.CSV_DIR, exist_ok=True)

        w = s.window
        avg_delay = (w.total_delay / w.msgs) if w.msgs else 0
        row = {
            "dev_eui"        : dev_eui,
            "window_size"    : w.msgs,
            "dup_fcnt_pct"   : round(100 * w.dup_fcnt / w.msgs, 2),
            "fcnt_gap_pct"   : round(100 * w.fcnt_gap / w.msgs, 2),
            "long_delay_pct" : round(100 * w.long_delay / w.msgs, 2),
            "avg_delay_s"    : round(avg_delay, 2),
            "poor_rf_pct"    : round(100 * w.poor_rf / w.msgs, 2),
            "good_rf_pct"    : round(100 * w.good_rf / w.msgs, 2),
            "same_payload_pct": round(100 * w.same_payload / w.msgs, 2),
            "counter_dec_pct": round(100 * w.counter_decrease / w.msgs, 2),
            "timestamp"      : datetime.utcnow().isoformat(),
        }

        file = os.path.join(self.CSV_DIR, f"{dev_eui}.csv")
        write_header = not os.path.exists(file)
        with open(file, "a", newline="") as fp:
            wcsv = csv.DictWriter(fp, fieldnames=row.keys())
            if write_header:
                wcsv.writeheader()
            wcsv.writerow(row)

        self._log.info("📄 50-msg stats appended to %s", file)

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
