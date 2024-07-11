import requests
from gps import *
import time

GPSError = False
last_speed_limit = 0
last_speed_limit_time = 0

def get_speed_limit(latitude, longitude):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
        [out:json];
        way(around:10, {latitude}, {longitude})[maxspeed];
        out;
    """

    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()
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

def getPositionData(gpsd):
    try:
        nx = gpsd.next()
        if nx['class'] == 'TPV':
            latitude = getattr(nx, 'lat', "Unknown")
            longitude = getattr(nx, 'lon', "Unknown")
            return speedLim(latitude, longitude)
    except Exception as e:
        print(f"Error getting position data: {e}")
        return None

def speedLim(latitude, longitude):
    speed_limit = get_speed_limit(latitude, longitude)
    if speed_limit is not None:
        return speed_limit
    else:
        return 0

try:
    gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
except Exception as e:
    print(f"Error initializing GPS: {e}")
    GPSError = True
    gpsd = None

def speed_limit():
    global last_speed_limit, last_speed_limit_time

    if gpsd is None:
        return 0

    try:
        current_time = time.time()
        # Check if it's been more than 10 seconds since last speed limit update
        if current_time - last_speed_limit_time > 10:
            new_speed_limit = getPositionData(gpsd)
            if new_speed_limit is not None:
                last_speed_limit = new_speed_limit
                last_speed_limit_time = current_time
            return last_speed_limit
        else:
            return last_speed_limit
    except KeyboardInterrupt:
        print("Applications closed!")
        return 0
    except Exception as e:
        print(f"Error in speed_limit function: {e}")
        return 0
