from LCDControl.LCDControl import LCDControl
import gaugette.rotary_encoder
import time
import datetime
import pytz
import threading
import MenuControl
import Settings
from InputWorker import InputWorker
import logging

log = logging.getLogger('root')

#
# Date convenience methods
#

def suffix(d):
   return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def formatDate(dateObj):
   message = dateObj.strftime("%a ")
   message+= dateObj.strftime("%d").lstrip("0")
   message+= suffix(dateObj.day)
   message+= dateObj.strftime(" %B")

   return message

#
# Class dealing with displaying relevant information on the LCD screen
#

class LcdThread(threading.Thread):

   def __init__(self,alarmThread,shutdownCallback,weatherFetcher):
      threading.Thread.__init__(self)
      self.alarmThread = alarmThread
      self.stopping=False

      self.message=""

      self.settings = Settings.Settings()

      self.weather = weatherFetcher

      self.menu = MenuControl.MenuControl(alarmThread,shutdownCallback)
      self.menu.setDaemon(True)

      self.lcd = LCDControl()
      self.lcd.white()
      self.setMessage("Booting up...")

      self.rotor = InputWorker(self)
      self.rotor.start()

   def setBrightness(self,brightness):
      # We get passes a value from 0 - 15, which we need to scale to 0-255 before passing to LCDControl
      colVal = int(255 * (float(brightness)/15))
      self.lcd.setColour(colVal,colVal,colVal)

   def setMessage(self,newMessage,center=False):
      if newMessage != self.message:
         self.message = newMessage
         self.lcd.setMessage(self.message,center)

   def scroll(self,direction):
      self.menu.scroll(direction)

   # Called by InputWorker on press of the select button
   def select(self):
      if self.alarmThread.isAlarmSounding():
         # Lets snooze for a while
         self.alarmThread.snooze()
         return

      self.menu.select()

   # Called by InputWorker on press of the cancel button
   def cancel(self):
      if self.alarmThread.isAlarmSounding() or self.alarmThread.isSnoozing():
         # Stop the alarm!
         self.alarmThread.stopAlarm()
         return

      if self.alarmThread.alarmInSeconds() < self.settings.getInt('preempt_cancel') and not self.menu.isActive():
         # We're in the allowable window for pre-empting a cancel alarm, and we're not in the menu
         log.info("Pre-empt cancel triggered")
         self.alarmThread.stopAlarm()
         return
      
      self.menu.cancel()

   def stop(self):
      self.stopping=True

   def run(self):
      self.menu.start()

      self.lcd.setMessage("Boot finished")

      while(not self.stopping):
         time.sleep(0.1)

         try:
            if self.alarmThread.isAlarmSounding():
               self.setMessage("Wakey wakey!",True)
               continue         

            if self.menu.isActive():
               message = self.menu.getMessage()
            elif self.menu.backgroundRadioActive():
               message = "Radio player on"
            else:
               now = datetime.datetime.now(pytz.timezone('Europe/London'))
               message = formatDate(now)
               message+="\n"
            
               message+=self.weather.getWeather().display()
               message+="\n"

               message+=self.alarmThread.getMenuLine()

            self.setMessage(message,True)
         except:
            log.exception("Error in LcdThread loop")

      # end while not stopping
      self.setMessage("Shutting down")
      self.lcd.shutdown()
      self.menu.stop()
