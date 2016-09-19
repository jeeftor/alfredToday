from workflow import Workflow3
from workflow.workflow3 import  Item3

#import calendar
#from datetime import datetime, timedelta
from settings import get_login, get_password, get_regex, get_server, get_timezone
import calendar
from datetime import datetime, timedelta
import logging
import logging.handlers

class EventProcessor(object):

    def __init__(self, wf):
        self.wf = wf

        self.PAST_ITEMS = []
        self.FUTURE_ITEMS = []


    def write_html_template(self, id, name, organizer, month_name, month_number, time, location, body):
        wf = self.wf

        with open('html/template.html', 'r') as template:
            html = template.read() \
                .replace('#FROM#', organizer) \
                .replace('#MONTH#', month_name)\
                .replace('#DAY#',month_number).replace('#TIME#',time)\
                .replace('#LOCATION#',location).replace('#TITLE#',name).replace('#TEXT#',body)

            filename = wf.cachedir + "/" + str(id) + ".html"
            out = open(filename, "w")
            out.write(html.encode('ascii', 'ignore'))
            out.close()

            filename = 'file://' + filename
            return  str(filename.replace(' ','%20'))

        return None

    def write_file(self, name, html):
        wf = self.wf
        filename = wf.cachedir + "/" + str(name) + ".html"
        out = open(filename, "w")
        out.write(html.encode('ascii','ignore'))
        out.close()
        return filename


    def process_google_event(self, event):
        wf = self.wf
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
        title = event.get('summary','No Title')
        url = event['htmlLink']

        try:
            loc = event['location']
            subtitle = subtitle + " [" + loc + "]"
        except:
            loc = ''
            pass

        body_html = event.get('description','No description given')

        creator = event.get('creator')
        org_name = creator.get('displayName','')
        org_email = creator.get('email','')
        organizer_html = org_name + " &lt;" + org_email + "&gt;"

        start_datetime = datetime.strptime(startdt.split('T')[0],'%Y-%m-%d')

        id =  str(event.get('etag').replace('"',''))


        description_url = self.write_html_template(id, title, organizer_html, start_datetime.strftime('%b'),
                                                   start_datetime.strftime('%d'), time_string, loc, body_html)

        # Pick icon color based on end time
        now = datetime.now(pytz.utc)
        if dateutil.parser.parse(enddt) < now:
            self.PAST_ITEMS.append(Item3(title, subtitle, arg=url, quicklookurl=description_url, type=u'file', valid=True, icon="img/eventGoogleGray.png"))
        else:
            iconfile = 'img/googleEvent_' + str(event.get('color',1)) +'.png'
            self.FUTURE_ITEMS.append(Item3(title, subtitle, arg=url, quicklookurl=description_url, icon=iconfile, valid=True))
            try:
                hangout_url = event['hangoutLink']
                hangout_title = u'\u21aa Join Hangout'
                hangout_subtitle = "        " + hangout_url
                self.FUTURE_ITEMS.append(Item3(hangout_title, hangout_subtitle, arg=hangout_url, valid=True, icon='img/hangout.png'))
            except:
                pass



    def process_events(self, exchange_events, google_events):
        """Processes both Google & Outlook events handling the interleving of data correctly (hopefully)"""
        wf = self.wf

        import dateutil.parser
        import pytz


        utc = pytz.UTC

        outlook_count = len(exchange_events)
        google_count  = len(google_events)

        o = 0
        g = 0


        while g < google_count and o < outlook_count:

            current_google_event = google_events[g]
            current_outlook_event = exchange_events[o]

            outlook_start = current_outlook_event.start #utc_to_local(current_outlook_event.start).replace(tzinfo=utc)

            google_date_time = current_google_event['start'].get('dateTime')
            if google_date_time is None:
                google_start = dateutil.parser.parse(current_google_event['start'].get('date') + "T00:00:00.000Z")
            else:
                google_start  = dateutil.parser.parse(google_date_time)


            outlook_start.replace(tzinfo=google_start.tzinfo)
            outlook_start.replace(tzinfo=google_start.tzinfo)


            if google_start < outlook_start:
                self.process_google_event(current_google_event)
                g +=1
            else:
                self.process_outlook_event(current_outlook_event)
                o += 1


        while g < google_count:
            self.process_google_event(google_events[g])
            g += 1

        while o < outlook_count:
            self.process_outlook_event(exchange_events[o])
            o += 1

        for item in self.FUTURE_ITEMS + self.PAST_ITEMS:
            for k in wf.variables:
                item.setvar(k, wf.variables[k])
            wf._items.append(item)



    def process_outlook_event(self, event):
        """Reads and processes an outlook event.  The UID field will be responsible for handling the sorting inside of Alfred"""
        import re
        REGEX = get_regex(self.wf)

        # extract fields
        id = str(event.id).replace("+", "").replace('/', '')
        location = event.location  # or "No Location Specified"
        subject = event.subject or "No Subject"
        start_datetime = self.utc_to_local(event.start)
        end_datetime = self.utc_to_local(event.end)
        body_html = event.html_body
        online_meeting = event.is_online_meeting

        # self.wf.logger.info('Searching regex')

        time_string = start_datetime.strftime("%I:%M %p") + " - " + end_datetime.strftime("%I:%M %p")

        org_name = event.organizer[0]
        org_email = event.organizer[1]

        organizer_html = org_name + " &lt;" + org_email + "&gt;"

        if body_html:
            description_url = self.write_html_template(id, subject, organizer_html, start_datetime.strftime('%b'), start_datetime.strftime('%d'), time_string, location, body_html)
                # write_file(id, body_html)
        else:
            description_url = ''

        lync_url = None

        self.wf.logger.info('Regex: ' + REGEX)
        self.wf.logger.info(body_html)

        if not REGEX is None:
            # Match pattern for LYNC
            p = re.compile(REGEX)
            if online_meeting == u'true' and body_html:
                match = re.search(p, body_html)
                if match:
                    lync_url = match.group(1)



        title = subject
        subtitle = time_string

        if location:
            subtitle += " [" + location + "]"

        subtitle += " hit shift for details"

        # Pick icon color based on end time
        now = datetime.now()
        if end_datetime < now:
            self.PAST_ITEMS.append(Item3(title, subtitle, type=u'file', arg=description_url, valid=False, icon="img/eventOutlookGray.png"))
            # wf.add_item(title, subtitle, type=u'file', arg=description_url, valid=False, icon="eventOutlookGray.png")

        else:

            if event.is_all_day:
                self.FUTURE_ITEMS.append(Item3(title, subtitle, type=u'file', arg=description_url, valid=False, icon="img/eventOutlook.png"))
            else:
                self.FUTURE_ITEMS.append(Item3(title, subtitle, type=u'file', arg=description_url, valid=False, icon="img/eventOutlook.png"))


            if lync_url != None:
                # subtitle += " [" + lync_url + "]"
                lync_title = u'\u21aa Join Meeting'
                lync_subtitle = "        " + lync_url
                self.FUTURE_ITEMS.append(Item3(lync_title, lync_subtitle, arg=lync_url, valid=True, icon='img/skype.png'))


    def utc_to_local(self, utc_dt):
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)


