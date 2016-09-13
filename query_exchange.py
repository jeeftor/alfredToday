# encoding: utf-8


from workflow import Workflow3, ICON_INFO
from settings import get_login, get_password, get_regex, get_server, get_value_from_settings_with_default_boolean
import sys, os
from workflow.background import run_in_background, is_running
from sets import Set
import subprocess
from today import get_cache_key

def asrun(ascript):
    "Run the given AppleScript and return the standard output and error."
    osa = subprocess.Popen(['osascript', '-'],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    return osa.communicate(ascript)[0]

def asquote(astr):
    "Return the AppleScript equivalent of the given string."
    astr = astr.replace('"', '" & quote & "')
    return '"{}"'.format(astr)



def query_exchange_server(wf, start_search, end_search, date_offset):
    """Runs a query against an exchange server for either today or a date offset by `date_offset`"""
    from lib.pyexchange import Exchange2010Service, ExchangeBasicAuthConnection, ExchangeNTLMAuthConnection

    log = wf.logger
    log.info("BG: Querying Exchange Calendar")
    log.info("BG:     param: start_search = " + str(start_search))
    log.info("BG:     param:   end_search = " + str(end_search))
    log.info("BG:     param:   date_offset = " + str(date_offset))

    # Get data from disk
    exchange_url, using_default_server = get_server(wf)
    exchange_username = get_login(wf, False)
    exchange_password = get_password(wf, False)
    using_ntlm = get_value_from_settings_with_default_boolean(wf, 'use_ntlm', False)

    if not using_ntlm:
        log.info("BG: Outlook connection - External Server - Basic Auth")
        # Set up the connection to Exchange
        connection = ExchangeBasicAuthConnection(url=exchange_url,
                                                 username=exchange_username,
                                                 password=exchange_password)
    else:
        connection = ExchangeNTLMAuthConnection(url=exchange_url,
                                                username=exchange_username,
                                                password=exchange_password)
        log.info("BG: Outlook connection - Internal NTML")

    service = Exchange2010Service(connection)

    try:
        # You can set event properties when you instantiate the event...
        event_list = service.calendar().list_events(start=start_search, end=end_search, details=True)

        log.info("BG: Event count: " + str(event_list.count))
        return event_list.events
    except:
        return None

EVENT_FIELD_NAMES = ['_id', 'end', 'start', 'html_body', 'subject']

def serialize_event(event):
    """ returns a string that serializes selected fields from an event"""
    return ''.join(['%s' % getattr(event, ff) for ff in EVENT_FIELD_NAMES])


def build_event_set(events):
    """returns a set"""
    # this bad boy uses set comprehensions (note the parens)
    return (serialize_event(evt) for evt in events)

def main(wf):
    log.debug('BG EXCHANGE: STARTED')
    import pytz
    from pytz import timezone
    from datetime import timedelta, datetime
    from settings import get_value_from_settings_with_default_boolean, get_value_from_settings_with_default_int
    import time

    query = None
    if len(wf.args):
        query = wf.args[0]
    log.debug('BG: query : {!r}'.format(query))


    # Get args or jsut run "raw dog"
    if len(wf.args) > 1:
        # Get arguments to call
        args = wf.args
        wf.logger.debug(args)
        start_param = args[0]  # "2016-08-26-04:00:01"
        end_param = args[1]  # "2016-08-27-03:59:59"
        date_offset = args[2]
        format = "%Y-%m-%d-%H:%M:%S"
        start_outlook = datetime.strptime(start_param, format)  # .astimezone(pytz.utc)
        end_outlook = datetime.strptime(end_param, format)  # .astimezone(pytz.utc)
    else:
        date_offset = 0
        morning = timezone("US/Eastern").localize(
            datetime.today().replace(hour=0, minute=0, second=1) + timedelta(days=date_offset))
        night = timezone("US/Eastern").localize(
            datetime.today().replace(hour=23, minute=59, second=59) + timedelta(days=date_offset))

        # Outlook needs a different time format than google it would appear
        start_outlook = morning.astimezone(pytz.utc)
        end_outlook = night.astimezone(pytz.utc)



    def wrapper():
        """A wrapper around doing an exchange server query"""
        return query_exchange_server(wf, start_outlook, end_outlook, date_offset)



    cache_key = get_cache_key('exchange', date_offset)

    notify_key = cache_key.replace('exchange.','')

    log.debug("-- BG: CacheKey  (exchange)   " + cache_key)
    log.debug("-- BG: NotifyKey (exchange)   " + notify_key)

    # Compare old events to new events to see if somethign is changed
    old_events = wf.cached_data(cache_key, max_age=0)

    new_events = wrapper()
    # Force rewrite of cache data
    wf.cache_data(cache_key, new_events)

    if old_events is None:
        wf.logger.debug('**BG --- Exchange Old: None')

    if new_events is None:
        wf.logger.debug('**BG --- Exchange New: None')


    if new_events is not None:
        new_set = set(map(lambda event: serialize_event(event), new_events))
    else:
        new_set = set()

    if old_events is not None:
        old_set = set(map(lambda event: serialize_event(event), old_events))
    else:
        old_set = set()

    cmd = 'tell application "Alfred 3" to run trigger "NotifyOfUpdate" in workflow "org.jeef.today" with argument "' + notify_key + '"'

    number_of_changed_events = len(new_set.symmetric_difference(old_set))

    log.debug("-- BG: Changed Event Count: " + str(number_of_changed_events))

    if  number_of_changed_events  > 0:
        wf.logger.debug('BG -- Exchange: ** Refresh required ')
        wf.logger.debug('BG -- Exchange: ' + str(number_of_changed_events) + " events changed")

        asrun(cmd)


if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    sys.exit(wf.run(main))
