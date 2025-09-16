#!/bin/bash
set -euo pipefail

# Test script for the camera trigger system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Camera Trigger System Tests ==="
echo "Project directory: $PROJECT_DIR"

cd "$PROJECT_DIR"

# Check if virtual environment exists
if [[ -d "venv" ]]; then
    echo "Using existing virtual environment"
    source venv/bin/activate
else
    echo "Creating virtual environment for testing..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-cov pytest-mock

# Run hardware tests
echo ""
echo "Running hardware tests..."
python -m pytest tests/test_hardware.py -v

# Run system tests
echo ""
echo "Running system tests..."
python -m pytest tests/test_system.py -v

# Run syntax checks
echo ""
echo "Running syntax checks..."
python -m py_compile main.py
python -m py_compile src/hardware/lis3dh.py
python -m py_compile src/hardware/atecc608.py
python -m py_compile src/hardware/ds3231.py
python -m py_compile src/camera/capture.py
python -m py_compile src/core/trigger_system.py
python -m py_compile src/core/provenance.py

echo ""
echo "Running import tests..."
PYTHONPATH="$PROJECT_DIR" python -c "
import sys
try:
    from src.hardware.lis3dh import LIS3DHSensor
    from src.hardware.atecc608 import ATECC608SecureElement
    from src.hardware.ds3231 import DS3231RTC
    from src.camera.capture import USBCamera
    from src.core.trigger_system import CameraTriggerSystem
    from src.core.provenance import ProvenanceLogger
    print('✓ All imports successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

# Check configuration validation
echo ""
echo "Testing configuration loading..."
python -c "
import json
import sys
try:
    with open('config/default.json', 'r') as f:
        config = json.load(f)
    print('✓ Configuration file is valid JSON')

    required_keys = ['hardware', 'camera', 'trigger', 'logging']
    for key in required_keys:
        if key not in config:
            print(f'✗ Missing required config key: {key}')
            sys.exit(1)
    print('✓ Configuration structure is valid')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    sys.exit(1)
"

echo ""
echo "=== Test Summary ==="
echo "✓ Hardware module tests passed"
echo "✓ System integration tests passed"
echo "✓ Syntax checks passed"
echo "✓ Import tests passed"
echo "✓ Configuration validation passed"
echo ""
echo "All tests completed successfully!"