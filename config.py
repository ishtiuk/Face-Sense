import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class CameraConfig:
    """Camera configuration for different deployment scenarios"""
    source_type: str  # 'webcam', 'ip_camera', 'rtsp', 'file'
    source: str  # Camera source (0 for webcam, URL for IP camera, file path for video)
    resolution: tuple = (640, 480)
    fps: int = 30
    username: Optional[str] = None
    password: Optional[str] = None

@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = 'sqlite'  # 'sqlite', 'postgresql', 'mysql'
    host: Optional[str] = None
    port: Optional[int] = None
    name: str = 'attendance_data/attendance.db'
    username: Optional[str] = None
    password: Optional[str] = None

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_auth: bool = False
    secret_key: str = 'your-secret-key-here'
    admin_username: str = 'admin'
    admin_password: str = 'admin123'
    jwt_secret: str = 'jwt-secret-key'
    session_timeout: int = 3600  # 1 hour

@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = False
    host: str = '0.0.0.0'
    port: int = 5000
    environment: str = 'development'  # 'development', 'staging', 'production'
    log_level: str = 'INFO'
    max_upload_size: int = 16 * 1024 * 1024  # 16MB

class Config:
    """Configuration manager for different environments"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self._load_config()
    
    def _load_config(self):
        """Load configuration based on environment"""
        if self.environment == 'production':
            self._load_production_config()
        elif self.environment == 'staging':
            self._load_staging_config()
        else:
            self._load_development_config()
    
    def _load_development_config(self):
        """Development environment configuration"""
        self.camera = CameraConfig(
            source_type='webcam',
            source='0',
            resolution=(640, 480),
            fps=30
        )
        
        self.database = DatabaseConfig(
            type='sqlite',
            name='attendance_data/attendance.db'
        )
        
        self.security = SecurityConfig(
            enable_auth=False,
            secret_key='dev-secret-key'
        )
        
        self.app = AppConfig(
            debug=True,
            host='127.0.0.1',
            port=5000,
            environment='development',
            log_level='DEBUG'
        )
    
    def _load_staging_config(self):
        """Staging environment configuration"""
        self.camera = CameraConfig(
            source_type=os.getenv('CAMERA_TYPE', 'ip_camera'),
            source=os.getenv('CAMERA_SOURCE', 'http://192.168.1.100:8080/video'),
            resolution=(1280, 720),
            fps=30,
            username=os.getenv('CAMERA_USERNAME'),
            password=os.getenv('CAMERA_PASSWORD')
        )
        
        self.database = DatabaseConfig(
            type=os.getenv('DB_TYPE', 'sqlite'),
            name=os.getenv('DB_NAME', 'attendance_data/attendance.db'),
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 0)) if os.getenv('DB_PORT') else None,
            username=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD')
        )
        
        self.security = SecurityConfig(
            enable_auth=True,
            secret_key=os.getenv('SECRET_KEY', 'staging-secret-key'),
            admin_username=os.getenv('ADMIN_USERNAME', 'admin'),
            admin_password=os.getenv('ADMIN_PASSWORD', 'admin123')
        )
        
        self.app = AppConfig(
            debug=False,
            host='0.0.0.0',
            port=int(os.getenv('PORT', 5000)),
            environment='staging',
            log_level='INFO'
        )
    
    def _load_production_config(self):
        """Production environment configuration"""
        self.camera = CameraConfig(
            source_type=os.getenv('CAMERA_TYPE', 'ip_camera'),
            source=os.getenv('CAMERA_SOURCE', 'rtsp://camera.example.com:554/stream'),
            resolution=(1920, 1080),
            fps=30,
            username=os.getenv('CAMERA_USERNAME'),
            password=os.getenv('CAMERA_PASSWORD')
        )
        
        self.database = DatabaseConfig(
            type=os.getenv('DB_TYPE', 'postgresql'),
            name=os.getenv('DB_NAME', 'face_sense_prod'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            username=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD')
        )
        
        self.security = SecurityConfig(
            enable_auth=True,
            secret_key=os.getenv('SECRET_KEY'),
            admin_username=os.getenv('ADMIN_USERNAME'),
            admin_password=os.getenv('ADMIN_PASSWORD'),
            jwt_secret=os.getenv('JWT_SECRET'),
            session_timeout=int(os.getenv('SESSION_TIMEOUT', 3600))
        )
        
        self.app = AppConfig(
            debug=False,
            host='0.0.0.0',
            port=int(os.getenv('PORT', 5000)),
            environment='production',
            log_level='WARNING'
        )
    
    def get_camera_source(self) -> str:
        """Get formatted camera source with authentication if needed"""
        if self.camera.source_type == 'ip_camera' and self.camera.username:
            # Format: http://username:password@host:port/path
            if '://' in self.camera.source:
                protocol, rest = self.camera.source.split('://', 1)
                return f"{protocol}://{self.camera.username}:{self.camera.password}@{rest}"
            else:
                return f"http://{self.camera.username}:{self.camera.password}@{self.camera.source}"
        return self.camera.source
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return any issues"""
        issues = []
        
        if self.environment == 'production':
            if not self.security.secret_key or self.security.secret_key == 'your-secret-key-here':
                issues.append("Production requires a secure SECRET_KEY")
            
            if not self.security.admin_password or self.security.admin_password == 'admin123':
                issues.append("Production requires a secure ADMIN_PASSWORD")
            
            if self.camera.source_type == 'ip_camera' and not self.camera.source:
                issues.append("IP camera source is required for production")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'environment': self.environment
        }

# Global config instance
config = Config()
