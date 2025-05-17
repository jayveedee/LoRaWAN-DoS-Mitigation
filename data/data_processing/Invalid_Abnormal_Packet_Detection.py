from flask import Flask, request, jsonify
import base64
import datetime

app = Flask(__name__)

# Cache to track the last frame counter per device
fcnt_cache = {}

@app.route("/uplink", methods=["POST"])
def uplink():
    data = request.json
    dev_eui = data.get("end_device_ids", {}).get("dev_eui", "unknown")
    fcnt = data.get("uplink_message", {}).get("f_cnt")
    payload = data.get("uplink_message", {}).get("frm_payload", "")
    time_rx = data.get("uplink_message", {}).get("received_at", "")
    rssi = data.get("uplink_message", {}).get("rx_metadata", [{}])[0].get("rssi", "N/A")

    # Decode Base64 payload to hex
    decoded_payload = base64.b64decode(payload).hex() if payload else None

    # Store any alerts to print
    alerts = []

    # Detect empty payloads
    if not payload:
        alerts.append("⚠️ Empty payload detected")

    # Detect repeated frame counter
    if dev_eui in fcnt_cache and fcnt == fcnt_cache[dev_eui]:
        alerts.append("⚠️ Duplicate FCnt detected")
    else:
        fcnt_cache[dev_eui] = fcnt

    # Print log
    print(f"[{datetime.datetime.now()}] Packet from {dev_eui} | FCnt: {fcnt} | RSSI: {rssi} | Time: {time_rx}")
    print(f"Payload: {decoded_payload}")
    for alert in alerts:
        print(alert)

    return jsonify({"status": "received", "alerts": alerts}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
