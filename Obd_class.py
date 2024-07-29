import os
import sys
import time
import subprocess
import firebase_admin
import json
import subprocess
from GPS_class import *
from firebase_admin import credentials, db

ID = '1'
NAME = "car_drive"
KEY = '1234'

OBD_REFERENCE = 'Obd'
ENTRIES_REFERENCE = 'ObdEntries'
USERS_REFERENCE = 'Users'


class Obd:
    is_alive = False
    is_available = False
    is_busy = False
    error_msg = ''

    def __init__(self, id=ID, name=NAME, key=KEY):
        self.id = id
        self.name = name
        self.key = key
        self.status = ''
        self.connected_uid = ''
        self.speed_limit = 0 
        self.is_alive = Obd.is_alive
        self.is_available = Obd.is_available
        self.is_busy = Obd.is_busy
        self.gps = GPS()

    def setAlive(self):
        self.is_alive = True
        self.updateData()

    def isConnected(self):
        return self.connected_uid != ''

    def updateSpeedLimit(self):
        currsl = 0
        if self.gps.isGPSConnected():
            currsl = self.gps.getSpeedLimit()
            print(f'1-current speed limit: {currsl}')
        try:
            currsl = int(currsl)
            print(f'2-current speed limit: {currsl}')
        except ValueError:
            currsl = 0  
        if currsl != self.speed_limit:
            print(f'3-current speed limit: {currsl}')
            self.speed_limit = currsl
            # self.updateStatus(f'SPEED_LIMIT: {self.speed_limit}')
            print(f'speed limit updated to: {self.speed_limit}')

    def updateStatus(self, status='available'):
        self.status = status
        self.updateData()

    def updateError(self, error_msg):
        self.error_msg = error_msg

    def updateUserStatus(self, status, uid):
        if uid is not None and uid != '':
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
        self.gps.connectGPS()
        # self.updateSpeedLimit()
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
            'is_connected': self.isConnected(),
            'speed_limit': self.speed_limit
        }
        db.reference(OBD_REFERENCE).child(self.id).set(dict)
        if self.isConnected():
            db.reference(USERS_REFERENCE).child(self.connected_uid).child('connected_obd').set(self.id)
