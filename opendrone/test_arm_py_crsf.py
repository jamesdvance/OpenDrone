from crsf_serial_parser import CrsfSerial

port = "/dev/ttyUSB0"
crsf = CrsfSerial(port)

try:
    # Neutral stick values (about midpoints)
    channels = [992, 992, 992, 992] + [992]*12  

    # ARM switch on channel 5 (index 4). Set it high (≈1811).
    channels[4] = 1811

    # Send RC frame
    crsf.send_channels(channels)
    print("Sent ARM frame!")

finally:
    crsf.close()
