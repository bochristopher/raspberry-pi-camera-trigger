#!/usr/bin/env python3
"""
Secure Continuous Recording Camera System
Records accelerometer data continuously while taking photos with secure provenance logging
"""
import time
import json
import threading
import logging
import hashlib
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

# Import secure elements from the existing system
try:
    from src.hardware.atecc608 import ATECC608SecureElement
    from src.hardware.ds3231 import DS3231RTC
    from src.core.provenance import ProvenanceLogger
    SECURE_ELEMENTS_AVAILABLE = True
except ImportError as e:
    SECURE_ELEMENTS_AVAILABLE = False
    print(f"Secure elements not available: {e}. Will use mock implementations.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSecureElement:
    """Mock secure element for testing"""
    def __init__(self, i2c_address=0x60, key_slot=0):
        self.i2c_address = i2c_address
        self.key_slot = key_slot
        self._mock_private_key = b'mock_private_key_32_bytes_____!!'

    def initialize(self) -> bool:
        logger.info("[MOCK] ATECC608 initialized")
        return True

    def get_public_key(self) -> bytes:
        return b'mock_public_key_64_bytes_for_testing_purposes_________________!'

    def sign_data(self, data: bytes) -> tuple:
        digest = hashlib.sha256(data).digest()
        signature = hashlib.sha256(self._mock_private_key + digest).digest()[:64]
        logger.info(f"[MOCK] Signed {len(data)} bytes of data")
        return signature, digest

    def verify_signature(self, data: bytes, signature: bytes, public_key: bytes = None) -> bool:
        expected_signature, _ = self.sign_data(data)
        return signature == expected_signature

    def get_device_info(self) -> dict:
        return {'is_hardware': False, 'type': 'mock', 'i2c_address': f"0x{self.i2c_address:02x}"}

    def is_connected(self) -> bool:
        return True

    def cleanup(self):
        logger.info("[MOCK] ATECC608 cleaned up")


class MockRTC:
    """Mock RTC for testing"""
    def __init__(self, i2c_address=0x68):
        self.i2c_address = i2c_address

    def initialize(self) -> bool:
        logger.info("[MOCK] DS3231 RTC initialized")
        return True

    def get_precise_timestamp(self) -> dict:
        timestamp = time.time()
        return {
            'timestamp': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
            'source': 'mock_rtc'
        }

    def get_device_info(self) -> dict:
        return {'is_hardware': False, 'type': 'mock', 'i2c_address': f"0x{self.i2c_address:02x}"}

    def is_connected(self) -> bool:
        return True

    def cleanup(self):
        logger.info("[MOCK] DS3231 cleaned up")


class MockProvenanceLogger:
    """Mock provenance logger for testing"""
    def __init__(self, log_file: str, secure_element):
        self.log_file = Path(log_file)
        self.secure_element = secure_element
        self._sequence_number = 0

    def initialize(self) -> bool:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[MOCK] Provenance logging initialized: {self.log_file}")
        return True

    def log_record(self, record: Dict[str, Any]) -> bool:
        self._sequence_number += 1
        timestamped_record = {
            'sequence_number': self._sequence_number,
            'record_timestamp': time.time(),
            **record
        }

        # Mock signing
        record_json = json.dumps(timestamped_record, sort_keys=True)
        signature, record_hash = self.secure_element.sign_data(record_json.encode())

        provenance_entry = {
            'record': timestamped_record,
            'hash': record_hash.hex(),
            'signature': signature.hex(),
            'public_key': self.secure_element.get_public_key().hex(),
            'signed_timestamp': time.time()
        }

        try:
            with open(self.log_file, 'a') as f:
                json.dump(provenance_entry, f, separators=(',', ':'))
                f.write('\n')
            logger.info(f"[MOCK] Logged record with sequence {self._sequence_number}")
            return True
        except Exception as e:
            logger.error(f"[MOCK] Failed to log record: {e}")
            return False

    def cleanup(self):
        logger.info("[MOCK] Provenance logger cleaned up")


class SecureContinuousRecordingSystem:
    """System that records accelerometer data continuously with secure provenance logging"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.data_lock = threading.Lock()
        self.accelerometer_data = []
        self.recording_active = False

        # Hardware setup
        self.sensor = None
        self.camera = None

        # Secure elements
        if SECURE_ELEMENTS_AVAILABLE:
            self.secure_element = ATECC608SecureElement(
                i2c_address=config.get('atecc_address', 0x60),
                key_slot=config.get('atecc_key_slot', 0)
            )
            self.rtc = DS3231RTC(
                i2c_address=config.get('rtc_address', 0x68)
            )
        else:
            self.secure_element = MockSecureElement()
            self.rtc = MockRTC()

        # Provenance logging
        provenance_log = config.get('provenance_log', './secure_recording_provenance.jsonl')
        if SECURE_ELEMENTS_AVAILABLE:
            self.provenance = ProvenanceLogger(provenance_log, self.secure_element)
        else:
            self.provenance = MockProvenanceLogger(provenance_log, self.secure_element)

        # Statistics
        self.stats = {
            'photos_taken': 0,
            'data_samples_collected': 0,
            'provenance_records_logged': 0,
            'start_time': None,
            'last_photo': None
        }

    def initialize(self) -> bool:
        """Initialize the accelerometer, camera, and secure elements"""
        logger.info("Initializing secure continuous recording system...")

        # Initialize secure elements first
        if not self.secure_element.initialize():
            logger.error("Failed to initialize secure element")
            return False

        if not self.rtc.initialize():
            logger.error("Failed to initialize RTC")
            return False

        if not self.provenance.initialize():
            logger.error("Failed to initialize provenance logging")
            return False

        # Initialize accelerometer
        if not self._init_accelerometer():
            logger.error("Failed to initialize accelerometer")
            return False

        # Initialize camera
        if not self._init_camera():
            logger.error("Failed to initialize camera")
            return False

        # Log system initialization
        init_record = {
            'event': 'system_initialization',
            'timestamp': time.time(),
            'timestamp_iso': datetime.fromtimestamp(time.time()).isoformat() + 'Z',
            'config': self._sanitize_config(self.config),
            'hardware_info': self._get_hardware_info()
        }

        if self.provenance.log_record(init_record):
            self.stats['provenance_records_logged'] += 1

        logger.info("Secure system initialized successfully")
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
        rtc_timestamp = self.rtc.get_precise_timestamp()

        if HARDWARE_AVAILABLE and self.sensor != "simulated":
            try:
                x, y, z = self.sensor.acceleration
                return {
                    'timestamp': timestamp,
                    'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
                    'rtc_timestamp': rtc_timestamp,
                    'acceleration_x': x,
                    'acceleration_y': y,
                    'acceleration_z': z,
                    'source': 'hardware'
                }
            except Exception as e:
                logger.error(f"Error reading accelerometer: {e}")
                return self._simulate_accelerometer_data(timestamp, rtc_timestamp)
        else:
            return self._simulate_accelerometer_data(timestamp, rtc_timestamp)

    def _simulate_accelerometer_data(self, timestamp: float, rtc_timestamp: dict) -> Dict[str, Any]:
        """Simulate accelerometer data for testing"""
        import random
        return {
            'timestamp': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
            'rtc_timestamp': rtc_timestamp,
            'acceleration_x': random.uniform(-1, 1),
            'acceleration_y': random.uniform(-1, 1),
            'acceleration_z': random.uniform(9, 11),  # Simulate gravity
            'source': 'simulated'
        }

    def capture_photo(self) -> Optional[Dict[str, Any]]:
        """Capture a photo using available method"""
        timestamp = time.time()
        rtc_timestamp = self.rtc.get_precise_timestamp()

        if self.camera and OPENCV_AVAILABLE:
            return self._capture_opencv(timestamp, rtc_timestamp)
        else:
            return self._capture_fswebcam(timestamp, rtc_timestamp)

    def _capture_opencv(self, timestamp: float, rtc_timestamp: dict) -> Optional[Dict[str, Any]]:
        """Capture photo using OpenCV"""
        try:
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture frame with OpenCV")
                return None

            # Save frame
            filename = f"secure_capture_{int(timestamp * 1000000)}.jpg"
            filepath = Path(self.config.get('capture_directory', './secure_captures')) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            cv2.imwrite(str(filepath), frame)

            # Calculate image hash for provenance
            with open(filepath, 'rb') as f:
                image_data = f.read()
                image_hash = hashlib.sha256(image_data).hexdigest()

            return {
                'timestamp': timestamp,
                'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
                'rtc_timestamp': rtc_timestamp,
                'filename': filename,
                'filepath': str(filepath),
                'method': 'opencv',
                'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'image_hash': image_hash,
                'size_bytes': len(image_data)
            }
        except Exception as e:
            logger.error(f"OpenCV capture failed: {e}")
            return None

    def _capture_fswebcam(self, timestamp: float, rtc_timestamp: dict) -> Optional[Dict[str, Any]]:
        """Capture photo using fswebcam"""
        try:
            filename = f"secure_capture_{int(timestamp * 1000000)}.jpg"
            filepath = Path(self.config.get('capture_directory', './secure_captures')) / filename
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

            # Calculate image hash for provenance
            with open(filepath, 'rb') as f:
                image_data = f.read()
                image_hash = hashlib.sha256(image_data).hexdigest()

            return {
                'timestamp': timestamp,
                'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
                'rtc_timestamp': rtc_timestamp,
                'filename': filename,
                'filepath': str(filepath),
                'method': 'fswebcam',
                'width': width,
                'height': height,
                'image_hash': image_hash,
                'size_bytes': len(image_data)
            }
        except Exception as e:
            logger.error(f"fswebcam capture failed: {e}")
            return None

    def data_collection_loop(self):
        """Continuously collect accelerometer data while recording is active"""
        logger.info("Starting secure accelerometer data collection loop")

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

        logger.info("Secure data collection loop stopped")

    def recording_session(self, duration_seconds: float = 5.0, photo_interval: float = 1.0):
        """
        Record data and take photos for specified duration with secure logging

        Args:
            duration_seconds: How long to record for
            photo_interval: Seconds between photos
        """
        logger.info(f"Starting secure recording session: {duration_seconds}s duration, photo every {photo_interval}s")

        # Clear previous data
        with self.data_lock:
            self.accelerometer_data = []

        # Log session start
        session_start = time.time()
        session_start_record = {
            'event': 'recording_session_start',
            'session_timestamp': session_start,
            'session_timestamp_iso': datetime.fromtimestamp(session_start).isoformat() + 'Z',
            'duration_seconds': duration_seconds,
            'photo_interval': photo_interval,
            'rtc_timestamp': self.rtc.get_precise_timestamp()
        }

        if self.provenance.log_record(session_start_record):
            self.stats['provenance_records_logged'] += 1

        # Start recording
        self.recording_active = True
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

                        # Log each photo capture to provenance
                        photo_record = {
                            'event': 'photo_capture',
                            'session_timestamp': session_start,
                            'photo_data': photo_data,
                            'sequence_in_session': len(session_data['photos'])
                        }

                        if self.provenance.log_record(photo_record):
                            self.stats['provenance_records_logged'] += 1

                        logger.info(f"Photo captured and logged: {photo_data['filename']}")

                    next_photo_time = current_time + photo_interval

                # Small sleep to avoid busy waiting
                time.sleep(0.01)

        finally:
            # Stop recording
            self.recording_active = False

            # Copy collected data
            with self.data_lock:
                session_data['accelerometer_data'] = self.accelerometer_data.copy()

            # Log session end
            session_end_record = {
                'event': 'recording_session_end',
                'session_timestamp': session_start,
                'session_end_timestamp': time.time(),
                'photos_captured': len(session_data['photos']),
                'data_samples_collected': len(session_data['accelerometer_data']),
                'rtc_timestamp': self.rtc.get_precise_timestamp()
            }

            if self.provenance.log_record(session_end_record):
                self.stats['provenance_records_logged'] += 1

            # Save session data to file
            self._save_session_data(session_data)

        logger.info(f"Secure recording session completed: {len(session_data['photos'])} photos, {len(session_data['accelerometer_data'])} data samples, {self.stats['provenance_records_logged']} provenance records")
        return session_data

    def _save_session_data(self, session_data: Dict[str, Any]):
        """Save session data to JSON file"""
        try:
            session_timestamp = int(session_data['session_start'] * 1000000)
            filename = f"secure_session_{session_timestamp}.json"
            filepath = Path(self.config.get('data_directory', './secure_data')) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)

            logger.info(f"Secure session data saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information for logging"""
        try:
            return {
                'accelerometer_available': HARDWARE_AVAILABLE,
                'opencv_available': OPENCV_AVAILABLE,
                'secure_elements_available': SECURE_ELEMENTS_AVAILABLE,
                'secure_element_info': self.secure_element.get_device_info(),
                'rtc_info': self.rtc.get_device_info(),
                'accelerometer_connected': self.sensor is not None,
                'camera_connected': self.camera is not None
            }
        except Exception as e:
            logger.error(f"Error getting hardware info: {e}")
            return {'error': str(e)}

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from config for logging"""
        sanitized = config.copy()
        sensitive_keys = ['password', 'secret', 'key', 'token']
        for key in list(sanitized.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
        return sanitized

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

        # Log system start
        start_record = {
            'event': 'system_start',
            'timestamp': time.time(),
            'timestamp_iso': datetime.fromtimestamp(time.time()).isoformat() + 'Z',
            'rtc_timestamp': self.rtc.get_precise_timestamp()
        }

        if self.provenance.log_record(start_record):
            self.stats['provenance_records_logged'] += 1

        logger.info("Secure continuous recording system started")

    def stop(self):
        """Stop the system"""
        if not self.running:
            return

        self.running = False
        self.recording_active = False

        # Wait for data thread to finish
        if hasattr(self, 'data_thread'):
            self.data_thread.join(timeout=1.0)

        # Log system stop
        stop_record = {
            'event': 'system_stop',
            'timestamp': time.time(),
            'timestamp_iso': datetime.fromtimestamp(time.time()).isoformat() + 'Z',
            'final_stats': self.stats.copy(),
            'rtc_timestamp': self.rtc.get_precise_timestamp()
        }

        if self.provenance.log_record(stop_record):
            self.stats['provenance_records_logged'] += 1

        logger.info("Secure continuous recording system stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            'running': self.running,
            'recording_active': self.recording_active,
            'stats': self.stats.copy(),
            'hardware': self._get_hardware_info(),
            'secure_element_connected': self.secure_element.is_connected(),
            'rtc_connected': self.rtc.is_connected()
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

        self.secure_element.cleanup()
        self.rtc.cleanup()
        self.provenance.cleanup()

        logger.info("Secure system cleaned up")


def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Secure Continuous Recording Camera System')
    parser.add_argument('--duration', '-d', type=float, default=10.0,
                       help='Recording duration in seconds (default: 10)')
    parser.add_argument('--photo-interval', '-p', type=float, default=2.0,
                       help='Interval between photos in seconds (default: 2)')
    parser.add_argument('--capture-dir', default='./secure_captures',
                       help='Directory for captured photos')
    parser.add_argument('--data-dir', default='./secure_data',
                       help='Directory for session data')
    parser.add_argument('--provenance-log', default='./secure_recording_provenance.jsonl',
                       help='Provenance log file')

    args = parser.parse_args()

    # Configuration
    config = {
        'camera_device': '/dev/video0',
        'camera_width': 1280,
        'camera_height': 720,
        'camera_quality': 90,
        'capture_directory': args.capture_dir,
        'data_directory': args.data_dir,
        'provenance_log': args.provenance_log,
        'atecc_address': 0x60,
        'atecc_key_slot': 0,
        'rtc_address': 0x68
    }

    # Create and run system
    system = SecureContinuousRecordingSystem(config)

    try:
        print("🔒 Initializing secure system...")
        if not system.initialize():
            print("❌ Failed to initialize system")
            return 1

        print("🚀 Starting secure system...")
        system.start()

        print(f"📹 Recording for {args.duration} seconds with photos every {args.photo_interval} seconds...")
        print("🔐 All events will be securely logged with cryptographic signatures")
        print("Press Ctrl+C to stop early")

        # Run recording session
        session_data = system.recording_session(
            duration_seconds=args.duration,
            photo_interval=args.photo_interval
        )

        print(f"\n🎉 Secure recording completed!")
        print(f"📸 Photos taken: {len(session_data['photos'])}")
        print(f"📊 Data samples: {len(session_data['accelerometer_data'])}")

        status = system.get_status()
        print(f"🔐 Provenance records: {status['stats']['provenance_records_logged']}")
        print(f"📋 Total stats: {status['stats']}")

        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        system.cleanup()


if __name__ == '__main__':
    import sys
    sys.exit(main())