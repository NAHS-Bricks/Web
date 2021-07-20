import os
import json
from mako.lookup import TemplateLookup


config = {
    'server_port': 8000,
    'brickserver': {
        'host': 'localhost',
        'port': 8081
    },
    'grafana': {
        'enabled': False,
        'host': '',
        'port': 3000,
        'datasource': 'InfluxDB'
    }
}
if os.path.isfile('config.json'):
    config.update(json.loads(open('config.json', 'r').read().strip()))
else:
    open('config.json', 'w').write(json.dumps(config, indent=2, sort_keys=True))

possible_disables = {'ui', 'metric'}

mylookup = TemplateLookup(directories=['./templates'], module_directory='/tmp/brickweb_cache', collection_size=500, filesystem_checks=True)


def serve_template(templatename, **kwargs):
    mytemplate = mylookup.get_template(templatename)
    return mytemplate.render(**kwargs)
