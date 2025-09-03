import os
import cv2
import csv
import sqlite3
import numpy as np
from pickle import load
import face_recognition
from datetime import datetime
from flask import Flask, render_template, Response, jsonify
import logging
from config import config
from camera_manager import camera_manager
from database import db_manager
from auth import auth_manager, init_auth_routes, add_security_headers
from monitoring import system_monitor, init_monitoring_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.app.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.security.secret_key

# Add security headers to all responses
app.after_request(add_security_headers)

# Use database name from config
db_name = config.database.name

# Load both original and enhanced encodings
try:
    known_names = load(open(os.path.join("model_data", "known_names.bin"), "rb"))
    known_encodings = load(open(os.path.join("model_data", "known_encodings.bin"), "rb"))
    enhanced_encodings = load(open(os.path.join("model_data", "enhanced", "enhanced_encodings.bin"), "rb"))
    quality_scores = load(open(os.path.join("model_data", "enhanced", "quality_scores.bin"), "rb"))
    print(f"[+] Loaded enhanced model with {len(enhanced_encodings)} enhanced profiles")
except FileNotFoundError:
    print("[!] Enhanced model not found, falling back to basic model")
    enhanced_encodings = []
    quality_scores = []

# Process employee photos and extract IDs
print("[+] Processing employee information...")
employee_ids = {}
employee_names = []
employee_id_list = []

# Parse filenames from student_photos directory
for filename in os.listdir("employee_photos"):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        # Extract name and ID from filename
        name_parts = filename.split('.')[0].split('_')
        
        if len(name_parts) >= 3:
            # Extract employee ID (last part)
            employee_id = name_parts[-1]
            # Extract name (all parts except the last one which is the employee ID)
            employee_name = " ".join(name_parts[:-1]).title()
            
            # Store mapping of name to ID
            employee_ids[employee_name] = employee_id
            employee_names.append(employee_name)
            employee_id_list.append(employee_id)
            
            print(f"[+] Extracted - Name: {employee_name}, ID: {employee_id}")
        else:
            # If filename doesn't match expected format
            employee_name = " ".join(name_parts).title()
            employee_ids[employee_name] = "N/A"
            employee_names.append(employee_name)
            employee_id_list.append("N/A")
            
            print(f"[+] Extracted - Name: {employee_name}, ID: N/A (ID not found in filename)")

# Use the extracted employee names instead of known_names if available
if employee_names:
    print(f"[+] Found {len(employee_names)} employees from filenames")
else:
    print("[!] No employee names extracted from filenames, using known_names")
    employee_names = known_names

# Initialize camera manager instead of direct VideoCapture
logger.info(f"Initializing camera manager for {config.camera.source_type}")
if not camera_manager.start_capture():
    logger.error("Failed to initialize camera manager")
    exit(1)

# Remove the problematic attendance_list - we'll track attendance properly in the database

def time_updater():
    return datetime.now().strftime("%d/%m/%Y  %I:%M:%S %p")

def insert_attendance_database(employee_name, time_entry, status):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Get employee ID if available
    employee_id = employee_ids.get(employee_name, "N/A")
    
    # Get current date in dd/mm/yyyy format
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    try:
        # Check if employee already has an entry for today
        cursor.execute("SELECT * FROM attendance WHERE employee_name = ? AND date = ?", (employee_name, current_date))
        existing_record = cursor.fetchone()
        
        if existing_record is None:
            # First detection of the day - create new record
            if status == "IN":
                cursor.execute(
                    "INSERT INTO attendance(employee_name, employee_id, time_in, time_out, status, date) VALUES (?, ?, ?, ?, ?, ?)", 
                    (employee_name, employee_id, time_entry, "", status, current_date)
                )
                print(f"[+] Employee first check-IN: {employee_name} (ID: {employee_id}) at {time_entry}")
            else:  # status == "OUT"
                cursor.execute(
                    "INSERT INTO attendance(employee_name, employee_id, time_in, time_out, status, date) VALUES (?, ?, ?, ?, ?, ?)", 
                    (employee_name, employee_id, "", time_entry, status, current_date)
                )
                print(f"[+] Employee first check-OUT: {employee_name} (ID: {employee_id}) at {time_entry}")
        else:
            # Employee already has record for today - update check-out time (last detection)
            print(f"[DEBUG] Updating existing record for {employee_name} - Current status: {status}")
            if status == "OUT":
                cursor.execute(
                    "UPDATE attendance SET time_out = ?, status = ? WHERE employee_name = ? AND date = ?", 
                    (time_entry, status, employee_name, current_date)
                )
                print(f"[+] Employee last check-OUT updated: {employee_name} (ID: {employee_id}) at {time_entry}")
            else:  # status == "IN" - update check-in time if it's earlier
                current_time_in = existing_record[2]  # time_in field
                if not current_time_in or time_entry < current_time_in:
                    cursor.execute(
                        "UPDATE attendance SET time_in = ? WHERE employee_name = ? AND date = ?", 
                        (time_entry, employee_name, current_date)
                    )
                    print(f"[+] Employee check-IN updated (earlier time): {employee_name} (ID: {employee_id}) at {time_entry}")
                else:
                    print(f"[DEBUG] Check-IN time not updated - current: {current_time_in}, new: {time_entry}")
        
        conn.commit()
    except sqlite3.IntegrityError as err:
        print(f"\n[Error: {err}] [{time_updater()}]")
        conn.rollback()
    except Exception as e:
        print(f"\n[Error: {e}] [{time_updater()}]")
        conn.rollback()
    finally:
        conn.close()

