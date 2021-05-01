import json
from helpers.brickserver import temp_sensor_get, latch_get
from helpers.shared import config


def convert_html(json_obj):
    return json.dumps(json_obj, indent=4, sort_keys=True).replace(' ', '&nbsp;').replace('\n', '<br />\n')


def list_of_sensor_ids_to_sensors(sensor_ids):
    return [temp_sensor_get(sensor) for sensor in sensor_ids]


def list_of_latches_of_brick(brick):
    return [latch_get(brick['_id'], i) for i in range(0, brick['latch_count'])]


def grafana_url_bat_level(brick_id):
    url = "http://" + config['grafana']['host'] + ":" + str(config['grafana']['port']) + "/explore"
    query = f"?orgId=1&left=%5B%22now-24h%22,%22now%22,%22{config['grafana']['datasource']}%22,%7B%22datasource%22:%22{config['grafana']['datasource']}%22,%22policy%22:%2226weeks%22,%22resultFormat%22:%22time_series%22,%22orderByTime%22:%22ASC%22,%22tags%22:%5B%7B%22key%22:%22brick_id%22,%22operator%22:%22%3D%22,%22value%22:%22{brick_id}%22%7D%5D,%22groupBy%22:%5B%5D,%22select%22:%5B%5B%7B%22type%22:%22field%22,%22params%22:%5B%22voltage%22%5D%7D%5D%5D,%22measurement%22:%22bat_levels%22%7D%5D"
    return url + query


def grafana_url_temp_sensor(sensor_id):
    url = "http://" + config['grafana']['host'] + ":" + str(config['grafana']['port']) + "/explore"
    query = f"?orgId=1&left=%5B%22now-1h%22,%22now%22,%22{config['grafana']['datasource']}%22,%7B%22datasource%22:%22{config['grafana']['datasource']}%22,%22policy%22:%228weeks%22,%22resultFormat%22:%22time_series%22,%22orderByTime%22:%22ASC%22,%22tags%22:%5B%7B%22key%22:%22sensor_id%22,%22operator%22:%22%3D%22,%22value%22:%22{sensor_id}%22%7D%5D,%22groupBy%22:%5B%5D,%22select%22:%5B%5B%7B%22type%22:%22field%22,%22params%22:%5B%22celsius%22%5D%7D%5D%5D,%22measurement%22:%22temps%22%7D%5D"
    return url + query


def grafana_url_latch(latch_id):
    url = "http://" + config['grafana']['host'] + ":" + str(config['grafana']['port']) + "/explore"
    return url
