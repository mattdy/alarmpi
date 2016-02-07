import time
from mplayer import Player
import Settings
import subprocess
import logging

log = logging.getLogger('root')

PANIC_ALARM = '/usr/share/scratch/Media/Sounds/Music Loops/GuitarChords2.mp3'
FX_DIRECTORY = '/root/sounds/'

class MediaPlayer:

   def __init__(self):
      self.settings = Settings.Settings()
      self.player = False
      self.effect = False

   def playerActive(self):
      return self.player!=False

   def soundAlarm(self, alarmThread):
      log.info("Playing alarm")
      self.playStation()
      log.debug("Alarm process opened")

      # Wait a few seconds and see if the mplayer instance is still running
      time.sleep(self.settings.getInt('radio_delay'))

      if alarmThread.isSnoozing() or alarmThread.getNextAlarm() is None:
         # We've snoozed or cancelled the alarm, so no need to check for player
         log.debug("Media player senses alarm already cancelled/snoozed, so not checking for mplayer instance")
         return

      # Fetch the number of mplayer processes running
      processes = subprocess.Popen('ps aux | grep mplayer | egrep -v "grep" | wc -l',
         stdout=subprocess.PIPE,
         shell=True
      )
      num = int(processes.stdout.read())

      if num < 2 and self.player is not False:
         log.error("Could not find mplayer instance, playing panic alarm")
         self.stopPlayer()
         time.sleep(2)
         self.playMedia(PANIC_ALARM,0)

   def playStation(self,station=-1):
      if station==-1:
         station = self.settings.getInt('station')

      station = Settings.STATIONS[station]

      log.info("Playing station %s", station['name'])
      self.player = Player()
      self.player.loadlist(station['url'])
      self.player.loop = 0

   def playMedia(self,file,loop=-1):
      log.info("Playing file %s", file)
      self.player = Player()
      self.player.loadfile(file)
      self.player.loop = loop

   # Play some speech. None-blocking equivalent of playSpeech, which also pays attention to sfx_enabled setting
   def playVoice(self,text): 
      if self.settings.get('sfx_enabled')==0:
         # We've got sound effects disabled, so skip
         log.info("Sound effects disabled, not playing voice")
         return
      path = self.settings.get("tts_path");
      log.info("Playing voice: '%s' through `%s`" % (text,path))
      play = subprocess.Popen('echo "%s" | %s' % (text,path), shell=True)

   # Play some speech. Warning: Blocks until we're done speaking
   def playSpeech(self,text):
      path = self.settings.get("tts_path");
      log.info("Playing speech: '%s' through `%s`" % (text,path))
      play = subprocess.Popen('echo "%s" | %s' % (text,path), shell=True)
      play.wait()

   def stopPlayer(self):
      if self.player:
         self.player.quit()
         self.player = False
         log.info("Player process terminated")
