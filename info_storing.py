import os
import sys
import numpy as np
import face_recognition
from pickle import dump

def fancy_progress_message(message):            ## just for fancy Terminal sms
    sys.stdout.write("\r\033[K") 
    sys.stdout.write(f"[+] {message}")
    sys.stdout.flush()

def fancy_banner():                             ## just for fancy Terminal sms
    banner = f"""
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█░████▄▀█▀▄█░▄▀████░▄▄▄█░▄▄▀██░▄▄▀██░▄▄▄████░▄▄▄░██░▄▄▄██░▀██░██░▄▄▄░██░▄▄▄██
█░▄▄░███░███░█░████░▄▄██░▀▀░██░█████░▄▄▄████▄▄▄▀▀██░▄▄▄██░█░█░██▄▄▄▀▀██░▄▄▄██
█▄██▄█▀▄█▄▀█▄▄█████░████░██░██░▀▀▄██░▀▀▀████░▀▀▀░██░▀▀▀██░██▄░██░▀▀▀░██░▀▀▀██
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
Starting Face Encoding...\n\n"""
    sys.stdout.write(banner)
    sys.stdout.flush()

fancy_banner()



files = sorted(os.listdir("student_photos/"))
known_names = list(map(lambda x: " ".join(x.split(".")[0].split("_")[:-1]).title(), files))

known_imgs = []
known_encodings = []

for i, f in enumerate(files):
    fancy_progress_message(f"Encoding ( {i + 1}/{len(files)} ): {f}...")
    img = face_recognition.load_image_file(os.path.join("student_photos", f))
    encoding = face_recognition.face_encodings(img)[0]
    known_imgs.append(img)
    known_encodings.append(encoding)

# dump(known_imgs, open(os.path.join("model_data", "known_imgs.bin"), "wb"))
dump(known_names, open(os.path.join("model_data", "known_names.bin"), "wb"))
dump(known_encodings, open(os.path.join("model_data", "known_encodings.bin"), "wb"))

sys.stdout.write("\n[+] Encoding completed.")
sys.stdout.write("\n[+] Ready to run [engine.py]\n\n")


