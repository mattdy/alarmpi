import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pin = 14
GPIO.setup(pin, GPIO.OUT)
led = GPIO.PWM(pin, 100)
led.start(0)

dir = 1
level = 1

while True:
   level+=dir
  
   if level==100:
      dir=-1
   if level==0:
      dir=1

   led.ChangeDutyCycle(level)
   time.sleep(0.01)
