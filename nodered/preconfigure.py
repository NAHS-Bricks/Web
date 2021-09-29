import requests
import json

config = {
    'host': '',
    'port': 3000,
    'mqtt_host': '',
    'mqtt_port': 1883,
    'brickserver_host': '',
    'brickserver_port': 8081
}

mqtt_node_id = '6c8bc1031ca33a4f'
brickserver_node_id = '80ae1dc59aca1268'

flows = json.loads(open('flows.json', 'r').read())

for node in flows:
    if node['id'] == brickserver_node_id:
        pass
    elif node['id'] == mqtt_node_id:
        pass

server = "http://192.168.1.232:1880"
s = requests.Session()
s.headers = {'Content-Type': 'application/json'}
s.post(server + '/flows', data=json.dumps(flows))
