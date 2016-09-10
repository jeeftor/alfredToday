from workflow import Workflow3
from workflow.workflow3 import  Item3

#import calendar
#from datetime import datetime, timedelta
from settings import get_login, get_password, get_regex, get_server, get_timezone
import calendar
from datetime import datetime, timedelta
import logging
import logging.handlers

PAST_ITEMS =  []
FUTURE_ITEMS = []

def write_file(wf, name, html):
    filename = wf.cachedir + "/" + str(name) + ".html"
    out = open(filename, "w")
    out.write(html.encode('ascii','ignore'))
    out.close()
    return filename


def process_google_event(wf, event):
    """Process google calendar events - sorting should be done by UID"""
    import dateutil.parser
    import pytz

    try:
        startdt = event['start'].get('dateTime')
        enddt = event['end']['dateTime']
    except KeyError:
        startdt = event['start'].get('date') + "T00:00:00.000Z"
        enddt = event['end']['date'] + "T23:59:59.000Z"

    start = dateutil.parser.parse(startdt).strftime('%I:%M %p')
    end = dateutil.parser.parse(enddt).strftime('%I:%M %p')

    time_string = start + " - " + end

    subtitle = time_string
    title = event['summary']
    url = event['htmlLink']

    try:
        loc = event['location']
        subtitle = subtitle + " [" + loc + "]"
    except:
        pass

    # Pick icon color based on end time
    now = datetime.now(pytz.utc)
    if dateutil.parser.parse(enddt) < now:
        PAST_ITEMS.append(Item3(title, subtitle, arg=url, valid=False, icon="img/eventGoogleGray.png"))
    else:
        FUTURE_ITEMS.append(Item3(title, subtitle, arg=url, icon='eventGoogle.png', valid=True))
        try:
            hangout_url = event['hangoutLink']
            hangout_title = u'\u21aa Join Hangout'
            hangout_subtitle = "        " + hangout_url
            FUTURE_ITEMS.append(Item3(hangout_title, hangout_subtitle, arg=hangout_url, valid=True, icon='img/hangout.png'))
        except:
            pass



def process_events(wf, outlook_events, google_events):
    """Processes both Google & Outlook events handling the interleving of data correctly (hopefully)"""
    import dateutil.parser
    import pytz


    utc = pytz.UTC

    outlook_count = len(outlook_events)
    google_count  = len(google_events)

    o = 0
    g = 0


    while g < google_count and o < outlook_count:

        current_google_event = google_events[g]
        current_outlook_event = outlook_events[o]

        outlook_start = current_outlook_event.start #utc_to_local(current_outlook_event.start).replace(tzinfo=utc)

        google_date_time = current_google_event['start'].get('dateTime')
        if google_date_time is None:
            google_start = dateutil.parser.parse(current_google_event['start'].get('date') + "T00:00:00.000Z")
        else:
            google_start  = dateutil.parser.parse(google_date_time)


        outlook_start.replace(tzinfo=google_start.tzinfo)
        outlook_start.replace(tzinfo=google_start.tzinfo)


        if google_start < outlook_start:
            process_google_event(wf, current_google_event)
            g +=1
        else:
            process_outlook_event(wf, current_outlook_event)
            o += 1


    while g < google_count:
        process_google_event(wf, google_events[g])
        g += 1

    while o < outlook_count:
        process_outlook_event(wf, outlook_events[o])
        o += 1

    for item in FUTURE_ITEMS + PAST_ITEMS:
        for k in wf.variables:
            item.setvar(k, wf.variables[k])
        wf._items.append(item)



def process_outlook_event(wf, event):
    """Reads and processes an outlook event.  The UID field will be responsible for handling the sorting inside of Alfred"""
    import re
    REGEX = get_regex(wf)

    # extract fields
    id = str(event.id).replace("+", "").replace('/', '')
    location = event.location  # or "No Location Specified"
    subject = event.subject or "No Subject"
    start_datetime = utc_to_local(event.start)
    end_datetime = utc_to_local(event.end)
    body_html = event.html_body
    online_meeting = event.is_online_meeting
    if body_html:
        description_url = write_file(wf, id, body_html)
    else:
        description_url = ""

    lync_url = None
    if not REGEX is None:
        # Match pattern for LYNC
        p = re.compile(REGEX)
        if online_meeting == u'true' and body_html:
            match = re.search(p, body_html)
            if match:
                lync_url = match.group(1)


    time_string = start_datetime.strftime("%I:%M %p") + " - " + end_datetime.strftime("%I:%M %p")

    title = subject
    subtitle = time_string

    if location:
        subtitle += " [" + location + "]"

    subtitle += " hit shift for details"

    # Pick icon color based on end time
    now = datetime.now()
    if end_datetime < now:
        PAST_ITEMS.append(Item3(title, subtitle, type=u'file', arg=description_url, valid=False, icon="img/eventOutlookGray.png"))
        # wf.add_item(title, subtitle, type=u'file', arg=description_url, valid=False, icon="eventOutlookGray.png")

    else:

        if event.is_all_day:
            FUTURE_ITEMS.append(Item3(title, subtitle, type=u'file', arg=description_url, valid=False, icon="img/eventOutlook.png"))
        else:
            FUTURE_ITEMS.append(Item3(title, subtitle, type=u'file', arg=description_url, valid=False, icon="img/eventOutlook.png"))


        if lync_url != None:
            # subtitle += " [" + lync_url + "]"
            lync_title = u'\u21aa Join Meeting'
            lync_subtitle = "        " + lync_url
            FUTURE_ITEMS.append(Item3(lync_title, lync_subtitle, arg=lync_url, valid=True, icon='img/skype.png'))


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)



if __name__ == "__main__":
    wf = Workflow3(libraries=['./lib'])