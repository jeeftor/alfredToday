from workflow import Workflow3
from GoogleInterface import GoogleInterface
from settings import get_value_from_settings_with_default_boolean


# def get_value_from_settings_with_default_boolean(wf, value, default_value):
#     """Returns either a value as set in the settings file or a default as specified by caller"""
#     try:
#         ret = wf.settings[value]['value']
#         if ret == u'0':
#             return False
#         return True
#     except KeyError:
#         return default_value

import sys

def main(wf):

    g = GoogleInterface(wf)

    calendars = g.get_calendars()



    for key in wf.settings:
        if 'calendar' in key and wf.settings.get(key):
            _, id = key.split(':')



    icon = 'img/no.png'
    for c in calendars:

        id = c.get('id')
        name = c.get('name','No Name Specified')
        settings_key = "calendar:" + id
        is_enabled = wf.settings.get(settings_key,False)

        if is_enabled:
            icon = 'img/ok.png'
        else:
            icon = 'img/no.png'

        item = wf.add_item(name, id, icon=icon, valid=True)
        item.setvar('settings_value', settings_key)
        item.setvar('value_to_store', not is_enabled)
        item.setvar('text_to_display', 'Google Calendar Settings')




    wf.send_feedback()




if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    sys.exit(wf.run(main))

