import json
from helpers.brickserver import temp_sensor_get, humid_sensor_get, latch_get, serverversion_get, signal_get, heater_get, bricks_get, brick_get
from helpers.config import config
from datetime import datetime, timedelta


def convert_html(json_obj):
    return json.dumps(json_obj, indent=4, sort_keys=True).replace(' ', '&nbsp;').replace('\n', '<br />\n')


def list_of_temp_sensors_of_brick(brick):
    if 'temp' in brick['features'] or 'heat' in brick['features']:
        return [temp_sensor_get(sensor) for sensor in brick['temp_sensors']]
    else:
        return list()


def list_of_humid_sensors_of_brick(brick):
    if 'humid' in brick['features']:
        return [humid_sensor_get(sensor) for sensor in brick['humid_sensors']]
    else:
        return list()


def list_of_latches_of_brick(brick):
    if 'latch' in brick['features'] and brick['latch_count'] is not None:
        return [latch_get(brick['_id'], i) for i in range(0, brick['latch_count'])]
    else:
        return list()


def list_of_signals_of_brick(brick):
    if 'signal' in brick['features'] and brick['signal_count'] is not None:
        return [signal_get(brick['_id'], i) for i in range(0, brick['signal_count'])]
    else:
        return list()


def list_of_heaters_of_brick(brick):
    r = list()
    if 'heat' in brick['features']:
        r.append(heater_get(brick['_id']))
    return r


def has_disabled_sensors(brick):
    for s in list_of_temp_sensors_of_brick(brick) + list_of_humid_sensors_of_brick(brick) + list_of_latches_of_brick(brick) + list_of_signals_of_brick(brick) + list_of_heaters_of_brick(brick):
        if 'ui' in s['disables']:
            return True
    return False


def grafana_url_bat_level(brick):
    url = f"http://{config['grafana']['host']}:{config['grafana']['port']}/d/2RQaypHnk/?"
    query = f"var-brick_desc={brick['desc'] if brick['desc'] is not None else ''}"
    query += f"&var-brick_id={brick['_id']}"
    return url + query


def grafana_url_temp_sensor(brick, sensor):
    url = f"http://{config['grafana']['host']}:{config['grafana']['port']}/d/bwVhKMEMz/?"
    query = f"var-brick_desc={brick['desc'] if brick['desc'] is not None else ''}"
    query += f"&var-brick_id={brick['_id']}"
    query += f"&var-sensor_desc={sensor['desc'] if sensor['desc'] is not None else ''}"
    query += f"&var-sensor_id={sensor['_id']}"
    return url + query


def grafana_url_humid_sensor(brick, sensor):
    url = f"http://{config['grafana']['host']}:{config['grafana']['port']}/d/5i1GBVNnz/?"
    query = f"var-brick_desc={brick['desc'] if brick['desc'] is not None else ''}"
    query += f"&var-brick_id={brick['_id']}"
    query += f"&var-sensor_desc={sensor['desc'] if sensor['desc'] is not None else ''}"
    query += f"&var-sensor_id={sensor['_id']}"
    return url + query


def grafana_url_latch(brick, latch):
    brick_id, lid = latch['_id'].split('_')
    url = f"http://{config['grafana']['host']}:{config['grafana']['port']}/d/0qV6PIN7z/?"
    query = f"var-brick_desc={brick['desc'] if brick['desc'] is not None else ''}"
    query += f"&var-brick_id={brick['_id']}"
    query += f"&var-latch_desc={latch['desc'] if latch['desc'] is not None else ''}"
    query += f"&var-latch_id={lid}"
    return url + query


def grafana_url_signal(brick, signal):
    brick_id, sid = signal['_id'].split('_')
    url = f"http://{config['grafana']['host']}:{config['grafana']['port']}/d/FKBPR0bnk/?"
    query = f"var-brick_desc={brick['desc'] if brick['desc'] is not None else ''}"
    query += f"&var-brick_id={brick['_id']}"
    query += f"&var-signal_desc={signal['desc'] if signal['desc'] is not None else ''}"
    query += f"&var-signal_id={sid}"
    return url + query


def grafana_url_heater(brick, heater):
    url = f"http://{config['grafana']['host']}:{config['grafana']['port']}/d/vSf8CudSz/?"
    query = f"var-brick_desc={brick['desc'] if brick['desc'] is not None else ''}"
    query += f"&var-brick_id={brick['_id']}"
    query += f"&var-heater_desc={heater['desc'] if heater['desc'] is not None else ''}"
    query += f"&var-heater_id={heater['_id']}"
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


def having_bricks_timeout():
    """
    returns true if at least one brick is having a timedeleta of last_ts more than 30 minutes
    """
    for brick_id in bricks_get():
        brick = brick_get(brick_id)
        if (datetime.now() - timedelta(minutes=30)) > datetime.fromtimestamp(brick['last_ts']):
            return True
    return False


def list_of_bricks_timed_out():
    """
    returns a list of all [brick_id, desc, delta, hour_passed] of all bricks having a timedeleta of last_ts more than 30 minutes
    """
    result = list()
    for brick_id in bricks_get():
        brick = brick_get(brick_id)
        if (datetime.now() - timedelta(minutes=30)) > datetime.fromtimestamp(brick['last_ts']):
            hour_passed = (datetime.now() - timedelta(minutes=60)) > datetime.fromtimestamp(brick['last_ts'])
            delta = time_ago_str(brick['last_ts'])
            result.append([brick['_id'], brick['desc'], delta, hour_passed])
    return result
