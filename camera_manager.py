import cv2
import threading
import time
import logging
from typing import Optional, Callable
from config import config

class CameraManager:
    """Manages different camera sources for production deployment"""
    
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.frame = None
        self.lock = threading.Lock()
        self.callbacks = []
        self.logger = logging.getLogger(__name__)
        
    def initialize_camera(self) -> bool:
        """Initialize camera based on configuration"""
        try:
            if config.camera.source_type == 'webcam':
                return self._init_webcam()
            elif config.camera.source_type == 'ip_camera':
                return self._init_ip_camera()
            elif config.camera.source_type == 'rtsp':
                return self._init_rtsp_camera()
            elif config.camera.source_type == 'file':
                return self._init_file_camera()
            else:
                self.logger.error(f"Unsupported camera type: {config.camera.source_type}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def _init_webcam(self) -> bool:
        """Initialize local webcam"""
        self.camera = cv2.VideoCapture(int(config.camera.source))
        if not self.camera.isOpened():
            self.logger.error(f"Failed to open webcam {config.camera.source}")
            return False
        
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.resolution[1])
        self.camera.set(cv2.CAP_PROP_FPS, config.camera.fps)
        
        self.logger.info(f"Webcam initialized: {config.camera.resolution} @ {config.camera.fps}fps")
        return True
    
    def _init_ip_camera(self) -> bool:
        """Initialize IP camera"""
        source = config.get_camera_source()
        self.camera = cv2.VideoCapture(source)
        
        if not self.camera.isOpened():
            self.logger.error(f"Failed to connect to IP camera: {source}")
            return False
        
        # Set buffer size to reduce latency
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.resolution[1])
        
        self.logger.info(f"IP camera connected: {source}")
        return True
    
    def _init_rtsp_camera(self) -> bool:
        """Initialize RTSP camera stream"""
        source = config.get_camera_source()
        self.camera = cv2.VideoCapture(source)
        
        if not self.camera.isOpened():
            self.logger.error(f"Failed to connect to RTSP stream: {source}")
            return False
        
        # RTSP specific settings
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.camera.set(cv2.CAP_PROP_FPS, config.camera.fps)
        
        self.logger.info(f"RTSP stream connected: {source}")
        return True
    
    def _init_file_camera(self) -> bool:
        """Initialize file-based camera (for testing)"""
        self.camera = cv2.VideoCapture(config.camera.source)
        
        if not self.camera.isOpened():
            self.logger.error(f"Failed to open video file: {config.camera.source}")
            return False
        
        self.logger.info(f"Video file opened: {config.camera.source}")
        return True
    
    def start_capture(self):
        """Start camera capture in separate thread"""
        if not self.initialize_camera():
            return False
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        return True
    
    def _capture_loop(self):
        """Main capture loop"""
        while self.is_running:
            ret, frame = self.camera.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
                
                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(frame)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")
            else:
                self.logger.warning("Failed to read frame from camera")
                time.sleep(0.1)
    
    def get_frame(self) -> Optional[any]:
        """Get latest frame"""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def add_callback(self, callback: Callable):
        """Add frame callback"""
        self.callbacks.append(callback)
    
    def stop_capture(self):
        """Stop camera capture"""
        self.is_running = False
        if self.camera:
            self.camera.release()
        self.logger.info("Camera capture stopped")
    
    def is_connected(self) -> bool:
        """Check if camera is connected"""
        return self.camera is not None and self.camera.isOpened()

# Global camera manager instance
camera_manager = CameraManager()
