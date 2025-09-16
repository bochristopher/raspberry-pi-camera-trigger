#!/usr/bin/env python3
"""
Hardware module tests
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hardware.lis3dh import LIS3DHSensor
from src.hardware.atecc608 import ATECC608SecureElement
from src.hardware.ds3231 import DS3231RTC


class TestLIS3DHSensor(unittest.TestCase):
    """Test LIS3DH sensor functionality"""

    def setUp(self):
        self.sensor = LIS3DHSensor()

    @patch('src.hardware.lis3dh.busio')
    @patch('src.hardware.lis3dh.adafruit_lis3dh')
    @patch('src.hardware.lis3dh.Button')
    def test_initialize_success(self, mock_button, mock_lis3dh, mock_busio):
        """Test successful sensor initialization"""
        mock_sensor = Mock()
        mock_lis3dh.LIS3DH_I2C.return_value = mock_sensor

        result = self.sensor.initialize()

        self.assertTrue(result)
        self.assertIsNotNone(self.sensor._sensor)

    def test_read_acceleration_without_init(self):
        """Test reading acceleration without initialization"""
        with self.assertRaises(RuntimeError):
            self.sensor.read_acceleration()

    @patch('src.hardware.lis3dh.time.time')
    def test_get_sample_with_timestamp(self, mock_time):
        """Test getting timestamped sample"""
        mock_time.return_value = 1234567890.0
        self.sensor._sensor = Mock()
        self.sensor._sensor.acceleration = (1.0, 2.0, 3.0)

        sample = self.sensor.get_sample_with_timestamp()

        self.assertIn('timestamp', sample)
        self.assertIn('acceleration_x', sample)
        self.assertEqual(sample['acceleration_x'], 1.0)


class TestATECC608SecureElement(unittest.TestCase):
    """Test ATECC608 secure element functionality"""

    def setUp(self):
        self.secure_element = ATECC608SecureElement()

    def test_initialize_fallback_to_software(self):
        """Test fallback to software crypto when hardware unavailable"""
        with patch('src.hardware.atecc608.CRYPTOAUTHLIB_AVAILABLE', False):
            with patch('src.hardware.atecc608.CRYPTOGRAPHY_AVAILABLE', True):
                with patch('src.hardware.atecc608.ec.generate_private_key') as mock_gen:
                    mock_key = Mock()
                    mock_gen.return_value = mock_key

                    result = self.secure_element.initialize()

                    self.assertTrue(result)
                    self.assertFalse(self.secure_element._is_hardware)
                    self.assertEqual(self.secure_element._fallback_private_key, mock_key)

    def test_sign_data_software_fallback(self):
        """Test data signing with software fallback"""
        self.secure_element._is_hardware = False
        mock_key = Mock()
        self.secure_element._fallback_private_key = mock_key

        test_data = b"test data"
        mock_signature = b"mock_signature_64_bytes_" + b"0" * 38

        with patch.object(self.secure_element, '_der_to_raw') as mock_der:
            mock_der.return_value = (b"r" * 32, b"s" * 32)
            mock_key.sign.return_value = mock_signature

            result = self.secure_element.sign_data(test_data)

            self.assertIsNotNone(result)
            signature, digest = result
            self.assertEqual(len(signature), 64)


class TestDS3231RTC(unittest.TestCase):
    """Test DS3231 RTC functionality"""

    def setUp(self):
        self.rtc = DS3231RTC()

    def test_initialize_fallback_to_system_time(self):
        """Test fallback to system time when hardware unavailable"""
        with patch('src.hardware.ds3231.DS3231_AVAILABLE', False):
            result = self.rtc.initialize()

            self.assertTrue(result)
            self.assertFalse(self.rtc._is_hardware)

    def test_get_datetime_system_fallback(self):
        """Test getting datetime with system time fallback"""
        self.rtc._is_hardware = False

        with patch('src.hardware.ds3231.datetime') as mock_datetime:
            mock_now = Mock()
            mock_datetime.now.return_value = mock_now

            result = self.rtc.get_datetime()

            self.assertEqual(result, mock_now)

    def test_get_precise_timestamp(self):
        """Test getting precise timestamp"""
        self.rtc._is_hardware = False

        with patch('src.hardware.ds3231.time.time') as mock_time:
            with patch('src.hardware.ds3231.datetime') as mock_datetime:
                mock_time.return_value = 1234567890.0
                mock_dt = Mock()
                mock_dt.isoformat.return_value = "2009-02-13T23:31:30"
                mock_dt.strftime.return_value = "2009-02-13 23:31:30.000000"
                mock_datetime.fromtimestamp.return_value = mock_dt

                result = self.rtc.get_precise_timestamp()

                self.assertIn('timestamp', result)
                self.assertIn('timestamp_iso', result)
                self.assertIn('source', result)
                self.assertEqual(result['source'], 'system_time')


if __name__ == '__main__':
    unittest.main()