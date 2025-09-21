#!/usr/bin/env python3
"""
Test script to validate drone binding by testing arm/disarm functionality.
This test connects directly to the drone via CRSF controller and attempts to arm 
then disarm the drone to verify the binding is working correctly.
"""

import time
import sys
from controller import CRSFController

def test_drone_binding():
    """Test drone binding by arming and disarming"""
    print("Starting drone binding test...")
    
    # Initialize controller
    controller = CRSFController(
        port='/dev/ttyUSB0',
        baud_rate=420000
    )
    
    try:
        # Get initial status
        print("Initializing controller...")
        print(f"Initial status - Armed: {controller.armed}")
        
        # Send initial commands to establish connection
        print("Establishing communication link...")
        for _ in range(10):
            controller.send_rc_channels()
            time.sleep(0.02)  # 50Hz rate
        
        # Test arming
        print("Testing drone arm...")
        controller.toggle_arm()
        time.sleep(1)  # Allow time for command to process
        
        # Send armed commands
        for _ in range(50):  # Send for 1 second at 50Hz
            controller.send_rc_channels()
            time.sleep(0.02)
        
        # Verify armed status
        if controller.armed:
            print("SUCCESS: Drone armed successfully")
        else:
            print("FAILED: Drone did not arm")
            controller.close()
            return False
        
        # Hold armed state briefly
        print("Holding armed state for 2 seconds...")
        for _ in range(100):  # Send for 2 seconds at 50Hz
            controller.send_rc_channels()
            time.sleep(0.02)
        
        # Test disarming
        print("Testing drone disarm...")
        controller.toggle_arm()
        time.sleep(1)  # Allow time for command to process
        
        # Send disarmed commands
        for _ in range(50):  # Send for 1 second at 50Hz
            controller.send_rc_channels()
            time.sleep(0.02)
        
        # Verify disarmed status
        if not controller.armed:
            print("SUCCESS: Drone disarmed successfully")
        else:
            print("FAILED: Drone did not disarm")
            controller.close()
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
            controller.close()
        except:
            pass

def main():
    """Main test function"""
    print("=" * 50)
    print("OpenDrone Controller Binding Test")
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