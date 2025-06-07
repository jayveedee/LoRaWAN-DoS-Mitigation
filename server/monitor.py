from flask import Flask, request, jsonify
import base64
import json
import csv
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from threading import Thread, Lock
import time
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@dataclass
class DeviceStatistics:
    """Statistics for each device"""
    dev_eui: str
    total_messages: int = 0
    duplicate_count: int = 0
    fcnt_gaps_count: int = 0
    fcnt_gaps_total: int = 0
    payload_count_gaps: int = 0
    timing_anomalies: int = 0
    rf_quality_good: int = 0  # RSSI > -100 and SNR > -5
    rf_quality_poor: int = 0  # RSSI < -115 or SNR < -10
    rf_quality_bad: int = 0   # RSSI < -120 or SNR < -15
    payload_empty: int = 0
    payload_repeated: int = 0
    payload_corruption: int = 0
    timestamp_errors: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    avg_rssi: float = 0.0
    avg_snr: float = 0.0
    min_rssi: float = 0.0
    max_rssi: float = -200.0
    min_snr: float = 0.0
    max_snr: float = -50.0
    gateway_count_total: int = 0
    messages_last_hour: int = 0
    messages_last_day: int = 0

class DeviceState:
    """Track state for each device"""
    def __init__(self):
        self.last_fcnt: Optional[int] = None
        self.last_string: str = ""
        self.last_count: Optional[int] = None
        self.last_time: Optional[datetime] = None
        self.last_rssi: Optional[float] = None
        self.last_snr: Optional[float] = None
        self.fcnt_sequence: List[int] = []
        self.rssi_history: List[float] = []
        self.snr_history: List[float] = []
        self.message_times: List[datetime] = []
        self.stats: DeviceStatistics = None
        
    def initialize_stats(self, dev_eui: str):
        if self.stats is None:
            self.stats = DeviceStatistics(dev_eui=dev_eui)
            self.stats.first_seen = datetime.now(timezone.utc).isoformat()

