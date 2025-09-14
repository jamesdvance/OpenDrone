import time
import threading
import keyboard


class KeyboardController:
    def __init__(self, client):
        self.client = client
        self.running = False
        self.keyboard_thread = None
        
        # Control sensitivity settings
        self.STEP_SIZE = 30
        self.THROTTLE_STEP = 40
        self.YAW_STEP = 20

    def start(self):
        """Start keyboard control in a separate thread"""
        if self.keyboard_thread and self.keyboard_thread.is_alive():
            return
            
        self.running = True
        self.keyboard_thread = threading.Thread(target=self._keyboard_control_loop, daemon=True)
        self.keyboard_thread.start()

    def stop(self):
        """Stop keyboard control"""
        self.running = False
        if self.keyboard_thread:
            self.keyboard_thread.join(timeout=1.0)

    def _keyboard_control_loop(self):
        """Handle keyboard input and send commands via client"""
        print("Keyboard control active. Use:")
        print(" W/S: Throttle")
        print(" A/D: Roll")
        print(" UP/DOWN: Pitch")
        print(" LEFT/RIGHT: Yaw")
        print(" SPACE: Arm/Disarm")
        print(" R: Reset controls")
        print(" Q: Quit")

        while self.running:
            # Throttle control (W/S)
            if keyboard.is_pressed("w"):
                self.client.channels[2] = min(self.client.MAX_VALUE, self.client.channels[2] + self.THROTTLE_STEP)
                self.client.send_channels()
            if keyboard.is_pressed("s"):
                self.client.channels[2] = max(self.client.MIN_VALUE, self.client.channels[2] - self.THROTTLE_STEP)
                self.client.send_channels()
            
            # Roll control (A/D)
            if keyboard.is_pressed('a'):
                self.client.channels[0] = max(self.client.MIN_VALUE, self.client.channels[0] - self.STEP_SIZE)
                self.client.send_channels()
            if keyboard.is_pressed('d'):
                self.client.channels[0] = min(self.client.MAX_VALUE, self.client.channels[0] + self.STEP_SIZE)
                self.client.send_channels()
            
            # Pitch control (Up/Down arrows)
            if keyboard.is_pressed('up'):
                self.client.channels[1] = min(self.client.MAX_VALUE, self.client.channels[1] + self.STEP_SIZE)
                self.client.send_channels()
            if keyboard.is_pressed('down'):
                self.client.channels[1] = max(self.client.MIN_VALUE, self.client.channels[1] - self.STEP_SIZE)
                self.client.send_channels()
            
            # Yaw control (Left/Right arrows)
            if keyboard.is_pressed('left'):
                self.client.channels[3] = max(self.client.MIN_VALUE, self.client.channels[3] - self.YAW_STEP)
                self.client.send_channels()
            if keyboard.is_pressed('right'):
                self.client.channels[3] = min(self.client.MAX_VALUE, self.client.channels[3] + self.YAW_STEP)
                self.client.send_channels()
            
            # Special functions
            if keyboard.is_pressed('space'):
                if self.client.armed:
                    self.client.disarm_drone()
                else:
                    self.client.arm_drone()
                time.sleep(0.3)  # Debounce
            if keyboard.is_pressed('r'):
                self.client.reset_controls()
                time.sleep(0.2)  # Debounce
            if keyboard.is_pressed('q'):
                self.client.stop()
                break
            
            time.sleep(0.01)  # 100Hz update rate