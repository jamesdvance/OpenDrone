# crsf_serial_handling.py

import serial
import time
from typing import List, Generator, Tuple

from crsf_parser import CRSFParser
from crsf_parser.handling import (
    crsf_build_frame,
    crsf_frame_crc,
    crsf_crc
)
from crsf_parser.frames import (
    crsf_header,
    crsf_frame
)
from crsf_parser.payloads import (
    PAYLOADS_SIZE,
    PacketsTypes
)

class CrsfSerial:
    def __init__(self, port: str, baud: int = 420000, timeout: float = 0.02):
        """
        port: serial device, e.g. '/dev/ttyUSB0' or 'COM3'
        baud: default 420000 (common for CRSF)
        timeout: how long serial.read operations block (seconds)
        """
        self.ser = serial.Serial(port, baudrate=baud, timeout=timeout)
        self.parser = CRSFParser()
        time.sleep(0.05)  # small delay to let serial buffers settle
        self.ser.reset_input_buffer()

    def close(self) -> None:
        self.ser.close()

    def send_raw_frame(self, addr: int, frame_type: int, payload: bytes) -> None:
        """
        Build a CRSF frame using payloads.build_frame, then send it.
        """
        frame_bytes = crsf_build_frame(addr, frame_type, payload)
        self.ser.write(frame_bytes)

    def send_channels(self, channels_11bit: List[int], dest_addr: int = ADDR_FLIGHT_CONTROLLER) -> None:
        """
        Send RC_CHANNELS_PACKED frame (type FRAMETYPE_RC_CHANNELS_PACKED).
        channels_11bit: 16 ints, each 0..2047
        """
        if len(channels_11bit) != 16:
            raise ValueError("send_channels(): expected 16 channels")
        payload = create_rc_channels_packed(channels_11bit)
        self.send_raw_frame(dest_addr, FRAMETYPE_RC_CHANNELS_PACKED, payload)

    def read_frames(self, timeout_s: float = 0.1) -> Generator[Tuple[int, int, bytes], None, None]:
        """
        Read from serial for up to timeout_s seconds; yield any parsed frames.
        Each yielded frame is a tuple: (device_addr, type, payload_bytes).
        """
        t_start = time.time()
        while time.time() - t_start < timeout_s:
            # Read one byte, or as many as available
            b = self.ser.read(1)
            if not b:
                continue
            # Note: handling.py’s CRSFParser expects int (0-255) input
            frame = self.parser.update(b[0])
            if frame is not None:
                # frame has attributes device_addr, type, payload
                yield (frame.device_addr, frame.type, frame.payload)

    def send_arm(self, arm_channel_index: int, arm_val: int = 2000, throttle_low_val: int = 0) -> None:
        """
        Convenience: send RC channels with the specified channel index set to the 'arm' value,
        throttle (index 2) set low, others neutral.
        """
        # neutral value: mid-stick ≈ (max/2)
        max11 = 2047
        neutral = max11 // 2

        channels = [neutral] * 16
        # throttle typically channel 3 (index 2)
        channels[2] = throttle_low_val
        # Set arm switch high
        channels[arm_channel_index] = arm_val

        self.send_channels(channels)

# Example usage
if __name__ == "__main__":
    port = "/dev/ttyUSB0"  # change as needed
    cr = CrsfSerial(port)
    try:
        # Suppose your ARM switch is on AUX1 = channel 5 → index 4
        cr.send_arm(arm_channel_index=4, arm_val=1800, throttle_low_val=0)
        print("ARM command frame sent")
        # read some frames (telemetry etc.) for half a second
        for addr, ftype, payload in cr.read_frames(timeout_s=0.5):
            print(f"Received: addr=0x{addr:02X}, type=0x{ftype:02X}, payload={payload.hex()}")
    finally:
        cr.close()
