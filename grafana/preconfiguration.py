import requests
import json
import os
import sys
import argparse

parser = argparse.ArgumentParser(description="Preconfigure-Grafana")
parser.add_argument('--host', dest='host', required=False, help='Used to inject the Host-Address')
args = parser.parse_args()

config = {
    'host': '',
    'port': 3000,
    'user': 'admin',
    'password': 'admin'
}

ds_name = 'NAHS-BrickServer'
directory_title = 'NAHS-BrickWeb_builtin'
directory = None
least_version = '8.1.5'


def create_datasource():
    default_influx_port = 8086
    influx_host = input("InfluxDB host: ")
    if influx_host.strip() == '':
        print('invalid input!')
        sys.exit(1)
    influx_port = input(f"InfluxDB port ({default_influx_port}): ")
    if influx_port.strip() == '':
        influx_port = default_influx_port
    config = {
        'name': ds_name,
        'type': 'influxdb',
        'access': 'proxy',
        'url': f'http://{influx_host}:{influx_port}',
        'database': 'brickserver',
        'basicAuth': False
    }
    s.post(server + '/api/datasources', data=json.dumps(config))


def create_dashboard(uid, title):
    global ds_name
    global directory
    dashboard = json.loads(open(f'dashboards/{title}.json', 'r').read().replace('${DS_NAHS-BRICKSERVER}', ds_name))
    dashboard['title'] = title
    dashboard['uid'] = uid
    dashboard['editable'] = False
    r = s.post(server + '/api/dashboards/db', data=json.dumps({'dashboard': dashboard, 'folderId': directory, 'overwrite': True}))
    print(r.text)


def version_greater_or_equal_than(a, b):
    """
    executes a >= b
    up to three dots are valid: major.minor.patch.fix
    version_greater_or_equal_than('1.0', '1.0.1') => False
    version_greater_or_equal_than('1.0', '1.0') => True
    version_greater_or_equal_than('1.0.1', '1.0') => True
    version_greater_or_equal_than('10.0', '9.0') => True
    """
    a = a.split('.')
    while len(a) < 4:
        a.append('0')
    b = b.split('.')
    while len(b) < 4:
        b.append('0')
    for i in range(4):
        if int(a[i]) < int(b[i]):
            return False
    return True


"""
gather login info
"""
if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config.update(json.loads(f.read()))

if args.host:
    config['host'] = args.host

host = input(f"grafana host ({config['host']}): ")
if host.strip() == '':
    if config['host'].strip() == '':
        print("invalid input!")
        sys.exit(1)
    else:
        host = config['host']

port = input(f"grafana port ({config['port']}): ")
if port.strip() == '':
    port = config['port']

user = input(f"grafana user ({config['user']}): ")
if user.strip() == '':
    user = config['user']

password = input(f"grafana password ({config['password']}): ")
if password.strip() == '':
    password = config['password']

with open('config.json', 'w') as f:
    f.write(json.dumps({'host': host, 'port': port, 'user': user, 'password': password}, indent=2))


"""
connect
"""
server = f'http://{host}:{port}'

s = requests.Session()
s.headers = {'Content-Type': 'application/json'}

s.post(server + '/login', data=json.dumps({'User': user, 'Password': password}))


"""
check server version
"""
server_version = s.get(server + '/api/health').json()['version']
if not version_greater_or_equal_than(server_version, least_version):
    print(f"At least version {least_version} is required. Your server is on {server_version}")
    sys.exit(1)


"""
check datasource
"""
if not s.get(f'{server}/api/datasources/name/{ds_name}').status_code == 200:
    create_datasource()


"""
configure/load directory id
"""
for d in s.get(server + '/api/folders').json():
    if d['title'] == directory_title:
        directory = d['id']
        break
else:
    directory = s.post(server + '/api/folders', data=json.dumps({'title': 'NAHS-BrickWeb_builtin'})).json()['id']


"""
create/update dashboards
"""
create_dashboard('bwVhKMEMz', 'temp_sensor')
create_dashboard('5i1GBVNnz', 'humid_sensor')
create_dashboard('0qV6PIN7z', 'latch')
create_dashboard('2RQaypHnk', 'bat')
create_dashboard('FKBPR0bnk', 'signal')
create_dashboard('vSf8CudSz', 'heater')
