import requests
import json
import time
from helpers.config import config


_request_cache = {}
_request_cache_stats = {'hits': 0, 'misses': 0, 'outdated': 0, 'clears': 0, 'partial': 0}
_server_url = 'http://' + config['brickserver']['host'] + ':' + str(config['brickserver']['port'])


def clear_request_cache(partial=None):
    global _request_cache
    global _request_cache_stats
    if partial is None:
        _request_cache_stats['clears'] += 1
        _request_cache = {}
    else:
        _request_cache_stats['partial'] += 1
        for k in [k for k in _request_cache.keys() if partial in k]:
            _request_cache.pop(k)


def _request_cached(payload):
    global _request_cache
    global _request_cache_stats
    global _server_url
    session = requests.Session()
    session.headers = {
        'content-type': "application/json",
        'accept': "application/json"
    }
    if isinstance(payload, dict):
        payload = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    elif isinstance(payload, string):
        payload = payload.replace(' ', '').replace('\n', '')
    else:
        raise ValueError('invalid payload')

    if payload in _request_cache:
        if (time.time() - _request_cache[payload]['time']) < 600:
            _request_cache_stats['hits'] += 1
            print(f"Request Cache Stats: {json.dumps(_request_cache_stats)}")
            return _request_cache[payload]['data']
        _request_cache_stats['outdated'] += 1

    _request_cache_stats['misses'] += 1
    url = _server_url + '/admin'
    r = session.post(url, data=payload).json()
    _request_cache[payload] = {'time': time.time(), 'data': r}
    print(f"Request Cache Misses: {payload}")
    print(f"Request Cache Stats: {json.dumps(_request_cache_stats)}")
    return r


def serverversion_get():
    r = _request_cached({"command": "get_version"})
    if r['s'] == 0:
        return r['version']
    else:
        return '0.0.0'


def features_get_available():
    return _request_cached({"command": "get_features"})['features']


def count_get(item):
    r = _request_cached({'command': 'get_count', 'item': item})
    if r['s'] == 0:
        return int(r['count'])
    else:
        return 0


"""
brick operations
"""


def brick_get(brick_id):
    return _request_cached({"command": "get_brick", "brick": brick_id})['brick']


def brick_exists(brick_id):
    return 0 == _request_cached({"command": "get_brick", "brick": brick_id})['s']


def brick_set_desc(brick_id, desc):
    _request_cached({'command': 'set', 'brick': brick_id, 'key': 'desc', 'value': desc})
    clear_request_cache(brick_id)


def brick_delete(brick_id):
    _request_cached({"command": "delete_brick", "brick": brick_id})
    clear_request_cache()


def bricks_get():
    brick_ids = _request_cached({"command": "get_bricks"})['bricks']
    for brick_id in brick_ids:
        brick_get(brick_id)
    return brick_ids


def bricks_get_filtered(feature=None, f=None):
    if feature == 'all':
        feature = None
    if f == "":
        f = None
    elif f is not None:
        f = f.lower()

    result = []
    for brick_id in bricks_get():
        brick = brick_get(brick_id)
        if feature is not None and feature not in brick['features']:
            continue
        if f is not None and f not in brick['_id'].lower() and (brick['desc'] is None or f not in brick['desc'].lower()):
            continue
        result.append((brick['_id'], brick['desc']))
    return result


def bricks_get_sorted_by_bat_runtime_prediction():
    result = []
    for brick_id in bricks_get():
        brick = brick_get(brick_id)
        if 'bat' in brick['features'] and not brick.get('bat_wall_powered', False):
            brp = (brick['bat_runtime_prediction'] if 'bat_runtime_prediction' in brick else None)
            volt = str(round(brick['bat_last_reading'], 2)) + 'V' if 'bat_last_reading' in brick else '???V'
            result.append([brick_id, brick['desc'], brp, volt])

    for i in range(0, len(result) - 1):
        for j in range(i + 1, len(result)):
            swap = False
            if result[i][2] is None and result[j][2] is not None:
                swap = True
            elif result[i][2] is not None and result[j][2] is not None and result[j][2] < result[i][2]:
                swap = True
            if swap:
                t = result[i]
                result[i] = result[j]
                result[j] = t
    return result


def brick_set_solar_charging(brick_id, enable):
    _request_cached({'command': 'set', 'brick': brick_id, 'key': 'bat_solar_charging', 'value': enable})
    clear_request_cache(brick_id)


