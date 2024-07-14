import os
import time
import threading
import firebase_admin
from firebase_admin import credentials, db

def update_obd_status():
    while True:
        obd_ref = db.reference('/Obd')
        obd_snapshot = obd_ref.get()

        for obd_id, obd_data in obd_snapshot.items():
            if 'is_alive' in obd_data and obd_data['is_alive']:
                obd_ref.child(obd_id).update({'is_alive': False})
                print(f'OBD {obd_id} is_alive updated')

        print("OBD is_alive statuses updated.")
        time.sleep(60)  # Run this check every 60 seconds

def run_alive_server():
    print("Starting OBD status updater server...")
    threading.Thread(target=update_obd_status, daemon=True).start()

if __name__ == '__main__':
    # Initialize Firebase Admin SDK
    while True:
        try:
            cred = credentials.Certificate(f"{os.getcwd()}/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://car-driver-bc91f-default-rtdb.asia-southeast1.firebasedatabase.app/'
            })
            print("Firebase initialized successfully.")
            break
        except Exception as e:
            print(f"Error initializing Firebase: {e}. Retrying in 5 seconds...")
            time.sleep(1)
    run_alive_server()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped by user")
