from flask import Flask, request, jsonify
import base64
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class DeviceState:
    """Track state for each device"""
    def __init__(self):
        self.last_fcnt: Optional[int] = None
        self.last_string: str = ""
        self.last_count: Optional[int] = None
        self.last_time: Optional[datetime] = None
        self.last_rssi: Optional[float] = None
        self.last_snr: Optional[float] = None
        self.fcnt_sequence: List[int] = []  # Track recent FCnt values
        self.duplicate_count: int = 0
        self.total_messages: int = 0
        self.first_seen: Optional[datetime] = None

class UplinkAnalyzer:
    """Analyze uplink messages for anomalies"""
    
    def __init__(self):
        self.device_states: Dict[str, DeviceState] = {}
        
        # Thresholds for anomaly detection
        self.RSSI_THRESHOLD = -115
        self.SNR_THRESHOLD = -10
        self.MAX_TIME_GAP = 20  # seconds
        self.EXPECTED_INTERVAL = 10  # seconds
        self.MAX_FCNT_GAP = 10
        self.FCNT_HISTORY_SIZE = 10
        
    def parse_timestamp(self, timestamp_str: str) -> Tuple[datetime, List[str]]:
        """Parse TTN timestamp with error handling"""
        alerts = []
        try:
            # Handle various timestamp formats from TTN
            clean_time = timestamp_str.replace("Z", "").split(".")
            if len(clean_time) == 2:
                time_part, nano = clean_time
                # Truncate nanoseconds to microseconds
                micro = nano[:6].ljust(6, "0")
                final_time = f"{time_part}.{micro}+00:00"
            else:
                final_time = timestamp_str.replace("Z", "+00:00")
            
            timestamp = datetime.fromisoformat(final_time)
        except Exception as e:
            timestamp = datetime.now(timezone.utc)
            alerts.append(f"⚠️ Invalid timestamp format: {e}")
            
        return timestamp, alerts
    
    def decode_payload(self, payload: str) -> Tuple[str, Optional[int], List[str]]:
        """Decode base64 payload with error handling"""
        alerts = []
        
        if not payload:
            alerts.append("⚠️ Empty payload detected")
            return "", None, alerts
            
        try:
            raw_bytes = base64.b64decode(payload)
            
            # Check for suspicious payload sizes
            if len(raw_bytes) == 0:
                alerts.append("⚠️ Zero-length decoded payload")
                return "", None, alerts
            elif len(raw_bytes) > 51:  # LoRaWAN max payload size
                alerts.append(f"⚠️ Payload size ({len(raw_bytes)}) exceeds LoRaWAN limits")
            
            # Attempt to decode as your expected format
            if len(raw_bytes) > 1:
                decoded_string = raw_bytes[:-1].decode("utf-8").strip()
                count = raw_bytes[-1]
            else:
                decoded_string = raw_bytes.decode("utf-8").strip()
                count = None
                
            # Check for non-printable characters (possible corruption)
            if any(ord(c) < 32 or ord(c) > 126 for c in decoded_string if c not in '\r\n\t'):
                alerts.append("⚠️ Non-printable characters in payload - possible corruption")
                
        except UnicodeDecodeError:
            alerts.append("⚠️ Payload contains non-UTF8 data")
            return "<non-utf8-data>", None, alerts
        except Exception as e:
            alerts.append(f"⚠️ Failed to decode payload: {e}")
            return "<decode-error>", None, alerts
            
        return decoded_string, count, alerts
    
    def analyze_fcnt(self, dev_eui: str, fcnt: Optional[int]) -> List[str]:
        """Analyze frame counter for anomalies"""
        alerts = []
        state = self.device_states[dev_eui]
        
        if not isinstance(fcnt, int):
            alerts.append("⚠️ Invalid or missing FCnt")
            return alerts
            
        # Check for FCnt rollover (16-bit counter)
        if fcnt > 65535:
            alerts.append("⚠️ FCnt exceeds 16-bit limit")
            
        if state.last_fcnt is not None:
            # Handle FCnt rollover
            if fcnt < state.last_fcnt and state.last_fcnt > 60000:
                alerts.append("ℹ️ FCnt rollover detected")
            elif fcnt <= state.last_fcnt:
                # Duplicate or out-of-order FCnt
                if fcnt == state.last_fcnt:
                    state.duplicate_count += 1
                    alerts.append(f"⚠️ Duplicate FCnt ({fcnt}) - retry #{state.duplicate_count}")
                else:
                    alerts.append(f"⚠️ FCnt went backwards: {state.last_fcnt} → {fcnt}")
            else:
                gap = fcnt - state.last_fcnt
                if gap > self.MAX_FCNT_GAP:
                    alerts.append(f"⚠️ Large FCnt gap of {gap} - significant packet loss")
                elif gap > 1:
                    alerts.append(f"⚠️ FCnt gap of {gap} - possible packet loss")
                    
        # Track FCnt sequence for pattern analysis
        state.fcnt_sequence.append(fcnt)
        if len(state.fcnt_sequence) > self.FCNT_HISTORY_SIZE:
            state.fcnt_sequence.pop(0)
            
        return alerts
    
    def analyze_timing(self, dev_eui: str, timestamp: datetime) -> List[str]:
        """Analyze message timing for anomalies"""
        alerts = []
        state = self.device_states[dev_eui]
        
        if state.last_time is not None:
            time_diff = (timestamp - state.last_time).total_seconds()
            
            if time_diff < 0:
                alerts.append("⚠️ Message timestamp is in the past")
            elif time_diff > self.MAX_TIME_GAP:
                alerts.append(f"⚠️ Long delay of {time_diff:.1f}s (expected ~{self.EXPECTED_INTERVAL}s)")
            elif time_diff < 1:
                alerts.append("⚠️ Messages arriving too quickly (<1s apart)")
                
        return alerts
    
    def analyze_rf_quality(self, rssi: float, snr: float, gateway_count: int = 1) -> List[str]:
        """Analyze RF signal quality"""
        alerts = []
        
        if rssi < self.RSSI_THRESHOLD:
            alerts.append(f"⚠️ Low RSSI ({rssi} dBm) - weak signal or interference")
        elif rssi > -30:
            alerts.append(f"⚠️ Unusually high RSSI ({rssi} dBm) - possible near-field interference")
            
        if snr < self.SNR_THRESHOLD:
            alerts.append(f"⚠️ Low SNR ({snr} dB) - noise or interference")
        elif snr > 10:
            alerts.append(f"ℹ️ Excellent SNR ({snr} dB)")
            
        if gateway_count == 0:
            alerts.append("⚠️ No gateways received this message")
        elif gateway_count > 10:
            alerts.append(f"ℹ️ Message received by {gateway_count} gateways")
            
        return alerts
    
    def analyze_payload_patterns(self, dev_eui: str, decoded_string: str, count: Optional[int]) -> List[str]:
        """Analyze payload for suspicious patterns"""
        alerts = []
        state = self.device_states[dev_eui]
        
        # Check for repeated identical payloads
        if decoded_string == state.last_string and decoded_string != "":
            alerts.append("⚠️ Identical payload repeated - possible device malfunction")
            
        # Check counter progression if available
        if count is not None and state.last_count is not None:
            if count == state.last_count:
                alerts.append("⚠️ Payload counter unchanged")
            elif count < state.last_count:
                alerts.append("⚠️ Payload counter decreased")
                
        # Check for empty or minimal content
        if len(decoded_string.strip()) == 0:
            alerts.append("⚠️ Empty decoded payload")
        elif len(decoded_string.strip()) < 3:
            alerts.append("⚠️ Very short payload - possible truncation")
            
        return alerts
    
    def analyze_uplink(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis function"""
        # Extract data from TTN payload
        dev_eui = data.get("end_device_ids", {}).get("dev_eui", "unknown")
        fcnt = data.get("uplink_message", {}).get("f_cnt")
        payload = data.get("uplink_message", {}).get("frm_payload", "")
        received_at = data.get("uplink_message", {}).get("received_at", "")
        
        # Extract metadata
        uplink_msg = data.get("uplink_message", {})
        rx_metadata = uplink_msg.get("rx_metadata", [])
        
        # Get first gateway's metadata
        primary_metadata = rx_metadata[0] if rx_metadata else {}
        rssi = primary_metadata.get("rssi", -999)
        snr = primary_metadata.get("snr", -999)
        gateway_count = len(rx_metadata)
        
        # Initialize device state if needed
        if dev_eui not in self.device_states:
            self.device_states[dev_eui] = DeviceState()
            self.device_states[dev_eui].first_seen = datetime.now(timezone.utc)
            
        state = self.device_states[dev_eui]
        state.total_messages += 1
        
        alerts = []
        
        # Parse timestamp
        timestamp, time_alerts = self.parse_timestamp(received_at)
        alerts.extend(time_alerts)
        
        # Decode payload
        decoded_string, count, payload_alerts = self.decode_payload(payload)
        alerts.extend(payload_alerts)
        
        # Analyze different aspects
        alerts.extend(self.analyze_fcnt(dev_eui, fcnt))
        alerts.extend(self.analyze_timing(dev_eui, timestamp))
        alerts.extend(self.analyze_rf_quality(rssi, snr, gateway_count))
        alerts.extend(self.analyze_payload_patterns(dev_eui, decoded_string, count))
        
        # Check for data rate and spreading factor anomalies
        settings = uplink_msg.get("settings", {})
        data_rate = settings.get("data_rate", {})
        spreading_factor = data_rate.get("lora", {}).get("spreading_factor")
        
        if spreading_factor and spreading_factor > 10:
            alerts.append(f"⚠️ High spreading factor (SF{spreading_factor}) - poor link quality")
        
        # Update device state
        state.last_fcnt = fcnt if isinstance(fcnt, int) else state.last_fcnt
        state.last_string = decoded_string
        state.last_count = count
        state.last_time = timestamp
        state.last_rssi = rssi
        state.last_snr = snr
        
        # Log comprehensive information
        logger.info(f"DevEUI: {dev_eui} | FCnt: {fcnt} | RSSI: {rssi} dBm | SNR: {snr} dB | Gateways: {gateway_count}")
        logger.info(f"Payload: '{decoded_string}' | Count: {count}")
        
        for alert in alerts:
            logger.warning(f"  {alert}")
            
        return {
            "status": "received",
            "device_eui": dev_eui,
            "fcnt": fcnt,
            "text": decoded_string,
            "count": count,
            "rssi": rssi,
            "snr": snr,
            "gateway_count": gateway_count,
            "alerts": alerts,
            "timestamp": timestamp.isoformat(),
            "device_stats": {
                "total_messages": state.total_messages,
                "duplicate_count": state.duplicate_count,
                "first_seen": state.first_seen.isoformat() if state.first_seen else None
            }
        }

# Global analyzer instance
analyzer = UplinkAnalyzer()

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

@app.route("/devices", methods=["GET"])
def get_devices():
    """Get status of all tracked devices"""
    devices = {}
    for dev_eui, state in analyzer.device_states.items():
        devices[dev_eui] = {
            "total_messages": state.total_messages,
            "duplicate_count": state.duplicate_count,
            "last_fcnt": state.last_fcnt,
            "last_seen": state.last_time.isoformat() if state.last_time else None,
            "first_seen": state.first_seen.isoformat() if state.first_seen else None,
            "last_rssi": state.last_rssi,
            "last_snr": state.last_snr
        }
    return jsonify(devices)

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "tracked_devices": len(analyzer.device_states)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)