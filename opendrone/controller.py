import serial
import time
import keyboard
import threading

class CRSFController:

    def __init__(self, port, baud_rate=420000):
        self.ser = serial.Serial(port, baud_rate, timeout=0.1)
        # Initial safe state: throttle=0, controls centered
        self.channels = [1024, 1024, 0, 1024, 1024, 1024, 1024, 1024]
        self.armed = False
        self.running = True

        # Control sensitivity settings (adjust as needed)
        self.STEP_SIZE = 30
        self.THROTTLE_STEP = 40
        self.YAW_STEP = 20
        self.MAX_VALUE = 2047
        self.MIN_VALUE = 0
        self.MID_VALUE = 1024

    def crc8_dvb_s2(self, data, crc=0):
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0xD5) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def send_rc_channels(self):
        payload = bytearray()
        for value in self.channels:
            value = max(self.MIN_VALUE, min(self.MAX_VALUE, value))
            value_16 = (value << 5)
            payload.append(value_16 & 0xFF)
            payload.append((value_16 >> 8) & 0xFF)

        packet_type = bytes([0x16])
        data_for_crc = packet_type + payload
        crc = self.crc8_dvb_s2(data_for_crc)
        packet = bytes([0xEE, len(data_for_crc) + 1]) + data_for_crc + bytes([crc])
        self.ser.write(packet)

    def toggle_arm(self):
        self.armed = not self.armed
        # Set Aux1 (channel 4) to high when armed, low when disarmed
        self.channels[4] = 2047 if self.armed else 1024
        print(f"Drone {'ARMED' if self.armed else 'DISARMED'}")

    def reset_controls(self):
        """Center all controls except throttle"""
        self.channels[0] = self.MID_VALUE # Roll
        self.channels[1] = self.MID_VALUE # Pitch
        self.channels[2] = self.MID_VALUE # Yaw

    def close(self):
        print(f"\nExiting...")
        self.running=False
        time.sleep(0.1)
        # Set throttle to 0 and disarm
        self.channels[2] = 0
        self.armed = False
        self.channels[4] = 1024
        self.send_rc_channels()
        time.sleep(0.1)
        self.ser.close()

    def keyboard_control(self):
        """Handle keyboard input in a separate thread"""
        print("Keyboard control active. Use:")
        print(" W/S: Throttle")
        print(" A/D: Roll")
        print(" UP/DOWN: Pitch")
        print(" SPACE: Arm/Disarm")
        print(" R: Reset controls")
        print(" Q: Quit")

        while self.running:
            # Throttle control (W/S)
            if keyboard.is_pressed("w"):
                self.channels[2] = min(self.MAX_VALUE, self.channels[2] + self.THROTTLE_STEP)
            if keyboard.is_pressed("s"):
                self.channels[2] = max(self.MIN_VALUE, self.channels[2] - self.THROTTLE_STEP)
            
            # Roll control (A/D)
            if keyboard.is_pressed('a'):
                self.channels[0] = max(self.MIN_VALUE, self.channels[0] - self.STEP_SIZE)
            if keyboard.is_pressed('d'):
                self.channels[0] = min(self.MAX_VALUE, self.channels[0] + self.STEP_SIZE)
            
            # Pitch control (Up/Down arrows)
            if keyboard.is_pressed('up'):
                self.channels[1] = min(self.MAX_VALUE, self.channels[1] + self.STEP_SIZE)
            if keyboard.is_pressed('down'):
                self.channels[1] = max(self.MIN_VALUE, self.channels[1] - self.STEP_SIZE)
            
            # Yaw control (Left/Right arrows)
            if keyboard.is_pressed('left'):
                self.channels[3] = max(self.MIN_VALUE, self.channels[3] - self.YAW_STEP)
            if keyboard.is_pressed('right'):
                self.channels[3] = min(self.MAX_VALUE, self.channels[3] + self.YAW_STEP)
            
            # Special functions
            if keyboard.is_pressed('space'):
                self.toggle_arm()
                time.sleep(0.3)  # Debounce
            if keyboard.is_pressed('r'):
                self.reset_controls()
            if keyboard.is_pressed('q'):
                self.close()
                break
            
            time.sleep(0.01)  # 100Hz update rate


# Main execution
if __name__ == "__main__":
    controller = CRSFController(port="/dev/ttyUSB0")  # Update to your serial port
    
    # Start keyboard control in separate thread
    keyboard_thread = threading.Thread(target=controller.keyboard_control)
    keyboard_thread.start()
    
    try:
        # Main loop: Send commands at 50Hz
        while controller.running:
            controller.send_rc_channels()
            time.sleep(0.02)  # 50Hz
            
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()
        keyboard_thread.join()
        print("Program terminated safely")


    

    
