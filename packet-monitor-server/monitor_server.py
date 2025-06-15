"""
Flask server for monitoring LoRaWAN uplinks.
"""
import logging
from flask import Flask, request, jsonify
from uplink_analyzer import UplinkAnalyzer

# ── basic, consistent logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
logger = logging.getLogger("monitor_server")

# ── flask app ------------------------------------------------------------------
app = Flask(__name__)
analyzer = UplinkAnalyzer(logger)

@app.route("/uplink", methods=["POST"])
def uplink():
    """Handle TTN uplink web-hooks (the only endpoint we keep)."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        result = analyzer.analyze_uplink(data)
        return jsonify(result)
    except Exception:
        logger.exception("Unexpected error while processing /uplink")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/save", methods=["POST"])
def save():
    """Save window state to CSV and return its contents as plain text."""
    analyzer.export_window_state('0004A30B00202875', force=True)
    return {"message": "Window flushed"}

if __name__ == "__main__":
    # bind to all interfaces so the test script can reach us
    app.run(host="0.0.0.0", port=5000, debug=False)
