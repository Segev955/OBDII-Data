import requests
from gps import *
import time
import threading


class GPS:
    def __init__(self):
        self.gpsd = None
        self.GPSError = False
        self.last_speed_limit = 0
        self.last_speed_limit_time = 0
        self.is_connected = False
        self.nx = None
        self.latitude = 0
        self.longitude = 0

    def get_speed_limit(self, latitude, longitude):
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
            [out:json];
            way(around:10, {latitude}, {longitude})[maxspeed];
            out;
        """

        try:
            response = requests.get(overpass_url, params={'data': overpass_query})
            data = response.json()
            print(data)
            if 'elements' in data:
                for element in data['elements']:
                    if 'tags' in element:
                        tags = element['tags']
                        if 'maxspeed' in tags:
                            speed_limit = tags['maxspeed']
                            return speed_limit
                return None
            else:
                return None
        except Exception as e:
            print("Error:", e)
            return None

    def getPositionData(self):
        try:
            if self.nx['class'] == 'TPV':
                self.latitude = getattr(self.nx, 'lat', "Unknown")
                self.longitude = getattr(self.nx, 'lon', "Unknown")
                print(f"Latitude: {self.latitude}, Longitude: {self.longitude}")
                return self.speedLim(self.latitude, self.longitude)
        except Exception as e:
            print(f"Error getting position data: {e}")
            return None

    def getCurrentValues(self):
        try:
            while True:
                self.nx = self.gpsd.next()
                time.sleep(0.2)
        except StopIteration:
            pass

    def speedLim(self, latitude, longitude):
        speed_limit = self.get_speed_limit(latitude, longitude)
        if speed_limit is not None:
            return speed_limit
        else:
            return 0

    def speed_limit(self):
        if not self.is_connected:
            return 0
        try:
            new_speed_limit = self.getPositionData()
            # print(f"Speed limit(speed_limit): {new_speed_limit}")
            if new_speed_limit is not None:
                self.last_speed_limit = new_speed_limit
                # print(f"Speed limit(speed_limit-if): {self.last_speed_limit}")
            return self.last_speed_limit
        except KeyboardInterrupt:
            print("Applications closed!")
            return 0
        except Exception as e:
            print(f"Error in speed_limit function: {e}")
            return 0

    def connectGPS(self):
        try:
            self.gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
            self.is_connected = True
            print("GPS connected successfully.")
            threading.Thread(target=self.getCurrentValues).start()
        except Exception as e:
            self.is_connected = False
            print(f"Error initializing GPS: {e}")
        return self.is_connected

    def isGPSConnected(self):
        try:
            if self.gpsd is not None:
                nx = self.gpsd.next()
                if nx['class'] == 'TPV':
                    self.is_connected = True
                else:
                    self.is_connected = False
            else:
                self.is_connected = False
        except Exception as e:
            self.is_connected = False
        return self.is_connected

    def getSpeedLimit(self):
        return self.speed_limit()


def monitorGPS():
    gps = GPS()
    gps.connectGPS()
    was_connected = None
    while True:
        is_connected = gps.isGPSConnected()
        if is_connected and was_connected != True:
            print("GPS connected")
            was_connected = True
        elif not is_connected and was_connected != False:
            print("GPS disconnected")
            was_connected = False

        speed_limit = gps.getSpeedLimit()
        print(f"Current speed limit: {speed_limit}")

        time.sleep(5)

# Start the monitorGPS function in a separate thread
# gps_thread = Thread(target=monitorGPS)
# gps_thread.start()
