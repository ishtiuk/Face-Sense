import os
import cv2
import csv
import sqlite3
import numpy as np
from pickle import load
import face_recognition
from datetime import datetime



db_name = "attendance_data/attendance.db"
known_names = load(open(os.path.join("model_data", "known_names.bin"), "rb"))
known_encodings = load(open(os.path.join("model_data", "known_encodings.bin"), "rb"))

video_capture = cv2.VideoCapture(0)
attendance_list = sorted(list(set(known_names[::-1][::-1])))            ## copying "known_names" list


def time_updater():
    return datetime.now().strftime("%Y-%m-%d  %I:%M:%S %p")

csv_file_nm = f"attendance_data/{time_updater().split()[0]}.csv"
sql_table_nm = "t_" + time_updater().split()[0].replace("-", "_")
f = open(csv_file_nm, "w")
f.close()


def insert_attendance_csv(student_name, time_entry):
    with open(csv_file_nm, mode='a', newline='\n') as file:
        writer = csv.writer(file)
        writer.writerow([student_name, time_entry])


def create_attendance_table():                          ## SQLite database file (secondary backup system)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create an attendance table if it doesn't exist
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {sql_table_nm} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name VARCHAR(255) UNIQUE,
            time_entry VARCHAR(255)
        )
    ''')
    conn.commit()
    conn.close()
    

def insert_attendance_database(student_name, time_entry):
    conn = sqlite3.connect(db_name)		## SQLite database file (secondary backup system)
    cursor = conn.cursor()
    try:
        cursor.execute(f"INSERT INTO {sql_table_nm}(student_name, time_entry) VALUES (?, ?)", (student_name, time_entry))		## skip duplicate value
        conn.commit()
    except sqlite3.IntegrityError as err:
        print(f"\n[Error: {err}] [{time_updater()}]")
        conn.rollback()
    conn.close()

create_attendance_table()


def recognizer_engine():
    face_locations = []
    face_encodings = []
    face_names = []
    p = True

    while True:
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if p:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            accuracies = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                name = "Unknown"

                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    name = known_names[best_match_index]
                
                accuracy = round((1 - min(face_distances)) * 100)
                face_names.append(name)
                accuracies.append(accuracy)

                if name in known_names and name in attendance_list and accuracy >= 53:          ## accuracy must be upper-equal to 54 for ensurity
                    entry_time = time_updater()
                    attendance_list.remove(name)
                    insert_attendance_csv(name, entry_time[10:])                                   ## insert in CSV
                    insert_attendance_database(name, f"{entry_time[10:]}")         ## insert in Database also

        p = not p


        for (top, right, bottom, left), name, accuracy in zip(face_locations, face_names, accuracies):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (204, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (204, 255, 0), cv2.FILLED)
            font = cv2.FONT_HERSHEY_TRIPLEX
            cv2.putText(frame, f"{name.split()[0]}:{accuracy}%", (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1)

        cv2.imshow('hXd FACE SENSE window', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

recognizer_engine()