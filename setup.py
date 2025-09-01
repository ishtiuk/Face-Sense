#!/usr/bin/env python3
"""
Face Sense Office Attendance System - Setup Script
Automates installation of dependencies and system initialization
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_banner():
    """Print the Face Sense banner"""
    banner = """
    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
    █░▄▄▀██░▄▄▄██░▄▄▄░██░▄▄▀██░▄▄▄██░▄▄▄░██░▄▄▄░██░▄▄▄░██░▄▄▄██░▄▄▀██░▄▄▄██░▄▄▄░██
    █░▀▀▄██░▄▄▄██▄▄▄▀▀██░▀▀▄██░▄▄▄██░███░██▄▄▄▀▀██▄▄▄▀▀██░▄▄▄██░▀▀▄██░▄▄▄██░███░██
    █░██░██░▀▀▀██░▀▀▀░██░██░██░▀▀▀██░▀▀▀░██░▀▀▀░██░▀▀▀░██░▀▀▀██░██░██░▀▀▀██░▀▀▀░██
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    
    🚀 Face Sense Office Attendance System - Setup Script
    =====================================================
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible (3.8.17)"""
    version = sys.version_info
    if version.major != 3 or version.minor != 8 or version.micro != 17:
        print(f"❌ Error: Python 3.8.17 is required, but you have Python {version.major}.{version.minor}.{version.micro}")
        print("Please install Python 3.8.17 and try again.")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_platform():
    """Check if platform is Windows"""
    if platform.system() != 'Windows':
        print(f"❌ Error: This setup script is designed for Windows, but you're running {platform.system()}")
        print("Please run this on a Windows system.")
        return False
    
    print(f"✅ Platform: {platform.system()} {platform.release()}")
    return True

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔧 Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to virtual environment Python executable"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\python.exe"
    else:
        return "venv/bin/python"

def get_venv_pip():
    """Get the path to virtual environment pip executable"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\pip.exe"
    else:
        return "venv/bin/pip"

def install_dlib_wheel():
    """Install the dlib wheel file"""
    wheel_file = os.path.join("dependencies", "dlib-19.22.99-cp38-cp38-win_amd64.whl")
    
    if not os.path.exists(wheel_file):
        print(f"❌ Error: {wheel_file} not found in current directory")
        print("Please ensure the dlib wheel file is present before running setup")
        return False
    
    print(f"🔧 Installing {wheel_file}...")
    try:
        venv_pip = get_venv_pip()
        subprocess.run([venv_pip, "install", wheel_file], check=True)
        print("✅ Dlib wheel installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dlib wheel: {e}")
        return False

def install_requirements():
    """Install requirements from requirements.txt"""
    if not os.path.exists("requirements.txt"):
        print("❌ Error: requirements.txt not found")
        return False
    
    print("🔧 Installing requirements from requirements.txt...")
    try:
        venv_pip = get_venv_pip()
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "attendance_data",
        "model_data",
        "model_data/enhanced",
        "employee_photos",
        "templates",
        "static",
        "static/employee_photos",
        "static/default"
    ]
    
    print("🔧 Creating necessary directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def run_init_db():
    """Run the database initialization script"""
    if not os.path.exists("init_db.py"):
        print("❌ Error: init_db.py not found")
        return False
    
    print("🔧 Initializing database...")
    try:
        venv_python = get_venv_python()
        subprocess.run([venv_python, "init_db.py"], check=True)
        print("✅ Database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error initializing database: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    next_steps = """
    🎉 Setup completed successfully!
    
    📋 Next Steps:
    1. Add employee photos to the 'employee_photos/' directory
       Format: firstname_lastname_employeeid.jpg
       Example: john_smith_EMP001.jpg
    
    2. Run the face encoding script:
       venv\\Scripts\\python.exe info_storing.py
    
    3. Start the Face Sense system:
       venv\\Scripts\\python.exe engine.py
    
    4. Open your browser and go to: http://localhost:5000
    
    🔧 Troubleshooting:
    - If you encounter issues, check the error messages above
    - Ensure Python 3.8.17 is installed
    - Make sure all files are in the correct directory structure
    
         📚 Documentation:
     - Check README.md for detailed usage instructions
    
    🚀 Welcome to Face Sense - Office Attendance System!
    """
    print(next_steps)

def main():
    """Main setup function"""
    print_banner()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_platform():
        return False
    
    print("\n🔧 Starting Face Sense setup...\n")
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    # Create directories
    create_directories()
    
    # Install dlib wheel
    if not install_dlib_wheel():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Initialize database
    if not run_init_db():
        print("⚠️  Warning: Database initialization failed, but setup can continue")
        print("   You can manually run 'python init_db.py' later")
    
    # Process employee photos for web display
    print("\n🔧 Processing employee photos for web display...")
    try:
        venv_python = get_venv_python()
        subprocess.run([venv_python, "resize_employee_photos.py"], check=True)
        print("✅ Employee photos processed successfully")
    except subprocess.CalledProcessError as e:
        print("⚠️  Warning: Photo processing failed, but setup can continue")
        print("   You can manually run 'python resize_employee_photos.py' later")
    
    # Encode employee faces
    print("\n🔧 Encoding employee faces...")
    try:
        venv_python = get_venv_python()
        subprocess.run([venv_python, "info_storing.py"], check=True)
        print("✅ Employee faces encoded successfully")
    except subprocess.CalledProcessError as e:
        print("⚠️  Warning: Face encoding failed, but setup can continue")
        print("   You can manually run 'python info_storing.py' later")
    
    print("\n" + "="*60)
    print_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup failed. Please check the error messages above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)
