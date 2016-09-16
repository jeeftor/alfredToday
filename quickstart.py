
from __future__ import print_function
import os

import sys
sys.path.insert(0, 'lib')
import httplib2


from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
    	'calendar-alfred-today.json')


    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=True))
    service = discovery.build('calendar', 'v3', http=http)


    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time



    page_token = None
    cals = service.calendarList().list(pageToken=page_token).execute()
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            print("\n********************************************")
            print("Name: " + calendar_list_entry['summary'] + " ACL: " + calendar_list_entry['accessRole'] + "   Calendar ID: " + calendar_list_entry['id'])
            cal_id = calendar_list_entry['id']
            eventsResult = service.events().list(
                calendarId=cal_id, timeMin=now, maxResults=10, singleEvents=True,
                orderBy='startTime').execute()

            events = eventsResult.get('items', [])

            if not events:
                print('No upcoming events found.')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event['summary'])

        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break


    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


if __name__ == '__main__':
    main()

# from __future__ import print_function
# import sys
# import os
# sys.path.insert(0, 'lib')

# import httplib2
# import os

# from apiclient import discovery
# import oauth2client
# from oauth2client import client
# from oauth2client import tools

# import datetime

# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
#     flags = None

# # If modifying these scopes, delete your previously saved credentials
# # at ~/.credentials/calendar-python-quickstart.json
# SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
# CLIENT_SECRET_FILE = 'client_secret.json'
# APPLICATION_NAME = 'Google Calendar API Python Quickstart'
# # Removed line calling for - ca_certs="/usr/local/etc/openssl/cert.pem"
# HTTP_INSTANCE = httplib2.Http()


# def get_credentials():
#     """Gets valid user credentials from storage.

#     If nothing has been stored, or if the stored credentials are invalid,
#     the OAuth2 flow is completed to obtain the new credentials.

#     Returns:
#         Credentials, the obtained credential.
#     """
#     home_dir = os.path.expanduser('~')
#     credential_dir = os.path.join(home_dir, '.credentials')
#     if not os.path.exists(credential_dir):
#         os.makedirs(credential_dir)
#     credential_path = os.path.join(credential_dir,
#                                    'calendar-alfred-today.json')

#     store = oauth2client.file.Storage(credential_path)
#     credentials = store.get()
#     if not credentials or credentials.invalid:
#         flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
#         flow.user_agent = APPLICATION_NAME
#         if flags:
#             credentials = tools.run_flow(flow, store, flags, http=HTTP_INSTANCE)
#         else: # Needed only for compatibility with Python 2.6
#             credentials = tools.run(flow, store)
#         print('Storing credentials to ' + credential_path, http=HTTP_INSTANCE)
#     return credentials

# def main():
#     """Shows basic usage of the Google Calendar API.

#     Creates a Google Calendar API service object and outputs a list of the next
#     10 events on the user's calendar.
#     """
#     credentials = get_credentials()
#     http = credentials.authorize(HTTP_INSTANCE)
#     service = discovery.build('calendar', 'v3', http=http)
#     import pytz
#     from pytz import timezone
#     from datetime import timedelta, datetime

#     date_offset = 0

#     morning = timezone("US/Eastern").localize(
#         datetime.today().replace(hour=0, minute=0, second=1) + timedelta(days=date_offset))
#     night = timezone("US/Eastern").localize(
#         datetime.today().replace(hour=23, minute=59, second=59) + timedelta(days=date_offset))

#      # start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=1).isoformat() + 'Z'  # 'Z' indicates UTC time
#     # stop = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59).isoformat() + 'Z'  # 'Z' indicates UTC time
#     start = morning.astimezone(pytz.utc).isoformat()
#     stop = night.astimezone(pytz.utc).isoformat()


#     print(start)
#     print(stop)
#     print('Getting the upcoming 10 events')

#     eventsResult = service.events().list(
#         calendarId='primary', timeMin=start, timeMax=stop, maxResults=10, singleEvents=True,
#         orderBy='startTime').execute()
#     events = eventsResult.get('items', [])

#     if not events:
#         print('No upcoming events found.')
#     for event in events:
#         start = event['start'].get('dateTime', event['start'].get('date'))
#         print(start)
#         print("\t" , event['summary'])
#         print("\t" , event['htmlLink'])
#         try:
#             print("\t" , event['description'])
#         except:
#             pass
#         try:
#             print("\t" , event['location'])
#         except:
#             pass

# if __name__ == '__main__':
#     main()