"""
Add statistics later by just adding new fields here and updating the analyzer—no changes needed in the server.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class WindowStats:          # ➊ new
    msgs:               int = 0
    dup_fcnt:           int = 0
    fcnt_gap:           int = 0
    long_delay:         int = 0
    total_delay:        float = 0.0
    poor_rf:            int = 0
    good_rf:            int = 0
    same_payload:       int = 0
    counter_decrease:   int = 0

@dataclass
class DeviceState:
    dev_eui: str

    last_fcnt:  Optional[int]       = None
    last_string: str               = ""
    last_count:  Optional[int]      = None
    last_time:   Optional[datetime] = None
    last_rssi:   Optional[float]    = None
    last_snr:    Optional[float]    = None

    fcnt_sequence: List[int]   = field(default_factory=list)
    rssi_history:  List[float] = field(default_factory=list)
    snr_history:   List[float] = field(default_factory=list)

    window: WindowStats            = field(default_factory=WindowStats)