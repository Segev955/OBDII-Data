import os
import time
import subprocess
import firebase_admin
import json
import subprocess
from firebase_admin import credentials, db


ID = '4567'
NAME = "fake4567"
KEY = '4567'

OBD_REFERENCE = 'Obd'
ENTRIES_REFERENCE = 'ObdEntries'
USERS_REFERENCE = 'Users'

class Obd:
    is_alive = False
    is_available = False
    is_busy = False
    def __init__(self, id = ID,name = NAME, key = KEY):
        self.id = id
        self.name = name
        self.key = key
        self.status = ''
        self.connected_uid = ''
        self.is_alive = Obd.is_alive
        self.is_available = Obd.is_available
        self.is_busy = Obd.is_busy


    def setAlive(self):
        self.is_alive =True
        self.updateData()

    def isConnected(self):
        return self.connected_uid != ''

    def updateStatus(self, status = 'available'):
        self.status = status
        self.updateData()

    def updateUserStatus(self, status , uid ):
        if uid is not None and uid !='':
            print(f'setting status <{status}> to user <{uid}>')
            db.reference(USERS_REFERENCE).child(uid).child('status').set(f'OBD {self.name}: {status}')


    def connect(self, uid, key):
        db.reference(ENTRIES_REFERENCE).child(self.id).delete()
        if self.is_available and not self.isConnected():
            print("checking key for connection")
            if self.key == key:
                self.connected_uid = uid
                self.is_available = False
                self.updateUserStatus(f'CONNECTED', self.connected_uid)
                self.updateStatus("Connected")
                print(f"User {uid} connected successfully!")
                return True
            else:
                self.updateUserStatus(f"WRONGKEY:{self.id}", uid)
                print(f"Got connection with wrong key")
        print(f"Connection failed! {uid}")
        return False

    def disconnect(self):
        if self.isConnected():
            db.reference(USERS_REFERENCE).child(self.connected_uid).child('connected_obd').set('')
            self.connected_uid = ''
            print(f"User disconnected!")
        self.startUp()


    def startUp(self):
        self.is_alive = True
        self.is_available = True
        self.is_busy = False
        print("Ready for connections...")
        self.updateStatus("Ready")

    def shutDown(self):
        if self.isConnected():
            db.reference(USERS_REFERENCE).child(self.connected_uid).child('connected_obd').set('')
            self.connected_uid = ''
            print(f"User disconnected!")
        print("Shutdown command received. Shutting down the Raspberry Pi...")
        self.is_alive = False
        self.is_available = False
        self.updateStatus("turned off")
        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"])

        except Exception as e:
            print(f"Error, no OBD device connected: {e}.")


    def updateData(self):
        dict = {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'connected_uid': self.connected_uid,
            'is_alive': self.is_alive,
            'is_available': self.is_available,
            'is_busy': self.is_busy,
            'is_connected': self.isConnected()
        }
        db.reference(OBD_REFERENCE).child(self.id).set(dict)
        if self.isConnected():
            db.reference(USERS_REFERENCE).child(self.connected_uid).child('connected_obd').set(self.id)



    def startDriving(self):
        if not self.is_busy:
            self.is_busy = True
            self.updateStatus("starting...")
            uid = self.connected_uid
            # Retrieve the car_type from the database
            try:
                car_type_snapshot = db.reference(USERS_REFERENCE).child(uid).child('carType').get()
                if car_type_snapshot:
                    car_type = car_type_snapshot
                    print(f"Start command received. Driver: {uid}, Car Type: {car_type}. Running data collection script...")
                    env = os.environ.copy()
                    env["DRIVER_UID"] = uid
                    env["CAR_TYPE"] = car_type

                    try:
                        subprocess.Popen(["python3", f"{os.getcwd()}/OBD_II.py"], env=env)
                        self.updateStatus("driving")
                        print("Script started successfully.")
                    except Exception as e:
                        self.updateStatus(f"Error starting script: {e}")
                        print(f"Error running script: {e}")
                else:
                    print(f"Car type not found for user {uid}")
            except Exception as e:
                print(f"Error retrieving car type for user {uid}: {e}")

    def stopDriving(self):
        if self.is_busy:
            self.is_busy = False
            self.updateStatus("stopping...")
            print("Stop command received. Sending SIGINT to data collection script...")
            try:
                subprocess.run(["pkill", "-SIGINT", "-f", "OBD_II.py"], check=True)
                self.updateStatus("Stopped successfully")
                print("Script stopped successfully.")
            except subprocess.CalledProcessError as e:
                self.updateStatus(f"Error stopping script: Nothing to stop")
                print(f"Error stopping script (CalledProcessError): {e}")
            except Exception as e:
                self.updateStatus(f"Error stopping script: {e}")
                print(f"Error stopping script (General Exception): {e}")
