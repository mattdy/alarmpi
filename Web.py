import web
from web import form
import time
import datetime
import pytz
import threading
import logging
from Settings import Settings

urls = (
    '/', 'index',
    '/settings', 'set',
    '/reset', 'reset',
    '/api', 'api',
)

render = web.template.render('web/', cache=False, base='layout')

settings = Settings()
alarm = None

log = logging.getLogger('root')

class index:
   def getAlarmForm(self):
      global alarm

      nextAlarm = alarm.getNextAlarm()
      alarmTime = ""

      if nextAlarm is not None:
         alarmTime = nextAlarm.strftime("%I%M")

      return form.Form(
         form.Textbox("time",
            form.notnull,
            form.regexp('[0-2][0-9][0-5][0-9]', 'Must be a 24hr time'),
            description="Set alarm time",
            value = alarmTime,
         ),
      )

   def GET(self):
      global alarm
      form = self.getAlarmForm()()
      return render.index(form,alarm)

   def POST(self):
      global alarm
      form = self.getAlarmForm()()
      if not form.validates():
         return render.index(form,alarm)

      alarmHour = int(form['time'].value[:2])
      alarmMin = int(form['time'].value[2:])
      time = datetime.datetime.now(pytz.timezone('Europe/London'))

      # So we don't set an alarm in the past
      if alarmHour < time.hour:
         time = time + datetime.timedelta(days=1)

      time = time.replace(hour=alarmHour, minute=alarmMin, microsecond=0, second=0)

      alarm.manualSetAlarm(time)

      return render.confirmation("Setting alarm to %s" % (time))

class reset:
   def GET(self):
      global alarm
      log.debug("Web request to reset alarm")
      alarm.autoSetAlarm()
 
      nextAlarm = alarm.getNextAlarm()
      alarmTime = "none"
      if nextAlarm is not None:
         alarmTime = nextAlarm.strftime("%c")

      return render.confirmation("Alarm has been auto-set to %s" % (alarmTime))

class set:
   def getForm(self):
      return form.Form(
         form.Textbox("home",
            form.notnull,
            description="Home location",
            value=settings.get('location_home'),
         ),
         form.Textbox("work",
            form.notnull,
            description="Work location",
            value=settings.get('location_work'),
         ),
         form.Textbox("weatherloc",
            form.notnull,
            description="Weather location",
            value=settings.get('weather_location'),
         ),         
         form.Textbox("snooze",
            form.notnull,
            form.regexp('\d+', 'Must be a digit'),
            description="Snooze Length (minutes)",
            value=settings.getInt('snooze_length'),
         ),
         form.Textbox("wakeup",
            form.notnull,
            form.regexp('\d+', 'Must be a digit'),
            description="Time (mins) before event for alarm",
            value=settings.getInt('wakeup_time'),
         ),
         form.Textbox("precancel",
            form.notnull,
            form.regexp('\d+', 'Must be a digit'),
            description="Pre-empt cancel alarm allowed (secs)",
            value=settings.get('preempt_cancel'),
         ),
         form.Textbox("waketime",
            form.notnull,
            form.regexp('[0-2][0-9][0-5][0-9]', 'Must be a 24hr time'),
            description="Default wakeup time",
            value=settings.get('default_wake'),
         ),
         form.Checkbox("holidaymode",
            description="Holiday mode enabled",
            checked=(settings.getInt('holiday_mode')==1),
            value="holiday",
         ),
         form.Checkbox("weatheronalarm",
            description="Play weather after alarm",
            checked=(settings.getInt('weather_on_alarm')==1),
            value="weatheronalarm",
         ),
         form.Checkbox("sfx",
            description="SFX enabled",
            checked=(settings.getInt('sfx_enabled')==1),
             value="sfx",
         ),
         form.Textbox("ttspath",
            description="TTS path",
            value=settings.get('tts_path'),
         ),
      )

   def GET(self):
      form = self.getForm()()
      return render.settings(form)

   def POST(self):
      form = self.getForm()()
      if not form.validates():
         return render.settings(form)

      changes = []
      log.debug("Processing web request for settings changes")

      if form['home'].value != settings.get('location_home'):
         changes.append("Set Home location to %s" % (form['home'].value))
         settings.set('location_home', form['home'].value)

      if form['work'].value != settings.get('location_work'):
         changes.append("Set Work location to %s" % (form['work'].value))
         settings.set('location_work', form['work'].value)

      if form['weatherloc'].value != settings.get('weather_location'):
         changes.append("Set weather location to %s" % (form['weatherloc'].value))
         settings.set('weather_location', form['weatherloc'].value)

      if int(form['snooze'].value) != settings.getInt('snooze_length'):
         changes.append("Set snooze length to %s" % (form['snooze'].value))
         settings.set('snooze_length', form['snooze'].value)

      if int(form['wakeup'].value) != settings.getInt('wakeup_time'):
         changes.append("Set wakeup time to %s" % (form['wakeup'].value))
         settings.set('wakup_time', form['wakeup'].value)

      if int(form['precancel'].value) != settings.getInt('preempt_cancel'):
         changes.append("Set pre-emptive cancel time to %s seconds" % (form['precancel'].value))
         settings.set('preempt_cancel', form['precancel'].value)

      if form['waketime'].value != settings.get('default_wake'):
         changes.append("Set default wake time to %s" % (form['waketime'].value))
         settings.set('default_wake', form['waketime'].value)

      if form['holidaymode'].checked != (settings.getInt('holiday_mode') == 1):
         changes.append("Setting holiday mode to %s" % (form['holidaymode'].checked))
         settings.set('holiday_mode', 1 if form['holidaymode'].checked else 0)
         if(settings.getInt('holiday_mode')==1):
            # Just enabled holiday mode, so clear any alarms
            log.debug("Enabling holiday mode, clearing alarms")
            alarm.clearAlarm()
         else:
            # Just disabled holiday mode, so do an auto-setup
            log.debug("Disabling holiday mode, auto-setting alarm")
            alarm.autoSetAlarm()

      if form['weatheronalarm'].checked != (settings.getInt('weather_on_alarm') == 1):
         changes.append("Setting weather on alarm to %s" % (form['weatheronalarm'].checked))
         settings.set('weather_on_alarm', 1 if form['weatheronalarm'].checked else 0)

      if form['sfx'].checked != (settings.getInt('sfx_enabled') == 1):
         changes.append("Setting SFX to %s" % (form['sfx'].checked))
         settings.set('sfx_enabled', 1 if form['sfx'].checked else 0)

      if form['ttspath'].value != settings.get('tts_path'):
         changes.append("Setting TTS path to %s" % (form['ttspath'].value))
         settings.set('tts_path', form['ttspath'].value)

      text = "Configuring settings:<p><ul><li>%s</li></ul>" % ("</li><li>".join(changes))
      # For debugging purposes
      for c in changes:
         log.debug(c)
      
      return render.confirmation(text)


class api:
   def GET(self):
      return "API not yet implemented"

class WebApplication(threading.Thread):
   def __init__(self, alarmThread):
      global alarm
      threading.Thread.__init__(self)
      alarm = alarmThread

   def run(self):
      log.debug("Starting up web server")
      self.app = web.application(urls, globals())
      self.app.internalerror = web.debugerror
      web.httpserver.runsimple(self.app.wsgifunc(), ("0.0.0.0", 80))
      log.debug("Web server has stopped")

   def stop(self):
      log.debug("Shutting down web server")
      self.app.stop()
