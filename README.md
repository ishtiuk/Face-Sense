# **Face Sense** - Office Attendance System

This project is a **Face Recognition Office Attendance System** developed using Python. It captures and processes real-time video from a webcam to recognize employee faces, logs office attendance with check-in/check-out times, and serves attendance data via a Flask web application.

## Project Structure

```bash
Face-Sense
│
├── attendance_data/
│   ├── attendance.db             # SQLite database for attendance records
│   ├── YYYY-MM-DD.csv            # Daily attendance CSV files
│
├── model_data/
│   ├── known_names.bin           # Pickle file containing the names of known faces
│   ├── known_encodings.bin       # Pickle file containing the encodings of known faces
│
├── employee_photos/
│   ├── [firstname_lastname_employeeid].jpg  # Photos of employees used for face encoding
│
├── templates/
│   ├── index.html                # HTML template for the Flask web application
│
├── requirements/
│   └── requirements.txt          # List of required Python packages
│
├── engine.py                     # Main script to start the Flask server and process video
├── info_storing.py               # Script to encode employee faces and store encodings
└── main.py                       # Main script for face recognition and attendance logging
```

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ishtiuk/Face-Sense.git
   cd Face-Sense
   ```

2. **Set up the environment:**

   Ensure you have Python 3.7 or higher installed. Install the required Python packages using the `requirements.txt` file:

   ```bash
   pip install -r requirements/requirements.txt
   ```

3. **Prepare the model data:**

   Ensure you have the employee photos in the `employee_photos/` directory. Run the `info_storing.py` script to generate face encodings and save them:

   ```bash
   python info_storing.py
   ```

## Usage

### Running the Application

1. **Start the Flask server:**

   Run the `engine.py` script to start the Flask server and initiate the face recognition process:

   ```bash
   python engine.py
   ```

   The server will be accessible at `http://localhost:5000`.

2. **View the video feed and attendance data:**

   - Open your web browser and navigate to `http://localhost:5000` to view the live video feed from the webcam.
   - The video feed will display the recognized faces with their names and confidence scores.
   - The attendance data can be accessed via the `/get_attendance_data` endpoint.

### Stopping the Application

To stop the application, press `q` in the terminal where the video feed is displayed or terminate the Flask server using `Ctrl+C`.

## Code Explanation

- **`engine.py`**: Contains the Flask application and the main face recognition logic. It captures video from the webcam, processes each frame to detect and recognize faces, and logs attendance data to both a CSV file and an SQLite database.

- **`info_storing.py`**: Prepares the model by encoding employee faces and saving the encodings and names to binary files. Run this script once to prepare the face recognition model.

- **`main.py`**: (Not actively used in this setup but similar to `engine.py` for standalone execution without Flask)

## Notes

- Ensure the webcam is properly connected and accessible by the application.
- Modify the `known_names` and `known_encodings` files if you add or remove employees from the `employee_photos/` directory.
- The system assumes that employee photos in the `employee_photos/` directory are formatted as `[firstname]_[lastname]_[employeeid].jpg`.

## Troubleshooting

- **Issue:** Faces not being recognized or attendance not being logged.
  - **Solution:** Check the employee photos and ensure they are clear and correctly formatted. Re-run `info_storing.py` to update the encodings.

- **Issue:** Flask server fails to start.
  - **Solution:** Ensure all required packages are installed and that no other process is using port 5000.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/ishtiuk/Face-Sense/?tab=MIT-1-ov-file) file for details.
