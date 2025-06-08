"""
Quick smoke-test:
  1. Start `python monitor_server.py`
  2. Run this script
"""
import base64
import datetime as dt
import time
import json
import requests

URL      = "http://localhost:5000/uplink"
DEV_EUI  = "ABCDEF1234567890"

def make_payload(fcnt: int, txt: str = "hello", counter: int = 1,
                 rssi: int = -120, snr: float = -9.0, dt_iso=None):

    # encode <txt><counterByte> as LoRa example
    raw = txt.encode() + bytes([counter])
    b64 = base64.b64encode(raw).decode()

    return {
        "end_device_ids": {"dev_eui": DEV_EUI},
        "uplink_message": {
            "f_cnt": fcnt,
            "frm_payload": b64,
            "received_at": dt_iso or (dt.datetime.utcnow().isoformat() + "Z"),
            "rx_metadata": [
                {"rssi": rssi, "snr": snr}
            ],
        },
    }

cases = [
    make_payload(1, "hello", 1, -80,  5),               # good
    make_payload(1, "hello", 1, -80,  5),               # duplicate FCnt
    make_payload(15, "hello", 1, -120, -12),            # gap + poor RF
    make_payload(16, "hello", 1, -80,  5,               # fast repeat
                 dt_iso=(dt.datetime.utcnow().isoformat() + "Z")),
]

for pk in cases:
    res = requests.post(URL, json=pk, timeout=3)
    print("\n", json.dumps(res.json(), indent=2))
    time.sleep(0.5)      # keep the demo visible
