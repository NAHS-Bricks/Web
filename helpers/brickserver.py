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
        brp = (brick['bat_runtime_prediction'] if 'bat_runtime_prediction' in brick else None)
        result.append([brick_id, brick['desc'], brp])

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
event operations
"""


def event_get(event_id):
    return _request_cached({'command': 'get_event', 'event': event_id})['event']


def event_add(brick_id):
    _request_cached({'command': 'add_event', 'brick': brick_id})
    clear_request_cache(brick_id)


def event_delete(brick_id, event_id):
    _request_cached({'command': 'delete_event', 'brick': brick_id, 'event': event_id})
    clear_request_cache(brick_id)


def event_set_pos(brick_id, event_id, index):
    _request_cached({'command': 'set', 'key': 'pos', 'event': event_id, 'value': int(index)})
    clear_request_cache(brick_id)
    clear_request_cache(event_id)


"""
event_command operations
"""


def event_commands_list():
    return _request_cached({'command': 'get_event_commands'})['commands']


def event_command_set(event_id, command_name, ed_name):
    _request_cached({'command': 'set', 'key': 'event_command', 'event': event_id, 'event_data': ed_name, 'value': command_name})
    clear_request_cache(event_id)


"""
event_reaction operations
"""


def event_reactions_list():
    return _request_cached({'command': 'get_event_reactions'})['reactions']


def event_reaction_add(event_id, reaction_name, ed_name):
    _request_cached({'command': 'add_event_reaction', 'event': event_id, 'event_reaction': reaction_name, 'event_data': ed_name})
    clear_request_cache(event_id)


def event_reaction_delete(event_id, pos):
    _request_cached({'command': 'delete_event_reaction', 'event': event_id, 'pos': int(pos)})
    clear_request_cache(event_id)


def event_reaction_move(event_id, from_pos, to_pos):
    _request_cached({'command': 'set', 'key': 'pos', 'event': event_id, 'reaction_src': int(from_pos), 'value': int(to_pos)})
    clear_request_cache(event_id)


"""
event_data operations
"""


def event_data_replace(event_id, ed_name, ed_data):
    _request_cached({'command': 'replace_event_data', 'event': event_id, 'event_data': ed_name, 'content': ed_data})
    clear_request_cache(event_id)


def event_data_get(event_id, ed_name):
    return _request_cached({'command': 'get_event_data', 'event': event_id, 'event_data': ed_name})['event_data']


def event_data_get_names(event_id, level):
    return _request_cached({'command': 'get_event_data_names', 'event': event_id, 'level': level})['event_data_names']
