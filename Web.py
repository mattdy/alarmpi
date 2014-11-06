import web
from web import form
import time
import threading
import logging
from Settings import Settings

urls = (
    '/', 'index',
    '/api', 'api',
)

render = web.template.render('web/', cache=False)

settings = Settings()
alarm = None

log = logging.getLogger('root')

class index:
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
      )

   def GET(self):
      global alarm
      form = self.getForm()()
      return render.index(form,alarm)

   def POST(self):
      global alarm
      form = self.getForm()()
      if not form.validates():
         return render.index(form,alarm)

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

      text = "<html>Configuring settings:<p><ul><li>%s</li></ul><hr>[<a href='/'>Back</a>]</html>" % ("</li><li>".join(changes))
      # For debugging purposes
      for c in changes:
         log.debug(c)
      
      return text


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
