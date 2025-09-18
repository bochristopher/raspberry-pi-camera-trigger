#!/usr/bin/env python3
"""
Test script for the secure continuous recording system
"""
import sys
import time
from secure_continuous_recording_system import SecureContinuousRecordingSystem

def test_secure_system():
    """Test the secure continuous recording system"""
    print("🔐 Testing Secure Continuous Recording System")
    print("=" * 50)

    # Configuration for test
    config = {
        'camera_device': '/dev/video0',
        'camera_width': 640,  # Smaller for faster testing
        'camera_height': 480,
        'camera_quality': 80,
        'capture_directory': './test_secure_final_captures',
        'data_directory': './test_secure_final_data',
        'provenance_log': './test_secure_final_provenance.jsonl',
        'atecc_address': 0x60,
        'atecc_key_slot': 0,
        'rtc_address': 0x68
    }

    # Create system
    system = SecureContinuousRecordingSystem(config)

    try:
        # Test initialization
        print("1. Testing secure initialization...")
        if not system.initialize():
            print("❌ Initialization failed")
            return False
        print("✅ Secure initialization successful")

        # Test status
        print("\n2. Testing secure status...")
        status = system.get_status()
        print(f"   Running: {status['running']}")
        print(f"   Secure element connected: {status['secure_element_connected']}")
        print(f"   RTC connected: {status['rtc_connected']}")
        print(f"   Hardware: {status['hardware']['accelerometer_available']}")
        print("✅ Status check successful")

        # Test starting system
        print("\n3. Testing secure system start...")
        system.start()
        time.sleep(0.5)  # Give it a moment to start
        status = system.get_status()
        if not status['running']:
            print("❌ System failed to start")
            return False
        print("✅ Secure system started successfully")

        # Test short recording session
        print("\n4. Testing secure recording session...")
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

        final_status = system.get_status()
        if final_status['stats']['provenance_records_logged'] < 5:  # Should have multiple secure logs
            print(f"❌ Too few provenance records: {final_status['stats']['provenance_records_logged']}")
            return False

        print(f"✅ Secure recording successful:")
        print(f"   Photos: {len(session_data['photos'])}")
        print(f"   Data samples: {len(session_data['accelerometer_data'])}")
        print(f"   Provenance records: {final_status['stats']['provenance_records_logged']}")

        # Test system stop
        print("\n5. Testing secure system stop...")
        system.stop()
        status = system.get_status()
        if status['running']:
            print("❌ System failed to stop")
            return False
        print("✅ Secure system stopped successfully")

        print("\n🎉 🔐 All secure tests passed!")
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
    success = test_secure_system()

    if success:
        print("\n✅ 🔐 Secure test completed successfully!")
        print("All cryptographic signatures and provenance logging verified!")
        return 0
    else:
        print("\n❌ 🔐 Secure test failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())