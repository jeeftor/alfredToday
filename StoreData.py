import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3

def main(wf):

    import os
    from workflow.notify import notify

    key =  os.environ['settings_value']
    value =  os.environ['value_to_store']

    if key == 'password':
        wf.save_password('today.workflow.password',value)
        notify('Password updated')
    else:
        wf.settings[key] = {'value':value}

        # wf.store_data(key, value)
        text = os.environ['text_to_display']
        notify('Updated ' + text, "To: " + value)

if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))