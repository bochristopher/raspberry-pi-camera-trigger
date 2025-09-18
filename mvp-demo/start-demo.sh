#!/bin/bash

# ProvenSense MVP Demo Startup Script

echo "Starting ProvenSense MVP Demo..."
echo "=================================="

# Check if we're on Raspberry Pi
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Detected Raspberry Pi"
    RPI_MODE=true
else
    echo "Running in development mode (non-Pi)"
    RPI_MODE=false
fi

# Check for required hardware
if [ "$RPI_MODE" = true ]; then
    echo "Checking hardware..."

    # Check I2C
    if [ -e /dev/i2c-1 ]; then
        echo "I2C interface available"
    else
        echo "I2C interface not found. Please enable I2C in raspi-config"
        exit 1
    fi

    # Check camera
    if [ -e /dev/video0 ]; then
        echo "USB camera detected"
    elif [ -e /dev/video10 ]; then
        echo "Pi camera detected"
    else
        echo "No camera detected. Photos will use mock data"
    fi

    # Check GPIO permissions
    if [ -w /dev/gpiomem ]; then
        echo "GPIO permissions available"
    else
        echo "GPIO permissions limited. Run as root or add user to gpio group"
    fi
fi

# Set up directories
echo "Setting up directories..."
mkdir -p mvp_captures mvp_data data logs

# Check if Python dependencies are installed
echo "Checking Python environment..."
cd backend

if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check if Node.js dependencies are installed
echo "Checking Node.js environment..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Build frontend for production
echo "Building frontend..."
npm run build

cd ..

# Start services
echo "Starting services..."

# Function to cleanup on exit
cleanup() {
    echo "Stopping services..."
    pkill -f "python.*main.py" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend in background
echo "Starting FastAPI backend..."
cd backend
python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "Backend started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend failed to start"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo "Starting React frontend..."
cd ../frontend
npm run preview -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "Frontend started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Frontend failed to start"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Get local IP address
if [ "$RPI_MODE" = true ]; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    LOCAL_IP="localhost"
fi

echo ""
echo "ProvenSense MVP Demo is running!"
echo "=================================="
echo ""
echo "Web Interface: http://$LOCAL_IP:3000"
echo "API Endpoint:  http://$LOCAL_IP:8000"
echo "API Docs:      http://$LOCAL_IP:8000/docs"
echo ""
echo "Demo Instructions:"
echo "1. Open the web interface in your browser"
echo "2. Tap the accelerometer sensor to trigger automatic capture"
echo "3. Use 'Manual Capture' button for immediate photos"
echo "4. Check the Gallery to view all captured photos"
echo "5. Use Verify page to check cryptographic signatures"
echo ""
if [ "$RPI_MODE" = true ]; then
    echo "Hardware Tips:"
    echo "- Gently tap or shake the LIS3DH sensor"
    echo "- Ensure camera is connected and working"
    echo "- Check system logs if captures fail"
    echo ""
fi
echo "Press Ctrl+C to stop the demo"
echo ""

# Wait for user interrupt
wait $BACKEND_PID $FRONTEND_PID