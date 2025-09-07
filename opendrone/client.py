import grpc
import time
import threading
import keyboard

# Generated protobuf imports (would be generated from drone_control.proto)
# import drone_control_pb2
# import drone_control_pb2_grpc

class DroneClient:
    def __init__(self, host='localhost', port=50051, serial_port='/dev/ttyUSB0', baud_rate=420000):
        self.host = host
        self.port = port
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.channel = None
        self.stub = None
        self.connected = False
        self.running = False
        
        self.channels = [1024, 1024, 0, 1024, 1024, 1024, 1024, 1024]
        self.armed = False
        
        # Control sensitivity settings
        self.STEP_SIZE = 30
        self.THROTTLE_STEP = 40
        self.YAW_STEP = 20
        self.MAX_VALUE = 2047
        self.MIN_VALUE = 0
        self.MID_VALUE = 1024

    def connect(self):
        """Establish gRPC connection to drone server"""
        try:
            self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
            grpc.channel_ready_future(self.channel).result(timeout=10)
            # self.stub = drone_control_pb2_grpc.DroneControlStub(self.channel)
            self.connected = True
            print(f"Connected to drone server at {self.host}:{self.port}")
            return True
        except grpc.RpcError as e:
            print(f"Failed to connect to server: {e}")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Close gRPC connection"""
        if self.channel:
            self.channel.close()
        self.connected = False
        print("Disconnected from server")

    def start_link(self):
        """Initialize drone communication link via gRPC"""
        if not self.connected:
            print("Not connected to server")
            return False
        
        try:
            # request = drone_control_pb2.StartLinkReq(
            #     port=self.serial_port,
            #     baud_rate=self.baud_rate
            # )
            # response = self.stub.startLink(request)
            print(f"Started drone link on {self.serial_port} at {self.baud_rate} baud")
            return True
        except grpc.RpcError as e:
            print(f"Failed to start link: {e}")
            return False

    def stop_link(self):
        """Stop drone communication link"""
        if not self.connected:
            return
        
        try:
            # response = self.stub.stopLink(google.protobuf.Empty())
            print("Stopped drone link")
        except grpc.RpcError as e:
            print(f"Failed to stop link: {e}")

    def send_channels(self):
        """Send current channel values to drone via gRPC"""
        if not self.connected:
            return
        
        try:
            # request = drone_control_pb2.SetChannelsReq(channels=self.channels)
            # response = self.stub.setChannels(request)
            pass
        except grpc.RpcError as e:
            print(f"Failed to send channels: {e}")

    def arm_drone(self):
        """Arm the drone"""
        if not self.connected:
            print("Not connected to server")
            return
        
        try:
            # response = self.stub.armDrone(google.protobuf.Empty())
            self.armed = True
            self.channels[4] = 2047  # Set Aux1 high
            print("Drone ARMED")
        except grpc.RpcError as e:
            print(f"Failed to arm drone: {e}")

    def disarm_drone(self):
        """Disarm the drone"""
        if not self.connected:
            print("Not connected to server")
            return
        
        try:
            # response = self.stub.disarmDrone(google.protobuf.Empty())
            self.armed = False
            self.channels[4] = 1024  # Set Aux1 low
            print("Drone DISARMED")
        except grpc.RpcError as e:
            print(f"Failed to disarm drone: {e}")

    def reset_controls(self):
        """Reset all controls to center position"""
        if not self.connected:
            return
        
        try:
            # response = self.stub.resetControls(google.protobuf.Empty())
            self.channels[0] = self.MID_VALUE  # Roll
            self.channels[1] = self.MID_VALUE  # Pitch
            self.channels[3] = self.MID_VALUE  # Yaw
            print("Controls reset to center")
        except grpc.RpcError as e:
            print(f"Failed to reset controls: {e}")

    def get_status(self):
        """Get current drone status"""
        if not self.connected:
            return None
        
        try:
            # response = self.stub.getStatus(google.protobuf.Empty())
            # return {
            #     'armed': response.armed,
            #     'connected': response.connected,
            #     'channels': list(response.channels),
            #     'timestamp': response.timestamp
            # }
            return {
                'armed': self.armed,
                'connected': self.connected,
                'channels': self.channels,
                'timestamp': int(time.time() * 1000)
            }
        except grpc.RpcError as e:
            print(f"Failed to get status: {e}")
            return None

    def keyboard_control(self):
        """Handle keyboard input and send commands via gRPC"""
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
                self.channels[2] = min(self.MAX_VALUE, self.channels[2] + self.THROTTLE_STEP)
                self.send_channels()
            if keyboard.is_pressed("s"):
                self.channels[2] = max(self.MIN_VALUE, self.channels[2] - self.THROTTLE_STEP)
                self.send_channels()
            
            # Roll control (A/D)
            if keyboard.is_pressed('a'):
                self.channels[0] = max(self.MIN_VALUE, self.channels[0] - self.STEP_SIZE)
                self.send_channels()
            if keyboard.is_pressed('d'):
                self.channels[0] = min(self.MAX_VALUE, self.channels[0] + self.STEP_SIZE)
                self.send_channels()
            
            # Pitch control (Up/Down arrows)
            if keyboard.is_pressed('up'):
                self.channels[1] = min(self.MAX_VALUE, self.channels[1] + self.STEP_SIZE)
                self.send_channels()
            if keyboard.is_pressed('down'):
                self.channels[1] = max(self.MIN_VALUE, self.channels[1] - self.STEP_SIZE)
                self.send_channels()
            
            # Yaw control (Left/Right arrows)
            if keyboard.is_pressed('left'):
                self.channels[3] = max(self.MIN_VALUE, self.channels[3] - self.YAW_STEP)
                self.send_channels()
            if keyboard.is_pressed('right'):
                self.channels[3] = min(self.MAX_VALUE, self.channels[3] + self.YAW_STEP)
                self.send_channels()
            
            # Special functions
            if keyboard.is_pressed('space'):
                if self.armed:
                    self.disarm_drone()
                else:
                    self.arm_drone()
                time.sleep(0.3)  # Debounce
            if keyboard.is_pressed('r'):
                self.reset_controls()
                time.sleep(0.2)  # Debounce
            if keyboard.is_pressed('q'):
                self.stop()
                break
            
            time.sleep(0.01)  # 100Hz update rate

    def start(self):
        """Start the drone client"""
        if not self.connect():
            return False
        
        if not self.start_link():
            self.disconnect()
            return False
        
        self.running = True
        
        # Start keyboard control in separate thread
        keyboard_thread = threading.Thread(target=self.keyboard_control, daemon=True)
        keyboard_thread.start()
        
        try:
            # Main loop: Send status updates
            while self.running:
                status = self.get_status()
                if status:
                    # Optional: Print status periodically
                    pass
                time.sleep(0.1)  # 10Hz status updates
                
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        finally:
            self.stop()
            keyboard_thread.join(timeout=1.0)
        
        return True

    def stop(self):
        """Stop the drone client safely"""
        print("\nStopping drone client...")
        self.running = False
        
        # Set throttle to 0 and disarm
        self.channels[2] = 0
        if self.armed:
            self.disarm_drone()
        
        self.send_channels()
        time.sleep(0.1)
        
        self.stop_link()
        self.disconnect()
        print("Drone client stopped safely")


# Example usage
if __name__ == "__main__":
    client = DroneClient(
        host='localhost',
        port=50051,
        serial_port='/dev/ttyUSB0',
        baud_rate=420000
    )
    
    try:
        client.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Program terminated")