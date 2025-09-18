#!/usr/bin/env python3
"""
Demo script showing how to use the continuous recording system
"""

from continuous_recording_system import ContinuousRecordingSystem

def main():
    print("🎥 Continuous Recording Camera System Demo")
    print("=" * 50)
    print()
    print("This system records accelerometer data continuously")
    print("while taking photos at regular intervals.")
    print()

    # Configuration
    config = {
        'camera_device': '/dev/video0',
        'camera_width': 1280,
        'camera_height': 720,
        'camera_quality': 90,
        'capture_directory': './demo_captures',
        'data_directory': './demo_data'
    }

    # Create and initialize system
    system = ContinuousRecordingSystem(config)

    try:
        print("🔧 Initializing system...")
        if not system.initialize():
            print("❌ Failed to initialize system")
            return 1

        status = system.get_status()
        print("✅ System initialized successfully!")
        print(f"   📊 Hardware available: {status['hardware']}")
        print()

        # Start system
        print("🚀 Starting system...")
        system.start()

        # Get user input for recording parameters
        try:
            duration = float(input("Enter recording duration in seconds (default: 10): ") or "10")
            interval = float(input("Enter photo interval in seconds (default: 2): ") or "2")
        except ValueError:
            duration = 10.0
            interval = 2.0

        print()
        print(f"📹 Starting recording session:")
        print(f"   Duration: {duration} seconds")
        print(f"   Photo interval: {interval} seconds")
        print(f"   Expected photos: ~{int(duration / interval)}")
        print()
        print("Press Ctrl+C to stop early...")

        # Run recording session
        session_data = system.recording_session(
            duration_seconds=duration,
            photo_interval=interval
        )

        # Show results
        print()
        print("🎉 Recording completed!")
        print(f"📸 Photos captured: {len(session_data['photos'])}")
        print(f"📊 Data samples: {len(session_data['accelerometer_data'])}")
        print()
        print("📁 Files created:")
        for photo in session_data['photos']:
            print(f"   📸 {photo['filename']}")
        print(f"   📊 Session data saved to: demo_data/session_*.json")

    except KeyboardInterrupt:
        print("\n⏹️ Recording stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        system.cleanup()
        print("\n🧹 System cleaned up")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())