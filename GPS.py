import requests


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


# Example usage:
latitude = 37.773972
longitude = -122.431297
speed_limit = get_speed_limit(latitude, longitude)
if speed_limit is not None:
    print("Speed Limit:", speed_limit)
else:
    print("Unable to retrieve speed limit.")
