import sys
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3, notify

def main(wf):
    from workflow.notify import notify

    should_reset = wf.args[0]

    if should_reset == 'True':
        # print "True = " + should_reset
        try:
            wf.delete_password('today.workflow.password')
        except PasswordNotFound:
            pass
        for value in ['exchange_login', 'regex', 'exchange_server', 'timezone']:
            try:
                del wf.settings[value]
            except AttributeError:
                pass
            except KeyError:
                pass
    else:
        pass
    notify('Today Menu', 'Reset to defaults')

if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))