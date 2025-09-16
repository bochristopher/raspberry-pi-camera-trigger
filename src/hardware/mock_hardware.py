"""
Mock hardware implementations for dry-run testing
"""
import time
import logging
import random
from typing import Tuple, Optional, Callable, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MockLIS3DHSensor:
    """Mock LIS3DH sensor for testing"""

    def __init__(self, i2c_address: int = 0x18, interrupt_pin: int = 17):
        self.i2c_address = i2c_address
        self.interrupt_pin = interrupt_pin
        self._interrupt_callback = None
        self._initialized = False

    def initialize(self) -> bool:
        """Mock initialization"""
        logger.info(f"[MOCK] LIS3DH initialized at address 0x{self.i2c_address:02x}")
        self._initialized = True
        return True

    def configure_tap_interrupt(self, threshold: int = 60, **kwargs) -> bool:
        """Mock tap interrupt configuration"""
        logger.info(f"[MOCK] Tap interrupt configured with threshold {threshold}")
        return True

    def set_interrupt_callback(self, callback: Callable[[], None]):
        """Set callback for mock interrupts"""
        self._interrupt_callback = callback
        logger.info("[MOCK] Interrupt callback set")

    def trigger_mock_interrupt(self):
        """Manually trigger a mock interrupt for testing"""
        if self._interrupt_callback:
            logger.info("[MOCK] Triggering mock interrupt")
            self._interrupt_callback()
        else:
            logger.warning("[MOCK] No interrupt callback set")

    def read_acceleration(self) -> Tuple[float, float, float]:
        """Generate mock acceleration data"""
        if not self._initialized:
            raise RuntimeError("Sensor not initialized")

        # Generate realistic acceleration values around gravity
        x = random.uniform(-1.0, 1.0)
        y = random.uniform(-1.0, 1.0)
        z = random.uniform(8.8, 10.8)  # ~9.8 m/s² ± variation

        return x, y, z

    def get_sample_with_timestamp(self) -> dict:
        """Get mock acceleration sample with timestamp"""
        timestamp = time.time()
        x, y, z = self.read_acceleration()

        return {
            'timestamp': timestamp,
            'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
            'acceleration_x': x,
            'acceleration_y': y,
            'acceleration_z': z,
            'units': 'm/s²',
            'mock': True
        }

    def is_connected(self) -> bool:
        """Mock connectivity check"""
        return self._initialized

    def cleanup(self):
        """Mock cleanup"""
        logger.info("[MOCK] LIS3DH cleaned up")


class MockATECC608SecureElement:
    """Mock ATECC608 secure element for testing"""

    def __init__(self, i2c_address: int = 0x60, key_slot: int = 0):
        self.i2c_address = i2c_address
        self.key_slot = key_slot
        self._initialized = False
        self._mock_private_key = b"mock_private_key_32_bytes_long!!"
        self._mock_public_key = b"mock_public_key_64_bytes_long_for_testing_purposes_only!!"

    def initialize(self) -> bool:
        """Mock initialization"""
        logger.info(f"[MOCK] ATECC608 initialized at 0x{self.i2c_address:02x}")
        self._initialized = True
        return True

    def get_public_key(self) -> Optional[bytes]:
        """Return mock public key"""
        return self._mock_public_key

    def sign_data(self, data: bytes) -> Optional[Tuple[bytes, bytes]]:
        """Generate mock signature"""
        import hashlib

        if not self._initialized:
            return None

        # Hash the data
        digest = hashlib.sha256(data).digest()

        # Generate deterministic "signature" for testing
        signature_data = self._mock_private_key + digest
        mock_signature = hashlib.sha256(signature_data).digest()[:32]  # R component
        mock_signature += hashlib.sha256(signature_data[::-1]).digest()[:32]  # S component

        logger.info(f"[MOCK] Signed {len(data)} bytes of data")
        return mock_signature, digest

    def verify_signature(self, data: bytes, signature: bytes, public_key: bytes = None) -> bool:
        """Mock signature verification (always returns True for mock signatures)"""
        if public_key is None:
            public_key = self._mock_public_key

        # For mock testing, we'll verify our own signatures
        expected_result = self.sign_data(data)
        if expected_result is None:
            return False

        expected_signature, _ = expected_result
        result = signature == expected_signature

        logger.info(f"[MOCK] Signature verification: {'PASS' if result else 'FAIL'}")
        return result

    def get_device_info(self) -> dict:
        """Return mock device info"""
        return {
            'is_hardware': False,
            'i2c_address': f"0x{self.i2c_address:02x}",
            'key_slot': self.key_slot,
            'device_revision': 'MOCK_DEVICE',
            'mock': True
        }

    def is_connected(self) -> bool:
        """Mock connectivity check"""
        return self._initialized

    def cleanup(self):
        """Mock cleanup"""
        logger.info("[MOCK] ATECC608 cleaned up")


