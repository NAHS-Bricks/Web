import cherrypy
import os
import sys
import json
from helpers.brickserver import brick_get, brick_exists, brick_delete, brick_set_desc, brick_set_solar_charging, brick_set_sleep_disabled, brick_set_adc5V
from helpers.brickserver import features_get_available, clear_request_cache
from helpers.brickserver import temp_sensor_exists, temp_sensor_get, temp_sensor_set_desc, temp_sensor_disable
from helpers.brickserver import humid_sensor_exists, humid_sensor_get, humid_sensor_set_desc, humid_sensor_disable
from helpers.brickserver import latch_exists, latch_get, latch_set_desc, latch_set_states_desc, latch_add_trigger, latch_del_trigger, latch_disable
from helpers.brickserver import signal_exists, signal_get, signal_set_desc, signal_set_states_desc, signal_set_state, signal_disable
from helpers.brickserver import firmware_get, firmware_update, firmware_upload as firmware_upload_bk, firmware_delete, firmware_fetch
from helpers.firmware import firmware_is_used
from helpers.config import config
from helpers.shared import serve_template, possible_disables
from helpers.template import server_is
import tempfile


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

        if brick is not None and 'alert' in cherrypy.session:
            alert = cherrypy.session['alert']
            cherrypy.session.pop('alert', None)
            if 'alert-level' in cherrypy.session:
                alert_level = cherrypy.session['alert-level']
                cherrypy.session.pop('alert-level', None)
            else:
                alert_level = 'info'
            if alert_level not in ['info', 'success', 'warning', 'danger']:
                alert_level = 'info'
        else:
            alert = None
            alert_level = None

        if brick is None:
            return serve_template('/index-no-brick.html', session=cherrypy.session)
        else:
            return serve_template('/index.html', brick=brick, session=cherrypy.session, alert=alert, alert_level=alert_level)

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
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/temp-sensor-detail.html', sensor=sensor, brick=brick)

    @cherrypy.expose
    def get_humid_sensor_detail(self, sensor_id):
        sensor = None
        if humid_sensor_exists(sensor_id):
            sensor = humid_sensor_get(sensor_id)
        if sensor is None:
            raise cherrypy.HTTPRedirect('/')
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/humid-sensor-detail.html', sensor=sensor, brick=brick)

    @cherrypy.expose
    def get_latch_detail(self, latch_id):
        latch = None
        brick_id, lid = latch_id.split('_')
        if latch_exists(brick_id, lid):
            latch = latch_get(brick_id, lid)
        if latch is None:
            raise cherrypy.HTTPRedirect('/')
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/latch-detail.html', latch=latch, brick=brick)

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

    @cherrypy.expose()
    def firmware_compare(self, fw1, fw2):
        fw1m = firmware_get(name=fw1)
        fw2m = firmware_get(name=fw2)
        return serve_template('/firmware/compare.html', fw1=fw1m, fw2=fw2m)

    @cherrypy.expose()
    def firmware_update(self, request):
        firmware_update(brick_id=cherrypy.session['brick_id'], request=(request == 'true'))
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/brick-detail.html', brick=brick, session=cherrypy.session)

    @cherrypy.expose()
    def firmware_upload(self, firmware):
        if firmware is not None:
            size = 0
            with tempfile.SpooledTemporaryFile(max_size=2105345) as tmp_file:
                while True:
                    data = firmware.file.read(8192)
                    if not data:
                        break
                    tmp_file.write(data)
                    size += len(data)
                    if size > 2097152:
                        return {'s': 2, 'm': 'file size is to big'}
                tmp_file.seek(0)
                result = firmware_upload_bk(tmp_file)
        if not result['s'] == 0:
            cherrypy.session['alert'] = result['m']
            cherrypy.session['alert-level'] = 'danger'
        else:
            cherrypy.session['alert'] = 'New firmware package successfully uploaded'
            cherrypy.session['alert-level'] = 'success'
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def firmware_browser(self):
        if 'fw_browser_filter' not in cherrypy.session:
            cherrypy.session['fw_browser_filter'] = None
        if 'fw_browser_filter_bt' not in cherrypy.session:
            cherrypy.session['fw_browser_filter_bt'] = None
        if 'fw_browser_detail' not in cherrypy.session:
            cherrypy.session['fw_browser_detail'] = None
        return serve_template('/firmware/browser.html', session=cherrypy.session)

    @cherrypy.expose()
    def firmware_browser_browse(self, f=None, t=None):
        cherrypy.session['fw_browser_filter'] = None if str(f) == 'None' else f
        cherrypy.session['fw_browser_filter_bt'] = None if str(t) == 'None' else t
        return serve_template('/firmware/browser-browse-column.html', session=cherrypy.session)

    @cherrypy.expose()
    def firmware_browser_detail(self, d=None):
        cherrypy.session['fw_browser_detail'] = d
        return serve_template('/firmware/browser-detail-column.html', session=cherrypy.session)

    @cherrypy.expose()
    def firmware_delete(self, name, bin_only='false'):
        if not bin_only == 'true' and firmware_is_used(fw=firmware_get(name=name)):
            cherrypy.session['alert'] = "Firmware can't be deleted as it is used!"
            cherrypy.session['alert-level'] = 'warning'
        else:
            result = firmware_delete(name=name, bin_only=(bin_only == 'true'))
            cherrypy.session['fw_browser_detail'] = None
            if not result.get('s', 0) == 0:
                cherrypy.session['alert'] = result['m']
                cherrypy.session['alert-level'] = 'danger'
            else:
                result = result.get('deleted')
                cherrypy.session['alert'] = 'Deleted: ' + (f"FirmwareBin ({result['firmware']}) " if 'firmware' in result else '') + \
                    ('and ' if 'firmware' in result and 'metadata' in result else '') + \
                    (f"FirmwareMetadata ({result['metadata']})" if 'metadata' in result else '')
                cherrypy.session['alert-level'] = 'success'
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def firmware_fetch(self, what, brick_id=None, brick_type=None, version=None):
        result = firmware_fetch(what=what, brick_id=brick_id, brick_type=brick_type, version=version)
        if not result.get('s', 0) == 0:
            cherrypy.session['alert'] = result.get('m', '')
            cherrypy.session['alert-level'] = 'danger'
        else:
            result = result.get('fetched')
            cherrypy.session['alert'] = 'Fetched: ' + (f"FirmwareBin {result['firmware']} " if 'firmware' in result else '') + \
                ('and ' if 'firmware' in result and 'metadata' in result else '') + \
                (f"FirmwareMetadata {result['metadata']}" if 'metadata' in result else '')
            cherrypy.session['alert-level'] = 'success'
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def bat_align_adc5v_dialog(self):
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/bat-align-adc5v-dialog.html', brick=brick)

    @cherrypy.expose()
    def bat_align_adc5v_submit(self, adc5v):
        brick_set_adc5V(brick_id=cherrypy.session['brick_id'], adc5V=adc5v)
        brick = brick_get(cherrypy.session['brick_id'])
        return serve_template('/brick-detail.html', brick=brick, session=cherrypy.session)


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
