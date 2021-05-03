import requests
import json
import time
from helpers.shared import config


_request_cache = {}
_request_cache_stats = {'hits': 0, 'misses': 0, 'outdated': 0, 'clears': 0, 'partial': 0}


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
    url = 'http://' + config['brickserver']['host'] + ':' + str(config['brickserver']['port']) + '/admin'
    r = session.post(url, data=payload).json()
    _request_cache[payload] = {'time': time.time(), 'data': r}
    print(f"Request Cache Misses: {payload}")
    print(f"Request Cache Stats: {json.dumps(_request_cache_stats)}")
    return r


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


def temp_sensor_get(sensor_id):
    return _request_cached({"command": "get_temp_sensor", "temp_sensor": sensor_id})['temp_sensor']


def temp_sensor_exists(sensor_id):
    return 0 == _request_cached({"command": "get_temp_sensor", "temp_sensor": sensor_id})['s']


def temp_sensor_set_desc(sensor_id, desc):
    _request_cached({'command': 'set', 'temp_sensor': sensor_id, 'key': 'desc', 'value': desc})
    clear_request_cache(sensor_id)


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


def features_get_available():
    return _request_cached({"command": "get_features"})['features']
