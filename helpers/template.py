import json


def convert_html(json_obj):
    return json.dumps(json_obj, indent=4).replace(' ', '&nbsp;').replace('\n', '<br />\n')
