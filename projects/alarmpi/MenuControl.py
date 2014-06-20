# Code from http://www.dronkert.net/rpi/vol.html for volume adjustment

import time
import datetime
import threading
import sys
import subprocess
import Settings

LOOP_TIME=0.1

menuItems = [ "Volume", "Station", "Auto-set Alarm", "Manual Alarm", "Restart" ]

class MenuControl(threading.Thread):
   def __init__(self,alarmThread,shutdownCallback):
      threading.Thread.__init__(self)
      
      self.shutdownCallback = shutdownCallback
      self.alarmThread = alarmThread
      self.settings = Settings.Settings()

      self.menuPointer = None
      self.menuTimeout = 0
      self.menuActive = False
      self.tmp = 0
      self.active = False
      self.stopping = False

   def isActive(self):
      return self.active

   def select(self):
      if self.menuPointer is None:
         return # We can ignore this button if we're not in a menu

      if self.menuActive:
         # We're in an active menu item and have just hit select, so we should save the setting here
         if(menuItems[self.menuPointer]=="Volume"):
            self.settings.set('volume',self.tmp)
         elif(menuItems[self.menuPointer]=="Manual Alarm"):
            self.alarmThread.manualSetAlarm(self.__alarmTimeFromInput())
         elif(menuItems[self.menuPointer]=="Station"):
            self.settings.set('station',self.tmp)

         self.exitMenu()
      else:
         # We're not in an active menu item, so we must have just selected one

         if(menuItems[self.menuPointer]=="Restart"):
            self.exitMenu()
            self.shutdownCallback()
            return

         if(menuItems[self.menuPointer]=="Auto-set Alarm"):
            self.alarmThread.autoSetAlarm()
            self.exitMenu()
            return

         self.menuActive = True

         # Set our temporary variable to current setting
         self.tmp = {
            'Volume': self.settings.getInt('volume'),
            'Manual Alarm': 0,
            'Station': self.settings.getInt('station')
         }.get(menuItems[self.menuPointer])

         print "Selected menu %s" % (menuItems[self.menuPointer])

   def cancel(self):
      self.exitMenu()

   def scroll(self,direction):
      self.menuTimeout = 0
      self.active = True

      if self.menuPointer is None:
         self.menuPointer = 0
      elif not self.menuActive:
         self.menuPointer += direction
      else:
         # FIXME: We don't always just want to increment in case of a scroll while menu active
         self.tmp+=direction

         max = {
            'Volume': 100,
            'Manual Alarm': 300,
            'Station': len(Settings.STATIONS)-1
         }.get(menuItems[self.menuPointer])

         if self.tmp>max:
            self.tmp = max
         if self.tmp<0:
            self.tmp = 0
         return

      if self.menuPointer > len(menuItems)-1:
         self.menuPointer = 0

      if self.menuPointer < 0:
         self.menuPointer = len(menuItems)-1

   def __alarmTimeFromInput(self):
      manAlarmTime = datetime.datetime.now()
      manAlarmTime += datetime.timedelta(minutes=1 + (5*self.tmp))
      manAlarmTime = manAlarmTime.replace(
         minute = (manAlarmTime.minute - (manAlarmTime.minute%5)),
         second = 0,
         microsecond = 0
      )

      return manAlarmTime

   # We need to catch a possible IndexError that crops up in getMessage()
   def __getStationName(self,index):
      try:
         return Settings.STATIONS[self.tmp]['name']
      except IndexError:
         return ""

   def getMessage(self):
      message = ""
      if self.menuPointer is not None:
         if not self.menuActive:
            # We're browsing the menu, so show what we have selected
            message = "Options\n\n%s" % (menuItems[self.menuPointer])
         else:
            # We have an item active, so display our current option
            msg = {
               'Volume': "Volume: %s" % (self.tmp),
               'Manual Alarm': "Alarm at: %s" % (self.__alarmTimeFromInput().strftime("%H:%M")),
               'Station': "Alarm Station:\n %s" % (self.__getStationName(self.tmp))
            }.get(menuItems[self.menuPointer])

            message = "Set %s" % (msg)

      return message
 
   def exitMenu(self):
      self.active = False
      self.menuPointer = None
      self.menuTimeout = 0
      self.menuActive = False
      self.tmp = ""

   def stop(self):
      self.stopping = True

   def run(self):
      calcTimeout = self.settings.getInt('menu_timeout')*(1/LOOP_TIME) # We're unlikely to update this on the fly
      while(not self.stopping):
         time.sleep(LOOP_TIME)
         if self.menuTimeout > calcTimeout:
            self.exitMenu()
         elif(self.menuPointer is not None):
            self.menuTimeout+=1
