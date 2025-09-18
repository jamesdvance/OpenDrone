import cv2
import threading
import time
import serial
import numpy as np


class VideoStreamOpenCV:
    def __init__(self, serial_port='/dev/ttyUSB1', baud_rate=115200, buffer_size=4096):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.buffer_size = buffer_size
        self.running = False
        self.serial_connection = None
        self.stream_thread = None
        
        # Video processing settings
        self.frame_width = 640
        self.frame_height = 480
        self.window_name = "Drone Video Feed"
        
    def connect(self):
        """Establish serial connection for video data"""
        try:
            self.serial_connection = serial.Serial(
                self.serial_port, 
                self.baud_rate,
                timeout=1.0
            )
            print(f"Connected to video stream on {self.serial_port} at {self.baud_rate} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to serial port: {e}")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def disconnect(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Video stream disconnected")
    
    def start_stream(self):
        """Start video streaming in a separate thread"""
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Serial connection not established")
            return False
            
        if self.stream_thread and self.stream_thread.is_alive():
            print("Video stream already running")
            return True
            
        self.running = True
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
        
        print("Video stream started")
        return True
        
    def stop_stream(self):
        """Stop video streaming"""
        self.running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2.0)
        
        cv2.destroyAllWindows()
        print("Video stream stopped")
        
    def _stream_loop(self):
        """Main video streaming loop"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        
        # Buffer for accumulating video data
        video_buffer = bytearray()
        
        while self.running:
            try:
                # Read data from serial port
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.buffer_size)
                    video_buffer.extend(data)
                    
                    # Try to decode frame from buffer
                    frame = self._decode_frame(video_buffer)
                    if frame is not None:
                        # Display frame
                        cv2.imshow(self.window_name, frame)
                        
                        # Clear processed data from buffer
                        video_buffer.clear()
                        
                # Handle window events
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.stop()
                    break
                elif key == ord('s'):
                    # Save current frame
                    if 'frame' in locals():
                        timestamp = int(time.time())
                        filename = f"drone_frame_{timestamp}.jpg"
                        cv2.imwrite(filename, frame)
                        print(f"Frame saved as {filename}")
                        
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
            except Exception as e:
                print(f"Stream error: {e}")
                time.sleep(0.1)
                
        cv2.destroyAllWindows()
        
    def _decode_frame(self, buffer):
        """Decode video frame from buffer data"""
        try:
            # Look for JPEG markers (0xFFD8 start, 0xFFD9 end)
            start_marker = b'\xff\xd8'
            end_marker = b'\xff\xd9'
            
            start_idx = buffer.find(start_marker)
            end_idx = buffer.find(end_marker)
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                # Extract JPEG data
                jpeg_data = buffer[start_idx:end_idx + 2]
                
                # Decode JPEG
                nparr = np.frombuffer(jpeg_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # Resize if needed
                    if frame.shape[:2] != (self.frame_height, self.frame_width):
                        frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                    
                    return frame
                    
        except Exception as e:
            print(f"Frame decode error: {e}")
            
        return None
        
    def start(self):
        """Start the video stream controller"""
        if not self.connect():
            return False
            
        return self.start_stream()
        
    def stop(self):
        """Stop the video stream controller safely"""
        print("Stopping video stream...")
        self.running = False
        self.stop_stream()
        self.disconnect()
        

class MockVideoStreamController(VideoStreamController):
    """Mock controller for testing without hardware"""
    
    def __init__(self):
        super().__init__()
        self.frame_counter = 0
        
    def connect(self):
        """Mock connection - always succeeds"""
        print("Mock video stream connected")
        return True
        
    def disconnect(self):
        """Mock disconnection"""
        print("Mock video stream disconnected")
        
    def _stream_loop(self):
        """Generate test pattern frames"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        
        while self.running:
            # Generate test pattern
            frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
            
            # Add moving pattern
            offset = (self.frame_counter * 2) % self.frame_width
            cv2.rectangle(frame, (offset, 100), (offset + 50, 150), (0, 255, 0), -1)
            cv2.putText(frame, f"Frame: {self.frame_counter}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow(self.window_name, frame)
            
            key = cv2.waitKey(33) & 0xFF  # ~30 FPS
            if key == ord('q'):
                break
                
            self.frame_counter += 1
            
        cv2.destroyAllWindows()