class MockDS3231RTC:
    """Mock DS3231 RTC for testing"""

    def __init__(self, i2c_address: int = 0x68):
        self.i2c_address = i2c_address
        self._initialized = False
        self._time_offset = 0  # Offset from system time for testing

    def initialize(self) -> bool:
        """Mock initialization"""
        logger.info(f"[MOCK] DS3231 RTC initialized at address 0x{self.i2c_address:02x}")
        self._initialized = True
        return True

    def get_datetime(self) -> datetime:
        """Return mock datetime (system time + offset)"""
        return datetime.fromtimestamp(time.time() + self._time_offset)

    def set_datetime(self, dt: datetime) -> bool:
        """Mock setting datetime"""
        self._time_offset = dt.timestamp() - time.time()
        logger.info(f"[MOCK] RTC time set to {dt} (offset: {self._time_offset:.2f}s)")
        return True

    def get_temperature(self) -> Optional[float]:
        """Return mock temperature"""
        # Generate realistic temperature value
        return random.uniform(20.0, 30.0)

    def get_precise_timestamp(self) -> dict:
        """Get mock precise timestamp"""
        timestamp = time.time() + self._time_offset
        dt = datetime.fromtimestamp(timestamp)

        return {
            'timestamp': timestamp,
            'timestamp_iso': dt.isoformat() + 'Z',
            'source': 'mock_rtc',
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'temperature': self.get_temperature(),
            'mock': True
        }

    def is_connected(self) -> bool:
        """Mock connectivity check"""
        return self._initialized

    def get_device_info(self) -> dict:
        """Return mock device info"""
        return {
            'is_hardware': False,
            'i2c_address': f"0x{self.i2c_address:02x}",
            'current_time': self.get_datetime().isoformat(),
            'temperature': self.get_temperature(),
            'time_offset': self._time_offset,
            'mock': True
        }

    def cleanup(self):
        """Mock cleanup"""
        logger.info("[MOCK] DS3231 RTC cleaned up")


class MockUSBCamera:
    """Mock USB camera for testing"""

    def __init__(self, device_path: str = "/dev/video0", **kwargs):
        self.device_path = device_path
        self.width = kwargs.get('width', 1280)
        self.height = kwargs.get('height', 720)
        self.quality = kwargs.get('quality', 90)
        self._initialized = False

    def initialize(self) -> bool:
        """Mock initialization"""
        logger.info(f"[MOCK] USB camera initialized at {self.device_path} ({self.width}x{self.height})")
        self._initialized = True
        return True

    def capture_frame(self, method: str = "opencv") -> Optional[Dict[str, Any]]:
        """Generate mock camera frame"""
        if not self._initialized:
            logger.error("[MOCK] Camera not initialized")
            return None

        timestamp = time.time()

        # Generate mock image data (small JPEG-like header)
        mock_image_data = b'\xff\xd8\xff\xe0' + b'MOCK_JPEG_DATA_' + str(int(timestamp)).encode() + b'\xff\xd9'

        import hashlib
        image_hash = hashlib.sha256(mock_image_data).hexdigest()

        logger.info(f"[MOCK] Captured frame using {method} method")

        return {
            'timestamp': timestamp,
            'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
            'image_data': mock_image_data,
            'image_hash': image_hash,
            'width': self.width,
            'height': self.height,
            'format': 'JPEG',
            'quality': self.quality,
            'size_bytes': len(mock_image_data),
            'device': self.device_path,
            'method': method,
            'mock': True
        }

    def save_frame(self, frame_data: Dict[str, Any], output_path: str) -> bool:
        """Mock save frame to file"""
        try:
            with open(output_path, 'wb') as f:
                f.write(frame_data['image_data'])
            logger.info(f"[MOCK] Frame saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"[MOCK] Failed to save frame: {e}")
            return False

    def get_camera_info(self) -> Dict[str, Any]:
        """Return mock camera info"""
        return {
            'device_path': self.device_path,
            'width': self.width,
            'height': self.height,
            'quality': self.quality,
            'is_opened': self._initialized,
            'mock': True
        }

    def is_connected(self) -> bool:
        """Mock connectivity check"""
        return self._initialized

    def cleanup(self):
        """Mock cleanup"""
        logger.info("[MOCK] USB camera cleaned up")