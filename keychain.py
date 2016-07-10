import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3

DEFAULT_SERVER = 'https://outlook.office365.com/EWS/Exchange.asmx'
CREDENTIAL_ENTRY = 'outlook.office365.com'


def get_server(wf):
    try:
        server = wf.settings['exchange_server']['exchange_server']
        return server, False
    except:
        return DEFAULT_SERVER, True


def get_regex(wf):
    try:
        regex = wf.settings['regex']['regex']
        return regex
    except:
        return None

def get_username_and_password():

    # Load Required LIbs
    from subprocess import Popen, PIPE
    import re

    # Fire off security to open up the site credentials
    p = Popen(['security', 'find-internet-password', '-w', '-g', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE,
              stderr=PIPE)
    raw_password, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    password = raw_password.strip('\n')

    p = Popen(['security', 'find-internet-password', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    keychain_result, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode

    # Run REGEX Match
    p = re.compile('acct\"<blob>="([^"]*)')
    m = re.search(p, keychain_result)

    if not m:
        return None, None
    else:
        return m.group(1), password


def main(wf):

    from workflow import Workflow3
    wf = Workflow3()

    #######################
    ## Load Credentials  ##
    #######################
    from subprocess import Popen, PIPE
    import re

    # Default items for workflow

    wf.add_item('Today workflow configuration Menu', icon='gear.png')
    #
    # p = Popen(['security', 'find-internet-password', '-w', '-g', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE,
    #           stderr=PIPE)
    # raw_password, err = p.communicate(b"input data that is passed to subprocess' stdin")
    # rc = p.returncode
    # password = raw_password.strip('\n')
    #
    # p = Popen(['security', 'find-internet-password', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    # keychain_result, err = p.communicate(b"input data that is passed to subprocess' stdin")
    # rc = p.returncode
    #
    # p = re.compile('acct\"<blob>="([^"]*)')
    # m = re.search(p, keychain_result)

    USERNAME,PASSWORD = get_username_and_password()


    if not USERNAME:
        wf.add_item('Unable to load credentials','Could not access keychain entry for ' + CREDENTIAL_ENTRY, valid=False, icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    wf.add_item('Login', USERNAME,
                valid=False, icon='ok.png')
    wf.add_item('Password', 'Successfully detected in keychain', valid=False, icon='ok.png')


    #################
    ## Load Server ##
    #################

    server, using_default = get_server(wf)
    if not using_default:
        server_item = wf.add_item('Exchange Server URL', server, arg=server, valid=True, icon='ok.png')
        server_item.setvar('text_to_display', 'Exchange Server:')
        server_item.setvar('settings_value', 'exchange_server')
    else:
        server_item = wf.add_item('Exchange Server URL (Using Default)', DEFAULT_SERVER, arg=DEFAULT_SERVER, valid=True, icon=ICON_NOTE)
        server_item.setvar('text_to_display', 'Exchange Server:')
        server_item.setvar('settings_value', 'exchange_server')

    ########################
    ## Load Regex Settings #
    ########################
    regex = get_regex(wf)

    if regex is not None:
        regex = wf.settings['regex']['regex']
        it = wf.add_item('Meeting Detection Regex', regex, arg=regex, valid=True, icon='ok.png')
        it.setvar('text_to_display', 'Regex:')
        it.setvar('settings_value', 'regex')
    else:
        it = wf.add_item('Meeting Detection Regex Not Set', 'Select this item to set', valid=True,
                    icon=ICON_WARNING)
        it.setvar('text_to_display','Regex:')
        it.setvar('settings_value', 'regex')

    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))
