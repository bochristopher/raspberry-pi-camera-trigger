"""
USB UVC Camera capture functionality
"""
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

logger = logging.getLogger(__name__)


class USBCamera:
    """Production-ready USB UVC camera interface"""

    def __init__(self, device_path: str = "/dev/video0",
                 width: int = 1280, height: int = 720,
                 quality: int = 90):
        """
        Initialize USB camera

        Args:
            device_path: Camera device path
            width: Image width
            height: Image height
            quality: JPEG quality (1-100)
        """
        self.device_path = device_path
        self.width = width
        self.height = height
        self.quality = quality
        self._cap = None

    def initialize(self) -> bool:
        """Initialize camera connection"""
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available, will use fswebcam fallback only")

        try:
            # Test with OpenCV first if available
            if OPENCV_AVAILABLE:
                self._cap = cv2.VideoCapture(self.device_path)
                if not self._cap.isOpened():
                    logger.warning(f"Failed to open camera with OpenCV at {self.device_path}")
                else:
                    # Set resolution
                    self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

                    # Test capture
                    ret, frame = self._cap.read()
                    if ret:
                        logger.info(f"USB camera initialized with OpenCV at {self.device_path} ({self.width}x{self.height})")
                        return True
                    else:
                        logger.warning("Failed to capture test frame with OpenCV")

            # Fallback to fswebcam test
            try:
                result = subprocess.run([
                    "fswebcam", "-d", self.device_path, "--list-controls"
                ], capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"USB camera initialized with fswebcam fallback at {self.device_path}")
                    return True
                else:
                    logger.error(f"fswebcam test failed: {result.stderr.decode()}")
            except subprocess.TimeoutExpired:
                logger.error("fswebcam test timed out")
            except FileNotFoundError:
                logger.error("fswebcam not found in PATH")

            return False

        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False

    def capture_frame_opencv(self) -> Optional[Dict[str, Any]]:
        """Capture frame using OpenCV"""
        if not self._cap or not self._cap.isOpened():
            logger.error("Camera not initialized")
            return None

        try:
            timestamp = time.time()
            ret, frame = self._cap.read()

            if not ret:
                logger.error("Failed to capture frame")
                return None

            # Encode as JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            success, encoded_img = cv2.imencode('.jpg', frame, encode_param)

            if not success:
                logger.error("Failed to encode image")
                return None

            image_data = encoded_img.tobytes()
            image_hash = hashlib.sha256(image_data).hexdigest()

            return {
                'timestamp': timestamp,
                'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
                'image_data': image_data,
                'image_hash': image_hash,
                'width': self.width,
                'height': self.height,
                'format': 'JPEG',
                'quality': self.quality,
                'size_bytes': len(image_data),
                'device': self.device_path,
                'method': 'opencv'
            }

        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            return None

    def capture_frame_fswebcam(self, output_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Capture frame using fswebcam (fallback method)"""
        try:
            timestamp = time.time()

            if output_path is None:
                output_path = f"/tmp/capture_{int(timestamp * 1000000)}.jpg"

            cmd = [
                "fswebcam",
                "-d", self.device_path,
                "-r", f"{self.width}x{self.height}",
                "--jpeg", str(self.quality),
                "--no-banner",
                "--quiet",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.error(f"fswebcam failed: {result.stderr}")
                return None

            # Read the captured image
            image_path = Path(output_path)
            if not image_path.exists():
                logger.error(f"Captured image not found: {output_path}")
                return None

            image_data = image_path.read_bytes()
            image_hash = hashlib.sha256(image_data).hexdigest()

            return {
                'timestamp': timestamp,
                'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
                'image_data': image_data,
                'image_hash': image_hash,
                'width': self.width,
                'height': self.height,
                'format': 'JPEG',
                'quality': self.quality,
                'size_bytes': len(image_data),
                'device': self.device_path,
                'method': 'fswebcam',
                'file_path': str(image_path)
            }

        except subprocess.TimeoutExpired:
            logger.error("fswebcam capture timed out")
            return None
        except Exception as e:
            logger.error(f"fswebcam capture failed: {e}")
            return None

    def capture_frame(self, method: str = "opencv") -> Optional[Dict[str, Any]]:
        """
        Capture a frame using specified method

        Args:
            method: "opencv" or "fswebcam"

        Returns:
            Dictionary containing image data and metadata
        """
        if method == "opencv":
            return self.capture_frame_opencv()
        elif method == "fswebcam":
            return self.capture_frame_fswebcam()
        else:
            logger.error(f"Unknown capture method: {method}")
            return None

    def save_frame(self, frame_data: Dict[str, Any], output_path: str) -> bool:
        """Save captured frame to file"""
        try:
            with open(output_path, 'wb') as f:
                f.write(frame_data['image_data'])
            logger.info(f"Frame saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save frame: {e}")
            return False

    def get_camera_info(self) -> Dict[str, Any]:
        """Get camera information"""
        info = {
            'device_path': self.device_path,
            'width': self.width,
            'height': self.height,
            'quality': self.quality,
            'is_opened': self._cap.isOpened() if self._cap else False
        }

        if self._cap and self._cap.isOpened():
            try:
                info['actual_width'] = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                info['actual_height'] = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info['fps'] = self._cap.get(cv2.CAP_PROP_FPS)
                info['fourcc'] = int(self._cap.get(cv2.CAP_PROP_FOURCC))
            except Exception:
                pass

        return info

    def is_connected(self) -> bool:
        """Check if camera is available and responding"""
        if self._cap and self._cap.isOpened():
            try:
                ret, _ = self._cap.read()
                return ret
            except Exception:
                pass

        # Test with fswebcam as fallback
        try:
            result = subprocess.run([
                "fswebcam", "-d", self.device_path, "--list-controls"
            ], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            pass

        return False

    def cleanup(self):
        """Clean up camera resources"""
        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("USB camera cleaned up")