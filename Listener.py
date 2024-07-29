from Driving import *
import atexit
import threading

def entrylistener(event):
    if event.data is not None:
        print("Event path:", event.path)
        print("Event data:", event.data)
        if event.path == "/" and "user_id" in event.data and "key" in event.data:
            uid = event.data.get("user_id", "Unknown")
            key = event.data.get("key", "Nothing")

            if driving.getOBD().connect(uid, key):
                ###### turn off Algorithm thread
                db.reference(OBD_REFERENCE).child(driving.getOBD().id).listen(drivelistener)

def drivelistener(event):
    if event.data is not None:
        if event.path == "/":
            status = event.data.get("status", "no_status")
            alive = event.data.get("is_alive", False)
            if not alive:
                driving.getOBD().setAlive()
            print(f"OBD status: <{status}>")
        else:
            print("Event path:", event.path)
            print("Event data:", event.data)

            if event.path == "/status":
                if isinstance(event.data, str):
                    status = event.data
                    if status == 'start':
                        driving_thread = threading.Thread(target=driving.startDriving)
                        driving_thread.start()
                    elif status == 'stop':
                        print('stoppppp')
                        driving.stopDriving()
                    elif status == 'Disconnect':
                        driving.getOBD().disconnect()
                        db.reference(ENTRIES_REFERENCE).child(driving.getOBD().id).listen(entrylistener)
                    elif status == 'Shutting down':
                        driving.getOBD().shutDown()
                    else:
                        print(f"got unknown status: <{status}>")

if __name__ == '__main__':
    if len(sys.argv) >= 4:
        id_arg = sys.argv[1]
        name_arg = sys.argv[2]
        key_arg = sys.argv[3]
        obd = Obd(id=id_arg, name=name_arg, key=key_arg)
        print(f"Details set successfully: id={id_arg}, name={name_arg}, key={key_arg}")
    else:
        obd = Obd()
        print(f"Using default details")

    driving = Driving(obd)

    # Schedule set_active to run periodically
    def set_alive_periodically():
        while True:
            driving.getOBD().setAlive()
            time.sleep(10)  # Run this check every 10 seconds

    # Run set_active in a separate thread
    threading.Thread(target=set_alive_periodically, daemon=True).start()

##### Thread for using the Algorithm

##driving.startDriving(True)

######




    # Get Available for connections
    try:
        success = False
        while not success:
            print("Attempting to set up Firebase listener...")
            try:
                db.reference(ENTRIES_REFERENCE).child(driving.getOBD().id).listen(entrylistener)
                driving.getOBD().startUp()
                success = True
            except Exception as e:
                print(f"Error setting up Firebase listener: {e}. Retrying in 5 seconds...")
                time.sleep(5)
    except Exception as e:
        driving.getOBD().shutDown()
        print(f"Crashed with error {e}.")
        time.sleep(5)
