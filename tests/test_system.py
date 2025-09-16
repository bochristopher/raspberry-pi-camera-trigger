#!/usr/bin/env python3
"""
System integration tests
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import json
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.trigger_system import CameraTriggerSystem
from src.core.provenance import ProvenanceLogger


class TestCameraTriggerSystem(unittest.TestCase):
    """Test camera trigger system integration"""

    def setUp(self):
        self.config = {
            'imu_address': 0x18,
            'imu_interrupt_pin': 17,
            'atecc_address': 0x60,
            'atecc_key_slot': 0,
            'rtc_address': 0x68,
            'camera_device': '/dev/video0',
            'camera_width': 1280,
            'camera_height': 720,
            'camera_quality': 90,
            'provenance_log': '/tmp/test_provenance.jsonl',
            'capture_directory': '/tmp'
        }

    @patch('src.core.trigger_system.LIS3DHSensor')
    @patch('src.core.trigger_system.ATECC608SecureElement')
    @patch('src.core.trigger_system.DS3231RTC')
    @patch('src.core.trigger_system.USBCamera')
    @patch('src.core.trigger_system.ProvenanceLogger')
    def test_initialization(self, mock_provenance, mock_camera, mock_rtc, mock_atecc, mock_imu):
        """Test system initialization"""
        # Mock all hardware components
        mock_imu.return_value.initialize.return_value = True
        mock_imu.return_value.configure_tap_interrupt.return_value = True
        mock_atecc.return_value.initialize.return_value = True
        mock_rtc.return_value.initialize.return_value = True
        mock_camera.return_value.initialize.return_value = True
        mock_provenance.return_value.initialize.return_value = True

        system = CameraTriggerSystem(self.config)
        result = system.initialize()

        self.assertTrue(result)

    def test_get_status(self):
        """Test getting system status"""
        with patch.multiple(
            'src.core.trigger_system',
            LIS3DHSensor=Mock(),
            ATECC608SecureElement=Mock(),
            DS3231RTC=Mock(),
            USBCamera=Mock(),
            ProvenanceLogger=Mock()
        ):
            system = CameraTriggerSystem(self.config)
            system.imu.is_connected.return_value = True
            system.secure_element.is_connected.return_value = True
            system.rtc.is_connected.return_value = True
            system.camera.is_connected.return_value = True

            status = system.get_status()

            self.assertIn('running', status)
            self.assertIn('stats', status)
            self.assertIn('hardware', status)


class TestProvenanceLogger(unittest.TestCase):
    """Test provenance logging functionality"""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.log_file = self.temp_file.name

        self.mock_secure_element = Mock()
        self.mock_secure_element.get_public_key.return_value = b"mock_public_key_64_bytes" + b"0" * 40
        self.mock_secure_element.sign_data.return_value = (b"signature64", b"hash32bytes" + b"0" * 20)

        self.logger = ProvenanceLogger(self.log_file, self.mock_secure_element)

    def tearDown(self):
        Path(self.log_file).unlink(missing_ok=True)

    def test_initialize(self):
        """Test provenance logger initialization"""
        result = self.logger.initialize()
        self.assertTrue(result)

    def test_log_record(self):
        """Test logging a record"""
        self.logger._public_key = b"mock_public_key"
        self.logger._sequence_number = 0

        test_record = {
            'event': 'test_event',
            'data': 'test_data'
        }

        result = self.logger.log_record(test_record)
        self.assertTrue(result)

        # Verify the record was written
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0)

    def test_verify_record(self):
        """Test record verification"""
        self.mock_secure_element.verify_signature.return_value = True

        provenance_entry = {
            'record': {'event': 'test', 'sequence_number': 1},
            'hash': 'mock_hash',
            'signature': 'mock_signature',
            'public_key': 'mock_public_key'
        }

        with patch('src.core.provenance.hashlib.sha256') as mock_hash:
            mock_hash.return_value.digest.return_value.hex.return_value = 'mock_hash'

            result = self.logger.verify_record(provenance_entry)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()