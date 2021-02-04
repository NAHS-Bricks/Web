import cherrypy
import sys
import json
from mako.template import Template
from mako.lookup import TemplateLookup
from helpers.brickserver import brick_get, brick_exists, brick_delete, brick_set_desc, features_get_available, clear_request_cache


if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):  # pragma: no cover
    raise Exception('At least Python3.5 required')


mylookup = TemplateLookup(directories=['./templates'], module_directory='/tmp/brickweb_cache', collection_size=500, filesystem_checks=True)


def serve_template(templatename, **kwargs):
    mytemplate = mylookup.get_template(templatename)
    return mytemplate.render(**kwargs)


class BrickWeb(object):

    @cherrypy.expose()
    def index(self, brick_id=None):
        # get brick - if it exists
        if brick_id is None and 'brick_id' in cherrypy.session:
            brick_id = cherrypy.session['brick_id']
        brick = None
        if brick_exists(brick_id):
            brick = brick_get(brick_id)
            cherrypy.session['brick_id'] = brick['_id']

        # init session variables
        for val in ['bricks_filter_feature', 'bricks_filter_string']:
            if val not in cherrypy.session:
                cherrypy.session[val] = None

        if brick is None:
            return serve_template('/index-no-brick.html', session=cherrypy.session)
        else:
            return serve_template('/index.html', brick=brick, session=cherrypy.session)

    @cherrypy.expose()
    def set_desc(self, brick_id, desc):
        brick_set_desc(brick_id, desc)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def set_bricks_filter_feature(self, feature):
        if feature in features_get_available() or feature == 'all':
            cherrypy.session['bricks_filter_feature'] = feature
        return serve_template('/select-brick-changing-content.html', session=cherrypy.session)

    @cherrypy.expose()
    def set_bricks_filter_string(self, f_string):
        cherrypy.session['bricks_filter_string'] = f_string
        return serve_template('/select-brick-changing-content.html', session=cherrypy.session)

    @cherrypy.expose()
    def delete_brick(self, brick_id):
        brick_delete(brick_id)
        cherrypy.session.pop('brick_id')
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def clear_cache(self, partial=None):
        clear_request_cache(partial)
        if partial is None:
            raise cherrypy.HTTPRedirect('/')
        else:
            return ""

    @cherrypy.expose
    def get_brick_detail(self, brick_id):
        brick = None
        if brick_exists(brick_id):
            brick = brick_get(brick_id)
            cherrypy.session['brick_id'] = brick['_id']
        if brick is None:
            raise cherrypy.HTTPRedirect('/')
        return serve_template('/brick-detail.html', brick=brick, session=cherrypy.session)


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8000, 'tools.sessions.on': True})
    cherrypy.quickstart(BrickWeb())