class UplinkAnalyzer:
    """Analyze uplink messages for anomalies with comprehensive statistics"""
    
    def __init__(self):
        self.device_states: Dict[str, DeviceState] = {}
        self.stats_lock = Lock()
        self.csv_dir = "statistics"
        self.ensure_csv_directory()
        
        # Thresholds for anomaly detection
        self.RSSI_THRESHOLD = -115
        self.SNR_THRESHOLD = -10
        self.RSSI_GOOD = -100
        self.SNR_GOOD = -5
        self.RSSI_BAD = -120
        self.SNR_BAD = -15
        self.MAX_TIME_GAP = 20
        self.EXPECTED_INTERVAL = 10
        self.MAX_FCNT_GAP = 10
        self.FCNT_HISTORY_SIZE = 10
        self.HISTORY_SIZE = 100
        
        # Start periodic statistics saving
        self.start_periodic_save()
        
    def ensure_csv_directory(self):
        """Create statistics directory if it doesn't exist"""
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)
    
    def start_periodic_save(self):
        """Start background thread to save statistics periodically"""
        def save_periodically():
            while True:
                time.sleep(300)  # Save every 5 minutes
                self.save_statistics_to_csv()
                
        thread = Thread(target=save_periodically, daemon=True)
        thread.start()
    
    def save_statistics_to_csv(self):
        """Save current statistics to CSV file"""
        with self.stats_lock:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.csv_dir, f"device_statistics_{timestamp}.csv")
            
            try:
                with open(filename, 'w', newline='') as csvfile:
                    if not self.device_states:
                        return
                        
                    # Get field names from the first device's stats
                    first_device = next(iter(self.device_states.values()))
                    if first_device.stats is None:
                        return
                        
                    fieldnames = list(asdict(first_device.stats).keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for dev_eui, state in self.device_states.items():
                        if state.stats:
                            # Update real-time statistics before saving
                            self.update_realtime_stats(state)
                            writer.writerow(asdict(state.stats))
                
                logger.info(f"Statistics saved to {filename}")
                
                # Also save a "latest" file for easy access
                latest_filename = os.path.join(self.csv_dir, "latest_statistics.csv")
                with open(filename, 'r') as src, open(latest_filename, 'w') as dst:
                    dst.write(src.read())
                    
            except Exception as e:
                logger.error(f"Error saving statistics: {e}")
    
    def update_realtime_stats(self, state: DeviceState):
        """Update real-time calculated statistics"""
        if not state.stats:
            return
            
        # Calculate averages
        if state.rssi_history:
            state.stats.avg_rssi = sum(state.rssi_history) / len(state.rssi_history)
            state.stats.min_rssi = min(state.rssi_history)
            state.stats.max_rssi = max(state.rssi_history)
            
        if state.snr_history:
            state.stats.avg_snr = sum(state.snr_history) / len(state.snr_history)
            state.stats.min_snr = min(state.snr_history)
            state.stats.max_snr = max(state.snr_history)
        
        # Calculate messages in time windows
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        state.stats.messages_last_hour = sum(1 for t in state.message_times if t > hour_ago)
        state.stats.messages_last_day = sum(1 for t in state.message_times if t > day_ago)
        
        state.stats.last_seen = now.isoformat()
    
    def parse_timestamp(self, timestamp_str: str) -> Tuple[datetime, List[str]]:
        """Parse TTN timestamp with error handling"""
        alerts = []
        try:
            clean_time = timestamp_str.replace("Z", "").split(".")
            if len(clean_time) == 2:
                time_part, nano = clean_time
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
            
            if len(raw_bytes) == 0:
                alerts.append("⚠️ Zero-length decoded payload")
                return "", None, alerts
            elif len(raw_bytes) > 51:
                alerts.append(f"⚠️ Payload size ({len(raw_bytes)}) exceeds LoRaWAN limits")
            
            if len(raw_bytes) > 1:
                decoded_string = raw_bytes[:-1].decode("utf-8").strip()
                count = raw_bytes[-1]
            else:
                decoded_string = raw_bytes.decode("utf-8").strip()
                count = None
                
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
            
        if fcnt > 65535:
            alerts.append("⚠️ FCnt exceeds 16-bit limit")
            
        if state.last_fcnt is not None:
            if fcnt < state.last_fcnt and state.last_fcnt > 60000:
                alerts.append("ℹ️ FCnt rollover detected")
            elif fcnt <= state.last_fcnt:
                if fcnt == state.last_fcnt:
                    state.stats.duplicate_count += 1
                    alerts.append(f"⚠️ Duplicate FCnt ({fcnt}) - retry #{state.stats.duplicate_count}")
                else:
                    alerts.append(f"⚠️ FCnt went backwards: {state.last_fcnt} → {fcnt}")
            else:
                gap = fcnt - state.last_fcnt
                if gap > 1:
                    state.stats.fcnt_gaps_count += 1
                    state.stats.fcnt_gaps_total += gap - 1
                    
                if gap > self.MAX_FCNT_GAP:
                    alerts.append(f"⚠️ Large FCnt gap of {gap} - significant packet loss")
                elif gap > 1:
                    alerts.append(f"⚠️ FCnt gap of {gap} - possible packet loss")
                    
        state.fcnt_sequence.append(fcnt)
        if len(state.fcnt_sequence) > self.FCNT_HISTORY_SIZE:
            state.fcnt_sequence.pop(0)
            
        return alerts
    
    def analyze_timing(self, dev_eui: str, timestamp: datetime) -> List[str]:
        """Analyze message timing for anomalies"""
        alerts = []
        state = self.device_states[dev_eui]
        
        # Add to message times history
        state.message_times.append(timestamp)
        if len(state.message_times) > self.HISTORY_SIZE:
            state.message_times.pop(0)
        
        if state.last_time is not None:
            time_diff = (timestamp - state.last_time).total_seconds()
            
            if time_diff < 0:
                alerts.append("⚠️ Message timestamp is in the past")
                state.stats.timing_anomalies += 1
            elif time_diff > self.MAX_TIME_GAP:
                alerts.append(f"⚠️ Long delay of {time_diff:.1f}s (expected ~{self.EXPECTED_INTERVAL}s)")
                state.stats.timing_anomalies += 1
            elif time_diff < 1:
                alerts.append("⚠️ Messages arriving too quickly (<1s apart)")
                state.stats.timing_anomalies += 1
                
        return alerts
    
    def analyze_rf_quality(self, dev_eui: str, rssi: float, snr: float, gateway_count: int = 1) -> List[str]:
        """Analyze RF signal quality and update statistics"""
        alerts = []
        state = self.device_states[dev_eui]
        
        # Update RF history
        if rssi != -999:
            state.rssi_history.append(rssi)
            if len(state.rssi_history) > self.HISTORY_SIZE:
                state.rssi_history.pop(0)
                
        if snr != -999:
            state.snr_history.append(snr)
            if len(state.snr_history) > self.HISTORY_SIZE:
                state.snr_history.pop(0)
        
        # Update gateway count statistics
        state.stats.gateway_count_total += gateway_count
        
        # Categorize RF quality
        good_signal = rssi > self.RSSI_GOOD and snr > self.SNR_GOOD
        poor_signal = rssi < self.RSSI_THRESHOLD or snr < self.SNR_THRESHOLD
        bad_signal = rssi < self.RSSI_BAD or snr < self.SNR_BAD
        
        if bad_signal:
            state.stats.rf_quality_bad += 1
        elif poor_signal:
            state.stats.rf_quality_poor += 1
        elif good_signal:
            state.stats.rf_quality_good += 1
        
        # Generate alerts
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
            state.stats.payload_repeated += 1
            alerts.append("⚠️ Identical payload repeated - possible device malfunction")
            
        # Check counter progression if available
        if count is not None and state.last_count is not None:
            if count == state.last_count:
                alerts.append("⚠️ Payload counter unchanged")
            elif count < state.last_count:
                state.stats.payload_count_gaps += 1
                alerts.append("⚠️ Payload counter decreased")
                
        # Check for empty or minimal content
        if len(decoded_string.strip()) == 0:
            state.stats.payload_empty += 1
            alerts.append("⚠️ Empty decoded payload")
        elif len(decoded_string.strip()) < 3:
            alerts.append("⚠️ Very short payload - possible truncation")
            
        return alerts
    
    def analyze_uplink(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis function with comprehensive statistics tracking"""
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
        
        with self.stats_lock:
            # Initialize device state if needed
            if dev_eui not in self.device_states:
                self.device_states[dev_eui] = DeviceState()
                self.device_states[dev_eui].initialize_stats(dev_eui)
                
            state = self.device_states[dev_eui]
            state.stats.total_messages += 1
        
        alerts = []
        
        # Parse timestamp
        timestamp, time_alerts = self.parse_timestamp(received_at)
        alerts.extend(time_alerts)
        if time_alerts:
            state.stats.timestamp_errors += 1
        
        # Decode payload
        decoded_string, count, payload_alerts = self.decode_payload(payload)
        alerts.extend(payload_alerts)
        if any("corruption" in alert for alert in payload_alerts):
            state.stats.payload_corruption += 1
        
        # Analyze different aspects
        alerts.extend(self.analyze_fcnt(dev_eui, fcnt))
        alerts.extend(self.analyze_timing(dev_eui, timestamp))
        alerts.extend(self.analyze_rf_quality(dev_eui, rssi, snr, gateway_count))
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
            "device_stats": asdict(state.stats) if state.stats else {}
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
    """Get status of all tracked devices with enhanced statistics"""
    with analyzer.stats_lock:
        devices = {}
        for dev_eui, state in analyzer.device_states.items():
            if state.stats:
                analyzer.update_realtime_stats(state)
                devices[dev_eui] = asdict(state.stats)
        return jsonify(devices)

@app.route("/statistics/save", methods=["POST"])
def save_statistics():
    """Manually trigger statistics save"""
    analyzer.save_statistics_to_csv()
    return jsonify({"status": "Statistics saved successfully"})

@app.route("/statistics/reset", methods=["POST"])
def reset_statistics():
    """Reset all statistics (use with caution)"""
    with analyzer.stats_lock:
        analyzer.device_states.clear()
    return jsonify({"status": "Statistics reset successfully"})

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "tracked_devices": len(analyzer.device_states),
        "statistics_dir": analyzer.csv_dir
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)