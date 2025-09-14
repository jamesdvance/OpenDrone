# Controllers

This directory contains controller modules for drone operations.

## Available Controllers

- **KeyboardController**: Handles keyboard input for drone control
- **VideoStreamController**: Manages video streaming from drone camera
- **MockVideoStreamController**: Testing utility for video streaming without hardware

## Video Streaming Technology Trade-offs

When implementing video streaming for drone applications, there are three main options to consider:

### OpenCV
**Pros:**
- ✅ Easy Python integration with simple API
- ✅ Built-in display windows and basic processing capabilities
- ✅ Excellent for prototyping and development
- ✅ Good documentation and community support

**Cons:**
- ❌ Higher CPU usage for video decoding
- ❌ Limited codec support compared to alternatives
- ❌ Not optimized for real-time streaming applications

**Best for:** Development, prototyping, simple applications

### FFmpeg (python-ffmpeg/ffmpeg-python)
**Pros:**
- ✅ Excellent codec support and performance
- ✅ Hardware acceleration support (GPU decoding)
- ✅ Low latency streaming capabilities
- ✅ Industry standard for video processing
- ✅ Extensive format support

**Cons:**
- ❌ More complex API and setup
- ❌ Requires external FFmpeg installation
- ❌ Steeper learning curve

**Best for:** Production applications, performance-critical streaming

### GStreamer
**Pros:**
- ✅ Best performance and lowest latency
- ✅ Hardware acceleration support
- ✅ Designed specifically for real-time streaming
- ✅ Plugin architecture for maximum flexibility
- ✅ Professional-grade streaming capabilities

**Cons:**
- ❌ Steepest learning curve
- ❌ More complex Python bindings
- ❌ Requires additional system dependencies

**Best for:** Professional streaming applications, lowest latency requirements

## Current Implementation

The current video streaming implementation uses **OpenCV** for rapid development and testing. This provides:

- Quick integration with existing Python codebase
- Simple debugging and development workflow
- Adequate performance for initial development phase

## Migration Path

For production deployment, consider migrating to **FFmpeg** for:
- Better real-time performance
- Lower latency critical for drone control
- Hardware acceleration for improved battery life
- Professional-grade streaming capabilities

## Usage Examples

```python
from controllers import KeyboardController, VideoStreamController

# Initialize drone client
client = DroneClient()

# Set up keyboard control
keyboard_ctrl = KeyboardController(client)
keyboard_ctrl.start()

# Set up video streaming
video_ctrl = VideoStreamController('/dev/ttyUSB1', 115200)
video_ctrl.start()

# For testing without hardware
from controllers import MockVideoStreamController
mock_video = MockVideoStreamController()
mock_video.start()
```