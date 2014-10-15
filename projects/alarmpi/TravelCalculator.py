import urllib
import json
import logging
import CalendarCredentials

log = logging.getLogger('root')

class TravelCalculator:
   def __init__(self,origin,default=20):
      self.origin = origin
      self.default = default

   def setOrigin(self, origin):
      self.origin = origin

   def getTravelTime(self,destination):
      params = {
         "origins": self.origin,
         "destinations": destination,
         "key": CalendarCredentials.DEVELOPER_KEY,
      }

      try:
         url = "https://maps.googleapis.com/maps/api/distancematrix/json?%s" % (urllib.urlencode(params))
         log.debug("Requesting travel time info from %s" % (url))
         response = json.loads(urllib.urlopen(url).read())

         if(response['status']!="OK"):
            if(response['error_message']):
               log.error("Error message from Distance Matrix API: %s" % (response['error_message']))
            raise Exception("Travel time request failed, status returned was %s" % (response['status']))

         seconds = response['rows'][0]['elements'][0]['duration']['value']
         minutes = int(seconds)/60 # Rough division to get number of minutes rather than seconds

         log.debug("Got travel time of %s seconds, converted to %s minutes" % (seconds,minutes))

         return minutes
      except:
         log.exception("Error fetching travel time. Returning default of %s" % (self.default))
         return self.default
