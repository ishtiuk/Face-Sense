import os
import sys
import numpy as np
import face_recognition
from pickle import dump
import cv2
from PIL import Image, ImageEnhance

def fancy_progress_message(message):            ## just for fancy Terminal sms
    sys.stdout.write("\r\033[K") 
    sys.stdout.write(f"[+] {message}")
    sys.stdout.flush()

def fancy_banner():                             ## just for fancy Terminal sms
    banner = f"""
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█░▄▄▀██░▄▄▄██░▄▄▄░██░▄▄▀██░▄▄▄██░▄▄▄░██░▄▄▄░██░▄▄▄░██░▄▄▄██░▄▄▀██░▄▄▄██░▄▄▄░██
█░▀▀▄██░▄▄▄██▄▄▄▀▀██░▀▀▄██░▄▄▄██░███░██▄▄▄▀▀██▄▄▄▀▀██░▄▄▄██░▀▀▄██░▄▄▄██░███░██
█░██░██░▀▀▀██░▀▀▀░██░██░██░▀▀▀██░▀▀▀░██░▀▀▀░██░▀▀▀░██░▀▀▀██░██░██░▀▀▀██░▀▀▀░██
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
Starting Office Attendance System - Enhanced Face Encoding...\n\n"""
    sys.stdout.write(banner)
    sys.stdout.flush()

def enhance_image_quality(image):
    """Enhance image quality for better face recognition"""
    # Convert to PIL Image for enhancement
    pil_image = Image.fromarray(image)
    
    # Enhance contrast
    contrast_enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = contrast_enhancer.enhance(1.3)
    
    # Enhance brightness
    brightness_enhancer = ImageEnhance.Brightness(pil_image)
    pil_image = brightness_enhancer.enhance(1.1)
    
    # Enhance sharpness
    sharpness_enhancer = ImageEnhance.Sharpness(pil_image)
    pil_image = sharpness_enhancer.enhance(1.2)
    
    return np.array(pil_image)

def create_face_variations(image, face_location):
    """Create multiple face variations for better recognition"""
    top, right, bottom, left = face_location
    
    # Extract face region with padding
    face_height = bottom - top
    face_width = right - left
    padding = int(min(face_height, face_width) * 0.2)
    
    # Ensure coordinates are within image bounds
    top = max(0, top - padding)
    bottom = min(image.shape[0], bottom + padding)
    left = max(0, left - padding)
    right = min(image.shape[1], right + padding)
    
    face_region = image[top:bottom, left:right]
    
    variations = []
    
    # Original face
    variations.append(face_region)
    
    # Slightly rotated variations (±5 degrees)
    for angle in [-5, 5]:
        height, width = face_region.shape[:2]
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(face_region, rotation_matrix, (width, height))
        variations.append(rotated)
    
    # Brightness variations
    bright_face = cv2.convertScaleAbs(face_region, alpha=1.2, beta=10)
    dark_face = cv2.convertScaleAbs(face_region, alpha=0.8, beta=-10)
    variations.extend([bright_face, dark_face])
    
    return variations

def get_face_quality_score(image, face_location):
    """Calculate face quality score based on blur, size, and lighting"""
    top, right, bottom, left = face_location
    face_region = image[top:bottom, left:right]
    
    # Convert to grayscale for blur detection
    gray = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)
    
    # Blur detection using Laplacian variance
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Face size score (larger faces are better)
    face_area = (right - left) * (bottom - top)
    size_score = min(face_area / 10000, 1.0)  # Normalize to 0-1
    
    # Lighting score using histogram analysis
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    lighting_score = 1.0 - (np.std(hist) / 100)  # Normalize to 0-1
    
    # Combined quality score
    quality_score = (blur_score * 0.4 + size_score * 0.4 + lighting_score * 0.2) / 100
    
    return quality_score

