#!/usr/bin/env python3
import subprocess
import re

def find_silicon_labs_usb():
    """
    Find USB port with Silicon Labs CP210x UART Bridge or Silicon Labs in description.
    Returns the device path (e.g., /dev/ttyUSB0) or None if not found.
    """
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if 'Silicon Labs' in line:
                # Extract bus and device numbers
                match = re.search(r'Bus (\d+) Device (\d+):', line)
                print(match)
                if match:
                    bus = match.group(1).zfill(3)
                    device = match.group(2).zfill(3)
                    
                    # Try to find corresponding tty device
                    try:
                        ls_result = subprocess.run(['ls', '/dev/ttyUSB*'], 
                                                 capture_output=True, text=True, shell=True)
                        if ls_result.returncode == 0:
                            devices = ls_result.stdout.strip().split('\n')
                            for dev in devices:
                                if dev.strip():
                                    return dev.strip()
                    except:
                        pass
                    
                    return f"Bus {bus} Device {device} (no tty device found)"
        
        return None
        
    except subprocess.CalledProcessError:
        return None

if __name__ == "__main__":
    device = find_silicon_labs_usb()
    if device:
        print(f"Silicon Labs device found: {device}")
    else:
        print("No Silicon Labs USB device found")