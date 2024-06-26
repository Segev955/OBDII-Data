import os
import subprocess
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase Admin SDK
cred = credentials.Certificate(
    "/home/segev/Project/OBDII-Data/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://car-driver-bc91f-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

def run_data_collection_script(name, car_type):
    print(f"Start command received. Driver: {name}, Car Type: {car_type}. Running data collection script...")
    env = os.environ.copy()
    env["DRIVER_NAME"] = name
    env["CAR_TYPE"] = car_type

    try:
        process = subprocess.Popen(["python3", "/home/segev/Project/OBDII-Data/OBD-II.py"], env=env)
        print("Script started successfully.")
    except Exception as e:
        print(f"Error running script: {e}")


def stop_data_collection_script():
    print("Stop command received. Sending SIGINT to data collection script...")
    try:
        subprocess.run(["pkill", "-SIGINT", "-f", "OBD-II.py"], check=True)
        print("Script stopped successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error stopping script: {e}")

def shutdown_raspberry():
    print("Shutdown command received. Shutting down the Raspberry Pi...")
    subprocess.run(["sudo", "shutdown", "-h", "now"])




def listener(event):
    print("Event path:", event.path)
    print("Event data:", event.data)

    if event.path == "/":
        if event.data.get("start"):
            print("Start command detected")
            name = event.data.get("name", "Unknown")
            car_type = event.data.get("carType", "Unknown")
            run_data_collection_script(name, car_type)
    elif event.path == "/stop" and event.data:
        print("Stop command detected")
        stop_data_collection_script()
    elif event.path == "/shutdown" and event.data:
        print("Shutdown command detected")
        shutdown_raspberry()


print("Firebase Listener started. Waiting for commands...")
db.reference('commands').listen(listener)