def determine_check_status():
    """Determine if current time is for check-in or check-out"""
    current_hour = datetime.now().hour
    
    # Morning hours (before 12 PM) - Check IN
    if current_hour < 12:
        return "IN"
    # Afternoon/Evening hours (after 12 PM) - Check OUT
    else:
        return "OUT"

# Database initialization handled by init_db.py

def enhanced_face_recognition(face_encoding):
    """Enhanced face recognition using multiple encodings per person"""
    try:
        if not enhanced_encodings or not known_encodings or len(known_encodings) == 0:
            # No encodings available or fallback to basic recognition
            return "Unknown", 0, 0.0
            
        # Basic recognition as fallback
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        
        if len(face_distances) == 0:
            return "Unknown", 0, 0.0
            
        best_match_index = np.argmin(face_distances)
        
        if matches[best_match_index]:
            name = known_names[best_match_index]
            accuracy = round((1 - min(face_distances)) * 100)
            basic_result = (name, accuracy, 1.0)  # Default quality for basic mode
        else:
            basic_result = ("Unknown", 0, 0.0)
        
        # If no enhanced encodings, return basic result
        if not enhanced_encodings:
            return basic_result
        
        # Enhanced recognition with multiple encodings
        best_match = None
        best_accuracy = 0
        best_quality = 0
        raw_accuracy = 0
        
        for i, enhanced_profile in enumerate(enhanced_encodings):
            try:
                profile_encodings = enhanced_profile['encodings']
                profile_quality = enhanced_profile['quality']
                
                # Compare against all variations of this person
                for profile_encoding in profile_encodings:
                    try:
                        distance = face_recognition.face_distance([profile_encoding], face_encoding)[0]
                        accuracy = round((1 - distance) * 100)
                        
                        # Weight accuracy with quality score (capped to prevent extreme values)
                        # Use a more balanced formula to prevent extremely high values for high quality images
                        quality_factor = min(0.7 + 0.3 * (profile_quality / 10), 1.3)  # Cap at 1.3 (30% boost)
                        weighted_accuracy = accuracy * quality_factor
                        
                        if weighted_accuracy > best_accuracy:
                            best_accuracy = weighted_accuracy
                            best_match = enhanced_profile['name']
                            best_quality = profile_quality
                            raw_accuracy = accuracy  # Store the raw accuracy before weighting
                    except Exception as e:
                        print(f"[!] Error comparing encoding variation: {e}")
                        continue
            except Exception as e:
                print(f"[!] Error processing enhanced profile: {e}")
                continue
        
        # If we found a match with enhanced recognition, return it
        if best_match:
            return best_match, best_accuracy, best_quality
        
        # Otherwise return the basic recognition result
        return basic_result
        
    except Exception as e:
        print(f"[!] Face recognition error: {e}")
        return "Unknown", 0, 0.0

def calculate_adaptive_threshold(quality_score):
    """Calculate adaptive threshold based on quality score"""
    # Base threshold for all images
    base_threshold = 60
    
    # Ensure quality_score is a valid number
    if not isinstance(quality_score, (int, float)) or quality_score <= 0:
        return base_threshold
    
    # Cap quality score at a reasonable maximum to prevent extreme thresholds
    capped_quality = min(quality_score, 10.0)
    
    # Adjust threshold based on quality, but less aggressively
    # For high quality images, we only slightly increase the threshold
    if capped_quality > 8:
        return 65  # Reduced from 75% to 65% for high quality images
    elif capped_quality > 5:
        return 62  # Reduced from 65% to 62% for medium quality
    else:
        return base_threshold  # Base threshold for lower quality

