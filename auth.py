import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
from config import config
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.secret_key = config.security.jwt_secret
        self.session_timeout = config.security.session_timeout
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed
    
    def generate_token(self, username: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        if not config.security.enable_auth:
            return True
        
        # Check against configured admin credentials
        if username == config.security.admin_username:
            return self.verify_password(password, self.hash_password(config.security.admin_password))
        
        # Here you could add database user authentication
        # For now, only admin user is supported
        return False
    
    def login_required(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not config.security.enable_auth:
                return f(*args, **kwargs)
            
            # Check session
            if 'username' in session:
                return f(*args, **kwargs)
            
            # Check JWT token in Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.split(' ')[1]  # Bearer <token>
                    payload = self.verify_token(token)
                    if payload:
                        session['username'] = payload['username']
                        return f(*args, **kwargs)
                except (IndexError, AttributeError):
                    pass
            
            # Return 401 for API requests, redirect for web requests
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect(url_for('login'))
        
        return decorated_function
    
    def admin_required(self, f):
        """Decorator to require admin privileges"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not config.security.enable_auth:
                return f(*args, **kwargs)
            
            username = session.get('username')
            if not username or username != config.security.admin_username:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Admin privileges required'}), 403
                else:
                    return redirect(url_for('login'))
            
            return f(*args, **kwargs)
        
        return decorated_function

# Global auth manager instance
auth_manager = AuthManager()

# Flask routes for authentication
def init_auth_routes(app):
    """Initialize authentication routes"""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page and authentication"""
        if not config.security.enable_auth:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if auth_manager.authenticate_user(username, password):
                session['username'] = username
                session['login_time'] = datetime.now().isoformat()
                
                # Generate JWT token for API access
                token = auth_manager.generate_token(username)
                session['token'] = token
                
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('index'))
            else:
                logger.warning(f"Failed login attempt for user {username}")
                return render_template('login.html', error='Invalid credentials')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout user"""
        username = session.get('username')
        if username:
            logger.info(f"User {username} logged out")
        
        session.clear()
        return redirect(url_for('login'))
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        """API login endpoint"""
        if not config.security.enable_auth:
            return jsonify({'token': 'no-auth-required'})
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if auth_manager.authenticate_user(username, password):
            token = auth_manager.generate_token(username)
            return jsonify({
                'token': token,
                'username': username,
                'expires_in': config.security.session_timeout
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    @app.route('/api/verify', methods=['POST'])
    def api_verify():
        """API token verification endpoint"""
        if not config.security.enable_auth:
            return jsonify({'valid': True})
        
        data = request.get_json()
        token = data.get('token')
        
        payload = auth_manager.verify_token(token)
        if payload:
            return jsonify({
                'valid': True,
                'username': payload['username']
            })
        else:
            return jsonify({'valid': False}), 401

# Security headers middleware
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    if config.environment == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Rate limiting decorator
def rate_limit(max_requests=100, window=3600):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting
            # In production, use Redis or similar
            client_ip = request.remote_addr
            current_time = datetime.now()
            
            # This is a simplified implementation
            # In production, implement proper rate limiting
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
