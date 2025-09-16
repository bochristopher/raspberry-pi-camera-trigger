# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-09-15

### Added
- Initial release of Raspberry Pi Camera Trigger System with Secure Provenance
- Hardware interrupt-driven triggering with LIS3DH accelerometer
- Secure cryptographic signing with ATECC608 P-256 ECDSA
- Precise timestamping with DS3231 RTC
- USB UVC camera capture with OpenCV and fswebcam fallback
- Production systemd service with security hardening
- Comprehensive provenance logging in JSONL format
- Dry-run mode for testing without hardware
- Mock hardware implementations for development
- Automated installation and setup scripts
- Complete test suite with unit and integration tests
- GitHub Actions CI/CD pipeline
- Comprehensive documentation and contributing guidelines

### Security Features
- Cryptographic signatures on all captured events
- Tamper-evident audit trails
- Hardware-based secure key storage
- User isolation and privilege minimization
- Systemd security hardening

### Hardware Support
- LIS3DH Triple-Axis Accelerometer (I²C 0x18, INT1 → GPIO17)
- ATECC608 Secure Element (I²C 0x60)
- DS3231 Real-Time Clock (I²C 0x68)
- USB UVC cameras at /dev/video0
- Raspberry Pi 4 with Raspberry Pi OS Bookworm

### Dependencies
- Python 3.9+
- OpenCV for Python
- Adafruit CircuitPython libraries
- cryptography library
- cryptoauthlib (optional, for hardware ATECC608)
- gpiozero
- fswebcam

### Configuration
- JSON-based configuration system
- Environment-specific configs (production, development, testing)
- Hardware fallback mechanisms
- Comprehensive logging controls

## [Unreleased]

### Planned Features
- Web dashboard for monitoring and configuration
- Email/SMS notifications for events
- Integration with cloud storage services
- Support for multiple camera devices
- Advanced motion detection algorithms
- Data export tools (CSV, PDF reports)
- Remote management API
- Docker containerization
- Support for additional hardware platforms