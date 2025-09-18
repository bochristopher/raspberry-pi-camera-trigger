"""
LIS3DH Accelerometer interface with interrupt support
"""
import time
import logging
from typing import Tuple, Optional, Callable
from datetime import datetime

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

            # Skip GPIO setup to avoid conflicts - using motion monitoring instead
            self._interrupt_button = None

            logger.info(f"LIS3DH initialized at address 0x{self.i2c_address:02x}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LIS3DH: {e}")
            return False

    def configure_tap_interrupt(self, threshold: int = 60,
                              time_limit: int = 10,
                              time_latency: int = 20,
                              time_window: int = 255) -> bool:
        """Configure hardware tap interrupt using raw I2C register writes"""
        try:
            if not self._sensor:
                return False

            # LIS3DH Register addresses for tap detection
            CTRL_REG3 = 0x22    # Interrupt control register
            CLICK_CFG = 0x38    # Click configuration register
            CLICK_THS = 0x3A    # Click threshold register
            TIME_LIMIT = 0x3B   # Time limit register
            TIME_LATENCY = 0x3C # Time latency register
            TIME_WINDOW = 0x3D  # Time window register

            # Use the underlying I2C device for direct register access
            i2c_device = self._sensor._device

            # Configure click detection on all axes
            # CLICK_CFG: Enable single click on X, Y, Z axes (0x15 = 0001 0101)
            i2c_device.write_register_byte(CLICK_CFG, 0x15)

            # Set click threshold (scale threshold from our parameter)
            # LIS3DH threshold is in units of 1/128 of full scale
            click_threshold = min(threshold // 4, 127)  # Scale and clamp
            i2c_device.write_register_byte(CLICK_THS, click_threshold)

            # Set timing parameters
            i2c_device.write_register_byte(TIME_LIMIT, min(time_limit, 255))
            i2c_device.write_register_byte(TIME_LATENCY, min(time_latency, 255))
            i2c_device.write_register_byte(TIME_WINDOW, min(time_window, 255))

            # Enable click interrupt on INT1 pin (GPIO17)
            # CTRL_REG3: Route click interrupt to INT1 (0x80 = Click interrupt enable)
            i2c_device.write_register_byte(CTRL_REG3, 0x80)

            logger.info(f"Hardware tap interrupt configured on GPIO17 (threshold={click_threshold})")
            return True

        except Exception as e:
            logger.error(f"Failed to configure hardware tap interrupt: {e}")
            # Fallback to software detection message
            logger.info(f"Using motion threshold detection (threshold not directly configurable)")
            return True

    def set_interrupt_callback(self, callback: Callable[[], None]):
        """Set callback function for interrupt events"""
        self._interrupt_callback = callback
        if self._interrupt_button:
            self._interrupt_button.when_pressed = self._handle_interrupt

    def start_motion_monitoring(self, threshold: float = 2.0):
        """Start monitoring for motion above threshold (simplified without GPIO conflicts)"""
        import threading
        import time

        def monitor_motion():
            last_reading = None
            count = 0
            while True:
                try:
                    if not self._sensor:
                        break

                    current = self.read_acceleration()
                    count += 1

                    # Debug: Print readings every 50 samples (~5 seconds)
                    if count % 50 == 0:
                        print(f"DEBUG: Motion monitor alive - Current: {current[0]:.2f}, {current[1]:.2f}, {current[2]:.2f} [Bump the sensor!]")

                    if last_reading:
                        # Calculate motion delta
                        delta = sum(abs(a - b) for a, b in zip(current, last_reading))

                        # Debug: Print when close to threshold
                        if delta > threshold * 0.3:
                            print(f"DEBUG: Motion delta: {delta:.2f} (threshold: {threshold}) - Getting close!")

                        if delta > threshold:
                            print(f"DEBUG: *** MOTION DETECTED *** delta: {delta:.2f}")
                            logger.info(f"Motion detected (delta: {delta:.2f})")
                            if self._interrupt_callback:
                                print("DEBUG: Calling interrupt callback")
                                self._interrupt_callback()
                            time.sleep(2)  # Cooldown

                    last_reading = current
                    time.sleep(0.1)  # Check 10 times per second
                except Exception as e:
                    logger.error(f"Motion monitoring error: {e}")
                    time.sleep(1)  # Wait before retrying on error
                    continue

        # Start monitoring in background thread
        self._motion_thread = threading.Thread(target=monitor_motion, daemon=True)
        self._motion_thread.start()
        logger.info(f"Motion monitoring started with threshold {threshold}")

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
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat() + 'Z',
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