import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3

DEFAULT_SERVER = 'https://outlook.office365.com/EWS/Exchange.asmx'
CREDENTIAL_ENTRY = 'outlook.office365.com'


def guess_domain():

    from subprocess import Popen, PIPE
    p = Popen(['grep', '^search', '/private/etc/resolv.conf'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    raw_result, err = p.communicate(b"input data that is passed to subprocess' stdin")
    domain = raw_result.strip('\n').split(' ')[1]
    return domain

def guess_username():
    import os
    import pwd
    return pwd.getpwuid(os.getuid()).pw_name

def get_server(wf):
    server = get_value_from_settings(wf, 'exchange_server')
    if server is None:
        return DEFAULT_SERVER, True
    else:
        return server, False

def get_regex(wf):
    return get_value_from_settings(wf, 'exchange_regex')

def get_stored_login(wf):
    return get_value_from_settings(wf, 'exchange_login')

def get_stored_password(wf):
    try:
        password = wf.get_password('today.workflow.password')
        return password
    except:
        return None


def get_value_from_settings(wf, value):
    try:
        ret = wf.settings[value]['value']
        return ret
    except KeyError:
       return None


def autodetect_password(wf):
    from subprocess import Popen, PIPE
    import re
    # Fire off security to open up the site credentials

    p = Popen(['security', 'find-internet-password', '-w', '-g', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE,stderr=PIPE)
    raw_password, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    password = raw_password.strip('\n')
    if password == "":
        return None
    return password


def autodetect_login(wf):
    from subprocess import Popen, PIPE
    import re

    p = Popen(['security', 'find-internet-password', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    keychain_result, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode

    # Run REGEX Match
    p = re.compile('acct\"<blob>="([^"]*)')
    m = re.search(p, keychain_result)
    if m:
        return m.group(1)
    return None



def get_login(wf, show_alfred_items=True):
    stored_login = get_stored_login(wf)
    auto_login= autodetect_login(wf)
    if stored_login is None:

        if auto_login is None:
            if show_alfred_items:
                login_item = wf.add_item('Please set Login', 'Could not auto detect a login from keychain for ' + CREDENTIAL_ENTRY,
                        valid=True, icon=ICON_WARNING)
            ret = None
        else:
            if show_alfred_items:
                login_item = wf.add_item('Login', "(autodetcted) " + auto_login, arg=auto_login, valid=True, icon='ok.png')
            ret = auto_login

    else:
        if show_alfred_items:
            login_item = wf.add_item('Login', stored_login, arg=stored_login, valid=True, icon='ok.png')
        ret = stored_login

    if show_alfred_items:
        login_item.setvar('text_to_display', 'Login:')
        login_item.setvar('settings_value' , 'exchange_login')
    return ret


def get_password(wf, show_alfred_items=True):
    stored_password = get_stored_password(wf)
    auto_password   = autodetect_password(wf)

    if stored_password is None:

        if auto_password is None:
            if show_alfred_items:
                password_item = wf.add_item('Please set Password', 'Could not auto detect password from keychain for ' + CREDENTIAL_ENTRY, valid=True, icon=ICON_WARNING)
            ret = None
        else:
            if show_alfred_items:
                password_item = wf.add_item('Password stored in keychain', '(auto detected from keychain)', valid=True, icon='ok.png')
            ret = auto_password

    else:
        if show_alfred_items:
            password_item = wf.add_item('Password stored in keychain', 'xxxxxxxxxx', valid=True, icon='ok.png')
        ret = stored_password

    if show_alfred_items:
        password_item.setvar('text_to_display','Password')
        password_item.setvar('settings_value' ,'password')
    return ret



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

    get_login(wf)
    get_password(wf)

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
        regex = get_regex(wf)
        it = wf.add_item('Meeting Detection Regex', regex, arg=regex, valid=True, icon='ok.png')
        it.setvar('text_to_display', 'Regex:')
    else:
        it = wf.add_item('Meeting Detection Regex Not Set', 'Select this item to set', valid=True,
                    icon=ICON_WARNING)
        it.setvar('text_to_display','Regex:')
        it.setvar('settings_value', 'regex')

    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))
