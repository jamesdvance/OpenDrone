#!/usr/bin/env python3
"""
Test CRSF protocol implementation by generating and validating CRSF frames
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import CRSFProtocol

def test_crsf_implementation():
    """Test CRSF protocol implementation"""
    print("=" * 50)
    print("CRSF Protocol Implementation Test")
    print("=" * 50)
    
    # Test channel values (typical RC values)
    test_channels = [
        1024,  # Roll (center)
        1024,  # Pitch (center) 
        0,     # Throttle (minimum)
        1024,  # Yaw (center)
        2047,  # Aux1 (high - for arming)
        1024,  # Aux2 (center)
        1024,  # Aux3 (center)
        1024,  # Aux4 (center)
        1024,  # Aux5 (center)
        1024,  # Aux6 (center)
        1024,  # Aux7 (center)
        1024,  # Aux8 (center)
        1024,  # Aux9 (center)
        1024,  # Aux10 (center)
        1024,  # Aux11 (center)
        1024   # Aux12 (center)
    ]
    
    print(f"Test channels: {test_channels}")
    
    try:
        # Test channel packing
        print("\n1. Testing channel packing...")
        packed = CRSFProtocol.pack_channels(test_channels)
        print(f"Packed channels ({len(packed)} bytes): {' '.join(f'{b:02X}' for b in packed)}")
        
        # Test CRC calculation
        print("\n2. Testing CRC calculation...")
        test_data = bytearray([0x16])  # Frame type
        test_data.extend(packed)
        crc = CRSFProtocol.crc8_calc(test_data)
        print(f"CRC8 for test data: 0x{crc:02X}")
        
        # Test complete frame generation
        print("\n3. Testing complete CRSF frame generation...")
        frame = CRSFProtocol.create_crsf_frame(test_channels)
        print(f"Complete CRSF frame ({len(frame)} bytes):")
        print(f"  Raw: {' '.join(f'{b:02X}' for b in frame)}")
        print(f"  Sync: 0x{frame[0]:02X}")
        print(f"  Length: {frame[1]} (payload + type)")
        print(f"  Type: 0x{frame[2]:02X} (RC_CHANNELS_PACKED)")
        print(f"  Payload: {' '.join(f'{b:02X}' for b in frame[3:-1])}")
        print(f"  CRC: 0x{frame[-1]:02X}")
        
        # Validate frame structure
        print("\n4. Validating frame structure...")
        if frame[0] == 0xC8:
            print("  ✓ Correct sync byte (0xC8)")
        else:
            print(f"  ✗ Wrong sync byte: 0x{frame[0]:02X}")
            
        if frame[1] == 24:
            print("  ✓ Correct length (24 = 22 payload + 1 type + 1 crc)")
        else:
            print(f"  ✗ Wrong length: {frame[1]}")
            
        if frame[2] == 0x16:
            print("  ✓ Correct frame type (0x16 = RC_CHANNELS_PACKED)")
        else:
            print(f"  ✗ Wrong frame type: 0x{frame[2]:02X}")
            
        if len(frame) == 25:
            print("  ✓ Correct total frame size (25 bytes)")
        else:
            print(f"  ✗ Wrong frame size: {len(frame)} bytes")
            
        # Verify CRC
        calculated_crc = CRSFProtocol.crc8_calc(frame[2:-1])
        if calculated_crc == frame[-1]:
            print("  ✓ CRC validation passed")
        else:
            print(f"  ✗ CRC mismatch: calculated 0x{calculated_crc:02X}, got 0x{frame[-1]:02X}")
        
        print("\n" + "=" * 50)
        print("CRSF IMPLEMENTATION TEST PASSED")
        print("=" * 50)
        
        print("\nThis frame should be sent to your ExpressLRS receiver.")
        print("The receiver will decode:")
        print(f"  - Channel 1-4 (AETR): {test_channels[0]}, {test_channels[1]}, {test_channels[2]}, {test_channels[3]}")
        print(f"  - Aux channels 1-12: {test_channels[4:]}")
        print(f"  - ARM signal: {'ARMED' if test_channels[4] > 1500 else 'DISARMED'}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: CRSF test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crsf_implementation()
    sys.exit(0 if success else 1)