# Raspberry Pi Camera Trigger System

A Python-based camera trigger system for Raspberry Pi that uses a LIS3DH accelerometer sensor to automatically capture photos based on motion detection or tap gestures.

## Features

- **Motion-triggered photography** - Automatically captures photos when device movement exceeds a configurable threshold
- **Tap-triggered photography** - Takes photos when the sensor is tapped (using hardware interrupt)
- **Real-time sensor monitoring** - View live accelerometer data for debugging and calibration
- **Configurable sensitivity** - Adjust motion thresholds and capture cooldown periods
- **High-quality image capture** - Uses fswebcam to capture 1280x720 images

## Hardware Requirements

- Raspberry Pi (tested on Pi 4)
- LIS3DH Triple-Axis Accelerometer sensor
- USB camera or Raspberry Pi Camera Module
- Breadboard and jumper wires for connections

### Wiring

Connect the LIS3DH sensor to your Raspberry Pi:

- VCC → 3.3V
- GND → Ground
- SCL → GPIO 3 (I2C Clock)
- SDA → GPIO 2 (I2C Data)
- INT1 → GPIO 17 (for tap detection)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd camera
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Enable I2C on your Raspberry Pi:
```bash
sudo raspi-config
# Navigate to Interface Options > I2C > Enable
```

4. Install fswebcam for camera capture:
```bash
sudo apt-get update
sudo apt-get install fswebcam
```

## Usage

### Motion-Triggered Photography

Captures photos when the sensor detects movement beyond normal gravity:

```bash
python trigge_photo_motion.py
```

Configuration options in the script:
- `DELTA = 1.0` - Motion threshold (m/s² above/below gravity)
- `COOLDOWN = 2.0` - Minimum seconds between captures

### Tap-Triggered Photography

Takes photos when you tap the sensor:

```bash
python trigger_photo_tap.py
```

Configuration options:
- `threshold=60` - Tap sensitivity (0-127, higher = harder tap required)
- Hardware interrupt-based for reliable detection

### Sensor Data Monitoring

View real-time accelerometer readings for debugging:

```bash
python lis3dh_read.py
```

Outputs timestamp and X, Y, Z acceleration values.

## Files

- `trigge_photo_motion.py` - Motion-based photo capture
- `trigger_photo_tap.py` - Tap-based photo capture
- `lis3dh_read.py` - Raw sensor data logging
- `requirements.txt` - Python dependencies
- `capture_*.jpg` - Sample captured images

## Configuration

### Motion Sensitivity

Edit `DELTA` in `trigge_photo_motion.py`:
- Lower values = more sensitive to small movements
- Higher values = only triggers on larger movements
- Default: 1.0 m/s²

### Tap Sensitivity

Edit `threshold` parameter in `trigger_photo_tap.py`:
- Range: 0-127
- Lower values = more sensitive to light taps
- Higher values = requires harder taps
- Default: 60

### Image Quality

Both scripts use fswebcam with these settings:
- Resolution: 1280x720
- No banner/timestamp overlay
- Format: JPEG

Modify the `cmd` array in either script to change settings.

## Troubleshooting

### Sensor Not Detected
- Check I2C wiring connections
- Verify I2C is enabled: `sudo i2cdetect -y 1`
- LIS3DH should appear at address 0x18

### No Photos Captured
- Test camera separately: `fswebcam test.jpg`
- Check motion threshold is appropriate for your use case
- Verify sensor readings with `lis3dh_read.py`

### Tap Detection Not Working
- Ensure GPIO 17 is connected to INT1 pin
- Try adjusting tap threshold
- Check for older library version (fallback to motion mode)

## License

MIT License - feel free to modify and distribute.

## Contributing

Contributions welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.