import sys
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3, notify

def main(wf):
    should_reset = wf.args[0]

    if should_reset == 'True':
        # print "True = " + should_reset

        wf.delete_password('today.workflow.password')
        for value in ['exchange_login', 'regex', 'exchange_server']:
            try:
                del wf.settings[value]
            except AttributeError:
                pass
            except KeyError:
                pass
    else:
        pass

if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))