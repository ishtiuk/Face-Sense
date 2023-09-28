# hXd Face Sense - Real-time Computer Vision Face Recognition Attendance System

Welcome to hXd Face Sense, a real-time computer vision face recognition attendance system. This project allows you to easily track attendance by recognizing students or employees based on their facial features. Please follow the instructions below to set up and use this system.

## System Requirements

Before you start, make sure you have the following Python packages installed. You can install them using `pip install -r requirements.txt`:

```plaintext
flask==2.3.1
certifi==2022.12.7
chardet==3.0.4
click==7.1.2
cmake==3.18.2.post1
decorator==5.1.1
dlib==19.22.99
face-recognition==1.3.0
face-recognition-models==0.3.0
idna==3.4
imageio==2.9.0
imageio-ffmpeg==0.4.2
moviepy==1.0.3
numpy==1.23.5
opencv-python==4.7.0
Pillow==9.3.0
proglog==0.1.9
requests==2.28.0
tqdm==4.65.0
urllib3==1.26.15
wincertstore==0.2
```

## Storing Facial Data

Facial data of students or employees should be extracted before running the detection engine. Run the info_storing.py script to store the facial data. Ensure that the photos are located in the "student_photos" folder and named in the format "firstname_lastname_integer.jpg".

```bash
python info_storing.py
```

## Running the Detection Engine

To use the face recognition attendance system, run the engine.py file. This Python Flask application displays a real-time attendance table and live-streaming detection camera footage side by side on a webpage.

```bash
python engine.py
```

## Web Interface

Access the system through a web interface. You can view the real-time attendance table and live-streaming camera footage. The system automatically updates the attendance data.

## Retrieving Attendance Data

You can retrieve attendance data in CSV format or from the SQLite database. The system creates a new CSV file each day to keep track of attendance. SQLite database is used as a secondary backup system for attendance data.

## Usage

- Store facial data using info_storing.py.
- Run the detection engine using engine.py.
- Access the system through the web interface.
- Monitor real-time attendance and camera footage.
- Retrieve attendance data from CSV or SQLite database as needed.
  
Enjoy using hXd Face Sense for convenient and efficient attendance tracking!
