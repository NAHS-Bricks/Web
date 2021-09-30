import requests
import json
import os

config = {
    'host': '',
    'port': 1880,
    'mqtt_host': '',
    'mqtt_port': 1883,
    'brickserver_host': '',
    'brickserver_port': 8081
}

mqtt_node_id = '6c8bc1031ca33a4f'
brickserver_node_id = '80ae1dc59aca1268'


"""
gather NodeRed server connection information
"""
if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config.update(json.loads(f.read()))

host = input(f"NodeRed Host ({config['host']}): ")
if host.strip() == '':
    if config['host'].strip() == '':
        print("invalid input!")
        sys.exit(1)
    else:
        host = config['host']
config['host'] = host

port = input(f"NodeRed Port ({config['port']}): ")
if port.strip() == '':
    port = config['port']
config['port'] = port

with open('config.json', 'w') as f:
    f.write(json.dumps(config, indent=2))


"""
connect to NodeRed and load present flows
"""
server = f"http://{config['host']}:{config['port']}"

s = requests.Session()
s.headers = {'Content-Type': 'application/json', 'Node-RED-API-Version': 'v1'}

flows_server = s.get(server + '/flows').json()


"""
try to gather BrickServer and MQTT information from present flows
"""
for node in flows_server:
    if node['id'] == brickserver_node_id:
        host, port = node['url'].split('//', 1)[1].split('/', 1)[0].split(':')
        config['brickserver_host'] = host
        config['brickserver_port'] = port
        pass
    elif node['id'] == mqtt_node_id:
        config['mqtt_host'] = node['broker']
        config['mqtt_port'] = node['port']


"""
gather BrickServer and MQTT information from user
"""
host = input(f"BrickServer Host ({config['brickserver_host']}): ")
if host.strip() == '':
    if config['brickserver_host'].strip() == '':
        print("invalid input!")
        sys.exit(1)
    else:
        host = config['brickserver_host']
config['brickserver_host'] = host
if config['mqtt_host'] == '':
    config['mqtt_host'] = host

port = input(f"BrickServer Port ({config['brickserver_port']}): ")
if port.strip() == '':
    port = config['brickserver_port']
config['brickserver_port'] = port

host = input(f"MQTT Host ({config['mqtt_host']}): ")
if host.strip() == '':
    if config['mqtt_host'].strip() == '':
        print("invalid input!")
        sys.exit(1)
    else:
        host = config['mqtt_host']
config['mqtt_host'] = host

port = input(f"MQTT Port ({config['mqtt_port']}): ")
if port.strip() == '':
    port = config['mqtt_port']
config['mqtt_port'] = port

with open('config.json', 'w') as f:
    f.write(json.dumps(config, indent=2))


"""
load new preconfigured flow and enrich them with gathered connection data
"""
flows = json.loads(open('flows.json', 'r').read())
flows_ids = list()
for node in flows:
    if 'id' in node:
        flows_ids.append(node['id'])
    if node['id'] == brickserver_node_id:
        node['url'] = f"http://{config['brickserver_host']}:{config['brickserver_port']}/admin"
        pass
    elif node['id'] == mqtt_node_id:
        node['broker'] = config['mqtt_host']
        node['port'] = str(config['mqtt_port'])


"""
copy over user custom flows to new flow set
"""
for node in flows_server:
    if 'id' in node:
        if node['id'] not in flows_ids:
            flows.append(node)


"""
commit new flow set to server
"""
s.post(server + '/flows', data=json.dumps(flows))
