#!/usr/bin/python3

import RPi.GPIO as GPIO
import can
import time
import os
import queue
from threading import Thread
import datetime
from GPS import speed_limit
import threading
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(
    "/home/segev/Project/OBDII-Data/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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

user_name = input("Please enter your name(only first name): ")
print(f"Hello {user_name}, Have a nice Drive!")

outfile = open(f'{user_name}.txt', 'a')

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


def upload_to_firestore(data):
    db.collection(user_name).add(data)


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
        # Sent a Engine coolant temperature request
        msg = can.Message(arbitration_id=PID_REQUEST,
                          data=[0x02, 0x01, ENGINE_COOLANT_TEMP, 0x00, 0x00, 0x00, 0x00, 0x00], is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Sent a Engine RPM request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, ENGINE_RPM, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Sent a Vehicle speed  request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, VEHICLE_SPEED, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Sent a Throttle position request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, THROTTLE, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, FUEL, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)

        # Sent a FUEL level request
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

temperature = 0
rpm = 0
speed = 0
throttle = 0
fuel = 0
test1 = 0
c = ''
count = 0
speedLimit = 0

# Main loop
try:
    while True:

        for i in range(4):
            while (q.empty() == True):  # Wait until there is a message
                pass
            message = q.get()
            dt_object = datetime.datetime.fromtimestamp(message.timestamp)
            formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

            c = '{0:f},{1:s},{2:d}'.format(message.timestamp, formatted_time, count)
            if message.arbitration_id == PID_REPLY and message.data[2] == ENGINE_COOLANT_TEMP:
                temperature = message.data[3] - 40  # Convert data into temperature in degree C

            if message.arbitration_id == PID_REPLY and message.data[2] == ENGINE_RPM:
                rpm = round(((message.data[3] * 256) + message.data[4]) / 4)  # Convert data to RPM

            if message.arbitration_id == PID_REPLY and message.data[2] == VEHICLE_SPEED:
                speed = message.data[3]  # Convert data to km

            if message.arbitration_id == PID_REPLY and message.data[2] == THROTTLE:
                throttle = round((message.data[3] * 100) / 255)  # Conver data to %

            if message.arbitration_id == PID_REPLY and message.data[2] == FUEL:
                fuel = round((100 / 255) * message.data[3])

            if speedLimit is None:
                speedLimit = 0
            speedLimit = int(speedLimit)

        c += '{0:d},{1:d},{2:d},{3:d},{4:d},{5:d}'.format(temperature, rpm, speed, throttle, fuel, speedLimit)
        print('\r {} '.format(c))
        print(c, file=outfile)  # Save data to file
        count += 1

except KeyboardInterrupt:
    # Catch keyboard interrupt
    GPIO.output(led, False)
    # Close the file before processing its content
    outfile.close()

    # Open the file from the beginning in read mode
    outfile = open(outfile.name, 'r')
    for line in outfile:
        data = line.strip().split(',')
        if len(data) == 8:  # Assuming each line has 8 fields
            timestamp = data[1]
            temperature = int(data[2])
            rpm = int(data[3])
            speed = int(data[4])
            throttle = int(data[5])
            fuel = int(data[6])
            speed_limitt = int(data[7])

            # Upload data to Firestore
            upload_to_firestore({
                'timestamp': timestamp,
                'temperature': temperature,
                'rpm': rpm,
                'speed': speed,
                'throttle': throttle,
                'fuel': fuel,
                'speed_limit': speed_limitt
            })

    # Clean up
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrupt')

# Remove the file after processing
outfile.close()

time.sleep(0.05)
if input("if you want to shutdown the Raspberry Pi press 's': ") == 's':
    os.system("sudo shutdown -h now")
print(f'See you again {user_name}')
