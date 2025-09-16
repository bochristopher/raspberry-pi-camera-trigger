#!/bin/bash
set -euo pipefail

# Raspberry Pi Camera Trigger System Setup Script
# This script sets up the production environment for the camera trigger system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/camera-trigger"
CONFIG_DIR="/etc/camera-trigger"
LOG_DIR="/var/log/camera-trigger"
DATA_DIR="/var/lib/camera-trigger"
SERVICE_USER="camera-trigger"
SERVICE_GROUP="camera-trigger"

echo "=== Raspberry Pi Camera Trigger System Setup ==="
echo "Project directory: $PROJECT_DIR"
echo "Install directory: $INSTALL_DIR"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Create service user and group
echo "Creating service user and group..."
if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
    groupadd --system "$SERVICE_GROUP"
    echo "Created group: $SERVICE_GROUP"
fi

if ! getent passwd "$SERVICE_USER" >/dev/null 2>&1; then
    useradd --system --gid "$SERVICE_GROUP" --home-dir "$INSTALL_DIR" \
            --shell /bin/false --comment "Camera Trigger Service" "$SERVICE_USER"
    echo "Created user: $SERVICE_USER"
fi

# Add service user to required groups for hardware access
usermod -a -G i2c,video,gpio "$SERVICE_USER"
echo "Added $SERVICE_USER to hardware access groups"

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR" "$DATA_DIR/captures"

# Set ownership and permissions
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR" "$LOG_DIR" "$DATA_DIR"
chown root:root "$CONFIG_DIR"
chmod 755 "$INSTALL_DIR" "$LOG_DIR" "$DATA_DIR" "$CONFIG_DIR"
chmod 775 "$DATA_DIR/captures"

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    i2c-tools \
    fswebcam \
    libopencv-dev \
    python3-opencv \
    build-essential \
    pkg-config

# Enable I2C
echo "Enabling I2C..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
    echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
    echo "I2C enabled in config.txt"
fi

# Load I2C module
modprobe i2c-dev || true
if ! grep -q "^i2c-dev" /etc/modules; then
    echo "i2c-dev" >> /etc/modules
    echo "I2C module added to /etc/modules"
fi

# Copy project files
echo "Installing project files..."
cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

# Create Python virtual environment
echo "Creating Python virtual environment..."
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"

# Install Python dependencies
echo "Installing Python dependencies..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip

# Create requirements.txt with all needed packages
cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
opencv-python>=4.5.0
adafruit-circuitpython-lis3dh>=1.1.0
adafruit-blinka>=8.0.0
adafruit-circuitpython-ds3231>=2.4.0
gpiozero>=1.6.0
cryptography>=3.4.0
cryptoauthlib>=20220823
RPi.GPIO>=0.7.0
board>=1.0
busio>=5.0.0
digitalio>=3.3.0
EOF

sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Install configuration
echo "Installing configuration..."
if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
    cp "$PROJECT_DIR/config/default.json" "$CONFIG_DIR/config.json"
    echo "Installed default configuration"
else
    echo "Configuration file already exists, skipping"
fi

# Install systemd service
echo "Installing systemd service..."
cp "$PROJECT_DIR/scripts/camera-trigger.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable camera-trigger.service
echo "Service installed and enabled"

# Create log rotation
echo "Setting up log rotation..."
cat > /etc/logrotate.d/camera-trigger << 'EOF'
/var/log/camera-trigger/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 camera-trigger camera-trigger
    postrotate
        systemctl reload camera-trigger.service 2>/dev/null || true
    endscript
}

/var/log/camera-trigger/*.jsonl {
    daily
    missingok
    rotate 365
    compress
    delaycompress
    notifempty
    create 644 camera-trigger camera-trigger
    copytruncate
}
EOF

# Create helper scripts
echo "Creating helper scripts..."
cat > /usr/local/bin/camera-trigger-status << 'EOF'
#!/bin/bash
sudo -u camera-trigger /opt/camera-trigger/venv/bin/python /opt/camera-trigger/main.py --status
EOF

cat > /usr/local/bin/camera-trigger-verify << 'EOF'
#!/bin/bash
LOG_FILE=${1:-/var/log/camera-trigger/provenance.jsonl}
sudo -u camera-trigger /opt/camera-trigger/venv/bin/python /opt/camera-trigger/main.py --verify-log "$LOG_FILE"
EOF

chmod +x /usr/local/bin/camera-trigger-status /usr/local/bin/camera-trigger-verify

# Test hardware connectivity
echo "Testing hardware connectivity..."
echo "I2C devices detected:"
i2cdetect -y 1 || echo "Warning: i2cdetect failed"

echo "Camera devices:"
ls -la /dev/video* 2>/dev/null || echo "Warning: No video devices found"

# Security hardening
echo "Applying security hardening..."
# Ensure sensitive files have correct permissions
chmod 600 "$CONFIG_DIR/config.json"
chmod 755 "$INSTALL_DIR/main.py"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Installation summary:"
echo "  Install directory: $INSTALL_DIR"
echo "  Configuration: $CONFIG_DIR/config.json"
echo "  Log directory: $LOG_DIR"
echo "  Data directory: $DATA_DIR"
echo "  Service user: $SERVICE_USER"
echo ""
echo "Next steps:"
echo "  1. Review and customize the configuration: $CONFIG_DIR/config.json"
echo "  2. Test hardware connections: i2cdetect -y 1"
echo "  3. Start the service: systemctl start camera-trigger"
echo "  4. Check status: camera-trigger-status"
echo "  5. View logs: journalctl -u camera-trigger -f"
echo ""
echo "Commands:"
echo "  camera-trigger-status    - Show system status"
echo "  camera-trigger-verify    - Verify provenance log"
echo ""
echo "Service management:"
echo "  systemctl start camera-trigger     - Start service"
echo "  systemctl stop camera-trigger      - Stop service"
echo "  systemctl restart camera-trigger   - Restart service"
echo "  systemctl status camera-trigger    - Service status"
echo ""
echo "A reboot is recommended to ensure all modules are loaded correctly."