def brick_set_sleep_disabled(brick_id, disabled=False):
    _request_cached({'command': 'set', 'brick': brick_id, 'key': 'sleep_disabled', 'value': disabled})
    clear_request_cache(brick_id)


def brick_set_adc5V(brick_id, adc5V):
    _request_cached({'command': 'set', 'brick': brick_id, 'key': 'bat_adc5V', 'value': int(adc5V)})
    clear_request_cache(brick_id)


"""
temp-sensor operations
"""


def temp_sensor_get(sensor_id):
    return _request_cached({"command": "get_temp_sensor", "temp_sensor": sensor_id})['temp_sensor']


def temp_sensor_exists(sensor_id):
    return 0 == _request_cached({"command": "get_temp_sensor", "temp_sensor": sensor_id})['s']


def temp_sensor_set_desc(sensor_id, desc):
    _request_cached({'command': 'set', 'temp_sensor': sensor_id, 'key': 'desc', 'value': desc})
    clear_request_cache(sensor_id)


def temp_sensor_disable(sensor_id, what, enable):
    if enable:
        _request_cached({'command': 'set', 'temp_sensor': sensor_id, 'key': 'add_disable', 'value': what})
    else:
        _request_cached({'command': 'set', 'temp_sensor': sensor_id, 'key': 'del_disable', 'value': what})
    clear_request_cache(sensor_id)


"""
humid-sensor operations
"""


def humid_sensor_get(sensor_id):
    return _request_cached({"command": "get_humid_sensor", "humid_sensor": sensor_id})['humid_sensor']


def humid_sensor_exists(sensor_id):
    return 0 == _request_cached({"command": "get_humid_sensor", "humid_sensor": sensor_id})['s']


def humid_sensor_set_desc(sensor_id, desc):
    _request_cached({'command': 'set', 'humid_sensor': sensor_id, 'key': 'desc', 'value': desc})
    clear_request_cache(sensor_id)


def humid_sensor_disable(sensor_id, what, enable):
    if enable:
        _request_cached({'command': 'set', 'humid_sensor': sensor_id, 'key': 'add_disable', 'value': what})
    else:
        _request_cached({'command': 'set', 'humid_sensor': sensor_id, 'key': 'del_disable', 'value': what})
    clear_request_cache(sensor_id)


"""
latch operations
"""


def latch_get(brick_id, latch_id):
    lid = str(brick_id) + '_' + str(int(latch_id))
    return _request_cached({"command": "get_latch", "latch": lid})['latch']


def latch_exists(brick_id, latch_id):
    lid = str(brick_id) + '_' + str(int(latch_id))
    return 0 == _request_cached({"command": "get_latch", "latch": lid})['s']


def latch_set_desc(latch_id, desc):
    _request_cached({'command': 'set', 'latch': latch_id, 'key': 'desc', 'value': desc})
    clear_request_cache(latch_id)


def latch_set_states_desc(latch_id, state, desc):
    _request_cached({'command': 'set', 'latch': latch_id, 'state': int(state), 'key': 'state_desc', 'value': desc})
    clear_request_cache(latch_id)


def latch_add_trigger(latch_id, trigger_id):
    _request_cached({'command': 'set', 'latch': latch_id, 'key': 'add_trigger', 'value': int(trigger_id)})
    clear_request_cache(latch_id)


def latch_del_trigger(latch_id, trigger_id):
    _request_cached({'command': 'set', 'latch': latch_id, 'key': 'del_trigger', 'value': int(trigger_id)})
    clear_request_cache(latch_id)


def latch_disable(latch_id, what, enable):
    if enable:
        print(_request_cached({'command': 'set', 'latch': latch_id, 'key': 'add_disable', 'value': what}))
    else:
        print(_request_cached({'command': 'set', 'latch': latch_id, 'key': 'del_disable', 'value': what}))
    clear_request_cache(latch_id)


"""
signal operations
"""


def signal_get(brick_id, signal_id):
    sid = brick_id + '_' + str(signal_id)
    return _request_cached({"command": "get_signal", "signal": sid})['signal']


def signal_exists(brick_id, signal_id):
    sid = brick_id + '_' + str(signal_id)
    return 0 == _request_cached({"command": "get_signal", "signal": sid})['s']


def signal_set_desc(signal_id, desc):
    _request_cached({'command': 'set', 'signal': signal_id, 'key': 'desc', 'value': desc})
    clear_request_cache(signal_id)


