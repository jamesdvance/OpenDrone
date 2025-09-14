import grpc
import time

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


    def start(self):
        """Start the drone client"""
        if not self.connect():
            return False
        
        if not self.start_link():
            self.disconnect()
            return False
        
        self.running = True
        
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