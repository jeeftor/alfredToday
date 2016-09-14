# encoding: utf-8

from workflow import Workflow3, ICON_INFO
from workflow.background import run_in_background, is_running

UPDATE_SETTINGS = {'github_slug': 'jeeftor/alfredToday'}
HELP_URL = 'https://github.com/jeeftor/AlfredToday'

def get_cache_key(prefix, date_offset):
    """Gets the cache key to be used"""
    if date_offset in ['1',1]:
        return prefix + ".Tomorrow"
    return prefix + ".Today"


def main(wf):

    from event_processor import process_events
    from query_exchange   import query_exchange_server
    from query_google    import query_google_calendar

    import pytz
    from pytz import timezone
    from datetime import timedelta, datetime
    from settings import get_value_from_settings_with_default_boolean, get_value_from_settings_with_default_int
    import time

    # Check to see if updates are available
    if wf.update_available:

        wf.add_item('A newer version is available',
                    '↩ to install update',
                    autocomplete='workflow:update',
                    icon='update-available.png')


    # Parse and log the query variable
    query = None
    if len(wf.args):
        query = wf.args[0]
    log.debug('query : {!r}'.format(query))

    # Get date offset
    args = wf.args
    date_offset = 0
    if len(args) > 0:
        date_offset = int(args[0])


    #Start calculating elapsed time - displayed in results page at end
    action_start_time = time.time()

    # Find out cache time
    cache_time = get_value_from_settings_with_default_int(wf, 'cache_time', 9000)

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

    def exchange_wrapper():
        """Wrapper around outlook query so can be used with caching"""
        return query_exchange_server(wf,start_outlook, end_outlook, date_offset)



    # Format date text for displays
    date_text = night.strftime("%A %B %d, %Y")
    date_text_numeric = night.strftime("%m/%d/%y")

    # Build Cache Keys
    exchange_cache_key = get_cache_key('exchange', date_offset)
    google_cache_key  = get_cache_key('google', date_offset)
    log.debug("-- FG: CacheKey (Google)   " + google_cache_key)
    log.debug("-- FG: CacheKey (Exchange) " + exchange_cache_key)


    # Check which calendars to use from settings
    use_exchange = get_value_from_settings_with_default_boolean(wf, 'use_exchange', False)
    use_google   = get_value_from_settings_with_default_boolean(wf, 'use_google', False)

    if not use_google and not use_exchange:
        wf.add_item('Calendars are disabled','use the tc command to setup a calendar', icon=ICON_INFO, arg="tc")
        wf.send_feedback()
        return

    log.debug("Max Age: %i  Cache Age Google:  %i   Exchange: %i",
              cache_time,
              wf.cached_data_age(google_cache_key),
              wf.cached_data_age(exchange_cache_key)
              )
    # Check cache status
    google_fresh   = wf.cached_data_fresh(google_cache_key, max_age=cache_time)
    exchange_fresh = wf.cached_data_fresh(exchange_cache_key, max_age=cache_time)



    # Determine whether cache data is being shown or "live" data
    showing_cached_data = True

    if use_google:
        showing_cached_data &= google_fresh

    if use_exchange:
        showing_cached_data &= exchange_fresh


    event_count = 0
    error_state = False


    log.debug('--FG:   Use Exchange:' + str(use_exchange))
    log.debug('--FG: Exchange Fresh:' + str(exchange_fresh))
    if use_exchange:

        # If the cache is fresh we need to do a bg refresh - because who knows what has happened
        # If the cache is stale then directly query the exchange server

        if exchange_fresh:
            log.debug('--FG: Loading Exchange events from Cache')

            #Extract the cached events
            exchange_events = wf.cached_data(exchange_cache_key, max_age=0)

            log.debug(str(exchange_events))

            # Run update in the background
            if not is_running('update_exchange'):
                cmd = ['/usr/bin/python',
                       wf.workflowfile('query_exchange.py'),
                       start_outlook.strftime("%Y-%m-%d-%H:%M:%S"),
                       end_outlook.strftime("%Y-%m-%d-%H:%M:%S"),
                       str(date_offset)]

                log.debug('--FG: Launching background exchange update')
                # Fire off in the background the script to update things! :)
                run_in_background('update_exchange', cmd)
            else:
                log.debug('--FG: Background exchange update already running')

        else:
            log.debug('--FG: Directly querying Exchange')

            # Directly query the exchange server
            exchange_events = wf.cached_data(exchange_cache_key, exchange_wrapper, max_age=cache_time)

        if exchange_events is None:
            log.debug('--FG: Exchange Events returned NONE!!!')
            error_state = True

            wf.add_item('Unable to connect to exchange server', 'Check your connectivity or NTLM auth settings', icon='img/disclaimer.png')
            exchange_events = []
        else:
            event_count += len(exchange_events)

    else:
        exchange_events = []

    if use_google:
        # If the cache is "fresh" we need to do a bg refresh - because we are loading from the cache
        # If the cache isnt fresh - the server will be queried directly anyways

        if google_fresh:

            # Extract cached events
            google_events = wf.cached_data(google_cache_key, max_age=0)

            # Run update in background
            if not is_running('update_google'):
                cmd = ['/usr/bin/python',
                       wf.workflowfile('query_google.py'),
                       start_google,
                       stop_google,
                       str(date_offset)]

                # Fire off in the background the script to update things! :)
                run_in_background('update_google', cmd)
        else:

            # Directly run event update - ignore background stuff
            google_events = wf.cached_data(google_cache_key, google_wrapper, max_age=cache_time)

        if google_events is None:

            error_state = True

            import httplib
            conn = httplib.HTTPConnection("www.google.com")
            try:
                conn.request("HEAD", "/")
                wf.add_item('Unable to connect to Google', 'Authorization or Connection error - use tc to reauthorize',
                            icon='img/disclaimer.png')
            except Exception as ex:
                wf.logger.info("Unable to connect to google")
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                wf.logger.info(message)
                import traceback
                wf.logger.info(traceback.format_exc())
                wf.add_item('Unable to connect to Google', 'Check your internet connection or proxy settings',
                            icon='img/disclaimer.png')

            google_events = []
        else:

            for e in google_events:
                wf.logger.debug(' '.join(['**FG --- Google:', str(e.get(u'start').get(u'dateTime', 'All Day')),
                                          e.get('summary', 'NoTitle')]))

            event_count += len(google_events)
    else:
        google_events = []









    # Build Header
    icon_file = 'img/date_span.png'

    if use_exchange and use_google:
        icon_file = 'img/iconBoth.png'
    elif use_exchange:
        icon_file = 'img/iconOutlook.png'
    elif use_google:
        icon_file = 'img/iconGoogle.png'

    # Fire off some log data
    log.info("Event Count   Google: " + str(len(google_events)))
    log.info("Event Count Exchange: " + str(len(exchange_events)))
    log.info("Event Count    Total: " + str(event_count))

    if event_count == 0:
        if error_state is False:
            wf.add_item('Calendar is empty', date_text, icon=icon_file)
        wf.send_feedback()
        return

    first_menu_entry = wf.add_item(date_text, date_text_numeric, icon=icon_file)

    # Process events
    process_events(wf, exchange_events, google_events)

    # Update elapsed time counter
    action_elapsed_time = time.time() - action_start_time


    if showing_cached_data:
        first_menu_entry.subtitle += " - Cached Data"
    else:
        first_menu_entry.subtitle += " query time: " + "{:.1f}".format(
            action_elapsed_time) + " seconds"

    wf.send_feedback()



if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'],
                   help_url=HELP_URL,
                   update_settings={
                       'github_slug': 'jeeftor/alfredToday',
                       'frequency': 7}
                   )
    log = wf.logger

    log.info('        ______          __')
    log.info('       /_  __/___  ____/ /___ ___  __')
    log.info('        / / / __ \/ __  / __ `/ / / /')
    log.info('       / / / /_/ / /_/ / /_/ / /_/ /')
    log.info('      /_/  \____/\__,_/\__,_/\__, /')
    log.info('                            /____/')

    wf.run(main)
