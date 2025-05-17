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

    # Decode payload
    decoded_payload = base64.b64decode(payload).hex() if payload else ""
    alerts = []

    # Detect empty payload
    if not payload:
        alerts.append("⚠️ Empty payload detected")

    # Parse timestamp from TTN ISO format
    try:
        timestamp = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
    except Exception:
        timestamp = datetime.now(timezone.utc)
        alerts.append("⚠️ Invalid timestamp format")

    # Init state for new device
    if dev_eui not in device_state:
        device_state[dev_eui] = {
            "last_fcnt": fcnt,
            "last_payload": decoded_payload,
            "last_time": timestamp,
        }

    else:
        state = device_state[dev_eui]

        # FCnt gap detection
        gap = fcnt - state["last_fcnt"]
        if gap > 1:
            alerts.append(f"⚠️ FCnt gap of {gap} — possible packet loss or jamming")

        # Irregular interval detection
        time_diff = (timestamp - state["last_time"]).total_seconds()
        if time_diff > 20:
            alerts.append(f"⚠️ Delay of {time_diff:.1f}s — expected ~10s. Possible disruption")

        # Repeated payload
        if decoded_payload == state["last_payload"]:
            alerts.append("⚠️ Repeated payload with new FCnt — retry likely due to missing ACK")

        # RSSI or SNR drops
        if rssi < -115:
            alerts.append(f"⚠️ Low RSSI ({rssi}) — could indicate interference")
        if snr < -10:
            alerts.append(f"⚠️ Low SNR ({snr}) — possible jamming or noise")

        # Update device state
        device_state[dev_eui] = {
            "last_fcnt": fcnt,
            "last_payload": decoded_payload,
            "last_time": timestamp,
        }

    # Print log
    print(f"[{datetime.now()}] DevEUI: {dev_eui} | FCnt: {fcnt} | RSSI: {rssi} | SNR: {snr}")
    print(f"Payload (hex): {decoded_payload}")
    for alert in alerts:
        print("  •", alert)

    return jsonify({"status": "received", "alerts": alerts}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
