from workflow import Workflow3, ICON_INFO
from settings import get_login, get_password, get_regex, get_server
import sys, os




def query_google_calendar(wf, start_search, end_search, date_offset):
    """Queries against the GoogleCalendar API and does magical things (hopefully)"""

    Workflow3().logger.info("Refreshing Data Cache [Google]")

    # Load Imports
    import os
    import httplib2
    import dateutil.parser
    from apiclient import discovery
    import oauth2client
    from oauth2client import client
    from oauth2client import tools


    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/calendar-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Alfred Today'
    HTTP_INSTANCE = httplib2.Http( disable_ssl_certificate_validation=True)

    # Load OAuth2.0 credentials
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'calendar-alfred-today.json')

    flags = None

    # Store fancy credential things
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags, http=HTTP_INSTANCE)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)

    http = credentials.authorize(HTTP_INSTANCE)
    service = discovery.build('calendar', 'v3', http=http)

    try:
        eventsResult = service.events().list(calendarId='primary', timeMin=start_search, timeMax=end_search, singleEvents=True, orderBy='startTime').execute()
        event_list = eventsResult.get('items', [])
        return event_list
    except IOError:
        return []


def query_exchange_server(wf, start_search, end_search, date_offset):
    """Runs a query against an exchange server for either today or a date offset by `date_offset`"""
    from lib.pyexchange import Exchange2010Service, ExchangeBasicAuthConnection

    wf.logger.info("Refreshing Data Cache [Outlook]")
    wf.logger.info(wf.cachedir)

    # Get data from disk
    exchange_url, using_default_server = get_server(wf)
    exchange_username = get_login(wf, False)
    exchange_password = get_password(wf, False)

    # Set up the connection to Exchange
    connection = ExchangeBasicAuthConnection(url=exchange_url,
                                             username=exchange_username,
                                             password=exchange_password)

    service = Exchange2010Service(connection)

    try:
        # You can set event properties when you instantiate the event...
        event_list = service.calendar().list_events(start=start_search, end=end_search, details=True)
        return event_list.events

    except:
        return None





def main(wf):
    from EventProcessing import process_outlook_event, process_google_event, process_events
    import pytz
    from pytz import timezone
    from datetime import timedelta, datetime
    from settings import get_value_from_settings_with_default_boolean, get_value_from_settings_with_default_int
    import time

    #Start timer
    action_start_time = time.time()

    # Get date offset
    args = wf.args
    date_offset = 0
    if len(args) > 0:
        date_offset = int(args[0])

    cache_time = get_value_from_settings_with_default_int(wf, 'cache_time', 30)

    date_offset = 0

    morning = timezone("US/Eastern").localize(datetime.today().replace(hour=0, minute=0, second=1) + timedelta(days=date_offset))
    night = timezone("US/Eastern").localize(datetime.today().replace(hour=23, minute=59, second=59) + timedelta(days=date_offset))

    # Outlook needs a different time format than google it would appear
    start_outlook = morning.astimezone(pytz.utc)
    end_outlook   = night.astimezone(pytz.utc)
    start_google  = morning.astimezone(pytz.utc).isoformat()
    stop_google   = night.astimezone(pytz.utc).isoformat()


    def google_wrapper():
        """A wrapper around doing a google query so this can be used with a cache function"""

        return query_google_calendar(wf, start_google, stop_google, date_offset)

    def outlook_wrapper():
        """Wrapper around outlook query so can be used with caching"""
        return query_exchange_server(wf,start_outlook, end_outlook, date_offset)

    # Format date text for displays
    date_text = night.strftime("%A %B %d %Y")
    date_text_numeric = night.strftime("%m/%d/%y")

    outlook_cache_key = 'event_list.outlook.' + str(date_offset)
    google_cache_key =  'event_list.google.' + str(date_offset)

    using_cached_data = wf.cached_data_fresh('use_exchange', cache_time) and wf.cached_data_fresh('use_google', cache_time)

    use_exchange = get_value_from_settings_with_default_boolean(wf, 'use_exchange', True)
    use_google   = get_value_from_settings_with_default_boolean(wf, 'use_google', True)

    if not use_google and not use_exchange:
        wf.add_item('Calendars are disabled','use the tc command to setup a calendar', icon=ICON_INFO, arg="tc")
        wf.send_feedback()
        return

    event_count = 0

    if use_exchange:
        outlook_events = wf.cached_data(outlook_cache_key, outlook_wrapper, max_age=cache_time)

        if outlook_events is None:
            wf.add_item('Unable to Connect to exchange server', '', icon='disclaimer.png')
            outlook_events = []
        else:
            event_count += len(outlook_events)
    else:
        outlook_events = []

    if use_google:
        google_events  = wf.cached_data(google_cache_key, google_wrapper, max_age=cache_time)
        event_count += len(google_events)
    else:
        google_events = []

    if event_count == 0:
        wf.add_item('Calendar is empty for today', date_text, icon='date_span.png')
        wf.send_feedback()
        return

    # Build Header
    first_menu_entry = wf.add_item(date_text, date_text_numeric, icon='date_span.png')

    # Process events
    process_events(wf, outlook_events, google_events)

    action_elapsed_time = time.time() - action_start_time

    if using_cached_data:
        first_menu_entry.subtitle = first_menu_entry.subtitle + " using cached data"

    else:
        first_menu_entry.subtitle = first_menu_entry.subtitle + " query time: " + "{:.1f}".format(
            action_elapsed_time) + " seconds"

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    wf.run(main)