import requests
import json

flows = json.loads(open('flows.json', 'r').read())

server = "http://192.168.1.232:1880"
s = requests.Session()
s.headers = {'Content-Type': 'application/json'}
s.post(server + '/flows', data=json.dumps(flows))
