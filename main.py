#!/usr/bin/env python3
"""
Raspberry Pi Camera Trigger System with Secure Provenance
Main application entry point
"""
import sys
import json
import signal
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

from src.core.trigger_system import CameraTriggerSystem


def setup_logging(config: Dict[str, Any]):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())

    # Create log directory
    log_file = Path(log_config.get('file', '/var/log/camera-trigger/system.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set up log rotation if possible
    try:
        from logging.handlers import RotatingFileHandler
        max_size = log_config.get('max_size_mb', 50) * 1024 * 1024
        backup_count = log_config.get('backup_count', 5)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        # Replace the basic file handler
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler) and not isinstance(handler, RotatingFileHandler):
                root_logger.removeHandler(handler)
        root_logger.addHandler(file_handler)

    except Exception as e:
        logging.warning(f"Failed to setup log rotation: {e}")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Convert hex strings to integers for I2C addresses
        if 'hardware' in config:
            for key in ['imu_address', 'atecc_address', 'rtc_address']:
                if key in config['hardware'] and isinstance(config['hardware'][key], str):
                    config['hardware'][key] = int(config['hardware'][key], 16)

        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")


def create_directories(config: Dict[str, Any]):
    """Create necessary directories"""
    directories = [
        Path(config.get('camera', {}).get('capture_directory', '/tmp')),
        Path(config.get('logging', {}).get('file', '/tmp/system.log')).parent,
        Path(config.get('logging', {}).get('provenance_log', '/tmp/provenance.jsonl')).parent
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logging.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            raise


class CameraTriggerApp:
    """Main application class"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trigger_system = None
        self._shutdown_requested = False

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self) -> int:
        """Run the main application"""
        try:
            print("DEBUG: Creating directories...")
            # Create directories
            create_directories(self.config)

            print("DEBUG: Creating trigger system...")
            # Initialize trigger system
            self.trigger_system = CameraTriggerSystem(self.config)

            print("DEBUG: Initializing trigger system...")
            if not self.trigger_system.initialize():
                logging.error("Failed to initialize trigger system")
                return 1

            print("DEBUG: Starting trigger system...")
            # Start the system
            if not self.trigger_system.start():
                logging.error("Failed to start trigger system")
                return 1

            print("DEBUG: System started successfully - entering main loop")
            logging.info("Camera trigger system is running. Press Ctrl+C to stop.")

            # Main loop
            while not self._shutdown_requested:
                try:
                    # Perform periodic health checks
                    import time
                    time.sleep(30)

                    print("DEBUG: Periodic health check...")
                    if self.trigger_system:
                        status = self.trigger_system.get_status()
                        if not status['hardware']['camera_connected']:
                            logging.warning("Camera disconnected")
                        if not status['hardware']['imu_connected']:
                            logging.warning("IMU disconnected")

                except KeyboardInterrupt:
                    print("DEBUG: KeyboardInterrupt received")
                    self._shutdown_requested = True
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    print(f"DEBUG: Main loop error: {e}")

            print("DEBUG: Shutting down...")
            logging.info("Shutting down...")
            return 0

        except Exception as e:
            print(f"DEBUG: Application error: {e}")
            logging.error(f"Application error: {e}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            print("DEBUG: Cleanup...")
            if self.trigger_system:
                self.trigger_system.cleanup()

    def status(self) -> int:
        """Get system status"""
        try:
            self.trigger_system = CameraTriggerSystem(self.config)

            if not self.trigger_system.initialize():
                print("System initialization failed")
                return 1

            status = self.trigger_system.get_status()
            health = self.trigger_system.health_check()

            print("=== Camera Trigger System Status ===")
            print(f"Running: {status['running']}")
            print(f"Overall Health: {health['overall_status']}")
            print(f"Uptime: {status.get('uptime_seconds', 0):.1f} seconds")
            print()

            print("Hardware Status:")
            for component, connected in status['hardware'].items():
                status_str = "✓ Connected" if connected else "✗ Disconnected"
                print(f"  {component}: {status_str}")
            print()

            print("Statistics:")
            stats = status['stats']
            print(f"  Total triggers: {stats['triggers_total']}")
            print(f"  Successful: {stats['triggers_successful']}")
            print(f"  Failed: {stats['triggers_failed']}")
            if stats['last_trigger']:
                import datetime
                last_trigger = datetime.datetime.fromtimestamp(stats['last_trigger'])
                print(f"  Last trigger: {last_trigger}")

            return 0

        except Exception as e:
            print(f"Status check failed: {e}")
            return 1

        finally:
            if self.trigger_system:
                self.trigger_system.cleanup()

    def verify_log(self, log_file: str = None) -> int:
        """Verify provenance log integrity"""
        try:
            from src.core.provenance import ProvenanceLogger
            from src.hardware.atecc608 import ATECC608SecureElement

            # Initialize secure element for verification
            secure_element = ATECC608SecureElement()
            if not secure_element.initialize():
                print("Failed to initialize secure element for verification")
                return 1

            # Initialize provenance logger
            provenance_log = log_file or self.config.get('logging', {}).get('provenance_log')
            if not provenance_log:
                print("No provenance log specified")
                return 1

            logger = ProvenanceLogger(provenance_log, secure_element)
            results = logger.verify_log_file(provenance_log)

            print("=== Provenance Log Verification ===")
            print(f"Log file: {provenance_log}")
            print(f"Total records: {results['total_records']}")
            print(f"Valid records: {results['valid_records']}")
            print(f"Invalid records: {results['invalid_records']}")

            if results['sequence_gaps']:
                print(f"Sequence gaps: {len(results['sequence_gaps'])}")

            if results['errors']:
                print("Errors:")
                for error in results['errors']:
                    print(f"  {error}")

            if results['invalid_records'] == 0 and not results['errors']:
                print("✓ All records verified successfully")
                return 0
            else:
                print("✗ Verification failed")
                return 1

        except Exception as e:
            print(f"Verification failed: {e}")
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Raspberry Pi Camera Trigger System')
    parser.add_argument('--config', '-c', default='config/default.json',
                       help='Configuration file path')
    parser.add_argument('--status', action='store_true',
                       help='Show system status and exit')
    parser.add_argument('--verify-log', metavar='LOG_FILE',
                       help='Verify provenance log integrity')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode with mock hardware (for testing)')
    parser.add_argument('--trigger-test', action='store_true',
                       help='Trigger a test event in dry-run mode')

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args.config)

        # Enable dry-run mode if requested
        if args.dry_run:
            print("DEBUG: Enabling dry-run mode")
            config['dry_run'] = True
            if args.trigger_test:
                config['trigger_test'] = True

            # Use local directories for dry-run
            print("DEBUG: Setting up local directories for dry-run")
            config['logging']['file'] = './dry-run.log'
            config['logging']['provenance_log'] = './dry-run-provenance.jsonl'
            config['camera']['capture_directory'] = './dry-run-captures'

            # Convert hardware config properly
            if 'hardware' in config:
                print("DEBUG: Converting hardware config")
                for key in ['imu_address', 'atecc_address', 'rtc_address']:
                    if key in config['hardware'] and isinstance(config['hardware'][key], str):
                        old_val = config['hardware'][key]
                        config['hardware'][key] = int(config['hardware'][key], 16)
                        print(f"DEBUG: Converted {key}: {old_val} -> {config['hardware'][key]}")

                # Flatten hardware config for backward compatibility
                config.update(config['hardware'])
                config.update(config.get('camera', {}))
                config.update(config.get('trigger', {}))
                print(f"DEBUG: Final config keys: {list(config.keys())}")
                print(f"DEBUG: Provenance log path: {config.get('provenance_log', 'NOT FOUND')}")

        # Setup logging
        setup_logging(config)

        if args.dry_run:
            logging.info("Running in DRY-RUN mode with mock hardware")

        # Create application
        print("DEBUG: Creating CameraTriggerApp...")
        app = CameraTriggerApp(config)

        if args.status:
            print("DEBUG: Running status check...")
            return app.status()
        elif args.verify_log:
            print("DEBUG: Running log verification...")
            return app.verify_log(args.verify_log)
        else:
            print("DEBUG: Setting up signal handlers...")
            app.setup_signal_handlers()
            print("DEBUG: Starting application...")
            return app.run()

    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())