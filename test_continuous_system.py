#!/usr/bin/env python3
"""
Test script for the continuous recording system
"""
import sys
import time
from continuous_recording_system import ContinuousRecordingSystem

def test_continuous_system():
    """Test the continuous recording system"""
    print("Testing Continuous Recording System")
    print("=" * 40)

    # Configuration for test
    config = {
        'camera_device': '/dev/video0',
        'camera_width': 640,  # Smaller for faster testing
        'camera_height': 480,
        'camera_quality': 80,
        'capture_directory': './test_continuous_captures',
        'data_directory': './test_continuous_data'
    }

    # Create system
    system = ContinuousRecordingSystem(config)

    try:
        # Test initialization
        print("1. Testing initialization...")
        if not system.initialize():
            print("❌ Initialization failed")
            return False
        print("✅ Initialization successful")

        # Test status
        print("\n2. Testing status...")
        status = system.get_status()
        print(f"   Running: {status['running']}")
        print(f"   Hardware available: {status['hardware']}")
        print("✅ Status check successful")

        # Test starting system
        print("\n3. Testing system start...")
        system.start()
        time.sleep(0.5)  # Give it a moment to start
        status = system.get_status()
        if not status['running']:
            print("❌ System failed to start")
            return False
        print("✅ System started successfully")

        # Test short recording session
        print("\n4. Testing short recording session...")
        session_data = system.recording_session(
            duration_seconds=2.0,
            photo_interval=0.5
        )

        # Validate results
        if len(session_data['photos']) < 3:  # Should be at least 3-4 photos
            print(f"❌ Too few photos captured: {len(session_data['photos'])}")
            return False

        if len(session_data['accelerometer_data']) < 50:  # Should be plenty of data
            print(f"❌ Too little accelerometer data: {len(session_data['accelerometer_data'])}")
            return False

        print(f"✅ Recording successful:")
        print(f"   Photos: {len(session_data['photos'])}")
        print(f"   Data samples: {len(session_data['accelerometer_data'])}")

        # Test system stop
        print("\n5. Testing system stop...")
        system.stop()
        status = system.get_status()
        if status['running']:
            print("❌ System failed to stop")
            return False
        print("✅ System stopped successfully")

        print("\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Always cleanup
        system.cleanup()

def main():
    """Run the test"""
    success = test_continuous_system()

    if success:
        print("\n✅ Test completed successfully!")
        return 0
    else:
        print("\n❌ Test failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())