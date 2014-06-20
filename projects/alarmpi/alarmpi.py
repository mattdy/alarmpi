#!/usr/bin/python

import time
import datetime
import threading
import ClockThread
import AlarmThread
import LcdThread
import BrightnessThread
import Settings
import MediaPlayer

class AlarmPi:
   def __init__(self):
      self.stopping = False

   def stop(self):
      self.stopping = True

   def execute(self):
      print "Starting up AlarmPi"

      print "Loading settings"
      settings = Settings.Settings()
      settings.setup()

      print "Loading media"
      media = MediaPlayer.MediaPlayer()
      media.playEffect('activated.wav')

      print "Loading clock"
      clock = ClockThread.ClockThread()
      clock.setDaemon(True)

      print "Loading alarm control"
      alarm = AlarmThread.AlarmThread()
      alarm.setDaemon(True)

      print "Loading LCD"
      lcd = LcdThread.LcdThread(alarm,self.stop)
      lcd.setDaemon(True)
      lcd.start()

      print "Loading brightness control"
      bright = BrightnessThread.BrightnessThread()
      bright.setDaemon(True)
      bright.registerControlObject(clock.segment.disp)
      bright.registerControlObject(lcd)
      bright.start()

      # If there's a manual alarm time set in the database, then load it
      manual = settings.getInt('manual_alarm')
      if manual==0 or manual is None:
         alarm.autoSetAlarm()
      else:
         alarmTime = datetime.datetime.utcfromtimestamp(manual)
         print "Loaded previously set manual alarm time of %s" % (alarmTime)
         alarm.manualSetAlarm(alarmTime)

      print "Starting clock"
      clock.start()

      print "Starting alarm control"
      alarm.start()

      # Main loop where we just spin until we receive a shutdown request
      try:
         while(self.stopping is False):
            time.sleep(1)
      except (KeyboardInterrupt, SystemExit):
         print "Interrupted, shutting down"

      print "Shutting down"
      media.playEffect('shutting_down.wav')
      time.sleep(2)

      print "Stopping all services"
      alarm.stop()
      clock.stop()
      lcd.stop()
      bright.stop()

      print "Shutdown complete, now exiting"

      time.sleep(2) # To give threads time to shut down

alarm = AlarmPi()
alarm.execute()
