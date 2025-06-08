import logging
from uplink_analyzer import UplinkAnalyzer
from flask import Flask, request, jsonify
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
analyzer = UplinkAnalyzer(logger)

@app.route("/uplink", methods=["POST"])
def uplink():
    """Handle TTN uplink webhook"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        result = analyzer.analyze_uplink(data)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing uplink: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)