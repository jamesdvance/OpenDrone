# crsf_serial.py
# Requirements: pip install pyserial
import serial
import time
from typing import List, Generator, Tuple

# --- CRC8 implementation (poly 0xD5) ---
# table-based for speed (table derived for poly 0xD5, same as many community implementations)
_CRC8_TABLE = [
    0x00,0xD5,0x7F,0xAA,0xFE,0x2B,0x81,0x54,0x29,0xFC,0x56,0x83,0xD7,0x02,0xA8,0x7D,
    0x52,0x87,0x2D,0xF8,0xAC,0x79,0xD3,0x06,0x7B,0xAE,0x04,0xD1,0x85,0x50,0xFA,0x2F,
    0xA4,0x71,0xDB,0x0E,0x5A,0x8F,0x25,0xF0,0x8D,0x58,0xF2,0x27,0x73,0xA6,0x0C,0xD9,
    0xF6,0x23,0x89,0x5C,0x08,0xDD,0x77,0xA2,0xDF,0x0A,0xA0,0x75,0x21,0xF4,0x5E,0x8B,
    0x9D,0x48,0xE2,0x37,0x63,0xB6,0x1C,0xC9,0xB4,0x61,0xCB,0x1E,0x4A,0x9F,0x35,0xE0,
    0xCF,0x1A,0xB0,0x65,0x31,0xE4,0x4E,0x9B,0xE6,0x33,0x99,0x4C,0x18,0xCD,0x67,0xB2,
    0x39,0xEC,0x46,0x93,0xC7,0x12,0xB8,0x6D,0x10,0xC5,0x6F,0xBA,0xEE,0x3B,0x91,0x44,
    0x6B,0xBE,0x14,0xC1,0x95,0x40,0xEA,0x3F,0x42,0x97,0x3D,0xE8,0xBC,0x69,0xC3,0x16,
    0x3E,0xEB,0x41,0x94,0xC0,0x15,0xBF,0x6A,0x17,0xC2,0x68,0xBD,0xE9,0x3C,0x96,0x43,
    0xE8,0x3D,0x97,0x42,0x16,0xC3,0x69,0xBC,0xC1,0x14,0xBE,0x6B,0x3F,0xEA,0x40,0x95,
    0xB1,0x64,0xCE,0x1B,0x4F,0x9A,0x30,0xE5,0x98,0x4D,0xE7,0x32,0x66,0xB3,0x19,0xCC,
    0xE3,0x36,0x9C,0x49,0x1D,0xC8,0x62,0xB7,0xCA,0x1F,0xB5,0x60,0x34,0xE1,0x4B,0x9E,
    0x7E,0xAB,0x01,0xD4,0x80,0x55,0xFF,0x2A,0x57,0x82,0x28,0xFD,0xA9,0x7C,0xD6,0x03,
    0xFE,0x2B,0x81,0x54,0x00,0xD5,0x7F,0xAA,0xD7,0x02,0xA8,0x7D,0x29,0xFC,0x56,0x83,
    0xA8,0x7D,0xD7,0x02,0x56,0x83,0x29,0xFC,0x81,0x54,0xFE,0x2B,0x7F,0xAA,0x00,0xD5,
    0x4F,0x9A,0x30,0xE5,0xB1,0x64,0xCE,0x1B,0x66,0xB3,0x19,0xCC,0x98,0x4D,0xE7,0x32,
]

def crc8_bytes(data: bytes) -> int:
    """CRC8 (poly 0xD5) for CRSF: compute over TYPE + PAYLOAD bytes."""
    crc = 0
    for b in data:
        crc = _CRC8_TABLE[(crc ^ b) & 0xFF]
    return crc & 0xFF

# --- pack_channels: 16 channels of 11-bit values -> 22 bytes (common CRSF packing) ---
def pack_channels(channels: List[int]) -> bytes:
    """
    channels: list of 16 integers, each 0..2047 (11 bits). Many FWs use 992..2000 ticks mapping;
    caller is responsible for converting PWM to ticks if needed.
    Returns 22 bytes payload for CRSF_FRAMETYPE_RC_CHANNELS_PACKED (0x16).
    """
    if len(channels) != 16:
        raise ValueError("pack_channels expects 16 channels")
    # ensure 11-bit values
    vals = [c & 0x7FF for c in channels]
    bits = ''.join(f'{v:011b}' for v in reversed(vals))  # reversed order like many references
    # produce 22 bytes from bitstream (MSB first groups)
    bytes_out = []
    for i in range(22):
        byte_bits = bits[i*8:(i+1)*8]
        if len(byte_bits) < 8:
            byte_bits = byte_bits.ljust(8, '0')
        bytes_out.append(int(byte_bits, 2))
    bytes_out.reverse()
    return bytes(bytes_out)

