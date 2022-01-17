from helpers.brickserver import firmware_get, bricks_get, brick_get


def firmware_name(fw):
    if fw is None:
        return "None"
    return f"{fw['brick_type']}_{fw['version']}"


def firmware_bin_present(brick_type=None, sketchMD5=None, latest=None, version=None, name=None, brick=None, fw=None):
    if fw is not None:
        return fw.get('bin', False)
    if brick is not None:
        brick_type = brick.get('type')
        sketchMD5 = brick.get('sketchMD5')
    fw = firmware_get(brick_type=brick_type, sketchMD5=sketchMD5, latest=latest, version=version, name=name)
    return False if fw is None else fw.get('bin', False)


def firmware_is_latest(fw):
    result = firmware_get(latest=fw.get('brick_type'))
    return fw.get('sketchMD5') == result.get('sketchMD5')


def firmware_is_used(fw):
    for brick_id in bricks_get():
        brick = brick_get(brick_id=brick_id)
        if brick.get('sketchMD5', None) == fw.get('sketchMD5', '') and brick.get('type', 0) == int(fw.get('brick_type')):
            return True
    return False


def firmware_is_dev(fw):
    return fw.get('dev', False)


def firmware_used_on(fw):
    result = list()
    for brick_id in bricks_get():
        brick = brick_get(brick_id=brick_id)
        if brick.get('sketchMD5', None) == fw.get('sketchMD5', '') and brick.get('type', 0) == int(fw.get('brick_type')):
            result.append(brick)
    return result


def firmware_browser_is_shown(f, t, fw):
    if not f or \
            (f == 'latest' and firmware_is_latest(fw=fw)) or \
            (f == 'present' and firmware_bin_present(fw=fw)) or \
            (f == 'used' and firmware_is_used(fw=fw)) or \
            (f == 'dev' and firmware_is_dev(fw=fw)):
        if not t or t == str(fw.get('brick_type')):
            return True
    return False


def firmware_compare_table(fw1, fw2):
    result = list()
    for k in sorted({k for k in list((fw1['content'].keys()) if fw1 is not None else []) + (list(fw2['content'].keys() if fw2 is not None else []))}):
        result.append([
            k,
            ('' if k not in fw1['content'] else fw1['content'][k]) if fw1 is not None else '',
            ('' if k not in fw2['content'] else fw2['content'][k]) if fw2 is not None else ''
        ])
    return result


def firmware_state(brick):
    if brick['features']['os'] < 1.01:
        return 'outdated'
    elif 'otaUpdate' in brick and not brick['otaUpdate'] == 'canceled':
        return brick['otaUpdate']
    elif brick['sketchMD5'] is None:
        return 'pending'
    elif firmware_get(latest=brick['type']) is None:
        return 'outdated'
    elif brick['sketchMD5'] == firmware_get(latest=brick['type'])['sketchMD5']:
        return 'up to date'
    else:
        return 'outdated'


def firmware_version(brick):
    if brick['features']['os'] < 1.01:
        return 'unknown'
    if brick['sketchMD5'] is None:
        return 'unknown'
    fw = firmware_get(brick_type=brick['type'], sketchMD5=brick['sketchMD5'])
    if fw is None:
        return 'unknown'
    else:
        return firmware_name(fw)


def firmware_is_updating(brick):
    if brick.get('otaUpdate', 'requested') not in ['requested', 'canceled']:
        return True
    return False
