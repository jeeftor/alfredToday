from workflow import Workflow, web, Workflow3, ICON_INFO

__version__ = '0.5'


from workflow.background import run_in_background, is_running
from keychain import get_username_and_password, get_regex, get_server
import os, sys
from os.path import expanduser
home = expanduser("~")


def get_cache_directory():

    # Create cache directory for mii pictures - if it doesnt exist
    cache_dir = home + '/Library/Caches/com.runningwithcrayons.Alfred-3/Workflow Data/org.jeef.today'
    if not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(cache_dir):
                pass
            else:
                raise

    return cache_dir



def main(wf):
    from pytz import timezone

    URL, using_default_server = get_server(wf)
    USERNAME, PASSWORD = get_username_and_password()
    REGEX = get_regex(wf)

    import pytz, datetime
    utc = pytz.utc






    # Python exchange stuff
    from lib.pyexchange import Exchange2010Service, ExchangeBasicAuthConnection
    import re
    from datetime import datetime

    # Set up the connection to Exchange
    connection = ExchangeBasicAuthConnection(url=URL,
                                            username=USERNAME,
                                            password=PASSWORD)

    service = Exchange2010Service(connection)


    morning = timezone("US/Eastern").localize(datetime.today().replace(hour=0, minute=0, second=1))
    night = timezone("US/Eastern").localize(datetime.today().replace(hour=23, minute=59, second=59))
    start_search = morning.astimezone(pytz.utc)
    end_search = night.astimezone(pytz.utc)

    try:
        # You can set event properties when you instantiate the event...
        event_list = service.calendar().list_events(start= start_search, end=end_search,   details=True)
            #start=timezone("US/Eastern").localize(datetime.today().replace(hour=0, minute=0, second=1)),
            #end=timezone("US/Eastern").localize(datetime.today().replace(hour=23, minute=59, second=59)),
    except:
        wf.add_item('Unable to Connect to exchange server', icon='disclaimer.png')
        wf.send_feedback()

    # wf.add_item('Start', str(event_list.start))
    # wf.add_item('End', str(event_list.end))

    # Match pattern for LYNC
    p = re.compile(REGEX)

    if len(event_list.events) == 0:
        wf.add_item('Calendar is empty for today')
        wf.send_feedback()

    # Process Events
    for event in event_list.events:

        #extract fields
        id = str(event.id).replace("+", "").replace('/', '')
        location = event.location  # or "No Location Specified"
        subject = event.subject or "No Subject"
        start_datetime = utc_to_local(event.start)
        end_datetime = utc_to_local(event.end)
        body_html = event.html_body
        online_meeting = event.is_online_meeting
        if body_html:
            description_url = write_file(id, body_html)
        else:
            description_url = ""

        if online_meeting == u'true':
            match = re.search(p, body_html)
            if match:
                lync_url = match.group(1)
        else:
            lync_url = None

        time_string = start_datetime.strftime("%I:%M %p") + " - " + end_datetime.strftime("%I:%M %p")

        title = subject
        subtitle = time_string

        if location:
            subtitle += " [" + location + "]"

        subtitle += " hit shift for details"

        # Pick icon color based on end time
        now = datetime.now()
        if end_datetime < now:
            wf.add_item(title, subtitle, type=u'file', arg=description_url, valid=False, icon="icon_gray.png")
        else:

            if event.is_all_day:
                wf.add_item(title, subtitle, type=u'file', arg=description_url, valid=False, icon="age.png")
            else:
                wf.add_item(title, subtitle, type=u'file', arg=description_url, valid=False)



            if lync_url != None:
                #subtitle += " [" + lync_url + "]"
                lync_title = u'\u21aa Join Meeting'
                lync_subtitle = "        " + lync_url
                wf.add_item(lync_title, lync_subtitle, arg=lync_url, valid=True, icon='skype.png')


    wf.send_feedback()

def write_file(name, html):
    filename = get_cache_directory() + "/" + str(name) + ".html"
    out = open(filename, "w")
    out.write(html.encode('ascii','ignore'))
    out.close()
    return filename



import calendar
from datetime import datetime, timedelta

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)



if __name__ == u"__main__":
    wf = Workflow(libraries=['./lib'],update_settings={
        'github_slug': 'jeeftor/alfredToday',
        'version': __version__,
        'frequency': 7
    })

    if wf.update_available:
        # Add a notification to top of Script Filter results
        wf.add_item('New version available',
                    'Action this item to install the update',
                    autocomplete='workflow:update',
                    icon=ICON_INFO)

    sys.exit(wf.run(main))