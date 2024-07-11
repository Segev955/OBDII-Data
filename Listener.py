import os
import time
import subprocess
import firebase_admin
from firebase_admin import credentials, db


# Initialize Firebase Admin SDK
while True:
    try:
        cred = credentials.Certificate("/home/segev/Project/OBDII-Data/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://car-driver-bc91f-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
        print("Firebase initialized successfully.")
        break
    except Exception as e:
        print(f"Error initializing Firebase: {e}. Retrying in 5 seconds...")
        time.sleep(1)

def update_status(status):
    db.reference('status').set(status)
def run_data_collection_script(uid, car_type):
    print(f"Start command received. Driver: {uid}, Car Type: {car_type}. Running data collection script...")
    env = os.environ.copy()
    env["DRIVER_UID"] = uid
    env["CAR_TYPE"] = car_type

    try:
        subprocess.Popen(["python3", "/home/segev/Project/OBDII-Data/OBD_II.py"], env=env)
        update_status("Started successfully")
        print("Script started successfully.")
    except Exception as e:
        update_status(f"Error starting script: {e}")
        print(f"Error running script: {e}")


def stop_data_collection_script():
    print("Stop command received. Sending SIGINT to data collection script...")
    try:
        subprocess.run(["pkill", "-SIGINT", "-f", "OBD_II.py"], check=True)
        update_status("Stopped successfully")
        print("Script stopped successfully.")
    except subprocess.CalledProcessError as e:
        update_status(f"Error stopping script: Noting to stop")
        print(f"Error stopping script: {e}")

def shutdown_raspberry():
    print("Shutdown command received. Shutting down the Raspberry Pi...")
    update_status("Shutting down")
    subprocess.run(["sudo", "shutdown", "-h", "now"])




def listener(event):
    print("Event path:", event.path)
    print("Event data:", event.data)

    if event.path == "/":
        if event.data.get("start"):
            print("Start command detected")
            uid = event.data.get("uid", "Unknown")
            car_type = event.data.get("carType", "Unknown")
            run_data_collection_script(uid, car_type)
    elif event.path == "/stop" and event.data:
        print("Stop command detected")
        stop_data_collection_script()
    elif event.path == "/shutdown" and event.data:
        print("Shutdown command detected")
        shutdown_raspberry()


success = False
while not success:
    print("Attempting to set up Firebase listener...")
    try:
        db.reference('commands').listen(listener)
        update_status("Ready..")
        success = True
    except Exception as e:
        print(f"Error setting up Firebase listener: {e}. Retrying in 5 seconds...")
        time.sleep(5)
