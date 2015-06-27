import array
from ola.ClientWrapper import ClientWrapper

wrapper = None
loop_count = 0
TICK_INTERVAL = 40  # in ms (40 == 25fps)

def DmxSent(state):
  if not state.Succeeded():
    wrapper.Stop()

def SendDMXFrame():
  # schdule a function call in 100ms
  # we do this first in case the frame computation takes a long time.
  wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)

  # compute frame here
  data = array.array('B')
  global loop_count
  val1 = loop_count % 50
  val2 = loop_count % 100
  print "val", val1, val2
  data.append(val1)
  data.append(val1)
  data.append(val1)
  data.append(val2)
  data.append(val2)
  data.append(val2)
  loop_count += 4

  # send
  wrapper.Client().SendDmx(1, data, DmxSent)

wrapper = ClientWrapper()
wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)
wrapper.Run()