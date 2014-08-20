#!/usr/bin/python

import logging
import sys

log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)

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
      log.info("Starting up AlarmPi")

      log.debug("Loading settings")
      settings = Settings.Settings()
      settings.setup()

      log.debug("Loading media")
      media = MediaPlayer.MediaPlayer()
      media.playEffect('activated.wav')

      log.debug("Loading clock")
      clock = ClockThread.ClockThread()
      clock.setDaemon(True)

      log.debug("Loading alarm control")
      alarm = AlarmThread.AlarmThread()
      alarm.setDaemon(True)

      log.debug("Loading LCD")
      lcd = LcdThread.LcdThread(alarm,self.stop)
      lcd.setDaemon(True)
      lcd.start()

      log.debug("Loading brightness control")
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
         log.info("Loaded previously set manual alarm time of %s",alarmTime)
         alarm.manualSetAlarm(alarmTime)

      log.debug("Starting clock")
      clock.start()

      log.debug("Starting alarm control")
      alarm.start()

      # Main loop where we just spin until we receive a shutdown request
      try:
         while(self.stopping is False):
            time.sleep(1)
      except (KeyboardInterrupt, SystemExit):
         log.warn("Interrupted, shutting down")

      log.warn("Shutting down")
      media.playEffect('shutting_down.wav')
      time.sleep(2)

      log.info("Stopping all services")
      alarm.stop()
      clock.stop()
      lcd.stop()
      bright.stop()

      log.info("Shutdown complete, now exiting")

      time.sleep(2) # To give threads time to shut down

alarm = AlarmPi()
alarm.execute()
