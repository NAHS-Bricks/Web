import json
from helpers.brickserver import temp_sensor_get


def convert_html(json_obj):
    return json.dumps(json_obj, indent=4, sort_keys=True).replace(' ', '&nbsp;').replace('\n', '<br />\n')


def list_of_sensor_ids_to_sensors(sensor_ids):
    return [temp_sensor_get(sensor) for sensor in sensor_ids]
