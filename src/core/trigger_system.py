"""
Main trigger system coordinating IMU interrupts, camera capture, and secure logging
"""
import time
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..hardware.lis3dh import LIS3DHSensor
from ..hardware.atecc608 import ATECC608SecureElement
from ..hardware.ds3231 import DS3231RTC
from ..camera.capture import USBCamera
from .provenance import ProvenanceLogger

logger = logging.getLogger(__name__)


class CameraTriggerSystem:
    """Production-ready camera trigger system with secure provenance"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the trigger system

        Args:
            config: System configuration dictionary
        """
        self.config = config
        self.running = False
        self._trigger_lock = threading.Lock()
        self.dry_run = config.get('dry_run', False)

        # Hardware components - use mock hardware in dry-run mode
        if self.dry_run:
            from ..hardware.mock_hardware import (
                MockLIS3DHSensor, MockATECC608SecureElement,
                MockDS3231RTC, MockUSBCamera
            )

            self.imu = MockLIS3DHSensor(
                i2c_address=config.get('imu_address', 0x18),
                interrupt_pin=config.get('imu_interrupt_pin', 17)
            )
            self.secure_element = MockATECC608SecureElement(
                i2c_address=config.get('atecc_address', 0x60),
                key_slot=config.get('atecc_key_slot', 0)
            )
            self.rtc = MockDS3231RTC(
                i2c_address=config.get('rtc_address', 0x68)
            )
            self.camera = MockUSBCamera(
                device_path=config.get('camera_device', '/dev/video0'),
                width=config.get('camera_width', 1280),
                height=config.get('camera_height', 720),
                quality=config.get('camera_quality', 90)
            )
        else:
            self.imu = LIS3DHSensor(
                i2c_address=config.get('imu_address', 0x18),
                interrupt_pin=config.get('imu_interrupt_pin', 17)
            )
            self.secure_element = ATECC608SecureElement(
                i2c_address=config.get('atecc_address', 0x60),
                key_slot=config.get('atecc_key_slot', 0)
            )
            self.rtc = DS3231RTC(
                i2c_address=config.get('rtc_address', 0x68)
            )
            self.camera = USBCamera(
                device_path=config.get('camera_device', '/dev/video0'),
                width=config.get('camera_width', 1280),
                height=config.get('camera_height', 720),
                quality=config.get('camera_quality', 90)
            )

        # Provenance logging
        provenance_log = config.get('provenance_log') or config.get('logging', {}).get('provenance_log', '/var/log/camera_provenance.jsonl')
        if self.dry_run:
            print(f"DEBUG: TriggerSystem provenance_log path: {provenance_log}")
            print(f"DEBUG: Config keys: {list(config.keys())}")
            print(f"DEBUG: Logging config: {config.get('logging', {})}")

        self.provenance = ProvenanceLogger(
            log_file=provenance_log,
            secure_element=self.secure_element
        )

        # Stats
        self.stats = {
            'triggers_total': 0,
            'triggers_successful': 0,
            'triggers_failed': 0,
            'start_time': None,
            'last_trigger': None
        }

    def initialize(self) -> bool:
        """Initialize all hardware components"""
        logger.info("Initializing camera trigger system...")

        success = True

        # Initialize RTC first for accurate timestamps
        if not self.rtc.initialize():
            logger.error("Failed to initialize RTC")
            success = False

        # Initialize IMU
        if not self.imu.initialize():
            logger.error("Failed to initialize IMU")
            success = False

        # Configure IMU tap interrupt
        if success and not self.imu.configure_tap_interrupt(
            threshold=self.config.get('tap_threshold', 60),
            time_limit=self.config.get('tap_time_limit', 10),
            time_latency=self.config.get('tap_time_latency', 20),
            time_window=self.config.get('tap_time_window', 255)
        ):
            logger.error("Failed to configure IMU tap interrupt")
            success = False

        # Initialize secure element
        if not self.secure_element.initialize():
            logger.error("Failed to initialize secure element")
            success = False

        # Initialize camera
        if not self.camera.initialize():
            logger.error("Failed to initialize camera")
            success = False

        # Initialize provenance logging
        if not self.provenance.initialize():
            logger.error("Failed to initialize provenance logging")
            success = False

        if success:
            # Set up interrupt callback
            self.imu.set_interrupt_callback(self._handle_trigger)
            logger.info("Camera trigger system initialized successfully")

            # In dry-run mode, optionally trigger a test event
            if self.dry_run and self.config.get('trigger_test', False):
                logger.info("Scheduling test trigger in 3 seconds...")
                def delayed_test():
                    import time
                    time.sleep(3)
                    if hasattr(self.imu, 'trigger_mock_interrupt'):
                        self.imu.trigger_mock_interrupt()

                import threading
                threading.Thread(target=delayed_test, daemon=True).start()

            # For real hardware, start motion monitoring as fallback
            elif not self.dry_run and hasattr(self.imu, 'start_motion_monitoring'):
                self.imu.start_motion_monitoring(threshold=1.0)  # More sensitive for tap detection

        else:
            logger.error("Camera trigger system initialization failed")

        return success

    def start(self) -> bool:
        """Start the trigger system"""
        if not self.running:
            print("DEBUG: Setting running = True")
            self.running = True
            self.stats['start_time'] = time.time()

            print("DEBUG: Creating startup record...")
            # Log system startup
            try:
                startup_record = {
                    'event': 'system_startup',
                    'timestamp': time.time(),
                    'timestamp_iso': datetime.fromtimestamp(time.time()).isoformat() + 'Z',
                    'config': self._sanitize_config(self.config),
                    'hardware_info': self._get_hardware_info()
                }
                print("DEBUG: Startup record created successfully")

                print("DEBUG: Logging startup record...")
                self.provenance.log_record(startup_record)
                print("DEBUG: Startup record logged successfully")
                logger.info("Camera trigger system started")
                return True
            except Exception as e:
                print(f"DEBUG: Error creating/logging startup record: {e}")
                import traceback
                traceback.print_exc()
                raise

        return False

    def stop(self):
        """Stop the trigger system"""
        if self.running:
            self.running = False

            # Log system shutdown
            shutdown_record = {
                'event': 'system_shutdown',
                'timestamp': time.time(),
                'timestamp_iso': datetime.fromtimestamp(time.time()).isoformat() + 'Z',
                'stats': self.stats.copy(),
                'uptime_seconds': time.time() - self.stats['start_time']
            }

            self.provenance.log_record(shutdown_record)
            logger.info("Camera trigger system stopped")

    def _handle_trigger(self):
        """Handle IMU interrupt trigger"""
        with self._trigger_lock:
            if not self.running:
                print("DEBUG: Trigger called but system not running")
                return

            self.stats['triggers_total'] += 1
            trigger_start = time.time()

            print(f"DEBUG: *** TRIGGER EVENT #{self.stats['triggers_total']} ***")
            logger.info("Trigger event detected")

            try:
                # Capture IMU sample
                print("DEBUG: Capturing IMU sample...")
                imu_sample = self.imu.get_sample_with_timestamp()

                # Capture camera frame
                print("DEBUG: Capturing camera frame...")
                camera_frame = self.camera.capture_frame(
                    method=self.config.get('camera_method', 'opencv')
                )

                if camera_frame is None:
                    raise RuntimeError("Camera capture failed")

                print(f"DEBUG: Camera frame captured: {camera_frame['size_bytes']} bytes")

                # Get precise timestamp from RTC
                print("DEBUG: Getting RTC timestamp...")
                rtc_timestamp = self.rtc.get_precise_timestamp()

                # Create comprehensive record
                trigger_record = {
                    'event': 'trigger_capture',
                    'trigger_timestamp': trigger_start,
                    'trigger_timestamp_iso': datetime.fromtimestamp(trigger_start).isoformat() + 'Z',
                    'imu_data': imu_sample,
                    'camera_data': {
                        'timestamp': camera_frame['timestamp'],
                        'timestamp_iso': camera_frame['timestamp_iso'],
                        'image_hash': camera_frame['image_hash'],
                        'width': camera_frame['width'],
                        'height': camera_frame['height'],
                        'format': camera_frame['format'],
                        'quality': camera_frame['quality'],
                        'size_bytes': camera_frame['size_bytes'],
                        'device': camera_frame['device'],
                        'method': camera_frame['method']
                    },
                    'rtc_data': rtc_timestamp,
                    'processing_time_ms': (time.time() - trigger_start) * 1000
                }

                # Log to provenance system (will hash and sign)
                if self.provenance.log_record(trigger_record):
                    # Save camera frame to disk
                    timestamp_str = str(int(trigger_start * 1000000))
                    frame_path = Path(self.config.get('capture_directory', '/tmp')) / f"capture_{timestamp_str}.jpg"

                    if self.camera.save_frame(camera_frame, str(frame_path)):
                        logger.info(f"Trigger event processed successfully - image saved to {frame_path}")
                        self.stats['triggers_successful'] += 1
                    else:
                        logger.error("Failed to save camera frame")
                        self.stats['triggers_failed'] += 1
                else:
                    logger.error("Failed to log to provenance system")
                    self.stats['triggers_failed'] += 1

                self.stats['last_trigger'] = trigger_start

            except Exception as e:
                logger.error(f"Trigger processing failed: {e}")
                self.stats['triggers_failed'] += 1

                # Log the failure
                error_record = {
                    'event': 'trigger_error',
                    'timestamp': time.time(),
                    'timestamp_iso': datetime.now().isoformat() + 'Z',
                    'error': str(e),
                    'trigger_timestamp': trigger_start
                }
                self.provenance.log_record(error_record)

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        status = {
            'running': self.running,
            'stats': self.stats.copy(),
            'hardware': {
                'imu_connected': self.imu.is_connected(),
                'secure_element_connected': self.secure_element.is_connected(),
                'rtc_connected': self.rtc.is_connected(),
                'camera_connected': self.camera.is_connected()
            },
            'config': self._sanitize_config(self.config)
        }

        if self.stats['start_time']:
            status['uptime_seconds'] = time.time() - self.stats['start_time']

        return status

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information for logging"""
        try:
            return {
                'imu_connected': self.imu.is_connected(),
                'secure_element_connected': self.secure_element.is_connected(),
                'rtc_connected': self.rtc.is_connected(),
                'camera_connected': self.camera.is_connected()
            }
        except Exception as e:
            logger.error(f"Error getting hardware info: {e}")
            return {'error': str(e)}

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from config for logging"""
        sanitized = config.copy()

        # Remove any potential secrets
        sensitive_keys = ['password', 'secret', 'key', 'token']
        for key in list(sanitized.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'

        return sanitized

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            'timestamp': time.time(),
            'timestamp_iso': datetime.now().isoformat() + 'Z',
            'overall_status': 'healthy',
            'components': {}
        }

        # Check IMU
        try:
            if self.imu.is_connected():
                sample = self.imu.get_sample_with_timestamp()
                health['components']['imu'] = {
                    'status': 'healthy',
                    'last_sample': sample
                }
            else:
                health['components']['imu'] = {'status': 'disconnected'}
                health['overall_status'] = 'degraded'
        except Exception as e:
            health['components']['imu'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'unhealthy'

        # Check secure element
        try:
            if self.secure_element.is_connected():
                health['components']['secure_element'] = {
                    'status': 'healthy',
                    'info': self.secure_element.get_device_info()
                }
            else:
                health['components']['secure_element'] = {'status': 'disconnected'}
                health['overall_status'] = 'degraded'
        except Exception as e:
            health['components']['secure_element'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'unhealthy'

        # Check RTC
        try:
            if self.rtc.is_connected():
                health['components']['rtc'] = {
                    'status': 'healthy',
                    'info': self.rtc.get_device_info()
                }
            else:
                health['components']['rtc'] = {'status': 'disconnected'}
                health['overall_status'] = 'degraded'
        except Exception as e:
            health['components']['rtc'] = {'status': 'error', 'error': str(e)}

        # Check camera
        try:
            if self.camera.is_connected():
                health['components']['camera'] = {
                    'status': 'healthy',
                    'info': self.camera.get_camera_info()
                }
            else:
                health['components']['camera'] = {'status': 'disconnected'}
                health['overall_status'] = 'unhealthy'
        except Exception as e:
            health['components']['camera'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'unhealthy'

        return health

    def cleanup(self):
        """Clean up all resources"""
        self.stop()

        self.imu.cleanup()
        self.secure_element.cleanup()
        self.rtc.cleanup()
        self.camera.cleanup()
        self.provenance.cleanup()

        logger.info("Camera trigger system cleaned up")