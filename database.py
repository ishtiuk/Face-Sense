import sqlite3
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager supporting SQLite and PostgreSQL"""
    
    def __init__(self):
        self.db_type = config.database.type
        self.db_config = config.database
        
    def get_connection(self):
        """Get database connection based on configuration"""
        if self.db_type == 'postgresql':
            return self._get_postgresql_connection()
        else:
            return self._get_sqlite_connection()
    
    def _get_sqlite_connection(self):
        """Get SQLite connection"""
        return sqlite3.connect(self.db_config.name)
    
    def _get_postgresql_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(
            host=self.db_config.host,
            port=self.db_config.port,
            database=self.db_config.name,
            user=self.db_config.username,
            password=self.db_config.password
        )
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        conn = self.get_connection()
        try:
            if self.db_type == 'postgresql':
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        if self.db_type == 'postgresql':
            self._create_postgresql_tables()
        else:
            self._create_sqlite_tables()
    
    def _create_sqlite_tables(self):
        """Create SQLite tables"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_name TEXT NOT NULL,
                    employee_id TEXT,
                    time_in TEXT,
                    time_out TEXT,
                    status TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def _create_postgresql_tables(self):
        """Create PostgreSQL tables"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    employee_name VARCHAR(255) NOT NULL,
                    employee_id VARCHAR(50),
                    time_in VARCHAR(20),
                    time_out VARCHAR(20),
                    status VARCHAR(10) NOT NULL,
                    date VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id SERIAL PRIMARY KEY,
                    level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_date 
                ON attendance(date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_employee 
                ON attendance(employee_name)
            ''')
    
    def insert_attendance(self, employee_name, employee_id, time_in, time_out, status, date):
        """Insert attendance record"""
        with self.get_cursor() as cursor:
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO attendance (employee_name, employee_id, time_in, time_out, status, date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (employee_name, employee_id, time_in, time_out, status, date))
            else:
                cursor.execute('''
                    INSERT INTO attendance (employee_name, employee_id, time_in, time_out, status, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (employee_name, employee_id, time_in, time_out, status, date))
    
    def update_attendance(self, employee_name, date, time_out, status):
        """Update attendance record"""
        with self.get_cursor() as cursor:
            if self.db_type == 'postgresql':
                cursor.execute('''
                    UPDATE attendance 
                    SET time_out = %s, status = %s 
                    WHERE employee_name = %s AND date = %s
                ''', (time_out, status, employee_name, date))
            else:
                cursor.execute('''
                    UPDATE attendance 
                    SET time_out = ?, status = ? 
                    WHERE employee_name = ? AND date = ?
                ''', (time_out, status, employee_name, date))
    
    def get_attendance_by_date(self, date):
        """Get attendance records for a specific date"""
        with self.get_cursor() as cursor:
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT * FROM attendance 
                    WHERE date = %s 
                    ORDER BY created_at DESC
                ''', (date,))
            else:
                cursor.execute('''
                    SELECT * FROM attendance 
                    WHERE date = ? 
                    ORDER BY created_at DESC
                ''', (date,))
            
            if self.db_type == 'postgresql':
                return [dict(row) for row in cursor.fetchall()]
            else:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_attendance_by_employee(self, employee_name, start_date=None, end_date=None):
        """Get attendance records for a specific employee"""
        with self.get_cursor() as cursor:
            if start_date and end_date:
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT * FROM attendance 
                        WHERE employee_name = %s AND date BETWEEN %s AND %s
                        ORDER BY date DESC
                    ''', (employee_name, start_date, end_date))
                else:
                    cursor.execute('''
                        SELECT * FROM attendance 
                        WHERE employee_name = ? AND date BETWEEN ? AND ?
                        ORDER BY date DESC
                    ''', (employee_name, start_date, end_date))
            else:
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT * FROM attendance 
                        WHERE employee_name = %s 
                        ORDER BY date DESC
                    ''', (employee_name,))
                else:
                    cursor.execute('''
                        SELECT * FROM attendance 
                        WHERE employee_name = ? 
                        ORDER BY date DESC
                    ''', (employee_name,))
            
            if self.db_type == 'postgresql':
                return [dict(row) for row in cursor.fetchall()]
            else:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_attendance_stats(self, date):
        """Get attendance statistics for a specific date"""
        with self.get_cursor() as cursor:
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_employees,
                        COUNT(CASE WHEN status = 'IN' THEN 1 END) as checked_in,
                        COUNT(CASE WHEN status = 'OUT' THEN 1 END) as checked_out
                    FROM attendance 
                    WHERE date = %s
                ''', (date,))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_employees,
                        COUNT(CASE WHEN status = 'IN' THEN 1 END) as checked_in,
                        COUNT(CASE WHEN status = 'OUT' THEN 1 END) as checked_out
                    FROM attendance 
                    WHERE date = ?
                ''', (date,))
            
            result = cursor.fetchone()
            if self.db_type == 'postgresql':
                return dict(result)
            else:
                return {
                    'total_employees': result[0],
                    'checked_in': result[1],
                    'checked_out': result[2]
                }
    
    def log_system_event(self, level, message):
        """Log system event to database"""
        with self.get_cursor() as cursor:
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO system_logs (level, message)
                    VALUES (%s, %s)
                ''', (level, message))
            else:
                cursor.execute('''
                    INSERT INTO system_logs (level, message)
                    VALUES (?, ?)
                ''', (level, message))
    
    def get_system_logs(self, limit=100):
        """Get recent system logs"""
        with self.get_cursor() as cursor:
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT * FROM system_logs 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT * FROM system_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            if self.db_type == 'postgresql':
                return [dict(row) for row in cursor.fetchall()]
            else:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                if self.db_type == 'postgresql':
                    cursor.execute('SELECT 1')
                else:
                    cursor.execute('SELECT 1')
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()
