#!/usr/bin/env python3
"""
Continuous Recording Camera System
Records accelerometer data continuously while taking photos at regular intervals
"""
import time
import json
import threading
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess

# Try to import hardware libraries
try:
    import board
    import busio
    import adafruit_lis3dh
    HARDWARE_AVAILABLE = True
except ImportError as e:
    HARDWARE_AVAILABLE = False
    print(f"Hardware libraries not available: {e}. Will simulate.")

# Try to import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("OpenCV not available, will use fswebcam fallback")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ContinuousRecordingSystem:
    """System that records accelerometer data continuously during photo capture"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.data_lock = threading.Lock()
        self.accelerometer_data = []
        self.recording_active = False

        # Hardware setup
        self.sensor = None
        self.camera = None

        # Statistics
        self.stats = {
            'photos_taken': 0,
            'data_samples_collected': 0,
            'start_time': None,
            'last_photo': None
        }

    def initialize(self) -> bool:
        """Initialize the accelerometer and camera"""
        logger.info("Initializing continuous recording system...")

        # Initialize accelerometer
        if not self._init_accelerometer():
            logger.error("Failed to initialize accelerometer")
            return False

        # Initialize camera
        if not self._init_camera():
            logger.error("Failed to initialize camera")
            return False

        logger.info("System initialized successfully")
        return True

    def _init_accelerometer(self) -> bool:
        """Initialize the LIS3DH accelerometer"""
        if HARDWARE_AVAILABLE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.sensor = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x18)
                self.sensor.range = adafruit_lis3dh.RANGE_4_G
                self.sensor.data_rate = adafruit_lis3dh.DATARATE_100_HZ
                logger.info("LIS3DH accelerometer initialized")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize accelerometer: {e}")
                return False
        else:
            logger.info("Hardware not available - simulating accelerometer")
            self.sensor = "simulated"
            return True

    def _init_camera(self) -> bool:
        """Initialize camera (OpenCV or fswebcam)"""
        if OPENCV_AVAILABLE:
            try:
                self.camera = cv2.VideoCapture(self.config.get('camera_device', '/dev/video0'))
                if not self.camera.isOpened():
                    logger.warning("OpenCV camera failed, will use fswebcam")
                    self.camera = None
                    return self._test_fswebcam()
                else:
                    # Set resolution
                    width = self.config.get('camera_width', 1280)
                    height = self.config.get('camera_height', 720)
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    logger.info(f"OpenCV camera initialized ({width}x{height})")
                    return True
            except Exception as e:
                logger.error(f"OpenCV camera initialization failed: {e}")
                return self._test_fswebcam()
        else:
            return self._test_fswebcam()

    def _test_fswebcam(self) -> bool:
        """Test if fswebcam is available"""
        try:
            result = subprocess.run([
                "fswebcam", "-d", self.config.get('camera_device', '/dev/video0'), "--list-controls"
            ], capture_output=True, timeout=5)
            if result.returncode == 0:
                logger.info("fswebcam available as camera fallback")
                return True
            else:
                logger.error("fswebcam test failed")
                return False
        except Exception as e:
            logger.error(f"fswebcam test error: {e}")
            return False

    def read_accelerometer(self) -> Dict[str, Any]:
        """Read current accelerometer values"""
        timestamp = time.time()

        if HARDWARE_AVAILABLE and self.sensor != "simulated":
            try:
                x, y, z = self.sensor.acceleration
                return {
                    'timestamp': timestamp,
                    'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
                    'acceleration_x': x,
                    'acceleration_y': y,
                    'acceleration_z': z,
                    'source': 'hardware'
                }
            except Exception as e:
                logger.error(f"Error reading accelerometer: {e}")
                return self._simulate_accelerometer_data(timestamp)
        else:
            return self._simulate_accelerometer_data(timestamp)

    def _simulate_accelerometer_data(self, timestamp: float) -> Dict[str, Any]:
        """Simulate accelerometer data for testing"""
        import random
        return {
            'timestamp': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
            'acceleration_x': random.uniform(-1, 1),
            'acceleration_y': random.uniform(-1, 1),
            'acceleration_z': random.uniform(9, 11),  # Simulate gravity
            'source': 'simulated'
        }

    def capture_photo(self) -> Optional[Dict[str, Any]]:
        """Capture a photo using available method"""
        timestamp = time.time()

        if self.camera and OPENCV_AVAILABLE:
            return self._capture_opencv(timestamp)
        else:
            return self._capture_fswebcam(timestamp)

    def _capture_opencv(self, timestamp: float) -> Optional[Dict[str, Any]]:
        """Capture photo using OpenCV"""
        try:
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture frame with OpenCV")
                return None

            # Save frame
            filename = f"capture_{int(timestamp * 1000000)}.jpg"
            filepath = Path(self.config.get('capture_directory', './captures')) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            cv2.imwrite(str(filepath), frame)

            return {
                'timestamp': timestamp,
                'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
                'filename': filename,
                'filepath': str(filepath),
                'method': 'opencv',
                'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            }
        except Exception as e:
            logger.error(f"OpenCV capture failed: {e}")
            return None

    def _capture_fswebcam(self, timestamp: float) -> Optional[Dict[str, Any]]:
        """Capture photo using fswebcam"""
        try:
            filename = f"capture_{int(timestamp * 1000000)}.jpg"
            filepath = Path(self.config.get('capture_directory', './captures')) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            width = self.config.get('camera_width', 1280)
            height = self.config.get('camera_height', 720)
            quality = self.config.get('camera_quality', 90)

            cmd = [
                "fswebcam",
                "-d", self.config.get('camera_device', '/dev/video0'),
                "-r", f"{width}x{height}",
                "--jpeg", str(quality),
                "--no-banner",
                "--quiet",
                str(filepath)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.error(f"fswebcam failed: {result.stderr}")
                return None

            return {
                'timestamp': timestamp,
                'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
                'filename': filename,
                'filepath': str(filepath),
                'method': 'fswebcam',
                'width': width,
                'height': height
            }
        except Exception as e:
            logger.error(f"fswebcam capture failed: {e}")
            return None

    def data_collection_loop(self):
        """Continuously collect accelerometer data while recording is active"""
        logger.info("Starting accelerometer data collection loop")

        while self.running:
            if self.recording_active:
                # Read accelerometer data
                accel_data = self.read_accelerometer()

                with self.data_lock:
                    self.accelerometer_data.append(accel_data)
                    self.stats['data_samples_collected'] += 1

                # Sample at 50Hz during recording
                time.sleep(0.02)
            else:
                # Sleep longer when not actively recording
                time.sleep(0.1)

        logger.info("Data collection loop stopped")

    def recording_session(self, duration_seconds: float = 5.0, photo_interval: float = 1.0):
        """
        Record data and take photos for specified duration

        Args:
            duration_seconds: How long to record for
            photo_interval: Seconds between photos
        """
        logger.info(f"Starting recording session: {duration_seconds}s duration, photo every {photo_interval}s")

        # Clear previous data
        with self.data_lock:
            self.accelerometer_data = []

        # Start recording
        self.recording_active = True
        session_start = time.time()
        next_photo_time = session_start

        session_data = {
            'session_start': session_start,
            'session_start_iso': datetime.fromtimestamp(session_start).isoformat() + 'Z',
            'duration_seconds': duration_seconds,
            'photo_interval': photo_interval,
            'photos': [],
            'accelerometer_data': []
        }

        try:
            while time.time() - session_start < duration_seconds:
                current_time = time.time()

                # Take photo if it's time
                if current_time >= next_photo_time:
                    photo_data = self.capture_photo()
                    if photo_data:
                        session_data['photos'].append(photo_data)
                        self.stats['photos_taken'] += 1
                        self.stats['last_photo'] = current_time
                        logger.info(f"Photo captured: {photo_data['filename']}")

                    next_photo_time = current_time + photo_interval

                # Small sleep to avoid busy waiting
                time.sleep(0.01)

        finally:
            # Stop recording
            self.recording_active = False

            # Copy collected data
            with self.data_lock:
                session_data['accelerometer_data'] = self.accelerometer_data.copy()

            # Save session data to file
            self._save_session_data(session_data)

        logger.info(f"Recording session completed: {len(session_data['photos'])} photos, {len(session_data['accelerometer_data'])} data samples")
        return session_data

    def _save_session_data(self, session_data: Dict[str, Any]):
        """Save session data to JSON file"""
        try:
            session_timestamp = int(session_data['session_start'] * 1000000)
            filename = f"session_{session_timestamp}.json"
            filepath = Path(self.config.get('data_directory', './data')) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)

            logger.info(f"Session data saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")

    def start(self):
        """Start the system"""
        if self.running:
            logger.warning("System already running")
            return

        self.running = True
        self.stats['start_time'] = time.time()

        # Start data collection thread
        self.data_thread = threading.Thread(target=self.data_collection_loop, daemon=True)
        self.data_thread.start()

        logger.info("Continuous recording system started")

    def stop(self):
        """Stop the system"""
        if not self.running:
            return

        self.running = False
        self.recording_active = False

        # Wait for data thread to finish
        if hasattr(self, 'data_thread'):
            self.data_thread.join(timeout=1.0)

        logger.info("Continuous recording system stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            'running': self.running,
            'recording_active': self.recording_active,
            'stats': self.stats.copy(),
            'hardware': {
                'accelerometer_available': HARDWARE_AVAILABLE,
                'opencv_available': OPENCV_AVAILABLE,
                'camera_connected': self.camera is not None
            }
        }

        if self.stats['start_time']:
            status['uptime_seconds'] = time.time() - self.stats['start_time']

        with self.data_lock:
            status['current_data_samples'] = len(self.accelerometer_data)

        return status

    def cleanup(self):
        """Clean up resources"""
        self.stop()

        if self.camera and OPENCV_AVAILABLE:
            self.camera.release()

        logger.info("System cleaned up")


def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Continuous Recording Camera System')
    parser.add_argument('--duration', '-d', type=float, default=10.0,
                       help='Recording duration in seconds (default: 10)')
    parser.add_argument('--photo-interval', '-p', type=float, default=2.0,
                       help='Interval between photos in seconds (default: 2)')
    parser.add_argument('--capture-dir', default='./captures',
                       help='Directory for captured photos')
    parser.add_argument('--data-dir', default='./data',
                       help='Directory for session data')

    args = parser.parse_args()

    # Configuration
    config = {
        'camera_device': '/dev/video0',
        'camera_width': 1280,
        'camera_height': 720,
        'camera_quality': 90,
        'capture_directory': args.capture_dir,
        'data_directory': args.data_dir
    }

    # Create and run system
    system = ContinuousRecordingSystem(config)

    try:
        print("Initializing system...")
        if not system.initialize():
            print("Failed to initialize system")
            return 1

        print("Starting system...")
        system.start()

        print(f"Recording for {args.duration} seconds with photos every {args.photo_interval} seconds...")
        print("Press Ctrl+C to stop early")

        # Run recording session
        session_data = system.recording_session(
            duration_seconds=args.duration,
            photo_interval=args.photo_interval
        )

        print(f"\nRecording completed!")
        print(f"Photos taken: {len(session_data['photos'])}")
        print(f"Data samples: {len(session_data['accelerometer_data'])}")

        status = system.get_status()
        print(f"Total stats: {status['stats']}")

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        system.cleanup()


if __name__ == '__main__':
    import sys
    sys.exit(main())