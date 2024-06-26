import firebase_admin
from firebase_admin import credentials, db
import subprocess

# Initialize Firebase Admin SDK
cred = credentials.Certificate("/home/segev/Project/OBDII-Data/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://car-driver-bc91f-default-rtdb.asia-southeast1.firebasedatabase.app/'  # Replace with your database URL
})

# Function to run your existing Python script
def run_data_collection_script():
    print("Start command received. Running data collection script...")
    subprocess.run(["python3", "/home/segev/Project/OBDII-Data/OBD-II.py"])  # Adjust the path to your script

# Function to stop your script (optional: if you have a stop mechanism)
def stop_data_collection_script():
    print("Stop command received. Stopping data collection script...")
    subprocess.run(["pkill", "-f", "OBD-II.py"])  # This will kill the script process

# Listener for Firebase Realtime Database
def listener(event):
    if event.path == "/start":
        if event.data:
            run_data_collection_script()
    elif event.path == "/stop":
        if event.data:
            stop_data_collection_script()

# Attach listener
print("Firebase Listener started. Waiting for commands...")
db.reference('commands').listen(listener)