# --- CRSF constants ---
CRSF_ADDR_FLIGHT_CONTROLLER = 0xC8
CRSF_ADDR_TRANSMITTER = 0xEE
CRSF_FRAMETYPE_RC_CHANNELS_PACKED = 0x16

class CrsfSerial:
    def __init__(self, port: str, baud: int = 420000, timeout: float = 0.02):
        """
        port: serial device, e.g. '/dev/ttyUSB0' or 'COM3'
        baud: default 420000 (many devices use 420k; some versions use slightly different rates)
        """
        self.ser = serial.Serial(port, baudrate=baud, timeout=timeout)
        # flush any old data
        time.sleep(0.05)
        self.ser.reset_input_buffer()

    def close(self):
        self.ser.close()

    def build_frame(self, dest_addr: int, frame_type: int, payload: bytes) -> bytes:
        """
        Build full CRSF frame bytes: [addr][len][type][payload...][crc]
        len = payload_length + 2 (type + crc included in count as per spec)
        """
        payload_len = len(payload)
        # len field is (type + payload + crc) => payload_len + 2
        length_byte = payload_len + 2
        header = bytes([dest_addr & 0xFF, length_byte & 0xFF, frame_type & 0xFF])
        crc = crc8_bytes(bytes([frame_type]) + payload)
        return header + payload + bytes([crc & 0xFF])

    def send_frame(self, dest_addr: int, frame_type: int, payload: bytes) -> None:
        frame = self.build_frame(dest_addr, frame_type, payload)
        self.ser.write(frame)

    def send_channels(self, channels_11bit: List[int], dest_addr: int = CRSF_ADDR_FLIGHT_CONTROLLER) -> None:
        """
        Pack 16 channels (11-bit each) and send RC_CHANNELS_PACKED packet.
        channels_11bit must be 16-length list of ints 0..2047 (caller converts PWM->ticks).
        """
        packed = pack_channels(channels_11bit)
        self.send_frame(dest_addr, CRSF_FRAMETYPE_RC_CHANNELS_PACKED, packed)

    def read_bytes(self, timeout_s: float = 0.1) -> bytes:
        """Read whatever is available within timeout; return bytes."""
        t0 = time.time()
        out = bytearray()
        while time.time() - t0 < timeout_s:
            n = self.ser.in_waiting
            if n:
                out.extend(self.ser.read(n))
            else:
                time.sleep(0.001)
        return bytes(out)

    def read_frames(self, data: bytes) -> Generator[Tuple[int,int,bytes], None, None]:
        """
        Parse buffer 'data' and yield frames as tuples: (addr, frame_type, payload_bytes).
        This parser scans for plausible frames by reading the addr, len and checking CRC.
        """
        i = 0
        while i + 3 < len(data):
            addr = data[i]
            length = data[i+1]
            # full frame size = 1(addr) + 1(len) + length + 0  -- but length includes type+payload+crc
            total_len = 2 + length
            if i + total_len > len(data):
                # incomplete: break and wait for more bytes
                break
            frame_type = data[i+2]
            payload_len = length - 2  # subtract type+crc
            payload = data[i+3:i+3+payload_len] if payload_len > 0 else b''
            crc_byte = data[i+3+payload_len]
            calc_crc = crc8_bytes(bytes([frame_type]) + payload)
            if crc_byte == calc_crc:
                yield (addr, frame_type, payload)
                i += total_len
            else:
                # CRC mismatch: advance one byte to resync
                i += 1

# Example usage:
if __name__ == "__main__":
    # Example: send a neutral channels frame (example 11-bit values)
    port = "/dev/ttyUSB0"  # change for your OS
    crsf = CrsfSerial(port, baud=420000, timeout=0.02)
    try:
        # Example channels: all mid values (992..~2000 mapping is common; here we fill 1024 center-ish)
        channels = [1024] * 16
        crsf.send_channels(channels)  # sends RC channels packed to flight controller addr (0xC8)

        # Read loop: collect bytes and parse frames
        raw = crsf.read_bytes(timeout_s=0.05)
        for (addr, ftype, payload) in crsf.read_frames(raw):
            print(f"Got frame: addr=0x{addr:02X}, type=0x{ftype:02X}, payload_len={len(payload)}")
    finally:
        crsf.close()
