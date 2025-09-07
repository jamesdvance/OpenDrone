# OpenDrone

ExpressLRS (ELRS) - based autopilot software. The idea is to develop autonomous drones using the same basic inputs provided to a radio controller. Initially, the concept can be proven by providing a 'wasd' and up-down-left-right arrow-based control via the keyboard.

## Inspirations

https://github.com/kaack/elrs-joystick-control
https://github.com/hg6185/MuJoCo

## Materials

#### Micro TX
The Micro TX sends and receives CRSF (aka 'Crossfire') packets between the drone and a transmitter - in this case, a 

Examples:
* BetaVPV 1.4Ghz 1W Micro RF Model (recommended)

#### VRX
The VRX broadcasts video back from the drone to your local computer. 

Examples:
* Walksnail AvatarFPV VRX (recommended)

#### ELRS Drone

Examples:
* BetaFPV Air75 (recommended)

## Docker Usage

To build and run OpenDrone using Docker:

```bash
# Build the Docker image
docker build -t opendrone .

# Run the container with serial port access
docker run --privileged -p 50051:50051 opendrone
```

Note: The `--privileged` flag is required for serial port access to communicate with the drone hardware via `/dev/ttyUSB0`.

## Building Protobufs

```bash
  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. drone_control.proto
  ```

