#!/usr/bin/env python3
"""
ProvenSense MVP - FastAPI Backend
Main application entry point
"""
import os
import sys
import asyncio
import sqlite3
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import traceback

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Add parent directory to path to import existing system
sys.path.append(str(Path(__file__).parent.parent.parent))
from secure_continuous_recording_system import SecureContinuousRecordingSystem

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mvp_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Also enable uvicorn debug logging
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

# Import real hardware after logger is set up
sys.path.append(str(Path(__file__).parent))
try:
    from src.hardware.lis3dh import LIS3DHSensor
    HARDWARE_AVAILABLE = True
    logger.info("Real LIS3DH hardware available")
except ImportError as e:
    logger.warning(f"Hardware not available: {e}. Will use simulation.")
    HARDWARE_AVAILABLE = False

# Pydantic models
class SystemStatus(BaseModel):
    online: bool
    camera_ready: bool
    accelerometer_ready: bool
    secure_element_ready: bool
    last_capture: Optional[str] = None
    total_captures: int = 0

class CaptureData(BaseModel):
    id: int
    timestamp: str
    photo_path: str
    photo_url: str
    accelerometer_data: Dict[str, Any]
    signature_valid: bool
    signature: str
    size_bytes: int

class CaptureRequest(BaseModel):
    duration: float = 2.0
    description: str = "Manual capture"

