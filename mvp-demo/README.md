# ProvenSense MVP - Secure Camera Trigger Demo

A complete web application demonstrating secure sensor data capture with cryptographic provenance.

## What This Demo Shows

- **Interrupt-driven capture**: Tap the accelerometer - photo captured automatically
- **Hardware-backed signing**: Cryptographic signatures using secure elements
- **Real-time web interface**: Live monitoring and control via web dashboard
- **Signature verification**: Tamper-evident proof of data integrity

## Quick Start

### Prerequisites

- Raspberry Pi with camera and LIS3DH accelerometer connected
- Python 3.8+ and Node.js 16+
- All hardware libraries installed (see main project)

### 1. Backend Setup

```bash
cd mvp-demo/backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd mvp-demo/frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start on `http://localhost:3000`

### 3. Access the Demo

Open your browser to `http://localhost:3000` or `http://your-pi-ip:3000`

## Demo Features

### Dashboard
- **System Status**: Real-time hardware monitoring
- **Manual Capture**: Trigger photos manually
- **Recent Captures**: View latest photos with verification status
- **Live Updates**: WebSocket-powered real-time updates

### Gallery
- **Photo Grid**: All captured images with metadata
- **Detailed View**: Click any photo for full details
- **Download**: Save photos and data locally
- **Motion Data**: Accelerometer readings for each capture

### Verify
- **Individual Verification**: Check signatures for specific captures
- **Bulk Verification**: Verify all captures at once
- **Success Metrics**: Overall system integrity statistics
- **Technical Details**: Cryptographic signature information

## How It Works

### 1. Sensor Interrupt
```
LIS3DH Motion - Interrupt Callback - Photo Capture - Cryptographic Signing - Database Storage
```

### 2. Web Interface
```
React Frontend - WebSocket - FastAPI Backend - Secure Recording System - Hardware
```

### 3. Verification Process
```
Photo Data + Metadata - SHA-256 Hash - ECDSA Signature - Secure Element - Verification
```

## Demo Script (5 Minutes)

### Minute 1: Setup
- "Here's our secure sensor system running on Raspberry Pi"
- "Real-time web dashboard shows all hardware status"

### Minute 2: Capture
- "Watch this - I tap the accelerometer..."
- [Tap sensor] - Photo appears immediately in web interface
- "Automatic capture with cryptographic signing"

### Minute 3: Verification
- "Let's verify this data is authentic"
- Click "Verify" → Show green checkmarks
- "Cryptographic proof the data hasn't been tampered with"

### Minute 4: Gallery
- "Complete audit trail of all captures"
- Show metadata, accelerometer data, timestamps
- "Each photo linked to exact sensor readings"

### Minute 5: Value Proposition
- "This solves the provenance problem for sensor data"
- "Hardware-backed security for IoT and robotics"
- "Ready for compliance and auditing"

## Security Features

### Cryptographic Signing
- ECDSA P-256 signatures using secure element
- SHA-256 hashing of all data
- Tamper-evident audit trail

### Hardware Security
- ATECC608A secure element integration
- Hardware-backed key storage
- Software fallback for development

### Data Integrity
- Immutable provenance log
- Cross-referenced timestamps
- File integrity verification

## API Endpoints

### System Status
```
GET /api/status
```

### Captures
```
GET /api/captures              # List all captures
GET /api/capture/{id}          # Get specific capture
POST /api/capture/manual       # Manual capture trigger
GET /api/photo/{id}            # Download photo
```

### Verification
```
GET /api/verify/{id}           # Verify specific capture
GET /api/verify/all            # Verify all captures
```

### WebSocket
```
/ws                            # Real-time updates
```

## Development

### Backend Structure
```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
└── mvp_database.db     # SQLite database (auto-created)
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Main application pages
│   ├── hooks/          # Custom React hooks
│   └── main.jsx        # Application entry point
├── package.json        # Node.js dependencies
└── vite.config.js      # Build configuration
```

## Configuration

### Backend Config
Edit `main.py` to modify:
- Camera resolution and quality
- Database location
- Sensor thresholds
- API endpoints

### Frontend Config
Edit `vite.config.js` to modify:
- API proxy settings
- Build output location
- Development server options

## Customization

### Adding New Sensors
1. Extend the backend `recording_system` configuration
2. Add new API endpoints for sensor data
3. Update frontend to display new sensor types

### Custom UI Themes
1. Modify `src/index.css` for styling
2. Update component styles in individual files
3. Add new color schemes and layouts

### Integration Points
- REST API for external systems
- WebSocket for real-time integration
- Database exports for compliance systems
- Photo downloads for external processing

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check if port 8000 is available
- Ensure hardware libraries are installed
- Verify camera and sensor connections

**Frontend won't connect:**
- Check if backend is running on port 8000
- Verify CORS settings in main.py
- Check browser console for errors

**No captures appearing:**
- Test manual capture first
- Check accelerometer sensitivity
- Verify interrupt callback setup

**Photos not loading:**
- Check file permissions in capture directory
- Verify photo file paths in database
- Test direct photo URL access

### Debug Mode
Set environment variables:
```bash
export DEBUG=1
export LOG_LEVEL=DEBUG
```

## Performance

### Recommended Specs
- Raspberry Pi 4B (4GB RAM)
- Class 10 microSD card (32GB+)
- Hardware accelerometer (LIS3DH)
- USB camera or Pi Camera

### Optimization Tips
- Use faster storage for database
- Optimize image compression settings
- Reduce WebSocket update frequency
- Enable hardware acceleration for camera

## Next Steps

### Immediate Improvements
- Add user authentication
- Implement data export formats
- Add system configuration UI
- Create mobile-responsive design

### Future Enhancements
- Multi-sensor support (GPS, environmental)
- Cloud backup integration
- Advanced analytics dashboard
- Compliance reporting tools

## License

This MVP demo is part of the ProvenSense project. See main project for licensing information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For questions or issues:
- Check the troubleshooting section above
- Review the main project documentation
- Open an issue on GitHub

---

**You now have a complete secure sensor capture system with web interface!**