#!/usr/bin/python

import time
import datetime
import calendar
import threading
import Settings
import AlarmGatherer
import MediaPlayer

class AlarmThread(threading.Thread):

   def __init__(self):
      threading.Thread.__init__(self)
      self.stopping=False
      self.nextAlarm=None
      self.filenull=open(os.devnull, "w")
      self.snoozing = False

      self.settings = Settings.Settings()
      self.media = MediaPlayer.MediaPlayer()
      self.alarmGatherer = AlarmGatherer.AlarmGatherer()

   def stop(self):
      print "Stopping alarm thread"
      if(self.media.playerActive()):
         self.stopAlarm()
      self.stopping=True

   def isAlarmSounding(self):
      return (self.media.playerActive() and self.nextAlarm < datetime.datetime.now())

   def isSnoozing(self):
      return self.snoozing

   def getNextAlarm(self):
      return self.nextAlarm

   def snooze(self):
      print "Snoozing alarm for %s minutes" % (self.settings.getInt('snooze_length'))
      self.silenceAlarm()
      self.media.playEffect('sleep_mode_activated.wav')

      alarmTime = datetime.datetime.now()
      alarmTime += datetime.timedelta(minutes=self.settings.getInt('snooze_length'))
      self.setAlarmTime(alarmTime)
      self.snoozing = True

   def soundAlarm(self):
      print "Alarm triggered"
      self.media.soundAlarm()

   # Only to be called if we're stopping this alarm cycle - see silenceAlarm() for shutting off the player
   def stopAlarm(self):
      print "Stopping alarm"
      self.silenceAlarm()

      self.snoozing = False
      self.nextAlarm = None
      self.settings.set('manual_alarm','') # If we've just stopped an alarm, we can't have a manual one set yet

      # Automatically set up our next alarm. FIXME: This might choose the same one as we've just cancelled
      self.autoSetAlarm()

   # Stop whatever is playing
   def silenceAlarm(self):
      print "Silencing alarm"
      self.media.stopPlayer()

   def autoSetAlarm(self):
      print "Automatically setting next alarm"
      try:
         event = self.alarmGatherer.getNextEventTime() # The time of the next event on our calendar
         diff = datetime.timedelta(minutes=self.settings.getInt('wakeup_time')) # How long before event do we want alarm
         event -= diff
         self.setAlarmTime(event)
         self.settings.set('manual_alarm','') # We've just auto-set an alarm, so clear any manual ones
         self.media.playEffect('sentry_mode_activated.wav')
      except Exception as e:
         print "WARNING: Could not automatically set alarm"
         print e
         self.media.playEffect('critical_error.wav')
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

          if(self.nextAlarm is not None and self.nextAlarm < now and not self.media.playerActive()):
             self.soundAlarm()

          time.sleep(1)
