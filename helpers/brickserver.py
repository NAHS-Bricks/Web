import requests


bricks = {
    'aabbccddee11': {
        '_id': 'aabbccddee11',
        'desc': 'brick1',
        'features': ['temp', 'bat', 'sleep'],
        'temp_sensors': ['sensor1', 'sensor2']
    },
    'aabbccddee22': {
        '_id': 'aabbccddee22',
        'desc': 'brick2',
        'features': ['temp'],
        'temp_sensors': ['sensor3', 'sensor4', 'sensor5']
    },
    'aabbccddee33': {
        '_id': 'aabbccddee33',
        'desc': 'brick3',
        'features': ['bat']
    }
}


sensors = {
    'sensor1': 24,
    'sensor2': 24.1,
    'sensor3': 24.2,
    'sensor4': 24.3,
    'sensor5': 24.4
}


def get_bricks():
    global bricks
    return bricks.keys()


def get_bricks_filtered(feature=None, f=None):
    global bricks
    if feature == 'all':
        feature = None
    if f == "":
        f = None

    result = []
    for brick in bricks.values():
        if feature is not None and feature not in brick['features']:
            continue
        if f is not None and f not in brick['_id'] and f not in brick['desc']:
            continue
        result.append((brick['_id'], brick['desc']))
    return result


def get_brick(brick_id):
    global bricks
    return bricks[brick_id]


def get_temp_sensor(sensor_id):
    global sensors
    return {'last_temp': sensors[sensor_id]}


def set_desc(brick_id, desc):
    global bricks
    bricks[brick_id]['desc'] = desc
