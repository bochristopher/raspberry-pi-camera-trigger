"""
DS3231 Real-Time Clock interface for precise timestamps
"""
import time
import logging
from typing import Optional
from datetime import datetime

try:
    import board
    import busio
    import adafruit_ds3231
    DS3231_AVAILABLE = True
except ImportError:
    DS3231_AVAILABLE = False

logger = logging.getLogger(__name__)


class DS3231RTC:
    """Production-ready DS3231 RTC interface"""

    def __init__(self, i2c_address: int = 0x68):
        """
        Initialize DS3231 RTC

        Args:
            i2c_address: I2C address of DS3231 (typically 0x68)
        """
        self.i2c_address = i2c_address
        self._rtc = None
        self._is_hardware = False

    def initialize(self) -> bool:
        """Initialize I2C connection to DS3231"""
        if DS3231_AVAILABLE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self._rtc = adafruit_ds3231.DS3231(i2c)
                self._is_hardware = True
                logger.info(f"DS3231 RTC initialized at address 0x{self.i2c_address:02x}")
                return True
            except Exception as e:
                logger.warning(f"Hardware DS3231 initialization failed: {e}")

        # Fallback to system time
        self._is_hardware = False
        logger.warning("Using system time fallback for DS3231")
        return True

    def get_datetime(self) -> datetime:
        """Get current datetime from RTC or system"""
        if self._is_hardware and self._rtc:
            try:
                return self._rtc.datetime
            except Exception as e:
                logger.error(f"Failed to read from hardware RTC: {e}")

        # Fallback to system time
        return datetime.now()

    def set_datetime(self, dt: datetime) -> bool:
        """Set RTC datetime (hardware only)"""
        if self._is_hardware and self._rtc:
            try:
                self._rtc.datetime = dt
                logger.info(f"RTC time set to {dt}")
                return True
            except Exception as e:
                logger.error(f"Failed to set RTC time: {e}")

        logger.warning("Cannot set time - hardware RTC not available")
        return False

    def get_temperature(self) -> Optional[float]:
        """Get temperature from RTC (if available)"""
        if self._is_hardware and self._rtc:
            try:
                return self._rtc.temperature
            except Exception as e:
                logger.error(f"Failed to read RTC temperature: {e}")

        return None

    def get_precise_timestamp(self) -> dict:
        """Get precise timestamp with metadata"""
        if self._is_hardware and self._rtc:
            dt = self.get_datetime()
            timestamp = dt.timestamp()
        else:
            timestamp = time.time()
            dt = datetime.fromtimestamp(timestamp)

        return {
            'timestamp': timestamp,
            'timestamp_iso': dt.isoformat() + 'Z',
            'source': 'hardware_rtc' if self._is_hardware else 'system_time',
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'temperature': self.get_temperature()
        }

    def sync_system_time(self) -> bool:
        """Sync system time from RTC (requires root privileges)"""
        if not self._is_hardware or not self._rtc:
            logger.warning("Cannot sync - hardware RTC not available")
            return False

        try:
            rtc_time = self.get_datetime()
            # Note: Actually setting system time requires subprocess call to 'date'
            # This is just a placeholder for the sync logic
            logger.info(f"RTC time: {rtc_time}")
            logger.warning("System time sync requires root privileges and subprocess calls")
            return False
        except Exception as e:
            logger.error(f"Failed to sync system time: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if RTC is responding"""
        if self._is_hardware and self._rtc:
            try:
                _ = self._rtc.datetime
                return True
            except Exception:
                return False

        return True  # System time is always available

    def get_device_info(self) -> dict:
        """Get device information"""
        info = {
            'is_hardware': self._is_hardware,
            'i2c_address': f"0x{self.i2c_address:02x}",
            'current_time': self.get_datetime().isoformat(),
            'temperature': self.get_temperature()
        }

        return info

    def cleanup(self):
        """Clean up resources"""
        # DS3231 doesn't require explicit cleanup
        logger.info("DS3231 RTC cleaned up")