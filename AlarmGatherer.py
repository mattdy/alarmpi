import os
import datetime
import pytz
import dateutil.parser
import logging

from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import Settings
import CalendarCredentials # File with variables CLIENT_ID, CLIENT_SECRET, DEVELOPER_KEY and CALENDAR

log = logging.getLogger('root')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# If this key file exists we authenticate as a service account (the calendar must be shared with
#  the service account's email address). Otherwise we use the token saved by generateAuth()
SERVICE_ACCOUNT_FILE = 'service_account.json'
TOKEN_FILE = 'calendar_token.json'

# Port used for the one-off browser sign-in. If the Pi is headless, forward it over SSH first:
#  ssh -L 8080:localhost:8080 <pi>
AUTH_PORT = 8080

class AlarmGatherer:
   def __init__(self):
      self.settings = Settings.Settings()

      self.service = None
      self.credentials = self.loadCredentials()
      if not self.checkCredentials():
         log.error("GCal credentials missing or expired")
         log.warning("Run 'python3 AlarmGatherer.py' to fix")
         return

      self.service = build(
         serviceName='calendar',
         version='v3',
         credentials=self.credentials,
         cache_discovery=False
      )

   def loadCredentials(self):
      if os.path.exists(SERVICE_ACCOUNT_FILE):
         log.debug("Using service account credentials from %s", SERVICE_ACCOUNT_FILE)
         return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

      if os.path.exists(TOKEN_FILE):
         log.debug("Using saved user credentials from %s", TOKEN_FILE)
         return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

      return None

   def checkCredentials(self):
      if self.credentials is None:
         return False

      if isinstance(self.credentials, service_account.Credentials):
         return True # Service account tokens are fetched on demand

      # An expired access token is fine as long as we can refresh it
      return self.credentials.valid or bool(self.credentials.refresh_token)

   # One-off interactive sign-in, saves a token that we can keep refreshing
   def generateAuth(self):
      flow = InstalledAppFlow.from_client_config({
         'installed': {
            'client_id': CalendarCredentials.CLIENT_ID,
            'client_secret': CalendarCredentials.CLIENT_SECRET,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': ['http://localhost'],
         }
      }, SCOPES)

      self.credentials = flow.run_local_server(port=AUTH_PORT, open_browser=False)
      with open(TOKEN_FILE, 'w') as token:
         token.write(self.credentials.to_json())

   # Get the first event that isn't today
   def getNextEvent(self, today=False):
      log.debug("Fetching details of next event")
      if self.service is None or not self.checkCredentials():
         log.error("GCal credentials missing or expired")
         log.warning("Run 'python3 AlarmGatherer.py' to fix")
         raise Exception("GCal credentials not authorized")

      time = datetime.datetime.now(pytz.timezone('Europe/London'))
      if not today:
         # We want to find events tomorrow, rather than another one today
         log.debug("Skipping events from today")
         time += datetime.timedelta(days=1) # Move to tomorrow
         time = time.replace(hour=10,minute=0,second=0,microsecond=0) # Reset to 10am the next day
         # 10am is late enough that a night shift from today won't be caught, but a morning shift
         #  from tomorrow will be caught

      result = self.service.events().list(
         calendarId=self.settings.get('calendar'),
         maxResults='1',
         orderBy='startTime',
         singleEvents='true',
         timeMin=time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
      ).execute()

      events = result.get('items', [])
      return events[0]

   def getNextEventTime(self, includeToday=False):
      log.debug("Fetching next event time (including today=%s)" % (includeToday))
      nextEvent = self.getNextEvent(today=includeToday)
      start = dateutil.parser.parse(nextEvent['start']['dateTime'])
      #start = dateutil.parser.parse(nextEvent['start']['dateTime'],ignoretz=True)
      #start = start.replace(tzinfo=pytz.timezone('Europe/London'))

      return start

   def getNextEventLocation(self, includeToday=False):
      log.debug("Fetching next event location (including today=%s)" % (includeToday))
      nextEvent = self.getNextEvent(today=includeToday)
      return nextEvent.get('location') or None # Not all events have a location

   def getDefaultAlarmTime(self):
      defaultTime = self.settings.get('default_wake')
      defaultHour = int(defaultTime[:2])
      defaultMin = int(defaultTime[2:])
      
      alarm = datetime.datetime.now(pytz.timezone('Europe/London'))
      alarm += datetime.timedelta(days=1) # Move to tomorrow
      alarm = alarm.replace(hour=defaultHour,minute=defaultMin,second=0,microsecond=0)

      return alarm


if __name__ == '__main__':
   print("Running credential check")
   a = AlarmGatherer()
   try:
      if not a.checkCredentials():
         raise Exception("Credential check failed")
   except:
      print("Credentials not correct, please generate new code")
      a.generateAuth()
      a = AlarmGatherer()

   print(a.getNextEventTime())
   print(a.getNextEventLocation())
