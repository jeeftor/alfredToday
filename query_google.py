# encoding: utf-8
import sys
from query_exchange import asrun, asquote
from workflow import Workflow3, ICON_INFO
import subprocess
from today import  get_cache_key
from settings import  get_http_kw_args
import GoogleInterface
from GoogleInterface import GoogleInterface
#
#
# def _get_credentials(wf):
#     """Gets valid user credentials from storage.
#
#     If nothing has been stored, or if the stored credentials are invalid,
#     the OAuth2 flow is completed to obtain the new credentials.
#
#     Returns:
#         Credentials, the obtained credential.
#     """
#     """Queries against the GoogleCalendar API and does magical things (hopefully)"""
#     log = wf.logger
#
#
#
#     # Load Imports
#     import os
#     import httplib2
#     import dateutil.parser
#     import oauth2client
#     from oauth2client import client
#     from oauth2client import tools
#
#
#     # If modifying these scopes, delete your previously saved credentials
#     # at ~/.credentials/calendar-python-quickstart.json
#     SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
#     CLIENT_SECRET_FILE = 'client_secret.json'
#     APPLICATION_NAME = 'Alfred Today'
#
#     # Removed line calling for - ca_certs="/usr/local/etc/openssl/cert.pem"
#     HTTP_INSTANCE = httplib2.Http(**get_http_kw_args(wf))
#
#     # Load OAuth2.0 credentials
#     home_dir = os.path.expanduser('~')
#     credential_dir = os.path.join(home_dir, '.credentials')
#     if not os.path.exists(credential_dir):
#         os.makedirs(credential_dir)
#     credential_path = os.path.join(credential_dir, 'calendar-alfred-today.json')
#
#     # Store fancy credential things
#     store = oauth2client.file.Storage(credential_path)
#     credentials = store.get()
#     # if not credentials:
#     #     return None
#     #
#     # if credentials.invalid:
#     #     return None
#
#     return credentials
#
# def get_calendars(wf):
#     log = wf.logger
#
#     import httplib2
#     from apiclient import discovery
#     # Removed line calling for - ca_certs="/usr/local/etc/openssl/cert.pem"
#     HTTP_INSTANCE = httplib2.Http(**get_http_kw_args(wf))
#
#     credentials = _get_credentials(wf)
#     http = credentials.authorize(HTTP_INSTANCE)


def query_google_calendar(wf, start_search, end_search, date_offset):
    """Queries against the GoogleCalendar API and does magical things (hopefully)"""
    log = wf.logger


    log.info("BG: Querying Google Calendar")
    log.info("BG:     param: start_google = " + str(start_search))
    log.info("BG:     param:   end_google = " + str(end_search))
    log.info("BG:     param:   date_offset = " + str(date_offset))

    g = GoogleInterface(wf)
    return g.get_events_for_default_calendar(start_search, end_search)
    #
    #
    #
    # try:
    #     eventsResult = service.events().list(calendarId='primary', timeMin=start_search, timeMax=end_search, singleEvents=True, orderBy='startTime').execute()
    #     event_list = eventsResult.get('items', [])
    #     log.info("* Google returned " + str(len(event_list)) + " events")
    #     return event_list
    # except IOError as ex:
    #     template = "An exception of type {0} occured. Arguments:\n{1!r}"
    #     message = template.format(type(ex).__name__, ex.args)
    #     log.info(message)
    #     log.info("Google -- Cache error")
    #     import traceback
    #     log.info(traceback.format_exc())
    #
    #     return None


def main(wf):
    log.debug('BG GOOGLE: STARTED')
    import pytz
    from pytz import timezone
    from datetime import timedelta, datetime

    from settings import get_value_from_settings_with_default_boolean, get_value_from_settings_with_default_int
    import time

    query = None
    if len(wf.args):
        query = wf.args[0]
    log.debug('BG: query : {!r}'.format(query))

    # Get arguments to call
    args = wf.args

    if len(wf.args) > 1:
        wf.logger.debug(args)
        start_google = args[0]  # "2016-08-26-04:00:01"
        stop_google = args[1]  # "2016-08-27-03:59:59"
        date_offset = args[2]
    else:
        date_offset = 0
        morning = timezone("US/Eastern").localize(datetime.today().replace(hour=0, minute=0, second=1) + timedelta(days=date_offset))
        night = timezone("US/Eastern").localize(datetime.today().replace(hour=23, minute=59, second=59) + timedelta(days=date_offset))
        # #Setup start time for query
        start_google  = morning.astimezone(pytz.utc).isoformat()
        stop_google   = night.astimezone(pytz.utc).isoformat()

    def wrapper():
        """A wrapper around doing a google query so this can be used with a cache function"""
        return query_google_calendar(wf, start_google, stop_google, date_offset)


    cache_key = get_cache_key('google', date_offset)

    notify_key = cache_key.replace('google.', '')

    log.debug("-- BG: CacheKey  (Google)   " + cache_key)
    log.debug("-- BG: NotifyKey (Google)   " + notify_key)

    # Compare old events to new events to see if somethign is changed
    old_events = wf.cached_data(cache_key, max_age=0)

    new_events = wrapper()
    # Force rewrite of cache data
    wf.cache_data(cache_key, new_events)

    if old_events is None:
        wf.logger.debug('**BG --- Google Old: None')
    else:
        for o in old_events:
            wf.logger.debug(' '.join(['**BG --- Google Old:', str(o['start']), o.get('summary', 'NoTitle')]))

    if new_events is None:
        wf.logger.debug('**BG --- Google New: None')
    else:
        for n in new_events:
            wf.logger.debug(' '.join(['**BG --- Google New:', str(n['start']), n.get('summary', 'NoTitle')]))

    def lambda_func(x):
        return ':'.join([x['id'], x['updated'], str(x.get(u'start').get(u'dateTime','All_Day'))])

    if new_events is not None:
        new_set = set(map(lambda x: lambda_func(x), new_events))
    else:
        new_set = set()

    if old_events is not None:
        old_set = set(map(lambda x: lambda_func(x), old_events))
    else:
        old_set = set()

    wf.logger.debug('Old Set: ' + str(old_set))
    wf.logger.debug('New Set: ' + str(new_set))

    cmd = 'tell application "Alfred 3" to run trigger "NotifyOfUpdate" in workflow "org.jeef.today" with argument "' + notify_key + '"'

    number_of_changed_events = len(new_set.symmetric_difference(old_set))

    log.debug("-- BG: Changed Event Count: " + str(number_of_changed_events))

    if  number_of_changed_events  > 0:


        wf.logger.debug('BG -- Google: ** Refresh required ')
        wf.logger.debug('BG -- Google: ' + str(number_of_changed_events ) + " events changed")

        evts = wf.cached_data(cache_key, max_age=0)
        for e in evts:
            wf.logger.debug(' '.join(['**BG --- Google:', str(e['start']), e.get('summary', 'NoTitle')]))
            wf.logger.debug('BG -- Google: ' + cmd)

        asrun(cmd)


    log.debug("--- TERMINATING --")

if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    sys.exit(wf.run(main))