def signal_set_states_desc(signal_id, state, desc):
    _request_cached({'command': 'set', 'signal': signal_id, 'state': int(state), 'key': 'state_desc', 'value': desc})
    clear_request_cache(signal_id)


def signal_set_state(signal_id, state):
    _request_cached({'command': 'set', 'signal': signal_id, 'key': 'signal', 'value': int(state)})
    clear_request_cache(signal_id)


def signal_disable(signal_id, what, enable):
    if enable:
        _request_cached({'command': 'set', 'signal': signal_id, 'key': 'add_disable', 'value': what})
    else:
        _request_cached({'command': 'set', 'signal': signal_id, 'key': 'del_disable', 'value': what})
    clear_request_cache(signal_id)


"""
heater operations
"""


def heater_get(brick_id):
    return _request_cached({"command": "get_heater", "heater": brick_id})['heater']


def heater_exists(brick_id):
    return 0 == _request_cached({"command": "get_heater", "heater": brick_id})['s']


def heater_set_desc(heater_id, desc):
    _request_cached({'command': 'set', 'heater': heater_id, 'key': 'desc', 'value': desc})
    clear_request_cache(heater_id)


def heater_set_states_desc(heater_id, state, desc):
    _request_cached({'command': 'set', 'heater': heater_id, 'state': int(state), 'key': 'state_desc', 'value': desc})
    clear_request_cache(heater_id)


def heater_set_state(heater_id, state):
    _request_cached({'command': 'set', 'heater': heater_id, 'key': 'heater', 'value': int(state)})
    clear_request_cache(heater_id)


def heater_disable(heater_id, what, enable):
    if enable:
        _request_cached({'command': 'set', 'heater': heater_id, 'key': 'add_disable', 'value': what})
    else:
        _request_cached({'command': 'set', 'heater': heater_id, 'key': 'del_disable', 'value': what})
    clear_request_cache(heater_id)


"""
firmware operations
"""


def firmwares_get():
    return _request_cached({"command": "get_firmwares"}).get('firmwares')


def firmware_get(brick_type=None, sketchMD5=None, latest=None, version=None, name=None):
    if name is not None and not name.lower() == 'none':
        brick_type, version = name.split('_', 1)
    if brick_type is not None and version is not None:
        return _request_cached({"command": "get_firmware", "brick_type": brick_type, "version": version}).get('firmware')
    elif brick_type is not None and sketchMD5 is not None:
        return _request_cached({"command": "get_firmware", "brick_type": brick_type, "sketchmd5": sketchMD5}).get('firmware')
    elif latest is not None:
        return _request_cached({"command": "get_firmware", "latest": latest}).get('firmware')
    else:
        return None


def firmware_delete(brick_type=None, sketchMD5=None, latest=None, version=None, name=None, fw=None, bin_only=False):
    if fw is not None and not fw.lower() == 'none':
        brick_type = fw.get('brick_type')
        version = fw.get('version')
    elif name is not None and not name.lower() == 'none':
        brick_type, version = name.split('_', 1)
    result = None
    if brick_type is not None and version is not None:
        result = _request_cached({"command": "delete_firmware", "brick_type": brick_type, "version": version, "bin_only": bin_only})
    elif brick_type is not None and sketchMD5 is not None:
        result = _request_cached({"command": "delete_firmware", "brick_type": brick_type, "sketchmd5": sketchMD5, "bin_only": bin_only})
    elif latest is not None:
        result = _request_cached({"command": "delete_firmware", "latest": latest, "bin_only": bin_only})
    clear_request_cache('firmware')
    return result


def firmware_update(brick_id, request=True):
    """
    requests or canceles an OTA Update
    """
    _request_cached({'command': 'set', 'brick': brick_id, 'key': 'otaupdate', 'value': ('requested' if request else 'canceled')})
    clear_request_cache(brick_id)


def firmware_upload(firmware):
    global _server_url
    files = {'firmware': firmware}
    url = _server_url + '/upload'
    result = requests.post(url, files=files).json()
    clear_request_cache('firmware')
    return result


def firmware_fetch(what, brick_id=None, brick_type=None, version=None):
    payload = {'command': 'fetch_firmware', 'what': what}
    if brick_id is not None:
        payload['brick'] = brick_id
    if brick_type is not None:
        payload['brick_type'] = brick_type
    if version is not None:
        payload['version'] = version
    result = _request_cached(payload)
    clear_request_cache('firmware')
    return result
