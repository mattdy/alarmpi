import gflags
import httplib2
import datetime
import dateutil.parser

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

import Settings
import CalendarCredentials # File with variables CLIENT_ID, CLIENT_SECRET, DEVELOPER_KEY and CALENDAR

FLAGS = gflags.FLAGS

class AlarmGatherer:
   def __init__(self):
      self.FLOW = OAuth2WebServerFlow(
         client_id=CalendarCredentials.CLIENT_ID,
         client_secret=CalendarCredentials.CLIENT_SECRET,
         scope='https://www.googleapis.com/auth/calendar',
         user_agent='AlarmPi/1.0'
      )

      self.settings = Settings.Settings()

      FLAGS.auth_local_webserver = False

      self.storage = Storage('calendar.dat')
      self.credentials = self.storage.get()
      if not self.checkCredentials():
         print "Error: GCal credentials have expired."
         print "Remove calendar.dat and run 'python AlarmGatherer.py' to fix"
         return

      http = httplib2.Http()
      http = self.credentials.authorize(http)

      self.service = build(
         serviceName='calendar',
         version='v3',
         http=http,
         developerKey=CalendarCredentials.DEVELOPER_KEY
      )

   def checkCredentials(self):
      return not (self.credentials is None or self.credentials.invalid == True)

   def generateAuth(self):
      self.credentials = run(self.FLOW, self.storage)

   # Get the first event that isn't today
   def getNextEvent(self):
      if not self.checkCredentials():
         print "Error: GCal credentials have expired"
         print "Remove calendar.dat and run 'python AlarmGatherer.py' to fix"
         raise Exception("GCal credentials not authorized")

      # We want to find events tomorrow, rather than another one today
      time = datetime.datetime.now()
      time += datetime.timedelta(days=1) # Move to tomorrow
      time = time.replace(hour=10,minute=0,second=0,microsecond=0) # Reset to 10am the next day
      # 10am is late enough that a night shift from today won't be caught, but a morning shift
      #  from tomorrow will be caught

      result = self.service.events().list(
         calendarId=self.settings.get('calendar'),
         maxResults='1',
         orderBy='startTime',
         singleEvents='true',
         timeMin="%sZ" % (time.isoformat())
      ).execute()

      events = result.get('items', [])
      return events[0]

   def getNextEventTime(self):
      nextEvent = self.getNextEvent()
      start = dateutil.parser.parse(nextEvent['start']['dateTime'],ignoretz=True)

      return start


   def getDefaultAlarmTime(self):
      defaultTime = self.settings.get('default_wake')
      defaultHour = int(defaultTime[:2])
      defaultMin = int(defaultTime[2:])
      
      alarm = datetime.datetime.now()

      if alarm.hour > defaultHour:
         alarm += datetime.timedelta(days=1) # Move to tomorrow

      alarm = alarm.replace(hour=defaultHour,minute=defaultMin,second=0,microsecond=0)

      return alarm


if __name__ == '__main__':
   print "Running credential check"
   a = AlarmGatherer()
   try:
      if not a.checkCredentials():
         raise Exception("Credential check failed")
   except:
      print "Credentials not correct, please generate new code"
      a.generateAuth()
      a = AlarmGatherer()

   print a.getNextEventTime()
