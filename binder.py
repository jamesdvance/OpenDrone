import serial
import time
import sys

def crc8_dvb_s2(data, crc=0):
    """Compute CRC8-DVB-S2 checksum for ELRS packets"""
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0xD5) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def send_bind_command(ser):
    """Send CRSF bind command to TX module"""
    # CRSF bind packet structure:
    # [Address][Length][Type][CommandID][Payload][CRC]
    # Address: 0xEE (CRSF transmitter)
    # Type: 0x21 (ELRS specific command)
    # CommandID: 0x01 (Bind command)
    # Payload: [0x00, 0x00] (Binding parameters)
    
    # Build packet components
    address = bytes([0xEE])
    packet_type = bytes([0x21])
    command_id = bytes([0x01])
    payload = bytes([0x00, 0x00])
    
    # Assemble data for CRC calculation
    data_for_crc = packet_type + command_id + payload
    
    # Calculate CRC
    crc = crc8_dvb_s2(data_for_crc)
    
    # Full packet structure
    packet = (
        address +
        bytes([len(data_for_crc) + 1]) +  # Length (type + payload + CRC)
        data_for_crc +
        bytes([crc])
    )
    
    # Send packet
    ser.write(packet)
    print(f"Sent bind command: {packet.hex(' ').upper()}")

def main():
    # Configure your serial port (change as needed)
    port = "/dev/ttyUSB0"  # Linux example
    # port = "COM3"        # Windows example
    
    try:
        # Initialize serial connection
        ser = serial.Serial(
            port=port,
            baudrate=420000,   # ELRS standard baud rate
            timeout=1
        )
        print(f"Connected to {ser.name} at {ser.baudrate} baud")
        
        # Send bind command 5 times for reliability
        for i in range(5):
            send_bind_command(ser)
            time.sleep(0.2)
            
        print("\nBinding mode activated on TX module!")
        print("Now put your BetaFPV Air75 receiver in binding mode:")
        print("1. Power OFF the drone")
        print("2. Press and hold the bind button on the Air75 receiver")
        print("3. Power ON the drone while holding the button")
        print("4. Release button when LED blinks rapidly")
        print("\nBinding should complete within 10 seconds")
        
    except serial.SerialException as e:
        print(f"\nERROR: Could not open serial port {port}")
        print(f"Details: {str(e)}")
        print("Check your connection and port name")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("\nSerial connection closed")

if __name__ == "__main__":
    main()