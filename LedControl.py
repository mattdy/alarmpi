import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

class LedControl:
   def __init__(self,pin):
      GPIO.setup(pin, GPIO.OUT)
      self._led = GPIO.PWM(pin,100)
      self._led.start(0)

   def setValue(self,val):
      if val>100:
         val = 100
      if val<0:
         val = 0
      
      self._led.ChangeDutyCycle(val)

   def __del__(self):
      self._led.stop()
      GPIO.cleanup()
