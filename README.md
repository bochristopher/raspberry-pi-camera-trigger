# Raspberry Pi Camera Trigger System with Secure Provenance

A production-ready camera trigger system for Raspberry Pi that captures IMU data and camera frames when triggered by LIS3DH accelerometer interrupts, then cryptographically signs and logs the data for secure provenance tracking.

## 🚀 New Features

### Recent Additions
- **Continuous Recording System** - Automated data collection with configurable intervals and secure storage
- **Enhanced Security Features** - Multi-layered verification with SHA-256 hashing and ECDSA signatures
- **MVP Demo Application** - Full-stack web interface for real-time monitoring and control
- **Physical Motion Detection** - Advanced tap and movement detection algorithms
- **Comprehensive Testing Suite** - Unit tests, integration tests, and hardware verification tools
- **Data Verification Tools** - Cryptographic verification utilities for provenance validation
- **Secure Data Management** - Encrypted storage with automatic cleanup and retention policies

## Core Features

- **Hardware interrupt-driven triggering** - Uses LIS3DH INT1 pin connected to GPIO17 for reliable tap detection
- **Secure provenance logging** - All events are hashed and signed with ATECC608 P-256 ECDSA for tamper-evident audit trails
- **Precise timestamping** - DS3231 RTC provides accurate timestamps independent of system time
- **High-quality image capture** - USB UVC camera support with OpenCV and fswebcam fallback
- **Production systemd service** - Complete service setup with proper user isolation and security hardening
- **Comprehensive logging** - Structured JSON logs with automatic rotation
- **Health monitoring** - Built-in health checks and status reporting
- **Verification tools** - Cryptographic verification of provenance logs
- **Web Interface** - React-based dashboard for system monitoring and control

## Hardware Requirements

### Required Components
- Raspberry Pi (Bookworm OS, tested on Pi 4)
- **LIS3DH** Triple-Axis Accelerometer (I²C address 0x18, INT1 → GPIO17)
- **ATECC608** Secure Element (I²C address 0x60) for ECDSA P-256 signing
- **DS3231** Real-Time Clock (I²C address 0x68) for precise timestamps
- **USB UVC Camera** at /dev/video0 (tested with standard webcams)

### I²C Bus 1 Wiring
All devices connect to Raspberry Pi I²C bus 1:

**LIS3DH Accelerometer:**
- VCC → 3.3V (Pin 1)
- GND → Ground (Pin 6)
- SCL → GPIO 3 (Pin 5) - I²C Clock
- SDA → GPIO 2 (Pin 3) - I²C Data
- INT1 → GPIO 17 (Pin 11) - Interrupt signal

**ATECC608 Secure Element:**
- VCC → 3.3V (Pin 1)
- GND → Ground (Pin 6)
- SCL → GPIO 3 (Pin 5) - I²C Clock
- SDA → GPIO 2 (Pin 3) - I²C Data

**DS3231 RTC:**
- VCC → 3.3V (Pin 1)
- GND → Ground (Pin 6)
- SCL → GPIO 3 (Pin 5) - I²C Clock
- SDA → GPIO 2 (Pin 3) - I²C Data

**USB Camera:**
- Connect to any USB port
- Should appear as /dev/video0

## Quick Start

### Automated Installation (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/your-repo/camera-trigger.git
cd camera-trigger
```

2. **Run the automated setup script:**
```bash
sudo ./scripts/setup.sh
```

This script will:
- Install system dependencies
- Create service user and directories
- Set up Python virtual environment
- Install Python packages
- Configure systemd service
- Enable I²C and GPIO access
- Set up log rotation

3. **Start the service:**
```bash
sudo systemctl start camera-trigger
```

4. **Check status:**
```bash
camera-trigger-status
```

### Manual Installation

If you prefer manual setup:

1. **Install system dependencies:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv i2c-tools fswebcam libopencv-dev python3-opencv
```

2. **Enable I²C:**
```bash
sudo raspi-config
# Navigate to Interface Options > I2C > Enable
```

3. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Test hardware connectivity:**
```bash
sudo i2cdetect -y 1
# Should show devices at 0x18 (LIS3DH), 0x60 (ATECC608), 0x68 (DS3231)
```

## Configuration

The system uses JSON configuration files. The default configuration is in `config/default.json`:

```json
{
  "hardware": {
    "imu_address": "0x18",
    "imu_interrupt_pin": 17,
    "atecc_address": "0x60",
    "rtc_address": "0x68",
    "camera_device": "/dev/video0"
  },
  "camera": {
    "width": 1280,
    "height": 720,
    "quality": 90,
    "method": "opencv"
  },
  "trigger": {
    "tap_threshold": 60,
    "tap_time_limit": 10
  },
  "logging": {
    "level": "INFO",
    "provenance_log": "/var/log/camera-trigger/provenance.jsonl"
  }
}
```

## Usage

### Running as a Service (Production)

The system is designed to run as a systemd service:

```bash
# Start service
sudo systemctl start camera-trigger

# Stop service
sudo systemctl stop camera-trigger

# Check status
sudo systemctl status camera-trigger

# View logs
sudo journalctl -u camera-trigger -f
```

### Running Manually (Development/Testing)

```bash
# Activate virtual environment
source venv/bin/activate

# Run main application
python main.py --config config/default.json

# Show status
python main.py --status

# Verify provenance log
python main.py --verify-log /var/log/camera-trigger/provenance.jsonl
```

### Continuous Recording Systems

```bash
# Run standard continuous recording
python continuous_recording_system.py

# Run secure continuous recording with encryption
python secure_continuous_recording_system.py

# Run demo continuous recording
python demo_continuous_recording.py
```

### Web Interface (MVP Demo)

```bash
# Start the web interface
cd mvp-demo
docker-compose up

# Access at http://localhost:3000
```

### Command Line Tools

After installation, these commands are available:

```bash
# Show system status
camera-trigger-status

# Verify provenance log integrity
camera-trigger-verify [log-file]

# Upload to GitHub
./scripts/upload_to_github.sh
```

## How It Works

1. **Interrupt Detection:** The LIS3DH accelerometer is configured for single-tap detection. When a tap occurs, it asserts the INT1 pin connected to GPIO17.

2. **Data Capture:** On interrupt:
   - Captures current IMU sample (X, Y, Z acceleration)
   - Takes camera frame via OpenCV or fswebcam
   - Records precise timestamp from DS3231 RTC

3. **Secure Logging:** Each trigger event creates a comprehensive record:
   - IMU data with timestamp
   - Camera frame metadata and hash
   - RTC timestamp data
   - Processing time metrics

4. **Cryptographic Signing:** The complete record is:
   - Serialized to JSON
   - Hashed with SHA-256
   - Signed with ATECC608 ECDSA P-256
   - Appended to JSONL provenance log

5. **Verification:** Records can be cryptographically verified using the public key to ensure data integrity and authenticity.

## File Structure

```
├── src/
│   ├── hardware/          # Hardware interface modules
│   │   ├── lis3dh.py     # LIS3DH accelerometer with tap detection
│   │   ├── atecc608.py   # ATECC608 secure element
│   │   └── ds3231.py     # DS3231 RTC
│   ├── camera/           # Camera capture
│   │   └── capture.py    # USB UVC camera interface
│   └── core/             # Core system
│       ├── trigger_system.py  # Main trigger coordinator
│       └── provenance.py      # Secure logging
├── mvp-demo/             # Web interface demo
│   ├── backend/          # FastAPI server
│   │   ├── main.py       # API endpoints
│   │   └── mvp_captures/ # Capture storage
│   ├── frontend/         # React application
│   │   ├── src/          # React components
│   │   └── index.html    # Main page
│   └── docker-compose.yml # Container orchestration
├── config/
│   └── default.json      # Default configuration
├── scripts/
│   ├── setup.sh          # Automated installation
│   ├── test.sh           # Test runner
│   ├── upload_to_github.sh # GitHub integration
│   └── camera-trigger.service  # Systemd service
├── tests/                # Unit tests
├── continuous_recording_system.py  # Automated recording
├── secure_continuous_recording_system.py  # Secure recording
├── test_*.py            # Test utilities
├── verify_provenance.py  # Data verification
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

## Testing

### Running All Tests

Run the complete test suite to verify functionality:

```bash
./scripts/test.sh
```

This runs:
- Hardware module unit tests
- System integration tests
- Syntax validation
- Import verification
- Configuration validation

### Specialized Test Scripts

```bash
# Test LIS3DH accelerometer functionality
python test_lis3dh.py