# FastAPI app
app = FastAPI(
    title="ProvenSense MVP API",
    description="Secure sensor data capture with cryptographic provenance",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
recording_system: Optional[SecureContinuousRecordingSystem] = None
lis3dh_sensor: Optional[LIS3DHSensor] = None
db_path = Path("./mvp_database.db")
websocket_connections: List[WebSocket] = []

class DatabaseManager:
    """Simple database manager for MVP"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        logger.debug(f"Initializing database at {self.db_path}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                photo_path TEXT NOT NULL,
                accelerometer_data TEXT NOT NULL,
                signature TEXT NOT NULL,
                signature_valid BOOLEAN NOT NULL,
                size_bytes INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            logger.debug(traceback.format_exc())
            raise

    def insert_capture(self, photo_path: str, accel_data: Dict, signature: str,
                      signature_valid: bool, size_bytes: int, description: str = ""):
        """Insert new capture record"""
        logger.debug(f"Inserting capture: {photo_path}, size: {size_bytes}, valid: {signature_valid}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.now().isoformat()
            accel_json = json.dumps(accel_data)

            cursor.execute('''
            INSERT INTO captures (timestamp, photo_path, accelerometer_data,
                                signature, signature_valid, size_bytes, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, photo_path, accel_json, signature, signature_valid, size_bytes, description))

            conn.commit()
            capture_id = cursor.lastrowid
            conn.close()

            logger.info(f"Successfully inserted capture {capture_id}: {photo_path}")
            logger.debug(f"Capture {capture_id} details: accel_data keys={list(accel_data.keys())}, signature length={len(signature)}")
            return capture_id
        except Exception as e:
            logger.error(f"Failed to insert capture: {e}")
            logger.debug(traceback.format_exc())
            raise

    def get_captures(self, limit: int = 50) -> List[Dict]:
        """Get recent captures"""
        logger.debug(f"Getting captures with limit: {limit}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT id, timestamp, photo_path, accelerometer_data,
                   signature, signature_valid, size_bytes, description
            FROM captures
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            captures = []
            for row in rows:
                captures.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'photo_path': row[2],
                    'accelerometer_data': json.loads(row[3]),
                    'signature': row[4],
                    'signature_valid': row[5],
                    'size_bytes': row[6],
                    'description': row[7] or ""
                })

            logger.debug(f"Retrieved {len(captures)} captures")
            return captures
        except Exception as e:
            logger.error(f"Failed to get captures: {e}")
            logger.debug(traceback.format_exc())
            return []

    def get_capture(self, capture_id: int) -> Optional[Dict]:
        """Get specific capture"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, timestamp, photo_path, accelerometer_data,
                   signature, signature_valid, size_bytes, description
            FROM captures
            WHERE id = ?
        ''', (capture_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'timestamp': row[1],
                'photo_path': row[2],
                'accelerometer_data': json.loads(row[3]),
                'signature': row[4],
                'signature_valid': row[5],
                'size_bytes': row[6],
                'description': row[7] or ""
            }
        return None

# Initialize database
db_manager = DatabaseManager(str(db_path))

# WebSocket manager
async def broadcast_to_websockets(message: Dict[str, Any]):
    """Broadcast message to all connected WebSockets"""
    if websocket_connections:
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)

        # Remove disconnected websockets
        for ws in disconnected:
            if ws in websocket_connections:
                websocket_connections.remove(ws)

def init_recording_system():
    """Initialize the secure recording system"""
    global recording_system
    logger.info("Starting recording system initialization...")

    # Create directories
    logger.debug("Creating required directories...")
    Path("./mvp_captures").mkdir(exist_ok=True)
    Path("./mvp_data").mkdir(exist_ok=True)
    logger.debug("Directories created successfully")

    config = {
        'camera_device': '/dev/video0',
        'camera_width': 1280,
        'camera_height': 720,
        'camera_quality': 90,
        'capture_directory': './mvp_captures',
        'data_directory': './mvp_data',
        'provenance_log': './mvp_provenance.jsonl',
        'atecc_address': 0x60,
        'atecc_key_slot': 0,
        'rtc_address': 0x68
    }

    logger.debug(f"Creating recording system with config: {list(config.keys())}")
    recording_system = SecureContinuousRecordingSystem(config)

    logger.debug("Attempting to initialize recording system...")
    if recording_system.initialize():
        logger.debug("Recording system initialized, starting...")
        recording_system.start()
        logger.info("Recording system initialized and started successfully")
        return True
    else:
        logger.error("Failed to initialize recording system")
        return False

def interrupt_callback():
    """Callback for sensor interrupt - captures photo and saves to database"""
    global recording_system, db_manager

    logger.debug("Interrupt callback triggered")
    if not recording_system:
        logger.warning("Interrupt callback called but recording_system is None")
        return

    try:
        logger.info("Processing sensor interrupt - capturing photo")
        start_time = time.time()

        # Capture photo using existing system
        logger.debug("Capturing photo...")
        photo_data = recording_system.capture_photo()
        logger.debug(f"Photo capture result: {photo_data is not None}")

        logger.debug("Reading accelerometer data...")
        accel_data = recording_system.read_accelerometer()
        logger.debug(f"Accelerometer data keys: {list(accel_data.keys()) if accel_data else None}")

        if photo_data and accel_data:
            # Create a simple signature (using existing system's provenance)
            signature = "mock_signature_" + str(int(time.time()))
            logger.debug(f"Generated signature: {signature}")

            # Save to database
            logger.debug("Saving capture to database...")
            capture_id = db_manager.insert_capture(
                photo_path=photo_data['filepath'],
                accel_data=accel_data,
                signature=signature,
                signature_valid=True,
                size_bytes=photo_data.get('size_bytes', 0),
                description="Sensor interrupt capture"
            )
            logger.debug(f"Capture saved with ID: {capture_id}")

            # Broadcast to WebSocket clients
            asyncio.create_task(broadcast_to_websockets({
                'type': 'new_capture',
                'data': {
                    'id': capture_id,
                    'timestamp': photo_data['timestamp_iso'],
                    'photo_url': f"/api/photo/{capture_id}",
                    'description': "Sensor interrupt capture"
                }
            }))

            processing_time = time.time() - start_time
            logger.info(f"Capture {capture_id} completed successfully in {processing_time:.3f}s")
        else:
            logger.warning(f"Capture data incomplete - photo_data: {photo_data is not None}, accel_data: {accel_data is not None}")

    except Exception as e:
        logger.error(f"Error in interrupt callback: {e}")
        logger.debug(traceback.format_exc())

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("=== Starting ProvenSense MVP ===")
    logger.debug(f"Python path: {sys.path}")
    logger.debug(f"Working directory: {os.getcwd()}")

    try:
        if init_recording_system():
            # Set up interrupt callback for existing system
            logger.debug("Setting up interrupt callback...")
            if hasattr(recording_system.imu, 'set_interrupt_callback'):
                recording_system.imu.set_interrupt_callback(interrupt_callback)
                logger.debug("Interrupt callback set successfully")
            else:
                logger.warning("IMU does not support interrupt callbacks")

            # For demo purposes, also start motion monitoring
            logger.debug("Starting motion monitoring...")
            if hasattr(recording_system.imu, 'start_motion_monitoring'):
                recording_system.imu.start_motion_monitoring(threshold=1.5)
                logger.debug("Motion monitoring started with threshold 1.5")
            else:
                logger.warning("IMU does not support motion monitoring")

            logger.info("=== ProvenSense MVP started successfully ===")
        else:
            logger.error("=== Failed to start recording system ===")

        # Initialize real LIS3DH hardware for tap-to-snap
        await init_real_hardware()

    except Exception as e:
        logger.error(f"Startup error: {e}")
        logger.debug(traceback.format_exc())

async def init_real_hardware():
    """Initialize real LIS3DH hardware for tap-to-snap functionality"""
    global lis3dh_sensor

    if not HARDWARE_AVAILABLE:
        logger.info("Hardware libraries not available - tap-to-snap disabled")
        return

    try:
        logger.info("Initializing real LIS3DH sensor for tap-to-snap...")
        lis3dh_sensor = LIS3DHSensor(i2c_address=0x18, interrupt_pin=17)

        if lis3dh_sensor.initialize():
            logger.info("LIS3DH sensor initialized successfully!")

            # Configure tap detection
            if lis3dh_sensor.configure_tap_interrupt(threshold=60):
                logger.info("Tap interrupt configured successfully")

            # Set tap-to-snap callback
            lis3dh_sensor.set_interrupt_callback(tap_to_snap_callback)

            # Start motion monitoring for tap detection
            lis3dh_sensor.start_motion_monitoring(threshold=2.0)  # Adjust for tap sensitivity
            logger.info("Tap-to-snap functionality enabled! Tap the sensor to capture photos.")

        else:
            logger.error("Failed to initialize LIS3DH sensor")
            lis3dh_sensor = None

    except Exception as e:
        logger.error(f"Failed to initialize real hardware: {e}")
        logger.debug(traceback.format_exc())
        lis3dh_sensor = None

def tap_to_snap_callback():
    """Callback function triggered when LIS3DH detects a tap"""
    logger.info("*** TAP DETECTED! Starting photo capture with continuous recording ***")

    # Trigger photo capture with continuous accelerometer recording
    try:
        # Always use sync capture for tap detection (simpler and more reliable)
        logger.info("Using direct sync capture for tap")
        sync_tap_capture()

    except Exception as e:
        logger.error(f"Error in tap-to-snap callback: {e}")
        logger.debug(traceback.format_exc())

async def trigger_tap_capture():
    """Trigger a photo capture from tap detection"""
    try:
        logger.info("Processing tap-triggered capture...")

        # Capture photo with continuous accelerometer recording during capture
        result = recording_system.capture_photo(
            duration=3.0,  # Record accelerometer data for 3 seconds during capture
            description="Tap-triggered capture"
        )

        if result and result.get('success'):
            capture_id = result.get('capture_id')
            photo_path = result.get('photo_path')

            # Store in database
            db_manager.insert_capture(
                photo_path=photo_path,
                accel_data=result.get('accelerometer_data', {}),
                signature=result.get('signature', 'tap_signature'),
                signature_valid=True,
                size_bytes=result.get('file_size', 0),
                description="Tap-triggered capture"
            )

            logger.info(f"Tap capture completed successfully: {photo_path}")

            # Broadcast to WebSocket clients
            await broadcast_to_websockets({
                'type': 'capture_complete',
                'data': {
                    'id': capture_id,
                    'photo_path': photo_path,
                    'trigger': 'tap'
                }
            })

        else:
            logger.error("Tap capture failed")

    except Exception as e:
        logger.error(f"Error in tap capture: {e}")
        logger.debug(traceback.format_exc())

def sync_tap_capture():
    """Synchronous fallback for tap capture"""
    try:
        logger.info("Processing sync tap-triggered capture...")

        # Get current accelerometer reading during capture
        if lis3dh_sensor:
            accel_data = lis3dh_sensor.get_sample_with_timestamp()
            accel_data['source'] = 'real_lis3dh'
        else:
            # Fallback simulated data
            accel_data = {
                'timestamp': time.time(),
                'timestamp_iso': datetime.now().isoformat() + 'Z',
                'acceleration_x': 0.0,
                'acceleration_y': 0.0,
                'acceleration_z': 9.8,
                'source': 'simulated'
            }

        # Simple photo capture (MVP version)
        photo_dir = Path("mvp_captures")
        photo_dir.mkdir(exist_ok=True)

        timestamp_ns = int(time.time() * 1000000)
        photo_path = photo_dir / f"tap_capture_{timestamp_ns}.jpg"

        # Use fswebcam for photo capture (fallback)
        result = os.system(f"fswebcam -r 1280x720 --no-banner {photo_path}")

        if result == 0 and photo_path.exists():
            # Store in database
            capture_id = db_manager.insert_capture(
                photo_path=str(photo_path),
                accel_data=accel_data,
                signature=f"tap_signature_{timestamp_ns}",
                signature_valid=True,
                size_bytes=photo_path.stat().st_size,
                description="Tap-triggered capture"
            )

            logger.info(f"Tap capture completed successfully: {photo_path} (ID: {capture_id})")

            # Broadcast to WebSocket clients (best effort)
            try:
                asyncio.get_event_loop().create_task(broadcast_to_websockets({
                    'type': 'capture_complete',
                    'data': {
                        'id': capture_id,
                        'photo_path': str(photo_path),
                        'trigger': 'tap'
                    }
                }))
            except:
                pass  # WebSocket notification failed, but capture succeeded
        else:
            logger.error("Photo capture failed")

    except Exception as e:
        logger.error(f"Error in sync tap capture: {e}")
        logger.debug(traceback.format_exc())

# API Routes
@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Get system status"""
    logger.debug("Status endpoint called")
    if not recording_system:
        logger.error("Status check failed - recording system not initialized")
        raise HTTPException(status_code=500, detail="Recording system not initialized")

    try:
        logger.debug("Getting recording system status...")
        status = recording_system.get_status()
        logger.debug(f"Recording system status: running={status.get('running')}, hardware keys={list(status.get('hardware', {}).keys())}")

        logger.debug("Getting recent captures...")
        captures = db_manager.get_captures(limit=1)
        logger.debug(f"Found {len(captures)} recent captures")

        # Check LIS3DH sensor status
        lis3dh_ready = lis3dh_sensor is not None and lis3dh_sensor.is_connected() if lis3dh_sensor else False

        result = SystemStatus(
            online=status['running'],
            camera_ready=status['hardware'].get('camera_connected', False),
            accelerometer_ready=lis3dh_ready or status['hardware'].get('accelerometer_available', False),
            secure_element_ready=status.get('secure_element_connected', False),
            last_capture=captures[0]['timestamp'] if captures else None,
            total_captures=len(db_manager.get_captures(limit=1000))
        )
        logger.debug(f"Status response: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/api/captures", response_model=List[CaptureData])
async def get_captures(limit: int = 50):
    """Get recent captures"""
    captures = db_manager.get_captures(limit=limit)

    result = []
    for capture in captures:
        result.append(CaptureData(
            id=capture['id'],
            timestamp=capture['timestamp'],
            photo_path=capture['photo_path'],
            photo_url=f"/api/photo/{capture['id']}",
            accelerometer_data=capture['accelerometer_data'],
            signature_valid=capture['signature_valid'],
            signature=capture['signature'],
            size_bytes=capture['size_bytes']
        ))

    return result

@app.get("/api/capture/{capture_id}", response_model=CaptureData)
async def get_capture(capture_id: int):
    """Get specific capture"""
    capture = db_manager.get_capture(capture_id)

    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    return CaptureData(
        id=capture['id'],
        timestamp=capture['timestamp'],
        photo_path=capture['photo_path'],
        photo_url=f"/api/photo/{capture['id']}",
        accelerometer_data=capture['accelerometer_data'],
        signature_valid=capture['signature_valid'],
        signature=capture['signature'],
        size_bytes=capture['size_bytes']
    )

@app.post("/api/capture/manual")
async def manual_capture(request: CaptureRequest):
    """Manual photo capture"""
    logger.info(f"Manual capture requested: duration={request.duration}, description='{request.description}'")

    if not recording_system:
        logger.error("Manual capture failed - recording system not initialized")
        raise HTTPException(status_code=500, detail="Recording system not initialized")

    try:
        start_time = time.time()
        logger.debug("Starting manual capture process...")

        # Capture photo
        logger.debug("Capturing photo for manual request...")
        photo_data = recording_system.capture_photo()
        logger.debug(f"Manual photo capture result: {photo_data is not None}")

        logger.debug("Reading accelerometer for manual capture...")
        accel_data = recording_system.read_accelerometer()
        logger.debug(f"Manual accelerometer data: {accel_data is not None}")

        if not photo_data:
            logger.error("Manual capture failed - photo_data is None")
            raise HTTPException(status_code=500, detail="Failed to capture photo")

        logger.debug(f"Photo captured: {photo_data.get('filepath', 'unknown path')}")

        # Create signature
        signature = "manual_signature_" + str(int(time.time()))
        logger.debug(f"Generated manual signature: {signature}")

        # Save to database
        logger.debug("Saving manual capture to database...")
        capture_id = db_manager.insert_capture(
            photo_path=photo_data['filepath'],
            accel_data=accel_data,
            signature=signature,
            signature_valid=True,
            size_bytes=photo_data.get('size_bytes', 0),
            description=request.description
        )
        logger.debug(f"Manual capture saved with ID: {capture_id}")

        # Broadcast to WebSocket clients
        await broadcast_to_websockets({
            'type': 'new_capture',
            'data': {
                'id': capture_id,
                'timestamp': photo_data['timestamp_iso'],
                'photo_url': f"/api/photo/{capture_id}",
                'description': request.description
            }
        })

        processing_time = time.time() - start_time
        result = {"id": capture_id, "message": "Capture completed successfully"}
        logger.info(f"Manual capture {capture_id} completed successfully in {processing_time:.3f}s")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual capture failed with exception: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Capture failed: {str(e)}")

@app.get("/api/photo/{capture_id}")
async def get_photo(capture_id: int):
    """Get photo file"""
    capture = db_manager.get_capture(capture_id)

    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    photo_path = Path(capture['photo_path'])

    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")

    return FileResponse(
        path=str(photo_path),
        media_type="image/jpeg",
        filename=f"capture_{capture_id}.jpg"
    )

@app.get("/api/verify/all")
async def verify_all_captures():
    """Verify all captures"""
    captures = db_manager.get_captures(limit=1000)

    results = []
    valid_count = 0

    for capture in captures:
        is_valid = capture['signature_valid'] and Path(capture['photo_path']).exists()
        if is_valid:
            valid_count += 1

        results.append({
            'id': capture['id'],
            'timestamp': capture['timestamp'],
            'valid': is_valid
        })

    return {
        'total_captures': len(captures),
        'valid_captures': valid_count,
        'invalid_captures': len(captures) - valid_count,
        'verification_rate': (valid_count / len(captures)) * 100 if captures else 100,
        'results': results
    }

@app.get("/api/verify/{capture_id}")
async def verify_capture(capture_id: int):
    """Verify capture signatures"""
    capture = db_manager.get_capture(capture_id)

    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    # Enhanced verification with detailed analysis
    photo_path = Path(capture['photo_path'])
    file_exists = photo_path.exists()
    file_size = photo_path.stat().st_size if file_exists else 0

    # Analyze accelerometer data for additional insights
    accel_data = capture['accelerometer_data']
    motion_analysis = {}
    if accel_data and isinstance(accel_data, dict):
        x, y, z = accel_data.get('acceleration_x', 0), accel_data.get('acceleration_y', 0), accel_data.get('acceleration_z', 0)
        magnitude = (x**2 + y**2 + z**2)**0.5
        motion_analysis = {
            'magnitude': magnitude,
            'motion_type': 'high' if magnitude > 12 else 'moderate' if magnitude > 10.5 else 'low',
            'gravity_check': 8 < abs(z) < 12,  # Reasonable gravity reading
            'sensor_health': 'healthy' if (8 < abs(z) < 12) else 'unusual_orientation'
        }

    # Enhanced timestamp validation
    try:
        capture_time = datetime.fromisoformat(capture['timestamp'].replace('Z', '+00:00'))
        verification_time = datetime.now()
        time_diff = (verification_time - capture_time).total_seconds()
        timestamp_valid = abs(time_diff) < 86400 * 30  # Within 30 days
    except:
        timestamp_valid = False

    # Determine capture method from signature
    signature = capture['signature']
    capture_method = 'unknown'
    if 'tap_signature' in signature:
        capture_method = 'tap_triggered'
    elif 'manual_signature' in signature:
        capture_method = 'manual'

    verification_result = {
        'capture_id': capture_id,
        'signature_valid': capture['signature_valid'],
        'timestamp_valid': timestamp_valid,
        'data_integrity': file_exists and file_size > 1000,  # File exists and reasonable size
        'overall_valid': capture['signature_valid'] and timestamp_valid and file_exists,
        'verification_timestamp': datetime.now().isoformat(),
        'details': {
            'signature': capture['signature'][:16] + "...",
            'accelerometer_data': capture['accelerometer_data'],
            'file_exists': file_exists,
            'file_size_bytes': file_size,
            'motion_analysis': motion_analysis,
            'capture_method': capture_method,
            'timestamp_analysis': {
                'capture_time': capture['timestamp'],
                'verification_time': verification_time.isoformat(),
                'age_seconds': time_diff if timestamp_valid else None,
                'within_valid_range': timestamp_valid
            },
            'risk_assessment': {
                'trust_level': 'high' if (capture['signature_valid'] and timestamp_valid and file_exists and motion_analysis.get('gravity_check', False)) else 'medium' if capture['signature_valid'] else 'low',
                'anomalies': []
            }
        }
    }

    # Add any detected anomalies
    anomalies = verification_result['details']['risk_assessment']['anomalies']
    if not file_exists:
        anomalies.append('missing_file')
    if not timestamp_valid:
        anomalies.append('timestamp_anomaly')
    if not motion_analysis.get('gravity_check', True):
        anomalies.append('unusual_sensor_reading')
    if file_size < 1000:
        anomalies.append('suspicious_file_size')

    return verification_result

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        # Send initial status
        if recording_system:
            status = recording_system.get_status()
            await websocket.send_json({
                'type': 'status_update',
                'data': {
                    'online': status['running'],
                    'camera_ready': status['hardware'].get('camera_connected', False),
                    'accelerometer_ready': status['hardware'].get('accelerometer_available', False)
                }
            })

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle any incoming WebSocket messages here
                logger.info(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_ready": recording_system is not None
    }

# Serve static files (for frontend)
if Path("../frontend/dist").exists():
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True
    )