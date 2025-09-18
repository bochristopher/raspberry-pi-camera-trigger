#!/usr/bin/env python3
"""
Unit tests for ProvenSense MVP Backend
"""
import pytest
import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the main application
from main import app, DatabaseManager, init_recording_system

class TestDatabaseManager:
    """Test database operations"""

    def setup_method(self):
        """Setup test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db.name)

    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database table creation"""
        # Check if tables exist
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        assert ('captures',) in tables

    def test_insert_capture(self):
        """Test inserting capture data"""
        test_data = {
            'acceleration_x': 1.5,
            'acceleration_y': 2.0,
            'acceleration_z': 9.8,
            'timestamp': '2023-01-01T12:00:00Z'
        }

        capture_id = self.db_manager.insert_capture(
            photo_path='/test/path.jpg',
            accel_data=test_data,
            signature='test_signature',
            signature_valid=True,
            size_bytes=1024,
            description='Test capture'
        )

        assert capture_id is not None
        assert isinstance(capture_id, int)

    def test_get_captures(self):
        """Test retrieving captures"""
        # Insert test data first
        test_data = {'x': 1.0, 'y': 2.0, 'z': 3.0}
        self.db_manager.insert_capture(
            photo_path='/test/path.jpg',
            accel_data=test_data,
            signature='test_sig',
            signature_valid=True,
            size_bytes=500
        )

        captures = self.db_manager.get_captures(limit=10)

        assert len(captures) == 1
        assert captures[0]['photo_path'] == '/test/path.jpg'
        assert captures[0]['signature'] == 'test_sig'

    def test_get_capture_by_id(self):
        """Test retrieving specific capture"""
        test_data = {'x': 1.0, 'y': 2.0, 'z': 3.0}
        capture_id = self.db_manager.insert_capture(
            photo_path='/test/specific.jpg',
            accel_data=test_data,
            signature='specific_sig',
            signature_valid=True,
            size_bytes=750
        )

        capture = self.db_manager.get_capture(capture_id)

        assert capture is not None
        assert capture['id'] == capture_id
        assert capture['photo_path'] == '/test/specific.jpg'

    def test_get_nonexistent_capture(self):
        """Test retrieving non-existent capture"""
        capture = self.db_manager.get_capture(99999)
        assert capture is None


