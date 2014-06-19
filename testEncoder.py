import gaugette.rotary_encoder

A_PIN = 5
B_PIN = 4
encoder = gaugette.rotary_encoder.RotaryEncoder(A_PIN, B_PIN)
while True:
   delta = encoder.get_cycles()
   if delta!=0:
     print "rotate %d" % delta
