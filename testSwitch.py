import gaugette.switch
import time

switch = gaugette.switch.Switch(1)
state = False

while True:
   if switch.get_state():
#      print "State on"
      if not state:
         print "Press"
         state = True
   else:
#      print "State off"
      state = False

   time.sleep(0.001)