class TestAPI:
    """Test FastAPI endpoints"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    @patch('main.recording_system')
    def test_get_status(self, mock_recording_system):
        """Test system status endpoint"""
        # Mock the recording system
        mock_status = {
            'running': True,
            'hardware': {
                'camera_connected': True,
                'accelerometer_available': True
            }
        }
        mock_recording_system.get_status.return_value = mock_status

        response = self.client.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["online"] == True
        assert data["camera_ready"] == True

    def test_get_status_no_system(self):
        """Test status endpoint when recording system not initialized"""
        # Temporarily set recording_system to None
        import main
        original_system = main.recording_system
        main.recording_system = None

        try:
            response = self.client.get("/api/status")
            assert response.status_code == 500
        finally:
            main.recording_system = original_system

    @patch('main.db_manager')
    def test_get_captures(self, mock_db_manager):
        """Test get captures endpoint"""
        mock_captures = [
            {
                'id': 1,
                'timestamp': '2023-01-01T12:00:00Z',
                'photo_path': '/test/1.jpg',
                'accelerometer_data': {'x': 1.0, 'y': 2.0, 'z': 3.0},
                'signature': 'test_sig',
                'signature_valid': True,
                'size_bytes': 1024,
                'description': 'Test'
            }
        ]
        mock_db_manager.get_captures.return_value = mock_captures

        response = self.client.get("/api/captures")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["photo_url"] == "/api/photo/1"

    @patch('main.db_manager')
    def test_get_capture_by_id(self, mock_db_manager):
        """Test get specific capture endpoint"""
        mock_capture = {
            'id': 1,
            'timestamp': '2023-01-01T12:00:00Z',
            'photo_path': '/test/1.jpg',
            'accelerometer_data': {'x': 1.0, 'y': 2.0, 'z': 3.0},
            'signature': 'test_sig',
            'signature_valid': True,
            'size_bytes': 1024,
            'description': 'Test'
        }
        mock_db_manager.get_capture.return_value = mock_capture

        response = self.client.get("/api/capture/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["signature"] == "test_sig"

    @patch('main.db_manager')
    def test_get_capture_not_found(self, mock_db_manager):
        """Test get non-existent capture"""
        mock_db_manager.get_capture.return_value = None

        response = self.client.get("/api/capture/99999")

        assert response.status_code == 404

    @patch('main.recording_system')
    @patch('main.db_manager')
    def test_manual_capture_success(self, mock_db_manager, mock_recording_system):
        """Test manual capture endpoint"""
        # Mock successful capture
        mock_photo_data = {
            'filepath': '/test/manual.jpg',
            'timestamp_iso': '2023-01-01T12:00:00Z',
            'size_bytes': 1024
        }
        mock_accel_data = {'x': 1.0, 'y': 2.0, 'z': 3.0}

        mock_recording_system.capture_photo.return_value = mock_photo_data
        mock_recording_system.read_accelerometer.return_value = mock_accel_data
        mock_db_manager.insert_capture.return_value = 1

        response = self.client.post("/api/capture/manual", json={
            "duration": 2.0,
            "description": "Test manual capture"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "message" in data

    @patch('main.recording_system')
    def test_manual_capture_no_system(self, mock_recording_system):
        """Test manual capture when system not initialized"""
        import main
        original_system = main.recording_system
        main.recording_system = None

        try:
            response = self.client.post("/api/capture/manual", json={
                "duration": 2.0,
                "description": "Test"
            })
            assert response.status_code == 500
        finally:
            main.recording_system = original_system

    @patch('main.recording_system')
    def test_manual_capture_failure(self, mock_recording_system):
        """Test manual capture failure"""
        mock_recording_system.capture_photo.return_value = None

        response = self.client.post("/api/capture/manual", json={
            "duration": 2.0,
            "description": "Test"
        })

        assert response.status_code == 500

    @patch('main.db_manager')
    def test_verify_capture(self, mock_db_manager):
        """Test capture verification endpoint"""
        mock_capture = {
            'id': 1,
            'photo_path': '/test/1.jpg',
            'signature_valid': True,
            'signature': 'test_signature',
            'accelerometer_data': {'x': 1.0, 'y': 2.0, 'z': 3.0}
        }
        mock_db_manager.get_capture.return_value = mock_capture

        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            response = self.client.get("/api/verify/1")

        assert response.status_code == 200
        data = response.json()
        assert data["capture_id"] == 1
        assert data["overall_valid"] == True

    @patch('main.db_manager')
    def test_verify_all_captures(self, mock_db_manager):
        """Test verify all captures endpoint"""
        mock_captures = [
            {
                'id': 1,
                'timestamp': '2023-01-01T12:00:00Z',
                'signature_valid': True,
                'photo_path': '/test/1.jpg'
            },
            {
                'id': 2,
                'timestamp': '2023-01-01T12:01:00Z',
                'signature_valid': True,
                'photo_path': '/test/2.jpg'
            }
        ]
        mock_db_manager.get_captures.return_value = mock_captures

        with patch('pathlib.Path.exists', return_value=True):
            response = self.client.get("/api/verify/all")

        assert response.status_code == 200
        data = response.json()
        assert data["total_captures"] == 2
        assert data["valid_captures"] == 2
        assert data["verification_rate"] == 100.0


class TestRecordingSystemIntegration:
    """Test integration with recording system"""

    @patch('main.SecureContinuousRecordingSystem')
    def test_init_recording_system_success(self, mock_system_class):
        """Test successful recording system initialization"""
        mock_instance = Mock()
        mock_instance.initialize.return_value = True
        mock_system_class.return_value = mock_instance

        result = init_recording_system()

        assert result == True
        mock_instance.initialize.assert_called_once()
        mock_instance.start.assert_called_once()

    @patch('main.SecureContinuousRecordingSystem')
    def test_init_recording_system_failure(self, mock_system_class):
        """Test failed recording system initialization"""
        mock_instance = Mock()
        mock_instance.initialize.return_value = False
        mock_system_class.return_value = mock_instance

        result = init_recording_system()

        assert result == False
        mock_instance.initialize.assert_called_once()
        mock_instance.start.assert_not_called()


class TestInterruptCallback:
    """Test interrupt callback functionality"""

    @patch('main.recording_system')
    @patch('main.db_manager')
    def test_interrupt_callback_success(self, mock_db_manager, mock_recording_system):
        """Test successful interrupt callback"""
        from main import interrupt_callback

        # Mock successful capture
        mock_photo_data = {
            'filepath': '/test/interrupt.jpg',
            'timestamp_iso': '2023-01-01T12:00:00Z',
            'size_bytes': 1024
        }
        mock_accel_data = {'x': 1.0, 'y': 2.0, 'z': 3.0}

        mock_recording_system.capture_photo.return_value = mock_photo_data
        mock_recording_system.read_accelerometer.return_value = mock_accel_data
        mock_db_manager.insert_capture.return_value = 1

        # Should not raise any exceptions
        interrupt_callback()

        mock_recording_system.capture_photo.assert_called_once()
        mock_recording_system.read_accelerometer.assert_called_once()
        mock_db_manager.insert_capture.assert_called_once()

    @patch('main.recording_system')
    def test_interrupt_callback_no_system(self, mock_recording_system):
        """Test interrupt callback when no recording system"""
        from main import interrupt_callback

        import main
        original_system = main.recording_system
        main.recording_system = None

        try:
            # Should not raise any exceptions
            interrupt_callback()
        finally:
            main.recording_system = original_system


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])