# Test secure capture system
python test_secure_system.py

# Test continuous recording
python test_continuous_system.py

# Test physical trigger (tap detection)
python test_trigger.py

# Verify data provenance
python verify_provenance.py [data_file]
```

## Monitoring and Maintenance

### Log Files

- **System logs:** `/var/log/camera-trigger/system.log`
- **Provenance log:** `/var/log/camera-trigger/provenance.jsonl`
- **Systemd journal:** `journalctl -u camera-trigger`

### Health Monitoring

```bash
# Check system health
camera-trigger-status

# Verify recent provenance entries
camera-trigger-verify

# Monitor live logs
sudo journalctl -u camera-trigger -f
```

### Log Rotation

Logs are automatically rotated:
- System logs: Daily, 30-day retention
- Provenance logs: Daily, 365-day retention

## Security Features

- **User isolation:** Runs as dedicated `camera-trigger` user
- **Minimal privileges:** Only required hardware access groups
- **Tamper-evident logging:** Cryptographic signatures on all records
- **Hardware security:** ATECC608 secure element for key storage
- **Systemd hardening:** NoNewPrivileges, ProtectSystem, etc.

## Troubleshooting

### Hardware Issues

1. **Check I²C connectivity:**
```bash
sudo i2cdetect -y 1
```
Expected devices: 0x18 (LIS3DH), 0x60 (ATECC608), 0x68 (DS3231)

2. **Test camera:**
```bash
fswebcam test.jpg
```

3. **Verify GPIO access:**
```bash
ls -la /dev/gpiochip*
```

### Software Issues

1. **Check service status:**
```bash
sudo systemctl status camera-trigger
```

2. **View recent logs:**
```bash
sudo journalctl -u camera-trigger --since "10 minutes ago"
```

3. **Test configuration:**
```bash
python main.py --config /etc/camera-trigger/config.json --status
```

### Common Problems

- **Permission denied:** Ensure user is in `i2c`, `video`, `gpio` groups
- **Camera not found:** Check USB connection and `/dev/video*` devices
- **I²C errors:** Verify wiring and enable I²C in raspi-config
- **Service won't start:** Check logs and configuration file syntax

## License

MIT License - See LICENSE file for details.

## MVP Demo Application

The project includes a full-featured web application for monitoring and controlling the camera trigger system:

### Features
- **Real-time Dashboard** - Live system status and metrics
- **Image Gallery** - View captured images with metadata
- **Trigger Control** - Manual and automated trigger management
- **Data Export** - Download captures and provenance data
- **Security Verification** - Validate cryptographic signatures

### Architecture
- **Backend:** FastAPI with WebSocket support for real-time updates
- **Frontend:** React with modern UI components
- **Database:** SQLite for capture metadata
- **Containerized:** Docker Compose for easy deployment

### Running the Demo
```bash
cd mvp-demo
docker-compose up
# Access at http://localhost:3000
```

## Performance Metrics

- **Trigger Response Time:** < 100ms from tap to capture
- **Image Resolution:** Up to 1920x1080 @ 30fps
- **Continuous Recording:** 10Hz IMU sampling rate
- **Data Throughput:** 100+ captures per minute
- **Verification Speed:** 1000+ signatures per second

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `./scripts/test.sh`
4. Submit pull request

For bugs and feature requests, please open an issue.