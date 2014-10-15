import json
import datetime
import pytz
import urllib2
import Settings
import logging

log = logging.getLogger('root')

# Fetches weather information
class WeatherFetcher:
   def __init__(self):
      self.cacheTimeout = None
      self.cache = None
      self.settings = Settings.Settings()

   def getWeather(self):
      if(self.cache is None or self.cacheTimeout is None or self.cacheTimeout < datetime.datetime.now(pytz.timezone('Europe/London'))):
         log.info("Weather cache expired or doesn't exist, re-fetching")
         weather = Weather()

         place = self.settings.get('weather_location')
         if(place is None or place is ""):
            place = "Gatwick" # Default to Gatwick

         try:
            response = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=%s' % (place))
            response = json.loads(response.read())
         except:
            log.exception("Error fetching weather")
            if(self.cache is not None):
               return self.cache # we have a cache, so return that rather than an empty object
            else:
               return weather # return empty Weather object as we have nothing else
    
         weather.setTempK(response['main']['temp'])
         weather.setCondition(response['weather'][0]['description'])
         weather.setWindSpeedMps(response['wind']['speed'])
         weather.setWindDirection(response['wind']['deg'])
         weather.setPressure(response['main']['pressure'])

         timeout = datetime.datetime.now(pytz.timezone('Europe/London'))
         timeout += datetime.timedelta(minutes=30) # Cache for 30 minutes
         self.cacheTimeout = timeout

         self.cache = weather

      return self.cache

   def forceUpdate(self):
      self.cacheTimeout = None

# Take a number or string, and put spaces between each character, replacing 0 for the word zero
def splitNumber(num):
   split = ' '.join("%s" % num)
   return split.replace("0","zero")

# Holds our weather information
class Weather:
   def __init__(self):
      self.temp = 0
      self.condition = ""
      self.wspeed = 0
      self.wdir = 0
      self.pressure = 0

   def setTempK(self,temperature):
      self.temp = int(int(temperature) - 273.15)

   def setTempC(self,temperature):
      self.temp = int(temperature)

   def setCondition(self,condition):
      self.condition = condition

   def setWindSpeedMps(self,wspeed):
      self.wspeed = int(int(wspeed) * 1.9438444924406)

   def setWindSpeedKts(self,wspeed):
      self.wspeed = wspeed

   def setWindDirection(self,wdir):
      if wdir==0:
         wdir = 360
      self.wdir = wdir

   def setPressure(self,pressure):
      self.pressure = int(pressure)

   def display(self):
      return "%sC, %03d@%s, %shPa\n%s" % (self.temp,self.wdir,self.wspeed,self.pressure,self.condition)

   def speech(self):
      speech = ""
      speech += "The weather is currently %s. " % (self.condition)
      speech += "Temperature %s degrees, " % (self.temp)
      speech += "wind %s degrees at %s knots, " % (splitNumber(self.wdir), self.wspeed)
      speech += "Q N H %s hectopascals" % (splitNumber(self.pressure))

      return speech
