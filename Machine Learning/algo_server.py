import os
import sys
import time
import threading
import numpy as np
from enum import Enum
import firebase_admin
from firebase_admin import credentials, db
from keras import models
from pre_process import pre_process

REAL_TIME_REFERANCE = 'LiveData'
OBD_REFERENCE       = 'Obd'
TIMESTAMPS          = 100

obd_dict = {} #{key: value} - key: obd_id, value: row_counter

model_file  = 'LSTM_model.keras'
try: 
    model = models.load_model(model_file)
except FileNotFoundError as e:
    raise FileNotFoundError('Model not found - add the model.keras file to the dir.') from e



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
            with lock:
                thread = threading.Thread(target=run_algorithm, args=(obd_id,))
                thread.start()


        time.sleep(20)  # Run this check every 20 seconds


def run_algorithm(obd_id):
    data =[]
    for _ in range(TIMESTAMPS):
        row_index = obd_dict[obd_id]
        obd_ref = db.reference(f'{REAL_TIME_REFERANCE}/{obd_id}')
        obd_snapshot = obd_ref.get()
        # print(list(obd_snapshot.keys())[0])
        finished = False

        if isinstance(obd_snapshot, dict):
            if obd_snapshot and str(row_index) in list(obd_snapshot.keys()):
                data.append(obd_snapshot[str(row_index)])
            else:
                finished = True

        elif isinstance(obd_snapshot, list):
            if obd_snapshot and len(obd_snapshot) > row_index:
                data.append(obd_snapshot[row_index])
            else:
                finished = True

        if finished:
            #del obd_dict[obd_id]
            print(f'no more data from OBD {obd_id}')
            break

        else:
            print(f'Checked OBD {obd_id} row {row_index}: {data[-1]}')


        ####################### APPLY ALGORITHM HERE ##################################

        # data- a list of dictionaries, every dictionary is a second from the driving
        # the list grows every iteration, the list is ordered
        # data[0] is the first second from the driving
        # data[-1] is the last second that never checked
        # row_index is the index of the row, but it's better to use data[-1] because row_index not always starts at 0
        # you should update driver_result to the UID of the driver that the algorithm found that he is the driver.

        ## EXAMPLES
        print(f'Current Thread = {threading.current_thread()}')

        uids        = ['2W5Nq5aZ4cP9VA6zEWBbi7FicxE2', 'lT3ip6zL8gU34vuoONy5UTmWwPg1', 'vcAN0KURuBYtNhztFCJJR9y4EhR2']
        

        if len(data) <= 5 :
            input           = pre_process(data)
            prediction      = (model.predict(input))[0][-1]
            driver_result   = uids[np.argmax(prediction)]
            
            print(f'prediction= {prediction}' )

            print(f'driver result = \n {driver_result}')

            # print(data[-1]['datetime']) # should print the last date and time from the data
            # if 'rpm' in list(data[-1].keys()):
            #     print(data[-1]['rpm'])  # should print the last rpm from the data
            
            # for i in range(len(data)):
            #     print(data[i]['speed'])  # should print all the speed data from the start until now
            

            # driver_result = 'lT3ip6zL8gU34vuoONy5UTmWwPg1' # end of the iteration, save the current result
            obd_dict[obd_id] += 1
            db.reference(OBD_REFERENCE).child(obd_id).child('last_driver').set(driver_result)
            #time.sleep(1)

        if max(prediction) > 0.8: #if prediction certainty is greater than 80%
            return #TODO do we need to return a value? e.g. driver_result
        #TODO change while True to a for loop after which car reported stolen (ideal), or add a "forth" driver to the model that will be the thief.
    
    db.reference(OBD_REFERENCE).child(obd_id).child('last_driver').set('STOLEN')


def run_algo_server():
    print("Start listening for new drives...")
    # threading.Thread(target=get_live_data, daemon=True).start() #TODO
    get_live_data()

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

    run_algo_server()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped by user")
