import cherrypy
import os
import sys
import json
from helpers.brickserver import brick_get, brick_exists, brick_delete, brick_set_desc, brick_set_solar_charging, brick_set_sleep_disabled
from helpers.brickserver import features_get_available, clear_request_cache
from helpers.brickserver import temp_sensor_exists, temp_sensor_get, temp_sensor_set_desc, temp_sensor_disable
from helpers.brickserver import humid_sensor_exists, humid_sensor_get, humid_sensor_set_desc, humid_sensor_disable
from helpers.brickserver import latch_exists, latch_get, latch_set_desc, latch_set_states_desc, latch_add_trigger, latch_del_trigger, latch_disable
from helpers.brickserver import signal_exists, signal_get, signal_set_desc, signal_set_states_desc, signal_set_state, signal_disable
from helpers.config import config
from helpers.shared import serve_template, possible_disables
from helpers.template import server_is


if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):  # pragma: no cover
    raise Exception('At least Python3.5 required')


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

        if 'show_disabled' not in cherrypy.session:
            cherrypy.session['show_disabled'] = False

        if brick is None:
            return serve_template('/index-no-brick.html', session=cherrypy.session)
        else:
            return serve_template('/index.html', brick=brick, session=cherrypy.session)

    @cherrypy.expose()
    def runtime_overview(self):
        return serve_template('/runtime-overview.html', session=cherrypy.session)

    @cherrypy.expose()
    def set_desc(self, desc, brick_id=None, sensor_id=None, humid_id=None, latch_id=None, signal_id=None):
        if brick_id is not None:
            brick_set_desc(brick_id, desc)
        if sensor_id is not None:
            temp_sensor_set_desc(sensor_id, desc)
        if humid_id is not None:
            humid_sensor_set_desc(humid_id, desc)
        if latch_id is not None:
            latch_set_desc(latch_id, desc)
        if signal_id is not None:
            signal_set_desc(signal_id, desc)
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
    def reload_brick_detail(self, brick_id):
        brick = None
        if brick_exists(brick_id):
            brick = brick_get(brick_id)
            cherrypy.session['brick_id'] = brick['_id']
        if brick is None:
            return
        clear_request_cache(brick_id)
        if 'temp' in brick['features']:
            for sensor in brick['temp_sensors']:
                clear_request_cache(sensor)
        if 'humid' in brick['features']:
            for sensor in brick['humid_sensors']:
                clear_request_cache(sensor)
        return serve_template('/brick-detail.html', brick=brick, session=cherrypy.session)

    @cherrypy.expose
    def set_solar_charging(self, enable):
        brick_set_solar_charging(cherrypy.session['brick_id'], (enable == 'true'))
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/brick-detail.html', brick=brick, session=cherrypy.session)

    @cherrypy.expose
    def set_sleep_disabled(self, disabled):
        brick_set_sleep_disabled(cherrypy.session['brick_id'], (disabled == 'true'))
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/brick-detail.html', brick=brick, session=cherrypy.session)

    @cherrypy.expose
    def get_server_info(self):
        return serve_template('/server-info.html')

    @cherrypy.expose
    def get_temp_sensor_detail(self, sensor_id):
        sensor = None
        if temp_sensor_exists(sensor_id):
            sensor = temp_sensor_get(sensor_id)
        if sensor is None:
            raise cherrypy.HTTPRedirect('/')
        return serve_template('/temp-sensor-detail.html', sensor=sensor)

    @cherrypy.expose
    def get_humid_sensor_detail(self, sensor_id):
        sensor = None
        if humid_sensor_exists(sensor_id):
            sensor = humid_sensor_get(sensor_id)
        if sensor is None:
            raise cherrypy.HTTPRedirect('/')
        return serve_template('/humid-sensor-detail.html', sensor=sensor)

    @cherrypy.expose
    def get_latch_detail(self, latch_id):
        latch = None
        brick_id, lid = latch_id.split('_')
        if latch_exists(brick_id, lid):
            latch = latch_get(brick_id, lid)
        if latch is None:
            raise cherrypy.HTTPRedirect('/')
        return serve_template('/latch-detail.html', latch=latch)

    @cherrypy.expose
    def get_signal_detail(self, signal_id):
        signal = None
        brick_id, sid = signal_id.split('_')
        if signal_exists(brick_id, sid):
            signal = signal_get(brick_id, sid)
        if signal is None:
            raise cherrypy.HTTPRedirect('/')
        return serve_template('/signal-detail.html', signal=signal)

    @cherrypy.expose()
    def set_states_desc(self, desc, state, latch_id=None, signal_id=None):
        if latch_id is not None:
            latch_set_states_desc(latch_id, state, desc)
        if signal_id is not None:
            signal_set_states_desc(signal_id, state, desc)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def set_state(self, state, signal_id):
        signal_set_state(signal_id, state)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def set_latch_triggers(self, latch_id, triggers=list()):
        for t in range(0, 4):
            if str(t) in triggers:
                latch_add_trigger(latch_id, t)
            else:
                latch_del_trigger(latch_id, t)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def set_disables(self, disables=list(), sensor_id=None, humid_id=None, latch_id=None, signal_id=None):
        for d in possible_disables:
            if sensor_id is not None:
                temp_sensor_disable(sensor_id, d, d in disables)
            if humid_id is not None:
                humid_sensor_disable(humid_id, d, d in disables)
            if latch_id is not None:
                latch_disable(latch_id, d, d in disables)
            if signal_id is not None:
                signal_disable(signal_id, d, d in disables)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def toggle_show_disabled(self):
        cherrypy.session['show_disabled'] = not cherrypy.session['show_disabled']
        raise cherrypy.HTTPRedirect('/')


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['server_port']})
    cherrypy.quickstart(BrickWeb(), '/', conf)
