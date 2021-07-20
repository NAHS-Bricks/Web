import cherrypy
import os
import sys
import json
from helpers.brickserver import brick_get, brick_exists, brick_delete, brick_set_desc
from helpers.brickserver import features_get_available, clear_request_cache
from helpers.brickserver import temp_sensor_exists, temp_sensor_get, temp_sensor_set_desc, temp_sensor_disable
from helpers.brickserver import latch_exists, latch_get, latch_set_desc, latch_set_states_desc, latch_add_trigger, latch_del_trigger, latch_disable
from helpers.brickserver import signal_exists, signal_get, signal_set_desc, signal_set_states_desc, signal_set_state, signal_disable
from helpers.brickserver import event_get, event_add, event_delete, event_set_pos
from helpers.brickserver import event_command_set, event_reaction_add, event_reaction_delete, event_reaction_move
from helpers.brickserver import event_data_replace, event_data_get, event_data_get_names
from helpers.shared import config, serve_template, possible_disables
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
        if 'event_id' not in cherrypy.session:
            cherrypy.session['event_id'] = None

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
    def set_desc(self, desc, brick_id=None, sensor_id=None, latch_id=None, signal_id=None):
        if brick_id is not None:
            brick_set_desc(brick_id, desc)
        if sensor_id is not None:
            temp_sensor_set_desc(sensor_id, desc)
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
    def get_brick_detail(self, brick_id):
        brick = None
        if brick_exists(brick_id):
            brick = brick_get(brick_id)
            cherrypy.session['brick_id'] = brick['_id']
        if brick is None:
            raise cherrypy.HTTPRedirect('/')
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
    def set_disables(self, disables=list(), sensor_id=None, latch_id=None, signal_id=None):
        for d in possible_disables:
            if sensor_id is not None:
                temp_sensor_disable(sensor_id, d, d in disables)
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
    def event_editor(self, subpath=None, event_id=None, reaction_pos=None, reaction_name=None, command_name=None, ed_level=None, ed_name=None, ed_name_new=None, ed_data=None):
        if not server_is('0.6.0'):
            raise cherrypy.HTTPRedirect('/')
        brick = brick_get(cherrypy.session['brick_id'])
        if cherrypy.session['event_id'] is not None:
            event = event_get(cherrypy.session['event_id'])
        else:
            event = None
        if subpath is None:
            return serve_template('/events/editor.html', brick=brick, event=event)
        elif subpath == 'add_event':
            event_add(cherrypy.session['brick_id'])
            brick = brick_get(cherrypy.session['brick_id'])
            return serve_template('/events/column-events.html', brick=brick)
        elif subpath == 'delete_event' and event_id is not None:
            event_delete(cherrypy.session['brick_id'], event_id)
            if event_id == cherrypy.session['event_id']:
                cherrypy.session['event_id'] = None
                event = None
            brick = brick_get(cherrypy.session['brick_id'])
            return serve_template('/events/editor.html', brick=brick, event=event)
        elif subpath == 'move_up_event' and event_id is not None:
            event_set_pos(brick['_id'], event_id, brick['events'].index(event_id) - 1)
            brick = brick_get(cherrypy.session['brick_id'])
            return serve_template('/events/column-events.html', brick=brick)
        elif subpath == 'move_down_event' and event_id is not None:
            event_set_pos(brick['_id'], event_id, brick['events'].index(event_id) + 1)
            brick = brick_get(cherrypy.session['brick_id'])
            return serve_template('/events/column-events.html', brick=brick)
        elif subpath == 'select_event' and event_id is not None:
            cherrypy.session['event_id'] = event_id
            event = event_get(event_id)
            return serve_template('/events/editor.html', brick=brick, event=event)
        elif subpath == 'new_reaction':
            return serve_template('/events/reaction.html', event=event, reaction_pos=None, reaction=None, event_data=None)
        elif subpath == 'save_reaction' and reaction_pos is not None and reaction_name is not None and ed_level is not None and ed_name is not None and ed_name_new is not None and ed_data is not None:
            if ed_name == '_new_':
                ed_name = ed_name_new
            elif ed_name == '_auto_':
                auto_c = 0
                for name in event_data_get_names(event['_id'], ed_level):
                    if name.startswith('auto'):
                        auto_c += 1
                while 'auto_' + str(auto_c) in event_data_get_names(event['_id'], ed_level):
                    auto_c += 1
                ed_name = 'auto_' + str(auto_c)
            if ed_level == 'b':
                ed_name = '_' + ed_name
            elif ed_level == 'g':
                ed_name = '__' + ed_name
            ed_data = json.loads(ed_data)
            event_data_replace(event['_id'], ed_name, ed_data)
            event_reaction_add(event['_id'], reaction_name, ed_name)
            if not reaction_pos == 'None':
                reaction_pos = int(reaction_pos)
                event_reaction_delete(event['_id'], reaction_pos)
                event_reaction_move(event['_id'], len(event['reactions']) - 1, reaction_pos)
            event = event_get(event['_id'])
            return serve_template('/events/column-reactions.html', brick=brick, event=event)
        elif subpath == 'save_command' and command_name is not None and ed_level is not None and ed_name is not None and ed_name_new is not None and ed_data is not None:
            if ed_name == '_new_':
                ed_name = ed_name_new
            elif ed_name == '_auto_':
                auto_c = 0
                for name in event_data_get_names(event['_id'], ed_level):
                    if name.startswith('auto'):
                        auto_c += 1
                while 'auto_' + str(auto_c) in event_data_get_names(event['_id'], ed_level):
                    auto_c += 1
                ed_name = 'auto_' + str(auto_c)
            if ed_level == 'b':
                ed_name = '_' + ed_name
            elif ed_level == 'g':
                ed_name = '__' + ed_name
            ed_data = json.loads(ed_data)
            event_data_replace(event['_id'], ed_name, ed_data)
            event_command_set(event['_id'], command_name, ed_name)
            event = event_get(event['_id'])
            return serve_template('/events/column-command.html', brick=brick, event=event)
        elif subpath == 'delete_reaction' and reaction_pos is not None:
            if not reaction_pos == 'None':
                reaction_pos = int(reaction_pos)
                event_reaction_delete(event['_id'], reaction_pos)
            event = event_get(event['_id'])
            return serve_template('/events/column-reactions.html', brick=brick, event=event)
        elif subpath == 'move_up_reaction' and reaction_pos is not None:
            reaction_pos = int(reaction_pos)
            event_reaction_move(event['_id'], reaction_pos, reaction_pos - 1)
            event = event_get(event['_id'])
            return serve_template('/events/column-reactions.html', brick=brick, event=event)
        elif subpath == 'move_down_reaction' and reaction_pos is not None:
            reaction_pos = int(reaction_pos)
            event_reaction_move(event['_id'], reaction_pos, reaction_pos + 1)
            event = event_get(event['_id'])
            return serve_template('/events/column-reactions.html', brick=brick, event=event)
        elif subpath == 'event_data_data' and ed_level is not None and ed_name is not None:
            if ed_name in ['_new_', '_auto_']:
                return 'None'
            if ed_level == 'b':
                ed_name = '_' + ed_name
            elif ed_level == 'g':
                ed_name = '__' + ed_name
            return json.dumps({k: v for k, v in event_data_get(event['_id'], ed_name).items() if k != '_id'})
        else:
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
