#!/usr/bin/python

import time
import datetime
import calendar
import threading
import subprocess
import os
import Settings
import AlarmGatherer
from mplayer import Player

class AlarmThread(threading.Thread):

   def __init__(self):
      threading.Thread.__init__(self)
      self.stopping=False
      self.player=False
      self.nextAlarm=None
      self.filenull=open(os.devnull, "w")
      self.snoozing = False

      self.settings = Settings.Settings()
      self.alarmGatherer = AlarmGatherer.AlarmGatherer()

   def stop(self):
      print "Stopping alarm thread"
      if(self.player):
         self.stopAlarm()
      self.stopping=True

   def isAlarmSounding(self):
      return self.player!=False

   def isSnoozing(self):
      return self.snoozing

   def getNextAlarm(self):
      return self.nextAlarm

   def snooze(self):
      print "Snoozing alarm for %s minutes" % (self.settings.getInt('snooze_length'))
      self.stopAlarm()

      alarmTime = datetime.datetime.now()
      alarmTime += datetime.timedelta(minutes=self.settings.getInt('snooze_length'))
      self.setAlarmTime(alarmTime)
      self.snoozing = True

   def soundAlarm(self):
      print "Sounding alarm"
      station = Settings.STATIONS[self.settings.getInt('station')]
      print "Playing %s" % (station['name'])
      self.player = Player()
      self.player.loadlist(station['url'])
      self.player.loop = 0
      print "Alarm process opened"

      # Wait a few seconds and see if the mplayer instance is still running
      time.sleep(self.settings.getInt('radio_delay'))

      # Fetch the number of mplayer processes running
      processes = subprocess.Popen('ps aux | grep mplayer | egrep -v "grep" | wc -l', stdout=subprocess.PIPE, shell=True)
      num = int(processes.stdout.read())

      if num < 2 and self.player is not False:
         print "Could not find mplayer instance, playing panic alarm"
         self.player.quit()

         time.sleep(2)

         self.player = Player()
         self.player.loadfile('/usr/share/scratch/Media/Sounds/Music Loops/GuitarChords2.mp3')
         self.player.loop = 0

   def stopAlarm(self):
      print "Stopping alarm"
      self.snoozing = False
      self.nextAlarm = None
      self.settings.set('manual_alarm','') # If we've just stopped an alarm, we can't have a manual one set yet
      if self.player:
         self.player.quit()
         self.player=False
         self.nextAlarm=None
         print "Player process terminated"
      # Automatically set up our next alarm. FIXME: This might choose the same one as we've just cancelled
      self.autoSetAlarm()

   def autoSetAlarm(self):
      print "Automatically setting next alarm"
      try:
         event = self.alarmGatherer.getNextEventTime() # The time of the next event on our calendar
         diff = datetime.timedelta(minutes=self.settings.getInt('wakeup_time')) # How long before event do we want alarm
         event -= diff
         self.setAlarmTime(event)
         self.settings.set('manual_alarm','') # We've just auto-set an alarm, so clear any manual ones
      except Exception as e:
         print "WARNING: Could not automatically set alarm"
         print e
         self.nextAlarm = None

   def manualSetAlarm(self,alarmTime):
      print "Manually setting next alarm to %s" % (alarmTime)
      self.settings.set('manual_alarm',calendar.timegm(alarmTime.utctimetuple()))
      self.setAlarmTime(alarmTime)

   def setAlarmTime(self,alarmTime):
      self.nextAlarm = alarmTime
      print "Alarm set for %s" % (alarmTime)

   # Return a line of text describing the alarm state
   def getMenuLine(self):
      now = datetime.datetime.now()
      message = ""

      if self.nextAlarm is not None:
         diff = self.nextAlarm - now
         if diff.days < 1:
            if self.snoozing:
               message+="Snoozing"
            else:
               message+="Alarm"
            
            if diff.seconds < (2 * 60 * 60): # 2 hours
               if self.snoozing:
                  message+=" for "
               else:
                  message+=" in "
               message+="%s min" % ((diff.seconds//60)+1)
               if diff.seconds//60 != 0:
                  message+="s"
            else:
               if self.snoozing:
                  message+=" until "
               else:
                  message+=" at "
               message+=self.nextAlarm.strftime("%H:%M")   

      return message

   def run(self):
      while(not self.stopping):
          now = datetime.datetime.now()

          if(self.nextAlarm is not None and self.nextAlarm < now and not self.player):
             self.soundAlarm()

          time.sleep(1)
