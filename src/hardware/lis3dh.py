"""
LIS3DH Accelerometer interface with interrupt support
"""
import time
import logging
from typing import Tuple, Optional, Callable

try:
    import board
    import busio
    import adafruit_lis3dh
    from gpiozero import Button
    HARDWARE_AVAILABLE = True
except ImportError as e:
    HARDWARE_AVAILABLE = False
    logging.warning(f"Hardware libraries not available: {e}. Dry-run mode only.")

logger = logging.getLogger(__name__)


class LIS3DHSensor:
    """Production-ready LIS3DH accelerometer interface"""

    def __init__(self, i2c_address: int = 0x18, interrupt_pin: int = 17):
        """
        Initialize LIS3DH sensor

        Args:
            i2c_address: I2C address (0x18 or 0x19)
            interrupt_pin: GPIO pin for INT1 connection
        """
        self.i2c_address = i2c_address
        self.interrupt_pin = interrupt_pin
        self._sensor = None
        self._interrupt_button = None
        self._interrupt_callback = None

    def initialize(self) -> bool:
        """Initialize I2C connection and configure sensor"""
        if not HARDWARE_AVAILABLE:
            logger.error("Hardware libraries not available. Use dry-run mode with mock hardware.")
            return False

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._sensor = adafruit_lis3dh.LIS3DH_I2C(i2c, address=self.i2c_address)

            # Configure sensor settings
            self._sensor.range = adafruit_lis3dh.RANGE_4_G
            self._sensor.data_rate = adafruit_lis3dh.DATARATE_100_HZ

            # Setup interrupt pin
            self._interrupt_button = Button(self.interrupt_pin, pull_up=True)

            logger.info(f"LIS3DH initialized at address 0x{self.i2c_address:02x}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LIS3DH: {e}")
            return False

    def configure_tap_interrupt(self, threshold: int = 60,
                              time_limit: int = 10,
                              time_latency: int = 20,
                              time_window: int = 255) -> bool:
        """Configure single tap interrupt detection"""
        try:
            if hasattr(self._sensor, 'set_tap'):
                self._sensor.set_tap(
                    adafruit_lis3dh.TAP_SINGLE,
                    threshold=threshold,
                    time_limit=time_limit,
                    time_latency=time_latency,
                    time_window=time_window
                )
                logger.info(f"Tap interrupt configured with threshold {threshold}")
                return True
            else:
                logger.warning("set_tap method not available in this library version")
                return False
        except Exception as e:
            logger.error(f"Failed to configure tap interrupt: {e}")
            return False

    def set_interrupt_callback(self, callback: Callable[[], None]):
        """Set callback function for interrupt events"""
        self._interrupt_callback = callback
        if self._interrupt_button:
            self._interrupt_button.when_pressed = self._handle_interrupt

    def _handle_interrupt(self):
        """Internal interrupt handler"""
        if self._interrupt_callback:
            try:
                self._interrupt_callback()
            except Exception as e:
                logger.error(f"Error in interrupt callback: {e}")

    def read_acceleration(self) -> Tuple[float, float, float]:
        """Read current acceleration values"""
        if not self._sensor:
            raise RuntimeError("Sensor not initialized")

        x, y, z = self._sensor.acceleration
        return x, y, z

    def get_sample_with_timestamp(self) -> dict:
        """Get acceleration sample with precise timestamp"""
        timestamp = time.time()
        x, y, z = self.read_acceleration()

        return {
            'timestamp': timestamp,
            'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
            'acceleration_x': x,
            'acceleration_y': y,
            'acceleration_z': z,
            'units': 'm/s²'
        }

    def is_connected(self) -> bool:
        """Check if sensor is responding"""
        try:
            if self._sensor:
                _ = self._sensor.acceleration
                return True
        except Exception:
            pass
        return False

    def cleanup(self):
        """Clean up resources"""
        if self._interrupt_button:
            self._interrupt_button.close()
        logger.info("LIS3DH cleaned up")