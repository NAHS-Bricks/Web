import json
from helpers.brickserver import temp_sensor_get, latch_get, serverversion_get, signal_get
from helpers.shared import config
from datetime import datetime, timedelta


def convert_html(json_obj):
    return json.dumps(json_obj, indent=4, sort_keys=True).replace(' ', '&nbsp;').replace('\n', '<br />\n')


def list_of_temp_sensors_of_brick(brick):
    if 'temp' in brick['features']:
        return [temp_sensor_get(sensor) for sensor in brick['temp_sensors']]
    else:
        return list()


def list_of_latches_of_brick(brick):
    if 'latch' in brick['features']:
        return [latch_get(brick['_id'], i) for i in range(0, brick['latch_count'])]
    else:
        return list()


def list_of_signals_of_brick(brick):
    if 'signal' in brick['features']:
        return [signal_get(brick['_id'], i) for i in range(0, brick['signal_count'])]
    else:
        return list()


def has_disabled_sensors(brick):
    for s in list_of_temp_sensors_of_brick(brick) + list_of_latches_of_brick(brick) + list_of_signals_of_brick(brick):
        if 'ui' in s['disables']:
            return True
    return False


def grafana_url_bat_level(brick_id):
    url = "http://" + config['grafana']['host'] + ":" + str(config['grafana']['port']) + "/explore"
    query = f"?orgId=1&left=%5B%22now-24h%22,%22now%22,%22{config['grafana']['datasource']}%22,%7B%22datasource%22:%22{config['grafana']['datasource']}%22,%22policy%22:%2226weeks%22,%22resultFormat%22:%22time_series%22,%22orderByTime%22:%22ASC%22,%22tags%22:%5B%7B%22key%22:%22brick_id%22,%22operator%22:%22%3D%22,%22value%22:%22{brick_id}%22%7D%5D,%22groupBy%22:%5B%5D,%22select%22:%5B%5B%7B%22type%22:%22field%22,%22params%22:%5B%22voltage%22%5D%7D%5D%5D,%22measurement%22:%22bat_levels%22%7D%5D"
    return url + query


def grafana_url_temp_sensor(sensor_id):
    url = "http://" + config['grafana']['host'] + ":" + str(config['grafana']['port']) + "/explore"
    query = f"?orgId=1&left=%5B%22now-1h%22,%22now%22,%22{config['grafana']['datasource']}%22,%7B%22datasource%22:%22{config['grafana']['datasource']}%22,%22policy%22:%228weeks%22,%22resultFormat%22:%22time_series%22,%22orderByTime%22:%22ASC%22,%22tags%22:%5B%7B%22key%22:%22sensor_id%22,%22operator%22:%22%3D%22,%22value%22:%22{sensor_id}%22%7D%5D,%22groupBy%22:%5B%5D,%22select%22:%5B%5B%7B%22type%22:%22field%22,%22params%22:%5B%22celsius%22%5D%7D%5D%5D,%22measurement%22:%22temps%22%7D%5D"
    return url + query


def grafana_url_latch(latch_id):
    brick_id, lid = latch_id.split('_')
    url = "http://" + config['grafana']['host'] + ":" + str(config['grafana']['port']) + "/explore"
    query = f"?orgId=1&left=%5B%22now-6h%22,%22now%22,%22{config['grafana']['datasource']}%22,%7B%22datasource%22:%22{config['grafana']['datasource']}%22,%22policy%22:%2226weeks%22,%22resultFormat%22:%22time_series%22,%22orderByTime%22:%22ASC%22,%22tags%22:%5B%7B%22key%22:%22brick_id%22,%22operator%22:%22%3D%22,%22value%22:%22{brick_id}%22%7D,%7B%22condition%22:%22AND%22,%22key%22:%22latch_id%22,%22operator%22:%22%3D%22,%22value%22:%22{lid}%22%7D%5D,%22groupBy%22:%5B%5D,%22select%22:%5B%5B%7B%22type%22:%22field%22,%22params%22:%5B%22state%22%5D%7D%5D%5D,%22measurement%22:%22latches%22%7D%5D"
    return url + query


def time_ago_str(fromtime_ts):
    seconds = int((datetime.now() - datetime.fromtimestamp(fromtime_ts)).total_seconds())
    result = ''
    if seconds > (60 * 60 * 24):
        result += str(int(seconds / (60 * 60 * 24))) + 'd '
        seconds %= (60 * 60 * 24)
    if seconds > (60 * 60):
        result += str(int(seconds / (60 * 60))) + 'h '
        seconds %= (60 * 60)
    if seconds > 60:
        result += str(int(seconds / 60)) + 'm '
        seconds %= 60
    result += str(seconds) + 's'
    return result


def server_is(version):
    """
    executes version <= server
    this means: true is returned if server is at least at the version specified in version
    up to three dots are valid: major.minor.patch.fix
    """
    version = version.split('.')
    while len(version) < 4:
        version.append('0')
    server = serverversion_get().split('.')
    while len(server) < 4:
        server.append('0')
    for i in range(4):
        if int(server[i]) < int(version[i]):
            return False
    return True