def adaptive_frame_processing(frame, face_count, confidence_level):
    """Adaptive frame processing based on face count and confidence"""
    if face_count == 1 and confidence_level < 60:
        # Single face with low confidence - use higher resolution
        scale_factor = 0.5  # 50% instead of 25%
    elif face_count >= 3:
        # Multiple faces - use lower resolution for performance
        scale_factor = 0.2  # 20% for better performance
    else:
        # Default case
        scale_factor = 0.25
    
    return cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)

def recognizer_engine():
    face_locations = []
    face_encodings = []
    face_names = []
    p = True
    frame_count = 0
    # Initialize small_frame to avoid reference before assignment
    small_frame = None

    while True:
        frame = camera_manager.get_frame()
        if frame is None:
            continue  # Skip this iteration if frame couldn't be read
            
        frame_count += 1
        
        # Periodic cleanup of old cooldown entries (every 100 frames)
        if frame_count % 100 == 0:
            cleanup_old_cooldowns()
        
        # Create a default small_frame in case we skip processing
        if small_frame is None:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Adaptive frame processing
        if p:
            # Count faces first to determine processing strategy
            temp_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            temp_rgb = temp_frame[:, :, ::-1]
            temp_face_locations = face_recognition.face_locations(temp_rgb, model="hog")
            face_count = len(temp_face_locations)
            
            # Use adaptive processing
            small_frame = adaptive_frame_processing(frame, face_count, 50)  # Default confidence
            rgb_small_frame = small_frame[:, :, ::-1]
            
            face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            accuracies = []
            
            for face_encoding in face_encodings:
                name, accuracy, quality_score = enhanced_face_recognition(face_encoding)
                face_names.append(name)
                accuracies.append(accuracy)
                
                # Calculate adaptive threshold based on quality score
                adaptive_threshold = calculate_adaptive_threshold(quality_score)
                
                # Normalize accuracy if it's extremely high due to quality weighting
                normalized_accuracy = min(accuracy, 100)  # Cap at 100%
                
                # Determine check status (IN/OUT) based on time of day
                check_status = determine_check_status()
                
                # Enhanced attendance logic with adaptive threshold and cooldown
                if name in employee_names and normalized_accuracy >= adaptive_threshold:
                    # Check cooldown to prevent spam detections
                    current_time = datetime.now()
                    if name in detection_cooldown:
                        time_diff = (current_time - detection_cooldown[name]).total_seconds()
                        if time_diff < COOLDOWN_SECONDS:
                            # Still in cooldown period, skip this detection
                            continue
                    
                    # Update cooldown timestamp
                    detection_cooldown[name] = current_time
                    
                    entry_time = time_updater()
                    insert_attendance_database(name, f"{entry_time[10:]}", check_status)
                    print(f"[+] Attendance logged: {name} (Accuracy: {normalized_accuracy}%, Quality: {quality_score:.2f}, Status: {check_status})")
                elif name in employee_names:
                    print(f"[!] {name} detected but below adaptive threshold: {normalized_accuracy}% < {adaptive_threshold}% (Quality: {quality_score:.2f})")

        p = not p

        # Calculate scale factor for display
        original_height, original_width = frame.shape[:2]
        processed_height, processed_width = small_frame.shape[:2]
        scale_factor = original_height / processed_height

        # Draw face boxes and labels
        for (top, right, bottom, left), name, accuracy in zip(face_locations, face_names, accuracies):
            # Scale coordinates back to original frame size
            top = int(top * scale_factor)
            right = int(right * scale_factor)
            bottom = int(bottom * scale_factor)
            left = int(left * scale_factor)

            # Get quality score for this face (if available)
            quality_score = 1.0  # Default
            for profile in enhanced_encodings:
                if profile['name'] == name:
                    quality_score = profile['quality']
                    break
            
            # Calculate adaptive threshold based on quality score
            adaptive_threshold = calculate_adaptive_threshold(quality_score)
            
            # Normalize accuracy if it's extremely high due to quality weighting
            normalized_accuracy = min(accuracy, 100)  # Cap at 100%
            
            # Color coding based on adaptive threshold
            if normalized_accuracy >= adaptive_threshold:
                color = (0, 255, 0)  # Green for above adaptive threshold
            elif normalized_accuracy >= 60:  # Between 60% and threshold
                color = (0, 255, 255)  # Yellow for moderate confidence
            else:
                color = (0, 0, 255)  # Red for low confidence (<60%)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Enhanced text display with quality info
            font = cv2.FONT_HERSHEY_TRIPLEX
            normalized_accuracy = min(accuracy, 100)  # Cap at 100%
            
            # For low confidence detections (<60%), show as "Unknown"
            if normalized_accuracy < 60:
                display_text = "Unknown"
                # Override the name for display purposes
                name = "Unknown"
            else:
                # Get just the first name for display
                first_name = name.split()[0] if name else ""
                display_text = f"{first_name}"
                
            cv2.putText(frame, display_text, (left + 6, bottom - 6), font, 0.7, (0, 0, 0), 2)

        # Display frame info
        check_status = determine_check_status()
        info_text = f"Faces: {len(face_locations)} | Mode: {'Enhanced' if enhanced_encodings else 'Basic'} | Status: {check_status}"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('Face Sense - Office Attendance System', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html', date_now=time_updater()[:10])

@app.route('/details')
def details():
    return render_template('details.html')

@app.route('/video_feed')
def video_feed():
    return Response(recognizer_engine(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_attendance_data')
def get_attendance_data():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Get current date in dd/mm/yyyy format
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    try:
        # Get only today's attendance entries
        cursor.execute("""
            SELECT employee_name, employee_id, time_in, time_out, status 
            FROM attendance 
            WHERE date = ?
            ORDER BY id DESC
        """, (current_date,))
        data = cursor.fetchall()
        
        attendance_data = []
        for row in data:
            employee_name, employee_id, time_in, time_out, status = row
            attendance_data.append({
                'employee_name': employee_name,
                'employee_id': employee_id,
                'time_in': time_in or '',
                'time_out': time_out or '',
                'status': status or ''
            })
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        attendance_data = []
    finally:
        conn.close()
    
    return jsonify(attendance_data)

@app.route('/system_status')
def system_status():
    """API endpoint to check system status and model information"""
    status = {
        'model_type': 'Enhanced' if enhanced_encodings else 'Basic',
        'total_employees': len(employee_names),
        'enhanced_profiles': len(enhanced_encodings),
        'average_quality': round(np.mean(quality_scores), 2) if quality_scores else 0,
        'total_variations': sum(len(e['encodings']) for e in enhanced_encodings) if enhanced_encodings else 0
    }
    return jsonify(status)

@app.route('/find_employee_image/<employee_name>')
def find_employee_image(employee_name):
    """Find the correct image file for an employee"""
    import os
    import glob
    
    try:
        # Convert employee name to lowercase and replace spaces with underscores
        search_name = employee_name.lower().replace(' ', '_')
        
        # Look for image files in the static/employee_photos directory
        photo_dir = "static/employee_photos"
        if not os.path.exists(photo_dir):
            return jsonify({'error': 'Photo directory not found'}), 404
        
        # Try exact match first
        exact_match = f"{search_name}.jpg"
        if os.path.exists(os.path.join(photo_dir, exact_match)):
            return jsonify({'image_path': f'/static/employee_photos/{exact_match}'})
        
        # Try to find files that start with the employee name
        pattern = f"{search_name}*.jpg"
        matching_files = glob.glob(os.path.join(photo_dir, pattern))
        
        if matching_files:
            # Return the first matching file
            image_file = os.path.basename(matching_files[0])
            return jsonify({'image_path': f'/static/employee_photos/{image_file}'})
        
        # If no match found, return default avatar
        return jsonify({'image_path': '/static/default/default-avatar.png'})
        
    except Exception as e:
        print(f"Error finding employee image: {e}")
        return jsonify({'image_path': '/static/default/default-avatar.png'})

@app.route('/download_attendance')
def download_attendance():
    """Download attendance data in various formats"""
    from flask import request, send_file
    import tempfile
    
    format_type = request.args.get('format', 'csv')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    try:
        # Parse dates from dd/mm/yyyy format
        if start_date and end_date:
            start_parts = start_date.split('/')
            end_parts = end_date.split('/')
            
            if len(start_parts) == 3 and len(end_parts) == 3:
                start_date_sql = f"{start_parts[2]}-{start_parts[1]}-{start_parts[0]}"
                end_date_sql = f"{end_parts[2]}-{end_parts[1]}-{end_parts[0]}"
                
                # Query database for date range
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                
                # Query single attendance table with date filter
                cursor.execute("""
                    SELECT employee_name, employee_id, time_in, time_out, status 
                    FROM attendance
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC, id DESC
                """, (start_date, end_date))
                all_data = cursor.fetchall()
                
                conn.close()
            else:
                all_data = []
        else:
            # Get today's data
            all_data = get_attendance_data().json
        
        if format_type == 'csv':
            # Create CSV file
            csv_content = "Employee Name,Employee ID,Check IN,Check OUT,Status\n"
            for row in all_data:
                if isinstance(row, dict):
                    csv_content += f"{row['employee_name']},{row['employee_id']},{row['time_in']},{row['time_out']},{row['status']}\n"
                else:
                    csv_content += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n"
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(csv_content)
                temp_file = f.name
            
            return send_file(temp_file, as_attachment=True, 
                           download_name=f"attendance_{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}.csv",
                           mimetype='text/csv')
        
        elif format_type == 'json':
            # Return JSON data
            return jsonify(all_data)
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        print(f"Error downloading attendance data: {e}")
        return jsonify({'error': str(e)}), 500

# Add detection cooldown tracking to prevent spam
detection_cooldown = {}  # Track last detection time per person
COOLDOWN_SECONDS = 5  # Minimum seconds between detections of same person

def cleanup_old_cooldowns():
    """Clean up old cooldown entries to prevent memory issues"""
    current_time = datetime.now()
    expired_names = []
    
    for name, last_detection in detection_cooldown.items():
        time_diff = (current_time - last_detection).total_seconds()
        if time_diff > COOLDOWN_SECONDS * 2:  # Remove entries older than 2x cooldown
            expired_names.append(name)
    
    for name in expired_names:
        del detection_cooldown[name]
    
    if expired_names:
        print(f"[+] Cleaned up {len(expired_names)} expired cooldown entries")

# Add health check endpoints
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'camera_connected': camera_manager.is_connected(),
        'environment': config.environment,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health/camera')
def camera_health():
    """Camera-specific health check"""
    return jsonify({
        'camera_connected': camera_manager.is_connected(),
        'camera_type': config.camera.source_type,
        'camera_source': config.camera.source if config.environment != 'production' else 'hidden'
    })

@app.route('/health/db')
def database_health():
    """Database health check"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM attendance")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            'database_connected': True,
            'record_count': count,
            'database_type': config.database.type
        })
    except Exception as e:
        return jsonify({
            'database_connected': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Validate configuration
    validation = config.validate_config()
    if not validation['valid']:
        logger.error(f"Configuration validation failed: {validation['issues']}")
        if config.environment == 'production':
            exit(1)
    
    # Initialize database tables
    try:
        db_manager.create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        if config.environment == 'production':
            exit(1)
    
    # Initialize authentication routes
    init_auth_routes(app)
    
    # Initialize monitoring routes
    init_monitoring_routes(app)
    
    # Start system monitoring
    system_monitor.start_monitoring()
    
    print(f"[+] Starting Face Sense - Office Attendance System")
    print(f"[+] Environment: {config.environment}")
    print(f"[+] Model: {'Enhanced' if enhanced_encodings else 'Basic'}")
    print(f"[+] Employees: {len(employee_names)}")
    if enhanced_encodings:
        print(f"[+] Enhanced Profiles: {len(enhanced_encodings)}")
        print(f"[+] Total Variations: {sum(len(e['encodings']) for e in enhanced_encodings)}")
    
    print(f"[+] Camera: {config.camera.source_type} - {config.camera.source}")
    print(f"[+] Database: {config.database.type} - {config.database.name}")
    print(f"[+] Authentication: {'Enabled' if config.security.enable_auth else 'Disabled'}")
    print(f"[+] Web Interface: http://{config.app.host}:{config.app.port}")
    print(f"[+] Health Check: http://{config.app.host}:{config.app.port}/health")
    print(f"[+] API Endpoints: http://{config.app.host}:{config.app.port}/api/")
    print(f"[+] Press 'q' to quit\n")
    
    try:
        app.run(
            debug=config.app.debug,
            host=config.app.host,
            port=config.app.port,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Face-Sense...")
        camera_manager.stop_capture()
        system_monitor.stop_monitoring()
        logger.info("Face-Sense stopped successfully")