def parse_employee_info(filename):
    """Parse employee information from filename format: firstname_lastname_employeeid.jpg"""
    # Remove file extension and split by underscore
    name_parts = filename.split('.')[0].split('_')
    
    if len(name_parts) < 3:
        # If filename doesn't match expected format, use whole name
        return " ".join(name_parts).title(), "N/A"
    
    # Extract employee ID (last part)
    employee_id = name_parts[-1]
    
    # Extract name (all parts except the last one which is the employee ID)
    employee_name = " ".join(name_parts[:-1]).title()
    
    print(f"[+] Parsed: {filename} → Name: {employee_name}, ID: {employee_id}")
    
    return employee_name, employee_id

fancy_banner()

# Create enhanced model data directory if it doesn't exist
os.makedirs("model_data/enhanced", exist_ok=True)

# Use original photos
files = sorted(os.listdir("employee_photos/"))
known_names = []
employee_ids = []

# Parse employee names and IDs from filenames
for f in files:
    full_name, employee_id = parse_employee_info(f)
    known_names.append(full_name)
    employee_ids.append(employee_id)

known_imgs = []
known_encodings = []
enhanced_encodings = []
quality_scores = []

print(f"[+] Found {len(files)} employee photos")
print(f"[+] Generating enhanced encodings with multiple variations...\n")

for i, f in enumerate(files):
    fancy_progress_message(f"Processing ( {i + 1}/{len(files)} ): {f}...")
    
    # Load and enhance image
    img = face_recognition.load_image_file(os.path.join("employee_photos", f))
    enhanced_img = enhance_image_quality(img)
    
    # Detect faces
    face_locations = face_recognition.face_locations(enhanced_img, model="hog")
    
    if len(face_locations) == 0:
        print(f"\n[!] Warning: No face detected in {f}")
        continue
    
    # Get the best face location (usually the largest)
    best_face_location = max(face_locations, key=lambda loc: (loc[2] - loc[0]) * (loc[3] - loc[1]))
    
    # Calculate face quality
    quality = get_face_quality_score(enhanced_img, best_face_location)
    quality_scores.append(quality)
    
    # Create face variations
    face_variations = create_face_variations(enhanced_img, best_face_location)
    
    # Generate encodings for each variation with enhanced parameters
    variation_encodings = []
    for j, variation in enumerate(face_variations):
        try:
            # Use enhanced encoding parameters
            encoding = face_recognition.face_encodings(
                variation, 
                known_face_locations=[(0, variation.shape[1], variation.shape[0], 0)],
                num_jitters=3,  # Multiple samples for better accuracy
                model="large"    # Use large model for better features
            )[0]
            variation_encodings.append(encoding)
        except Exception as e:
            print(f"\n[!] Warning: Failed to encode variation {j+1} of {f}: {e}")
            continue
    
    if variation_encodings:
        # Store original encoding for backward compatibility
        original_encoding = face_recognition.face_encodings(img)[0]
        known_imgs.append(img)
        known_encodings.append(original_encoding)
        
        # Parse employee name and ID from filename
        full_name, employee_id = parse_employee_info(f)
        
        # Store enhanced encodings
        enhanced_encodings.append({
            'name': full_name,
            'employee_id': employee_id,
            'encodings': variation_encodings,
            'quality': quality,
            'variations': len(variation_encodings)
        })
        
        print(f" ✓ Generated {len(variation_encodings)} variations (Quality: {quality:.2f})")
    else:
        print(f"\n[!] Error: Failed to generate any encodings for {f}")

print(f"\n[+] Enhanced encoding completed!")
print(f"[+] Generated {sum(len(e['encodings']) for e in enhanced_encodings)} total encodings")
print(f"[+] Average quality score: {np.mean(quality_scores):.2f}")

# Save enhanced data
dump(known_names, open(os.path.join("model_data", "known_names.bin"), "wb"))
dump(known_encodings, open(os.path.join("model_data", "known_encodings.bin"), "wb"))
dump(enhanced_encodings, open(os.path.join("model_data", "enhanced", "enhanced_encodings.bin"), "wb"))
dump(quality_scores, open(os.path.join("model_data", "enhanced", "quality_scores.bin"), "wb"))
dump(employee_ids, open(os.path.join("model_data", "enhanced", "employee_ids.bin"), "wb"))

print(f"\n[+] Enhanced model data saved to model_data/enhanced/")
print(f"\033[92m[+] Ready to run enhanced [engine.py]\x1b[0m\n")
