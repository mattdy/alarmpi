import json
import datetime
import urllib2

# Fetches weather information
class WeatherFetcher:
   def __init__(self):
      self.cacheTimeout = None
      self.cache = None

   def getWeather(self):
      if(self.cache is None or self.cacheTimeout is None or self.cacheTimeout < datetime.datetime.now()):
         print "Weather cache expired or doesn't exist, re-fetching"
         # TODO: don't hardcode place
         # TODO: handle what happens if openweathermap is unavailable
         response = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=Gatwick')
         response = json.loads(response.read())

         weather = Weather()
         weather.setTempK(response['main']['temp'])
         weather.setCondition(response['weather'][0]['description'])
         weather.setWindSpeedMps(response['wind']['speed'])
         weather.setWindDirection(response['wind']['deg'])
         weather.setPressure(response['main']['pressure'])

         timeout = datetime.datetime.now()
         timeout += datetime.timedelta(minutes=30) # Cache for 30 minutes
         self.cacheTimeout = timeout

         self.cache = weather

      return self.cache

   def forceUpdate(self):
      self.cacheTimeout = None

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
      self.wdir = wdir

   def setPressure(self,pressure):
      self.pressure = int(pressure)

   def display(self):
      return "%sC, %s@%s, %shPa\n%s" % (self.temp,self.wdir,self.wspeed,self.pressure,self.condition)
