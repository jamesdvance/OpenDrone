# Communicators

## CRSF (Crossfire)

### 1. Ensure Drone is Bound To TX Connected to Computer

1. Ensure binding phrase is same on drone and TX. Ensure ELRS firmware matches to the second-to-last decimal.
2. Connect Drone to Comptuer via USB. Open Betaflight
3. Go To 'Receiver' Tab
4. Plug MicroTX into computer via usb-c / usb with a data-enabled cable
5. Press in the joystick after startup. Once the menu changes, push downward on the joystick until you get to the 'Bind Mode' screen. Press in the joystick
6. In Betaflight click 'Bind Receiver' in the lower right corner
7. Press the joystick downward (not in) to send the bind signal from MicroTX
8. Confirm drone and microtx are bound - Drone light should be solid, drone should be 'tumbling' in the receiver tab in Betaflight, and microTX should give connection stats

### 2. Run `test_arm.py` with drone bound
1. Activate drone environment or docker
2. Ensure Betaflight open and still on Receiver tab (And drone still bound to MicroTX)
2. Run test_arm.py
3. Check that AUX1 moves 