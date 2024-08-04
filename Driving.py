#!/usr/bin/python3
import sys
from Obd_class import *
import firebase_admin
from firebase_admin import credentials, firestore, storage
import RPi.GPIO as GPIO
import can
import time
import os
import queue
from threading import Thread
import datetime
import csv
import shutil

SAVE_DIR = 'drives'
UPLOADED_DIR = 'Uploaded'


class Driving:
    def __init__(self, obd_device: Obd):
        while True:
            try:
                cred = credentials.Certificate(
                    f"{os.getcwd()}/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
                firebase_admin.initialize_app(cred, {
                    'storageBucket': 'car-driver-bc91f.appspot.com',
                    'databaseURL': 'https://car-driver-bc91f-default-rtdb.asia-southeast1.firebasedatabase.app/'
                })
                print("Firebase initialized successfully.")
                break
            except Exception as e:
                print(f"Error initializing Firebase: {e}. Retrying in 5 seconds...")
                time.sleep(1)

        self.obd_device = obd_device
        self.db = firestore.client()
        self.bucket = storage.bucket()
        self.led = 22
        self.bus = None
        self.GPSConnected = False
        self.q = queue.Queue()
        self.drive_thread = None
        self.csvfile = None
        self.outfile_path = None

        self.ENGINE_COOLANT_TEMP = 0x05
        self.ENGINE_RPM = 0x0C
        self.VEHICLE_SPEED = 0x0D
        self.MAF_SENSOR = 0x10
        self.O2_VOLTAGE = 0x14
        self.THROTTLE = 0x11
        self.FUEL = 0x2F
        self.TEST1 = 0x50
        self.PID_REQUEST = 0x7DF
        self.PID_REPLY = 0x7E8

        # Start the speed limit update thread
        self.speed_limit_thread = threading.Thread(target=self.update_speed_limit)
        self.speed_limit_thread.daemon = True  # This will allow the thread to terminate when the main program exits
        self.speed_limit_thread.start()

        # Upload saved files that have not uploaded.
        # self.upload_all()

    def getOBD(self):
        return self.obd_device

    def startDriving(self, driver=True):
        try:
            if not self.obd_device.is_busy:
                if driver:
                    self.obd_device.updateStatus("starting...")
                else:
                    self.clean_data_realtime()
                print(
                    f"Start command received. Driver: {self.obd_device.connected_uid}. Running data collection script...")

                # Start PiCAN2 board
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.led, GPIO.OUT)
                GPIO.output(self.led, True)

                print('\n\rCAN Rx test')
                print('Bring up CAN0....')
                # Bring up can0 interface at 500kbps
                os.system("sudo /sbin/ip link set can0 down")
                time.sleep(0.1)
                os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
                time.sleep(0.1)
                print('Ready')
                try:
                    self.bus = can.interface.Bus(channel='can0', bustype='socketcan')
                except OSError:
                    print('Cannot find PiCAN board.')
                    GPIO.output(self.led, False)
                    if driver:
                        self.obd_device.updateStatus("CAN board error")
                    return

                self.obd_device.is_busy = True
                self.drive_thread = Thread(target=self.drive(driver))
                self.drive_thread.start()
        except Exception as e:
            self.obd_device.is_busy = False
            if driver:
                self.obd_device.updateStatus(f"Error during startDriving")
            print(f"Error during startDriving: {e}")

    def stopDriving(self):
        self.obd_device.updateStatus("Stop call")
        # if self.obd_device.is_busy:
        self.obd_device.is_busy = False

        if self.drive_thread is not None:
            self.drive_thread.join()
            self.drive_thread = None

        # if self.speed_limit_thread is not None:
        #     self.speed_limit_thread.join()
        #     self.speed_limit_thread = None

        self.obd_device.updateStatus("Stopping...")
        print("Stop command received")
        GPIO.output(self.led, False)
        os.system("sudo /sbin/ip link set can0 down")

        if self.csvfile is not None:
            self.csvfile.close()
            self.csvfile = None

        self.upload_file_to_storage(self.outfile_path)
        self.obd_device.updateStatus("Stopped successfully")
        print("Stopped successfully")

    def connectGPS(self):
        if not self.obd_device.gps.connectGPS():
            self.obd_device.updateStatus("GPS Error")
            print("GPS Error")
            return False
        print("GPS Connected")
        return True

    def update_speed_limit(self):
        print('Starting speed limit listener')
        while True:
            try:
                self.obd_device.updateSpeedLimit()
                time.sleep(1)  # Check for speed limit every 10 seconds
            except KeyboardInterrupt:
                print("Speed limit update interrupted")

    # Upload the file to Firebase Storage
    def upload_file_to_storage(self, file_path):
        blob = self.bucket.blob(f'{SAVE_DIR}/{self.obd_device.connected_uid}/{os.path.basename(file_path)}')
        blob.upload_from_filename(file_path)
        blob.make_public()

        print(f"File {file_path} uploaded to Firebase Storage and reference saved to Firestore.")
        self.obd_device.updateStatus('Upload complete')

        # Move the file to the "Uploaded" folder
        uploaded_folder = os.path.join(os.path.dirname(file_path), UPLOADED_DIR)
        os.makedirs(uploaded_folder, exist_ok=True)
        shutil.move(file_path, os.path.join(uploaded_folder, os.path.basename(file_path)))
        print(f"File {file_path} moved to {uploaded_folder}.")

    def upload_all(self, dir=SAVE_DIR):
        for file in os.listdir(dir):
            if file.endswith(".csv"):
                self.upload_file_to_storage(file)

    def can_rx_task(self):  # Receive thread
        try:
            while True:
                message = self.bus.recv()
                if message.arbitration_id == self.PID_REPLY:
                    self.q.put(message)  # Put message into queue
        except Exception as e:
            self.obd_device.is_busy = False
            self.obd_device.updateStatus(f"CAN RX Error")
            print(f"CAN RX Error: {e}")

    def can_tx_task(self):  # Transmit thread
        try:
            while True:
                GPIO.output(self.led, True)
                # Send a Engine coolant temperature request
                msg = can.Message(arbitration_id=self.PID_REQUEST,
                                  data=[0x02, 0x01, self.ENGINE_COOLANT_TEMP, 0x00, 0x00, 0x00, 0x00, 0x00],
                                  is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.05)

                # Send a Engine RPM request
                msg = can.Message(arbitration_id=self.PID_REQUEST,
                                  data=[0x02, 0x01, self.ENGINE_RPM, 0x00, 0x00, 0x00, 0x00, 0x00],
                                  is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.05)

                # Send a Vehicle speed request
                msg = can.Message(arbitration_id=self.PID_REQUEST,
                                  data=[0x02, 0x01, self.VEHICLE_SPEED, 0x00, 0x00, 0x00, 0x00, 0x00],
                                  is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.05)

                # Send a Throttle position request
                msg = can.Message(arbitration_id=self.PID_REQUEST,
                                  data=[0x02, 0x01, self.THROTTLE, 0x00, 0x00, 0x00, 0x00, 0x00],
                                  is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.05)

                # Send a FUEL level request
                msg = can.Message(arbitration_id=self.PID_REQUEST,
                                  data=[0x02, 0x01, self.FUEL, 0x00, 0x00, 0x00, 0x00, 0x00],
                                  is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.05)

                # Send a TEST1 level request
                msg = can.Message(arbitration_id=self.PID_REQUEST,
                                  data=[0x02, 0x01, self.TEST1, 0x00, 0x00, 0x00, 0x00, 0x00],
                                  is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.05)

                GPIO.output(self.led, False)
                time.sleep(0.1)
        except Exception as e:
            self.obd_device.is_busy = False
            self.obd_device.updateStatus(f"CAN TX Error")
            print(f"CAN TX Error: {e}")
            self.stopDriving()

    def upload_data_to_realtime(self, data):
        try:
            db.reference(f"LiveData/{ID}").push(data)
            print(f"Data uploaded to Realtime Database: {data}")
        except Exception as e:
            print(f"Error uploading data to Realtime Database: {e}")

    def clean_data_realtime(self):
        try:
            db.reference(f"LiveData/{ID}").delete()
            print("LiveData cleaned")
        except Exception as e:
            print(f"Error cleaning LiveData: {e}")

    def drive(self, drive=False):
        try:
            if self.obd_device.is_busy:
                rx = Thread(target=self.can_rx_task)
                rx.start()
                tx = Thread(target=self.can_tx_task)
                tx.start()

                temperature = None
                rpm = None
                speed = None
                throttle = None
                fuel = None
                c = ''
                count = 0
                previous_speed = None
                previous_time = None

                if not drive:
                    self.obd_device.is_available = True
                # Main loop
                try:
                    # Open CSV file and write header
                    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    outfile_name = f'{self.obd_device.connected_uid}_{current_time}'
                    print(f"Creating file: {outfile_name}")
                    self.outfile_path = f'{SAVE_DIR}/{outfile_name}.csv'

                    with open(self.outfile_path, 'w', newline='') as csvfile:
                        fieldnames = ['timestamp', 'datetime', 'count', 'temperature', 'rpm', 'speed', 'throttle',
                                      'fuel',
                                      'speedLimit',
                                      'acceleration']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        self.obd_device.updateStatus("Driving..")

                        while self.obd_device.is_busy:
                            for i in range(4):
                                while self.q.empty():  # Wait until there is a message
                                    pass
                                message = self.q.get()
                                dt_object = datetime.datetime.fromtimestamp(message.timestamp)
                                formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

                                if message.arbitration_id == self.PID_REPLY and message.data[
                                    2] == self.ENGINE_COOLANT_TEMP:
                                    temperature = message.data[3] - 40  # Convert data into temperature in degree C

                                if message.arbitration_id == self.PID_REPLY and message.data[2] == self.ENGINE_RPM:
                                    rpm = round(((message.data[3] * 256) + message.data[4]) / 4)  # Convert data to RPM

                                if message.arbitration_id == self.PID_REPLY and message.data[2] == self.VEHICLE_SPEED:
                                    speed = message.data[3]  # Convert data to km/h

                                if message.arbitration_id == self.PID_REPLY and message.data[2] == self.THROTTLE:
                                    throttle = round((message.data[3] * 100) / 255)  # Convert data to %

                                if message.arbitration_id == self.PID_REPLY and message.data[2] == self.FUEL:
                                    fuel = round((100 / 255) * message.data[3])

                                # Calculate acceleration
                                if previous_speed is not None and previous_time is not None:
                                    time_diff = message.timestamp - previous_time
                                    if time_diff > 0:
                                        acceleration = (speed - previous_speed) / time_diff
                                    else:
                                        acceleration = 0
                                else:
                                    acceleration = 0

                                previous_speed = speed
                                previous_time = message.timestamp

                                data = {
                                    'timestamp': message.timestamp,
                                    'datetime': formatted_time,
                                    'count': count,
                                    'temperature': temperature,
                                    'rpm': rpm,
                                    'speed': speed,
                                    'throttle': throttle,
                                    'fuel': fuel,
                                    'speedLimit': self.obd_device.speed_limit,
                                    'acceleration': acceleration
                                }
                                print(data)
                                writer.writerow(data)
                                count += 1
                                if not drive:
                                    self.upload_data_to_realtime(data)

                except Exception as e:
                    print(f"Error in main loop: {e}")
                    self.obd_device.is_busy = False
                    # self.obd_device.updateStatus(f"Error in main loop: {e}")
                    GPIO.output(self.led, False)
                    if self.csvfile is not None:
                        self.csvfile.close()
                        self.csvfile = None

                finally:
                    self.obd_device.is_busy = False
                    self.obd_device.updateStatus("Drive ended")
                    GPIO.output(self.led, False)
                    os.system("sudo /sbin/ip link set can0 down")
                    if self.csvfile is not None:
                        self.csvfile.close()
                        self.csvfile = None

        except Exception as e:
            print(f"Error in drive function: {e}")
            self.obd_device.is_busy = False
            # self.obd_device.updateStatus(f"Error in drive function: {e}")
            GPIO.output(self.led, False)
            if self.csvfile is not None:
                self.csvfile.close()
                self.csvfile = None
