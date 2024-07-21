from Obd_class import *
import atexit
import threading

obd_device = Obd()
def on_exit():
    obd_device.shutDown()
    print("The program is exiting. Shutting down...")



def entrylistener(event):
    if event.data is not None:
        print("Event path:", event.path)
        print("Event data:", event.data)
        if event.path == "/" and "user_id" in event.data and "key" in event.data:
            uid = event.data.get("user_id", "Unknown")
            key = event.data.get("key", "Nothing")

            if obd_device.connect(uid,key):
                db.reference(OBD_REFERENCE).child(obd_device.id).listen(drivelistener)



def drivelistener(event):
    if event.data is not None:
        if event.path == "/":
            status = event.data.get("status", "no_status")
            alive = event.data.get("is_alive", False)
            if not alive:
                obd_device.setAlive()
            print(f"OBD status: <{status}>")
        else:
            print("Event path:", event.path)
            print("Event data:", event.data)

            if event.path == "/status":
                if isinstance(event.data, str):
                    status = event.data
                    if status == 'start':
                        obd_device.startDriving()
                    elif status == 'stop':
                        obd_device.stopDriving()
                    elif status == 'disconnected':
                        obd_device.disconnect()
                        db.reference(ENTRIES_REFERENCE).child(obd_device.id).listen(entrylistener)
                    elif status == 'Shutting down':
                        obd_device.shutDown()
                    else:
                        print(f"got unknown status: <{status}>")



if __name__ == '__main__':
    atexit.register(on_exit)
    if len(sys.argv) >= 4:
        id_arg = sys.argv[1]
        name_arg = sys.argv[2]
        key_arg = sys.argv[3]
        obd_device = Obd(id=id_arg, name=name_arg, key=key_arg)
        print(f"Details set successfully: id={id_arg}, name={name_arg}, key={key_arg}")
    else:
        obd_device = Obd()
        print(f"Using default details")

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
            obd_device.shutDown()
            time.sleep(1)


    # Schedule set_active to run periodically
    def set_alive_periodically():
        while True:
            obd_device.setAlive()
            time.sleep(10)  # Run this check every 10 seconds


    # Run set_active in a separate thread
    threading.Thread(target=set_alive_periodically, daemon=True).start()

    # Get Available for connections
    try:
        success = False
        while not success:
            print("Attempting to set up Firebase listener...")
            try:
                db.reference(ENTRIES_REFERENCE).child(obd_device.id).listen(entrylistener)
                obd_device.startUp()
                success = True
            except Exception as e:
                print(f"Error setting up Firebase listener: {e}. Retrying in 5 seconds...")
                time.sleep(5)
    except Exception as e:
        obd_device.shutDown()
        print(f"Crashed with error {e}.")
        time.sleep(5)

