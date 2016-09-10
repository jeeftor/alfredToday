import os, sys
from workflow import Workflow3, PasswordNotFound, Workflow3, notify
from workflow.notify import notify



def remove_google_credentials():
    """This function will delete the credentials from the calendar causing you to have to re-authroize later"""
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-alfred-today.json')
    os.remove(credential_path)
    wf.logger.info("Deleting credentials at: " + credential_path)


def main(wf):

    should_reset = wf.args[0]

    if should_reset == 'True':

        # Remove stored google credentials
        remove_google_credentials()

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