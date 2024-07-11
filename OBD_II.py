#!/usr/bin/python3

import sys
import RPi.GPIO as GPIO
import can
import time
import os
import queue
from threading import Thread
import datetime
import csv
import threading
import firebase_admin
from firebase_admin import credentials, firestore, storage, db as realtime_db


# Initialize Firebase Admin SDK
cred = credentials.Certificate(
    "/home/segev/Project/OBDII-Data/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'car-driver-bc91f.appspot.com',
    'databaseURL': 'https://car-driver-bc91f-default-rtdb.asia-southeast1.firebasedatabase.app/'
})
db = firestore.client()
bucket = storage.bucket()

def update_status(status):
    realtime_db.reference('status').set(status)

from GPS import speed_limit, GPSError

if GPSError:
    update_status("GPS Error")
    sys.exit()


# Retrieve driver name and car type from environment variables

user_name = os.getenv('DRIVER_UID', 'Unknown')
car_type = os.getenv('CAR_TYPE', 'Unknown')
led = 22
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(led, GPIO.OUT)
GPIO.output(led, True)

# For a list of PIDs visit https://en.wikipedia.org/wiki/OBD-II_PIDs
ENGINE_COOLANT_TEMP = 0x05
ENGINE_RPM = 0x0C
VEHICLE_SPEED = 0x0D
MAF_SENSOR = 0x10
O2_VOLTAGE = 0x14
THROTTLE = 0x11
FUEL = 0x2F
TEST1 = 0x50

PID_REQUEST = 0x7DF
PID_REPLY = 0x7E8

print(f"Hello {user_name}, Have a nice Drive!")

current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
outfile_path = f'{user_name}_{current_time}.csv'

print('\n\rCAN Rx test')
print('Bring up CAN0....')

# Bring up can0 interface at 500kbps
os.system("sudo /sbin/ip link set can0 down")
time.sleep(0.1)
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
print('Ready')

try:
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
except OSError:
    print('Cannot find PiCAN board.')
    GPIO.output(led, False)
    exit()

cars_ref = db.collection('Cars').add({
    'car_type': car_type,
})
cars_id = cars_ref[1].id

drivers_ref = db.collection('Drivers').add({
    'driver_name': user_name,
    'cars_id': cars_id
})
drivers_id = drivers_ref[1].id


def update_speed_limit():
    global speedLimit
    try:
        while True:
            speedLimit = speed_limit()
            if speedLimit is None:
                speedLimit = 0
            time.sleep(10)  # Check for speed limit every 10 seconds
    except KeyboardInterrupt:
        print("Speed limit update interrupted")


# Start the speed limit update thread
speed_limit_thread = threading.Thread(target=update_speed_limit)
speed_limit_thread.daemon = True  # This will allow the thread to terminate when the main program exits
speed_limit_thread.start()


def can_rx_task():  # Receive thread
    while True:
        message = bus.recv()
        if message.arbitration_id == PID_REPLY:
            q.put(message)  # Put message into queue


def can_tx_task():  # Transmit thread
    while True:
        GPIO.output(led, True)
        # Send a Engine coolant temperature request
        msg = can.Message(arbitration_id=PID_REQUEST,
                          data=[0x02, 0x01, ENGINE_COOLANT_TEMP, 0x00, 0x00, 0x00, 0x00, 0x00], is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Send a Engine RPM request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, ENGINE_RPM, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Send a Vehicle speed request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, VEHICLE_SPEED, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Send a Throttle position request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, THROTTLE, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Send a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, FUEL, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Send a TEST1 level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST1, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        GPIO.output(led, False)
        time.sleep(0.1)


q = queue.Queue()
rx = Thread(target=can_rx_task)
rx.start()
tx = Thread(target=can_tx_task)
tx.start()

temperature = None
rpm = None
speed = None
throttle = None
fuel = None
test1 = None
c = ''
count = 0
speedLimit = 0
previous_speed = None
previous_time = None

# Main loop
try:
    # Open CSV file and write header
    with open(outfile_path, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'datetime', 'count', 'temperature', 'rpm', 'speed', 'throttle', 'fuel', 'speedLimit',
                      'acceleration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        while True:
            for i in range(4):
                while q.empty():  # Wait until there is a message
                    pass
                message = q.get()
                dt_object = datetime.datetime.fromtimestamp(message.timestamp)
                formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

                if message.arbitration_id == PID_REPLY and message.data[2] == ENGINE_COOLANT_TEMP:
                    temperature = message.data[3] - 40  # Convert data into temperature in degree C

                if message.arbitration_id == PID_REPLY and message.data[2] == ENGINE_RPM:
                    rpm = round(((message.data[3] * 256) + message.data[4]) / 4)  # Convert data to RPM

                if message.arbitration_id == PID_REPLY and message.data[2] == VEHICLE_SPEED:
                    speed = message.data[3]  # Convert data to km/h

                if message.arbitration_id == PID_REPLY and message.data[2] == THROTTLE:
                    throttle = round((message.data[3] * 100) / 255)  # Convert data to %

                if message.arbitration_id == PID_REPLY and message.data[2] == FUEL:
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
                    'speedLimit': speedLimit,
                    'acceleration': acceleration
                }

                writer.writerow(data)
                count += 1

except KeyboardInterrupt:
    # Catch keyboard interrupt
    GPIO.output(led, False)
    # Close the file before processing its content
    csvfile.close()


    # Upload the file to Firebase Storage
    def upload_file_to_storage(file_path, collection_name, document_id):
        blob = bucket.blob(f'drives/{os.path.basename(file_path)}')
        blob.upload_from_filename(file_path)
        blob.make_public()

        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.set({
            'file_name': os.path.basename(file_path),
            'file_url': blob.public_url
        })
        print(f"File {file_path} uploaded to Firebase Storage and reference saved to Firestore.")
        update_status('Upload complete')


    # Upload the file to Firebase Storage and save reference to Firestore
    document_id = f'{user_name}_{int(time.time())}'
    upload_file_to_storage(outfile_path, 'Drives', document_id)

    # Clean up
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrupt')

# Remove the file after processing
print(f'See you again{user_name}')
