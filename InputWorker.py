# Thread that just infinitely loops, passes any input to the MenuThread for interpretation

import threading
import time
import gaugette.rotary_encoder
import gaugette.switch
import LedControl

class InputWorker(threading.Thread):
   def __init__(
      self,
      inputReceiver,
      rotor_a_pin = 5,
      rotor_b_pin = 4,
      select_pin  = 6,
      cancel_pin  = 1,
      select_led  = 14, # Note use of BCM numbering rather than WiringPi
      cancel_led  = 15
      ):
      threading.Thread.__init__(self)

      self.encoder = gaugette.rotary_encoder.RotaryEncoder(rotor_a_pin, rotor_b_pin)
      self.select = gaugette.switch.Switch(select_pin)
      self.cancel = gaugette.switch.Switch(cancel_pin)

      self.select_state = False
      self.cancel_state = False

      self.select_led = LedControl.LedControl(select_led)
      self.cancel_led = LedControl.LedControl(cancel_led)

      self.select_led.setValue(100)
      self.cancel_led.setValue(100)

      self.daemon = True
      self.delta = 0
      self.receiver = inputReceiver

   def run(self):
      while True:
         # First, check if the rotary encoder has been cycled
         delta = self.encoder.get_cycles()
         if delta > 0:
            self.receiver.scroll(1)
         elif delta < 0:
            self.receiver.scroll(-1)

         # Next, check for our select button
         if self.select.get_state():
            if not self.select_state:
               self.receiver.select()
               self.select_state = True
         else:
               self.select_state = False

         # Finally, check for our cancel button
         if self.cancel.get_state():
            if not self.cancel_state:
               self.receiver.cancel()
               self.cancel_state = True
         else:
            self.cancel_state = False

         time.sleep(0.001)
