import hid
import serial
import threading
import time
import struct
from dataclasses import dataclass
from typing import Optional, Callable, List

class ControlState:
    """Normalized control state from RadioMaster Pocket"""
    channels: List[float]  # 16 channels, -1.0 to 1.0 range
    switches: int          # Button states bitfield
    timestamp: float
    sequence: int

