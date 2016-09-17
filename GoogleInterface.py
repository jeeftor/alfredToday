# encoding: utf-8

import sys, os
# Add local lib path to path
sys.path = [os.path.join(os.path.dirname(__file__), 'lib')] + sys.path

from workflow import Workflow3


import oauth2client
import googleapiclient
from apiclient import discovery

from oauth2client import client
from oauth2client import tools

from lib.apiclient import  discovery
from lib.oauth2client import  client, tools


import httplib2
from settings import get_http_kw_args


class AuthorizationNeededException(Exception):
    """Authorization Required"""
    pass

class NoCalendarException(Exception):
    pass

class GoogleInterface(object):

    def __init__(self, wf):
        """Construct a new GoogleInterface.  Checks Auth status and if unauthorized will prompt for authorization"""
        self.HTTP_INSTANCE = httplib2.Http(**get_http_kw_args(wf))

        self.log = wf.logger
        self.wf = wf

        self.CLIENT_SECRET_FILE = 'client_secret.json'
        self.APPLICATION_NAME = 'Alfred Today'
        self.SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

        credentials = self._get_credentials()


        if not credentials or credentials.invalid:
            self._authorize_google()

        http = credentials.authorize(self.HTTP_INSTANCE)
        self.service = discovery.build('calendar', 'v3', http=http)


    def __check_auth_status(self):
        """Checks authorization status and throws an error if not found"""
        if not self.credentials or self.credentials.invalid:
            raise AuthorizationNeededException()


    def _authorize_google(self):
        """Wrapper around the OAuth2 auth code"""

        try:
            self.__check_auth_status()
        except AuthorizationNeededException:

            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME

            # if flags:
            flags = None
            self.credentials = tools.run_flow_wf(self.wf, flow, self.store, flags, http=self.HTTP_INSTANCE)
            # print('Storing credentials to ' + self.credential_path)
            self.wf.logger.info("Storing credentials to [%s]", self.credential_path)


    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """

        # Load OAuth2.0 credentials
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        self.credential_path = os.path.join(credential_dir, 'calendar-alfred-today.json')

        # Store fancy credential things
        self.store = oauth2client.file.Storage(self.credential_path)
        self.credentials = self.store.get()

        return self.credentials


    def get_calendars(self):
        """Returns a dictionary of name and id for all calendars"""

        self.__check_auth_status()

        page_token = None
        cals = self.service.calendarList().list(pageToken=page_token).execute()

        calendar_ids = []

        while True:
            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                self.log.info("\n********************************************")
                self.log.info("Calendar Name: " + calendar_list_entry['summary'] + " ACL: " + calendar_list_entry[
                    'accessRole'] + "   Calendar ID: " + calendar_list_entry['id'])

                bg_color = calendar_list_entry['backgroundColor']
                fg_color = calendar_list_entry['foregroundColor']
                color_Id = calendar_list_entry['colorId']
                cal_id = calendar_list_entry['id']
                calendar_ids.append({'id':cal_id,'name':calendar_list_entry['summary'], 'color_id':color_Id})

            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        return calendar_ids


    def get_events_for_enabled_calendars(self,start,stop):
        events = []
        enabled_cal_count = 0

        for key in self.wf.settings:
            if 'calendar' in key:
                enabled_cal_count += 1

                enabled,color = self.wf.settings.get(key).get('value').split('\t')
                # enabled, color = self.wf.settings.get(key).get('value')

                id = key.split(':')[1]

                if enabled:

                    calendar_events = self.get_events_for_calendar_id(id,start,stop)
                    for event in calendar_events:
                        event['color'] = color
                        # events += event


                    events += calendar_events
        return events


    def get_events_for_default_calendar(self, start, stop):
        """REturns events from the 'primary' calendar"""

        self.__check_auth_status()

        return self.get_events_for_calendar_id('primary',start,stop)

    def get_events_for_calendar_id(self, calendar_id, start, end):
        """Queries the event set for a specific calendar in a specific time-range and date offset"""
        self.__check_auth_status()
        self.wf.logger.info("Querying calender [%s]", calendar_id)

        try:
            eventsResult = self.service.events().list(calendarId=str(calendar_id), timeMin=start, timeMax=end,
                                                 singleEvents=True, orderBy='startTime').execute()
            event_list = eventsResult.get('items', [])
            self.log.info("* Google returned " + str(len(event_list)) + " events")
            return event_list
        except IOError as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            log.info(message)
            log.info("Google -- Cache error")
            import traceback
            log.info(traceback.format_exc())
            return None
        except Exception as ex:
            log.info('HTTP ERROR [%s]', calendar_id)




def main(wf):
    g = GoogleInterface(wf)

    # print(g.get_calendars())
    g.print_colors()
    # print(g.get_events_for_enabled_calendars("2012-08-08","2012-0808"))




if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    sys.exit(wf.run(main))



