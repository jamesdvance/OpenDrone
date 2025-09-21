import grpc
import time
import threading
from concurrent import futures
import serial
from google.protobuf import empty_pb2

import drone_control_pb2
import drone_control_pb2_grpc

class CRSFProtocol:
    """CRSF Protocol implementation for ExpressLRS/TBS Crossfire"""
    
    SYNC_BYTE = 0xC8
    FRAME_TYPE_RC_CHANNELS = 0x16
    CRC_POLY = 0xD5
    
    @staticmethod
    def crc8_calc(data):
        """Calculate CRC8 with polynomial 0xD5"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ CRSFProtocol.CRC_POLY
                else:
                    crc <<= 1
        return crc & 0xFF
    
    @staticmethod
    def pack_channels(channels):
        """Pack 16 channels (11-bit each) into 22 bytes"""
        if len(channels) != 16:
            raise ValueError("Must provide exactly 16 channels")
        
        packed = bytearray(22)
        bit_offset = 0
        
        for channel in channels:
            # Clamp channel value to 11-bit range (0-2047)
            channel_val = max(0, min(2047, int(channel)))
            
            # Pack 11 bits into the byte array
            for bit in range(11):
                if channel_val & (1 << bit):
                    byte_idx = bit_offset // 8
                    bit_idx = bit_offset % 8
                    packed[byte_idx] |= (1 << bit_idx)
                bit_offset += 1
        
        return packed
    
    @staticmethod
    def create_crsf_frame(channels):
        """Create complete CRSF frame for RC channels"""
        # Pack channel data
        payload = CRSFProtocol.pack_channels(channels)
        
        # Build frame: [sync] [length] [type] [payload] [crc]
        frame = bytearray([
            CRSFProtocol.SYNC_BYTE,      # Sync byte
            24,                          # Length (22 payload + 1 type + 1 crc)
            CRSFProtocol.FRAME_TYPE_RC_CHANNELS  # Frame type
        ])
        
        # Add payload
        frame.extend(payload)
        
        # Calculate and add CRC (over type + payload)
        crc = CRSFProtocol.crc8_calc(frame[2:])  # Skip sync and length
        frame.append(crc)
        
        return frame

class DroneControlServicer(drone_control_pb2_grpc.DroneControlServicer):
    def __init__(self):
        self.armed = False
        self.connected = False
        self.channels = [1024, 1024, 0, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024]  # 16 channels
        self.serial_connection = None
        self.lock = threading.Lock()
        
    def startLink(self, request, context):
        with self.lock:
            try:
                # Try to open serial connection
                self.serial_connection = serial.Serial(
                    port=request.port,
                    baudrate=request.baud_rate,
                    timeout=1
                )
                self.connected = True
                print(f"Started drone link on {request.port} at {request.baud_rate} baud")
                return drone_control_pb2.StartLinkResp(
                    success=True,
                    message=f"Successfully connected to {request.port}"
                )
            except Exception as e:
                print(f"Failed to start link: {e}")
                return drone_control_pb2.StartLinkResp(
                    success=False,
                    message=f"Failed to connect: {str(e)}"
                )
    
    def stopLink(self, request, context):
        with self.lock:
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
            self.connected = False
            print("Stopped drone link")
        return empty_pb2.Empty()
    
    def setChannels(self, request, context):
        with self.lock:
            # Ensure we have exactly 16 channels
            channels = list(request.channels)
            while len(channels) < 16:
                channels.append(1024)  # Fill missing channels with center value
            self.channels = channels[:16]  # Take only first 16 channels
            
            print(f"Updated channels: {self.channels}")
            
            # Send to drone via serial using CRSF protocol
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    crsf_frame = CRSFProtocol.create_crsf_frame(self.channels)
                    self.serial_connection.write(crsf_frame)
                    self.serial_connection.flush()
                    print(f"Sent CRSF frame: {' '.join(f'{b:02X}' for b in crsf_frame)}")
                except Exception as e:
                    print(f"Error sending CRSF frame to serial: {e}")
        
        return empty_pb2.Empty()
    
    def armDrone(self, request, context):
        with self.lock:
            self.armed = True
            self.channels[4] = 2047  # Set Aux1 high for arming
            print("Drone ARMED")
            
            # Send updated channels to drone immediately
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    crsf_frame = CRSFProtocol.create_crsf_frame(self.channels)
                    self.serial_connection.write(crsf_frame)
                    self.serial_connection.flush()
                    print(f"Sent ARM command via CRSF: {' '.join(f'{b:02X}' for b in crsf_frame)}")
                except Exception as e:
                    print(f"Error sending ARM command: {e}")
        return empty_pb2.Empty()
    
    def disarmDrone(self, request, context):
        with self.lock:
            self.armed = False
            self.channels[4] = 1024  # Set Aux1 low for disarming
            self.channels[2] = 0     # Set throttle to 0
            print("Drone DISARMED")
            
            # Send updated channels to drone immediately
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    crsf_frame = CRSFProtocol.create_crsf_frame(self.channels)
                    self.serial_connection.write(crsf_frame)
                    self.serial_connection.flush()
                    print(f"Sent DISARM command via CRSF: {' '.join(f'{b:02X}' for b in crsf_frame)}")
                except Exception as e:
                    print(f"Error sending DISARM command: {e}")
        return empty_pb2.Empty()
    
    def resetControls(self, request, context):
        with self.lock:
            self.channels[0] = 1024  # Roll center
            self.channels[1] = 1024  # Pitch center  
            self.channels[3] = 1024  # Yaw center
            print("Controls reset to center")
        return empty_pb2.Empty()
    
    def getStatus(self, request, context):
        with self.lock:
            return drone_control_pb2.StatusResp(
                armed=self.armed,
                connected=self.connected,
                channels=self.channels,
                timestamp=int(time.time() * 1000)
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    drone_control_pb2_grpc.add_DroneControlServicer_to_server(
        DroneControlServicer(), server
    )
    
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    server.start()
    
    print(f"Drone control server started on {listen_addr}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop(0)

if __name__ == '__main__':
    serve()