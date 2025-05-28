from flask import Flask, request, jsonify
import base64
from datetime import datetime, timezone

app = Flask(__name__)

# State per device to track FCnt, payload, and timing
device_state = {}

@app.route("/uplink", methods=["POST"])
def uplink():
    data = request.json
    dev_eui = data.get("end_device_ids", {}).get("dev_eui", "unknown")
    fcnt = data.get("uplink_message", {}).get("f_cnt")
    payload = data.get("uplink_message", {}).get("frm_payload", "")
    received_at = data.get("uplink_message", {}).get("received_at", "")
    metadata = data.get("uplink_message", {}).get("rx_metadata", [{}])[0]
    rssi = metadata.get("rssi", -999)
    snr = metadata.get("snr", -999)

    alerts = []

    # Parse timestamp safely (truncate nanoseconds to microseconds)
    try:
        clean_time = received_at.replace("Z", "").split(".")
        if len(clean_time) == 2:
            time_part, nano = clean_time
            micro = nano[:6].ljust(6, "0")
            final_time = f"{time_part}.{micro}+00:00"
        else:
            final_time = received_at.replace("Z", "+00:00")
        timestamp = datetime.fromisoformat(final_time)
    except Exception:
        timestamp = datetime.now(timezone.utc)
        alerts.append("⚠️ Invalid timestamp format; using server time")

    # Decode payload
    try:
        raw_bytes = base64.b64decode(payload)
        decoded_string = raw_bytes[:-1].decode("utf-8").strip() if len(raw_bytes) > 1 else ""
        count = raw_bytes[-1] if raw_bytes else None
    except Exception:
        decoded_string = "<non-decodable>"
        count = None
        alerts.append("⚠️ Failed to decode payload")

    # Detect empty payload
    if not payload:
        alerts.append("⚠️ Empty payload detected")

    # Initialize device state
    if dev_eui not in device_state:
        device_state[dev_eui] = {
            "last_fcnt": fcnt if isinstance(fcnt, int) else None,
            "last_string": decoded_string,
            "last_count": count,
            "last_time": timestamp,
        }
    else:
        state = device_state[dev_eui]

        # FCnt gap detection
        if isinstance(fcnt, int) and isinstance(state["last_fcnt"], int):
            gap = fcnt - state["last_fcnt"]
            if gap > 1:
                alerts.append(f"⚠️ FCnt gap of {gap} — possible packet loss or jamming")
        else:
            alerts.append("⚠️ Invalid or missing FCnt; skipping FCnt gap detection")

        # Irregular timing detection
        time_diff = (timestamp - state["last_time"]).total_seconds()
        if time_diff > 20:
            alerts.append(f"⚠️ Delay of {time_diff:.1f}s — expected ~10s. Possible disruption")

        # Repeated payload string with different FCnt
        if decoded_string == state["last_string"] and fcnt != state["last_fcnt"]:
            alerts.append("⚠️ Repeated payload with new FCnt — likely retry")

        # RSSI and SNR thresholds
        if rssi < -115:
            alerts.append(f"⚠️ Low RSSI ({rssi}) — could indicate interference")
        if snr < -10:
            alerts.append(f"⚠️ Low SNR ({snr}) — possible jamming or noise")

        # Update device state
        device_state[dev_eui] = {
            "last_fcnt": fcnt if isinstance(fcnt, int) else state["last_fcnt"],
            "last_string": decoded_string,
            "last_count": count,
            "last_time": timestamp,
        }

    # Log output
    print(f"[{datetime.now()}] DevEUI: {dev_eui} | FCnt: {fcnt} | RSSI: {rssi} | SNR: {snr}")
    print(f"Payload: {decoded_string} {count}")
    for alert in alerts:
        print("  •", alert)

    return jsonify({
        "status": "received",
        "text": decoded_string,
        "count": count,
        "alerts": alerts
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
