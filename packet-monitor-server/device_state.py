"""
Add statistics later by just adding new fields here and updating the analyzer—no changes needed in the server.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class DeviceState:
    dev_eui: str
    # last-seen values
    last_fcnt:  Optional[int]       = None
    last_string: str               = ""
    last_count:  Optional[int]      = None
    last_time:   Optional[datetime] = None
    last_rssi:   Optional[float]    = None
    last_snr:    Optional[float]    = None
    # rolling histories (small, just for quick stats)
    fcnt_sequence: List[int]   = field(default_factory=list)
    rssi_history:  List[float] = field(default_factory=list)
    snr_history:   List[float] = field(default_factory=list)