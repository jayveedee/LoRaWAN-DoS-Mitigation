#!/usr/bin/env python3
"""
LoRa Statistics Analysis Runner
Demonstrates how to use the enhanced packet analyzer and visualizer
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

def test_analyzer_endpoints():
    """Test the analyzer endpoints to ensure it's working"""
    base_url = "http://localhost:5000"
    
    print("Testing analyzer endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health endpoint working")
            print(f"  Status: {response.json()}")
        else:
            print("✗ Health endpoint failed")
            return False
            
        # Test devices endpoint
        response = requests.get(f"{base_url}/devices")
        if response.status_code == 200:
            devices = response.json()
            print(f"✓ Devices endpoint working ({len(devices)} devices tracked)")
        else:
            print("✗ Devices endpoint failed")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to analyzer - make sure it's running on port 5000")
        return False
    except Exception as e:
        print(f"✗ Error testing endpoints: {e}")
        return False

def send_test_message():
    """Send a test TTN message to the analyzer"""
    base_url = "http://localhost:5000"
    
    # Sample TTN uplink message
    test_message = {
        "end_device_ids": {
            "dev_eui": "test_device_001"
        },
        "uplink_message": {
            "f_cnt": 123,
            "frm_payload": "SGVsbG8gV29ybGQh",  # "Hello World!" in base64
            "received_at": datetime.now().isoformat() + "Z",
            "rx_metadata": [
                {
                    "rssi": -85,
                    "snr": 7.5
                }
            ],
            "settings": {
                "data_rate": {
                    "lora": {
                        "spreading_factor": 7
                    }
                }
            }
        }
    }
    
    try:
        response = requests.post(f"{base_url}/uplink", json=test_message)
        if response.status_code == 200:
            result = response.json()
            print("✓ Test message sent successfully")
            print(f"  Device: {result.get('device_eui')}")
            print(f"  Text: {result.get('text')}")
            print(f"  Alerts: {len(result.get('alerts', []))}")
            return True
        else:
            print(f"✗ Test message failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error sending test message: {e}")
        return False

def run_statistics_analysis():
    """Run the statistics visualizer"""
    print("\nRunning statistics analysis...")
    
    try:
        # Import and run the visualizer
        from visualizer import LoRaStatisticsVisualizer
        
        visualizer = LoRaStatisticsVisualizer()
        visualizer.run_full_analysis()
        
        return True
        
    except ImportError:
        print("✗ Cannot import statistics_visualizer - make sure the file exists")
        return False
    except FileNotFoundError as e:
        print(f"✗ Statistics files not found: {e}")
        print("  Make sure the packet analyzer has been running and collecting data")
        return False
    except Exception as e:
        print(f"✗ Error running analysis: {e}")
        return False

def manual_save_statistics():
    """Manually trigger statistics save"""
    base_url = "http://localhost:5000"
    
    try:
        response = requests.post(f"{base_url}/statistics/save")
        if response.status_code == 200:
            print("✓ Statistics saved manually")
            return True
        else:
            print(f"✗ Failed to save statistics: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error saving statistics: {e}")
        return False

def main():
    """Main runner function"""
    print("LoRa Statistics Analysis Runner")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            # Test the analyzer
            if test_analyzer_endpoints():
                print("\nSending test message...")
                send_test_message()
                
        elif command == "analyze":
            # Run analysis only
            run_statistics_analysis()
            
        elif command == "save":
            # Manually save statistics
            manual_save_statistics()
            
        elif command == "demo":
            # Full demo workflow
            print("Running full demo workflow...\n")
            
            # 1. Test analyzer
            if not test_analyzer_endpoints():
                print("Analyzer not available - please start it first")
                return
            
            # 2. Send some test messages
            print("\nSending test messages...")
            for i in range(5):
                test_message = {
                    "end_device_ids": {
                        "dev_eui": f"demo_device_{i:03d}"
                    },
                    "uplink_message": {
                        "f_cnt": 100 + i,
                        "frm_payload": f"VGVzdCBtZXNzYWdlICN7aX0=",  # Test message base64
                        "received_at": datetime.now().isoformat() + "Z",
                        "rx_metadata": [
                            {
                                "rssi": -90 + (i * 2),  # Varying RSSI
                                "snr": 5 + i
                            }
                        ]
                    }
                }
                
                response = requests.post("http://localhost:5000/uplink", json=test_message)
                if response.status_code == 200:
                    print(f"  ✓ Sent message {i+1}/5")
                else:
                    print(f"  ✗ Failed to send message {i+1}/5")
                
                time.sleep(1)  # Small delay between messages
            
            # 3. Save statistics
            print("\nSaving statistics...")
            manual_save_statistics()
            
            # 4. Run analysis
            print("\nRunning analysis...")
            run_statistics_analysis()
            
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_usage()

def print_usage():
    """Print usage information"""
    print("\nUsage:")
    print("  python run_analysis.py test     - Test analyzer endpoints")
    print("  python run_analysis.py analyze  - Run statistics analysis")
    print("  python run_analysis.py save     - Manually save statistics")
    print("  python run_analysis.py demo     - Run full demo workflow")
    print("\nMake sure the packet analyzer is running on port 5000 first!")
    print("Example: python packetAnalyzer.py")

if __name__ == "__main__":
    main()