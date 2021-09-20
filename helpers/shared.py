from mako.lookup import TemplateLookup
from helpers.template import server_is


possible_disables = {'ui', 'metric'}
if server_is('0.7.0'):
    possible_disables.add('mqtt')

mylookup = TemplateLookup(directories=['./templates'], module_directory='/tmp/brickweb_cache', collection_size=500, filesystem_checks=True)


def serve_template(templatename, **kwargs):
    mytemplate = mylookup.get_template(templatename)
    return mytemplate.render(**kwargs)
