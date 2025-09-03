import psutil
import time
import threading
from datetime import datetime, timedelta
from flask import jsonify, request
from config import config
from camera_manager import camera_manager
from database import db_manager
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    """System monitoring and health check manager"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': [],
            'face_detections': 0,
            'attendance_records': 0,
            'errors': 0,
            'last_update': datetime.now()
        }
        self.monitoring_active = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start system monitoring in background thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                time.sleep(30)  # Collect metrics every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': cpu_percent
            })
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': memory.percent,
                'available': memory.available,
                'total': memory.total
            })
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics['disk_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': (disk.used / disk.total) * 100,
                'free': disk.free,
                'total': disk.total
            })
            
            # Network I/O
            network = psutil.net_io_counters()
            self.metrics['network_io'].append({
                'timestamp': datetime.now().isoformat(),
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            })
            
            # Keep only last 100 entries for each metric
            for key in ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io']:
                if len(self.metrics[key]) > 100:
                    self.metrics[key] = self.metrics[key][-100:]
            
            self.metrics['last_update'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            self.metrics['errors'] += 1
    
    def get_system_health(self):
        """Get comprehensive system health status"""
        try:
            # Current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Uptime
            uptime = datetime.now() - self.start_time
            
            # Camera status
            camera_status = camera_manager.is_connected()
            
            # Database status
            db_status = db_manager.test_connection()
            
            # Overall health
            health_status = 'healthy'
            issues = []
            
            if cpu_percent > 90:
                health_status = 'warning'
                issues.append('High CPU usage')
            
            if memory.percent > 90:
                health_status = 'critical'
                issues.append('High memory usage')
            
            if (disk.used / disk.total) * 100 > 90:
                health_status = 'warning'
                issues.append('Low disk space')
            
            if not camera_status:
                health_status = 'critical'
                issues.append('Camera not connected')
            
            if not db_status:
                health_status = 'critical'
                issues.append('Database connection failed')
            
            return {
                'status': health_status,
                'uptime': str(uptime),
                'timestamp': datetime.now().isoformat(),
                'environment': config.environment,
                'issues': issues,
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': (disk.used / disk.total) * 100,
                    'disk_free': disk.free
                },
                'services': {
                    'camera': camera_status,
                    'database': db_status
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_metrics(self, metric_type=None, hours=24):
        """Get historical metrics"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            if metric_type and metric_type in self.metrics:
                # Return specific metric
                filtered_metrics = [
                    m for m in self.metrics[metric_type]
                    if datetime.fromisoformat(m['timestamp']) > cutoff_time
                ]
                return {
                    'metric_type': metric_type,
                    'data': filtered_metrics,
                    'count': len(filtered_metrics)
                }
            else:
                # Return all metrics
                result = {}
                for key, values in self.metrics.items():
                    if isinstance(values, list):
                        filtered_values = [
                            v for v in values
                            if datetime.fromisoformat(v['timestamp']) > cutoff_time
                        ]
                        result[key] = {
                            'data': filtered_values,
                            'count': len(filtered_values)
                        }
                    else:
                        result[key] = values
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {'error': str(e)}
    
    def increment_face_detection(self):
        """Increment face detection counter"""
        self.metrics['face_detections'] += 1
    
    def increment_attendance_record(self):
        """Increment attendance record counter"""
        self.metrics['attendance_records'] += 1
    
    def increment_error(self):
        """Increment error counter"""
        self.metrics['errors'] += 1

# Global system monitor instance
system_monitor = SystemMonitor()

# Flask routes for monitoring
def init_monitoring_routes(app):
    """Initialize monitoring routes"""
    
    @app.route('/api/health')
    def api_health():
        """API health check endpoint"""
        return jsonify(system_monitor.get_system_health())
    
    @app.route('/api/metrics')
    def api_metrics():
        """API metrics endpoint"""
        metric_type = request.args.get('type')
        hours = int(request.args.get('hours', 24))
        return jsonify(system_monitor.get_metrics(metric_type, hours))
    
    @app.route('/api/status')
    def api_status():
        """API status endpoint"""
        return jsonify({
            'status': 'running',
            'uptime': str(datetime.now() - system_monitor.start_time),
            'environment': config.environment,
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/logs')
    def api_logs():
        """API logs endpoint"""
        try:
            limit = int(request.args.get('limit', 100))
            logs = db_manager.get_system_logs(limit)
            return jsonify({
                'logs': logs,
                'count': len(logs)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/camera/status')
    def api_camera_status():
        """API camera status endpoint"""
        return jsonify({
            'connected': camera_manager.is_connected(),
            'type': config.camera.source_type,
            'source': config.camera.source if config.environment != 'production' else 'hidden',
            'resolution': config.camera.resolution,
            'fps': config.camera.fps
        })
    
    @app.route('/api/database/status')
    def api_database_status():
        """API database status endpoint"""
        try:
            connected = db_manager.test_connection()
            stats = db_manager.get_attendance_stats(datetime.now().strftime("%d/%m/%Y"))
            return jsonify({
                'connected': connected,
                'type': config.database.type,
                'name': config.database.name if config.environment != 'production' else 'hidden',
                'today_stats': stats
            })
        except Exception as e:
            return jsonify({
                'connected': False,
                'error': str(e)
            }), 500
