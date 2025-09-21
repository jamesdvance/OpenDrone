#!/usr/bin/env python3
"""
Test script to validate drone binding by testing arm/disarm functionality.
This test connects to the drone server and attempts to arm then disarm the drone
to verify the binding is working correctly.
"""

import time
import sys
from client import DroneClient

def test_drone_binding():
    """Test drone binding by arming and disarming"""
    print("Starting drone binding test...")
    
    # Initialize client
    client = DroneClient(
        host='localhost',
        port=50051,
        serial_port='/dev/ttyUSB0',
        baud_rate=420000
    )
    
    try:
        # Connect to server
        print("Connecting to drone server...")
        if not client.connect():
            print("FAILED: Could not connect to drone server")
            return False
        
        # Start communication link
        print("Starting drone communication link...")
        if not client.start_link():
            print("FAILED: Could not start drone link")
            client.disconnect()
            return False
        
        # Get initial status
        print("Getting initial drone status...")
        status = client.get_status()
        if status:
            print(f"Initial status - Armed: {status['armed']}, Connected: {status['connected']}")
        else:
            print("WARNING: Could not get drone status")
        
        # Test arming
        print("Testing drone arm...")
        client.arm_drone()
        time.sleep(1)  # Allow time for command to process
        
        # Verify armed status
        status = client.get_status()
        if status and status['armed']:
            print("SUCCESS: Drone armed successfully")
        else:
            print("FAILED: Drone did not arm")
            client.disconnect()
            return False
        
        # Hold armed state briefly
        print("Holding armed state for 2 seconds...")
        time.sleep(2)
        
        # Test disarming
        print("Testing drone disarm...")
        client.disarm_drone()
        time.sleep(1)  # Allow time for command to process
        
        # Verify disarmed status
        status = client.get_status()
        if status and not status['armed']:
            print("SUCCESS: Drone disarmed successfully")
        else:
            print("FAILED: Drone did not disarm")
            client.disconnect()
            return False
        
        print("SUCCESS: Drone binding test completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        return False
    
    finally:
        # Clean shutdown
        print("Cleaning up...")
        try:
            client.stop_link()
            client.disconnect()
        except:
            pass

def main():
    """Main test function"""
    print("=" * 50)
    print("OpenDrone Binding Test")
    print("=" * 50)
    
    success = test_drone_binding()
    
    print("=" * 50)
    if success:
        print("BINDING TEST PASSED")
        sys.exit(0)
    else:
        print("BINDING TEST FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()