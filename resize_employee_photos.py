#!/usr/bin/env python3
"""
Face Sense - Employee Photo Resizer
Resizes employee photos to low resolution for web display in static folder
"""

import os
import cv2
from PIL import Image
import shutil
from pathlib import Path

def create_static_directories():
    """Create static directories if they don't exist"""
    directories = [
        "static",
        "static/employee_photos",
        "static/default"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def resize_image_for_web(image_path, output_path, max_width=200, max_height=200, quality=85):
    """Resize image for web display with low resolution"""
    try:
        # Open image with PIL for better quality control
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            width, height = img.size
            if width > height:
                new_width = max_width
                new_height = int(height * (max_width / width))
            else:
                new_height = max_height
                new_width = int(width * (max_height / height))
            
            # Resize image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with compression
            resized_img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            # Get file size
            file_size = os.path.getsize(output_path)
            file_size_kb = file_size / 1024
            
            print(f"✅ Resized: {os.path.basename(image_path)} → {new_width}x{new_height} ({file_size_kb:.1f} KB)")
            
            return True
            
    except Exception as e:
        print(f"❌ Error resizing {image_path}: {e}")
        return False

def create_default_avatar():
    """Create a default avatar image for missing employee photos"""
    default_path = "static/default/default-avatar.png"
    
    if os.path.exists(default_path):
        print("✅ Default avatar already exists")
        return
    
    try:
        # Create a simple default avatar (200x200 pixels)
        img = Image.new('RGB', (200, 200), color='#2c3e50')
        
        # Save as PNG
        img.save(default_path, 'PNG')
        print("✅ Created default avatar")
        
    except Exception as e:
        print(f"❌ Error creating default avatar: {e}")

def process_employee_photos():
    """Process all employee photos and resize them for web display"""
    source_dir = "employee_photos"
    output_dir = "static/employee_photos"
    
    if not os.path.exists(source_dir):
        print(f"❌ Source directory '{source_dir}' not found")
        return False
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    
    for file in os.listdir(source_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    if not image_files:
        print(f"❌ No image files found in '{source_dir}'")
        return False
    
    print(f"🔧 Found {len(image_files)} employee photos to process")
    print("📏 Resizing to 200x200 pixels for web display...\n")
    
    success_count = 0
    total_size_before = 0
    total_size_after = 0
    
    for image_file in image_files:
        source_path = os.path.join(source_dir, image_file)
        output_path = os.path.join(output_dir, image_file)
        
        # Get original file size
        original_size = os.path.getsize(source_path)
        total_size_before += original_size
        
        # Resize image
        if resize_image_for_web(source_path, output_path):
            success_count += 1
            # Get resized file size
            resized_size = os.path.getsize(output_path)
            total_size_after += resized_size
    
    # Print summary
    print(f"\n📊 Processing Summary:")
    print(f"✅ Successfully processed: {success_count}/{len(image_files)} photos")
    print(f"📁 Original total size: {total_size_before / 1024:.1f} KB")
    print(f"📁 Resized total size: {total_size_after / 1024:.1f} KB")
    print(f"💾 Space saved: {(total_size_before - total_size_after) / 1024:.1f} KB")
    
    return success_count > 0

def main():
    """Main function"""
    print("🚀 Face Sense - Employee Photo Resizer")
    print("=" * 50)
    
    # Create static directories
    create_static_directories()
    
    # Create default avatar
    create_default_avatar()
    
    # Process employee photos
    if process_employee_photos():
        print("\n🎉 Photo processing completed successfully!")
        print("📁 Resized photos saved in: static/employee_photos/")
        print("🖼️  Default avatar saved in: static/default/default-avatar.png")
        print("\n💡 These resized photos will be used in the employee profiles section")
    else:
        print("\n❌ Photo processing failed!")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
