#!/usr/bin/python3

import RPi.GPIO as GPIO
import can
import time
import os
import queue
from threading import Thread
import datetime


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
TEST1 = 0x0100
TEST2 = 0x0101
TEST3 = 0x0102
TEST4 = 0x0103
TEST5 = 0x0104
TEST6 = 0x0105
TEST7 = 0x0106
TEST8 = 0x0107

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

        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST2, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)
        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST3, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)
        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST4, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)
        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST5, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)
        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST6, 0x00, 0x00, 0x00, 0x00, 0x00],
                          is_extended_id=False)
        bus.send(msg)
        time.sleep(0.05)
        # Sent a FUEL level request
        msg = can.Message(arbitration_id=PID_REQUEST, data=[0x02, 0x01, TEST7, 0x00, 0x00, 0x00, 0x00, 0x00],
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
test2 = 0
test3 = 0
test4 = 0
test5 = 0
test6 = 0
test7 = 0
c = ''
count = 0


# Main loop
try:
    while True:

        for i in range(4):
            while (q.empty() == True):  # Wait until there is a message
                pass
            message = q.get()
            dt_object = datetime.datetime.fromtimestamp(message.timestamp)
            formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

            c = '{0:f},{1:s},{2:d}'.format(message.timestamp,formatted_time, count)
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
            #     ///////////////////////////////////////////////
            if message.arbitration_id == PID_REPLY and message.data[2] == TEST1:
                test1 = message.data[3]

            if message.arbitration_id == PID_REPLY and message.data[2] == TEST2:
                test2 = message.data[3]

            if message.arbitration_id == PID_REPLY and message.data[2] == TEST3:
                test3 = message.data[3]

            if message.arbitration_id == PID_REPLY and message.data[2] == TEST4:
                test4 = message.data[3]

            if message.arbitration_id == PID_REPLY and message.data[2] == TEST5:
                test5 = message.data[3]

            if message.arbitration_id == PID_REPLY and message.data[2] == TEST6:
                test6 = message.data[3]

            if message.arbitration_id == PID_REPLY and message.data[2] == TEST7:
                test7 = message.data[3]

        c += '{0:d},{1:d},{2:d},{3:d},{4:d},{5:d},{6:d},{7:d},{8:d},{9:d},{10:d},{11:d}'.format(temperature, rpm, speed, throttle, fuel, test1, test2, test3, test4, test5, test6, test7)
        print('\r {} '.format(c))
        print(c, file=outfile)  # Save data to file
        count += 1



except KeyboardInterrupt:
    # Catch keyboard interrupt
    GPIO.output(led, False)
    outfile.close()  # Close logger file
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrtupt')

time.sleep(0.05)
if input("if you want to shutdown the Raspberry Pi press 's': ") == 's':
    os.system("sudo shutdown -h now")
print(f'See you again {user_name}')
