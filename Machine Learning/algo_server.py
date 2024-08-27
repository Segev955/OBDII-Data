import os
import sys
import time
import threading
import numpy as np
from enum import Enum
import firebase_admin
from firebase_admin import credentials, db
from keras import models
from prediction_model import model_prediction

REAL_TIME_REFERANCE = 'LiveData'
OBD_REFERENCE       = 'Obd'

obd_dict = {} 

def get_live_data():
    while True:
        obd_ref = db.reference(REAL_TIME_REFERANCE)
        obd_snapshot = obd_ref.get()
        print("Listening for new live data...")
        if not obd_snapshot:
            print("Didn't find new live data.")
            time.sleep(10)
            continue

        for obd_id in obd_snapshot.keys():
            if obd_id not in obd_dict:
                print(f"OBD {obd_id} started driving.")

                obd_dict[obd_id] = 0
                if isinstance(obd_snapshot[obd_id], dict):
                    obd_dict[obd_id] = int (list(obd_snapshot[obd_id].keys())[0])
                print(f'Live drives: {obd_dict.keys()}')
            
            lock = threading.Lock()
            # with lock:
                # start_time = time.time()
                # thread = threading.Thread(target=run_algorithm, args=(obd_id, start_time,))

            #     thread.start()
            start_time = time.time()
            run_algorithm(obd_id, start_time) 


        time.sleep(5) 


def run_algorithm(obd_id, start_time):
    data =[]
    first5rows = True
    while True:
        row_index = obd_dict[obd_id]
        print(f' \nrow index = {row_index} \n') #TODO delete, only for testing
        obd_ref = db.reference(f'{REAL_TIME_REFERANCE}/{obd_id}')
        obd_snapshot = obd_ref.get()
        print(f'len of obd snap = {len(obd_snapshot)}')

        finished = False

        new_data = []
        if isinstance(obd_snapshot, dict):
            if obd_snapshot and str(row_index) in list(obd_snapshot.keys()):

                for i in range(row_index, len(obd_snapshot)): 
                    new_data.append(obd_snapshot[str(i)]) 
                data.extend(new_data)
            else:
                finished = True

        elif isinstance(obd_snapshot, list):
            if obd_snapshot and len(obd_snapshot) > row_index:

                for i in range(row_index, len(obd_snapshot)): 
                    new_data.append(obd_snapshot[i]) 
                data.extend(new_data)
            else:
                finished = True

        if finished:

            print(f'no more data from OBD {obd_id}')
            break

        else:
            print(f'Checked OBD {obd_id} row {row_index}: {data[-1]}')


        print(f'Current Thread = {threading.current_thread()}')

        uids        = ['2W5Nq5aZ4cP9VA6zEWBbi7FicxE2', 'lT3ip6zL8gU34vuoONy5UTmWwPg1', 'vcAN0KURuBYtNhztFCJJR9y4EhR2']
        

        obd_dict[obd_id] = len(obd_snapshot)
        
        if first5rows and len(data)>=5:
            first5rows = False
            data = data[5:]

        print('len data = ', len(data))

        prediction, data = model_prediction(uids, data)
        print(f'prediction= {prediction}')

        max_speed = max(item['speed'] for item in data)
        print(f'max speed = {max_speed}')
        if prediction and (time.time() - start_time >= 20*60 or max_speed > 30):
            db.reference(OBD_REFERENCE).child(obd_id).child('last_driver').set(prediction)
            break
        else:
            prediction = prediction if prediction != 'STOLEN' else 'UNKOWN DRIVER'
            db.reference(OBD_REFERENCE).child(obd_id).child('last_driver').set(prediction)

        #time.sleep(1)


def run_algo_server():
    print("Start listening for new drives...")

    get_live_data()

if __name__ == '__main__':

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

    run_algo_server()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped by user")
