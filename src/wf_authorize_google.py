
from __future__ import print_function
from workflow import Workflow3
from workflow.notify import notify
from settings import get_http_kw_args
import sys

from settings import get_value_from_settings_with_default_boolean


#
# def get_credentials(wf):
#     """Gets valid user credentials from storage.
#
#     If nothing has been stored, or if the stofrom workflow.notify import notify
#
#     import sys
#     import os
#     sys.path.insert(0, 'lib') red credentials are invalid,
#     the OAuth2 flow is completed to obtain the new credentials.
#
#     Returns:
#         Credentials, the obtained credential.
#     """
#
#     import httplib2
#     from apiclient import discovery
#     import oauth2client
#     from oauth2client import client
#     from oauth2client import tools
#     import os
#
#     # If modifying these scopes, delete your previously saved credentials
#     # at ~/.credentials/calendar-python-quickstart.json
#     SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
#     CLIENT_SECRET_FILE = 'client_secret.json'
#     APPLICATION_NAME = 'Google Calendar API Python Quickstart'
#
#     HTTP_INSTANCE = httplib2.Http(**get_http_kw_args(wf))
#
#
#     home_dir = os.path.expanduser('~')
#     credential_dir = os.path.join(home_dir, '.credentials')
#     if not os.path.exists(credential_dir):
#         os.makedirs(credential_dir)
#     credential_path = os.path.join(credential_dir,
#                                    'calendar-alfred-today.json')
#
#     store = oauth2client.file.Storage(credential_path)
#     credentials = store.get()
#     if not credentials or credentials.invalid:
#         flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
#         flow.user_agent = APPLICATION_NAME
#
#         # if flags:
#         flags = None
#         credentials = tools.run_flow_wf(wf, flow, store, flags, http=HTTP_INSTANCE)
#         print('Storing credentials to ' + credential_path)
#         wf.logger.info("Storing credentials to [%s]", credential_path)
#
#
#     return credentials

from GoogleInterface import GoogleInterface
def authorize(wf):


    wf.logger.info('Running Authorization')
    g = GoogleInterface(wf)

    # credentials = g.get_credentials()

    import httplib2

    if g.credentials:
        use_ssl = get_value_from_settings_with_default_boolean(wf, 'use_ssl', True)

        http = g.HTTP_INSTANCE

        #, ca_certs="/usr/local/etc/openssl/cert.pem"))
        notify(u'Google Authorization', 'Success!!')



def main(wf):
    authorize(wf)

if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))
