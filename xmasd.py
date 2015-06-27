"""
xmas.py
-------
Dan Seagrave
Christmas light effects for 50 RGB LEDs using Open Lighting Architecture
"""
import sys
import select
import array
import numpy as np
from ola.ClientWrapper import ClientWrapper
import zmq
from collections import OrderedDict

#################
# CONFIG
#################
FPS = 25
UNIVERSE = 1
NUM_LEDS = 50
SPEED = 3
DEFAULT_MODE = "red_green_trail"
BLACKOUT = False
BLACKOUT_DONE = False
MODES = OrderedDict()
MODES["red_green_jump"] = "Red Green Jump"
MODES["red_green_fade"] = "Red Green fade"
MODES["red_green_trail"] = "Red Green trail"
MODES["red_blue_fade"] = "ALW (colours) Fade"
MODES["red_blue_chase"] = "ALW (colours) Chase"
MODES["rainbow"] = "Rainbow"
MODES["rainbow2"] = "Rainbow 2"
MODES["hue_cyc"] = "Hue cycle"
MODES["silver_twinkle"] = "Silver twinkle"
MODES["warm_twinkle"] = "Warm twinkle"
MODES["silver_purple"] = "Silver Purple alternate"
# MODES["warm_flicker"] = "Warm flicker" # dangerous stroby flicker


##################
# Calcluated config (leave alone)
##################
# status file
statusfile = open('xmasd-status', 'w')

wrapper = None
loop_count = 0
TICK_INTERVAL = 1000 / FPS
old_mode_fn = ""
QUIT = False
CURRENT_MODE = None
QUEUE = None

data = np.zeros([NUM_LEDS,3], dtype=np.uint8)

mode_state = {}


####################
# MODES
####################
def red_green_jump(data, new=False):
  # new?
  if new:
    data[::2] = (255,0,0)
    # even
    data[1::2] = (0,255,0)

    print ("init data", data)

  # compute frame here
  global loop_count
  change_colour = ((loop_count % FPS) == 0)
  if change_colour:
    # save odd
    odd = np.copy(data[::2][0])
    # set odd
    data[::2] = data[1::2][0]
    # set even
    data[1::2] = odd
    #print ("SWAP complete", data)

  print "###############"
  return data

def red_green_fade(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [255, 0, 0],
        [0, 255, 0],
        ],
      'current_target_idx': [0, 1],
      'at_target': np.array([False] * 2),
      'change_delay': FPS,
      'change_delays': np.array([FPS] * 2),
    }

  return run_chase(data, SPEED)

def red_green_trail(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [255, 0, 0],
        [0, 0, 0],
        [0, 255, 0],
        [0, 0, 0],
        ],
      'current_target_idx': [0, 1, 2, 3],
      'at_target': np.array([False] * 4),
      'change_delay': FPS,
      'change_delays': np.array([FPS] * 4),
    }

  return run_chase(data, SPEED)

def rainbow(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [255, 0, 0],
        [170, 85, 0],
        [85, 170, 0],
        [0, 255, 0],
        [0, 170, 85],
        [0, 85, 170],
        [0, 0, 225],
        [85, 0, 170],
        [170, 0, 85],
        ],
      'current_target_idx': range(9),
      'at_target': np.array([False] * 9),
      'change_delay': 1,
      'change_delays': np.array([FPS*2] * 9),
    }

  return run_chase(data, SPEED*2)

def rainbow2(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [255, 0, 0],
        [255, 255, 0],
        [255, 0, 255],
        [0, 255, 0],
        [150, 255, 0],
        [80, 0, 130],
        [0, 0, 225],
        ],
      'current_target_idx': range(7),
      'at_target': np.array([False] * 7),
      'change_delay': FPS,
      'change_delays': np.array([FPS] * 7),
    }

  return run_chase(data, SPEED*FPS, all_must_match=False)

def hue_cyc(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [[255, 0, 0]],
        [[0, 255, 0]],
        [[0, 0, 225]],
        ],
      'current_target_idx': 0,
      'at_target': np.array([False]),
      'change_delay': FPS,
      'change_delays': np.array([FPS]),
    }

  return run_steps(data, SPEED)

def red_blue_fade(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [255, 0, 0],
        [0, 0, 255],
        ],
      'current_target_idx': [0, 1],
      'at_target': np.array([False] * 2),
      'change_delay': FPS,
      'change_delays': np.array([FPS] * 2),
    }

  return run_chase(data, SPEED*2)

def red_blue_chase(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [255, 0, 0],
        [255, 0, 0],
        [255, 0, 0],
        [255, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 255],
        [0, 0, 255],
        [0, 0, 255],
        [0, 0, 255],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        ],
      'current_target_idx': range(16),
      'at_target': np.array([False] * 16),
      'change_delay': 1,
      'change_delays': np.array([FPS] * 16),
    }

  return run_chase(data, 75)

def silver_twinkle(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [18, 9, 30],
        [150, 80, 255],
        [18, 9, 30],
        ],
      'current_target_idx': range(3),
      'at_target': np.array([False] * 3),
      'change_delay': FPS / 3,
      'change_delays': np.array([FPS] * 3),
    }

  return run_chase(data, SPEED*3)

def warm_twinkle(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
        [30, 18, 9],
        [60, 36, 18],
        [30, 18, 9],
        ],
      'current_target_idx': range(3),
      'at_target': np.array([False] * 3),
      'change_delay': FPS / 3,
      'change_delays': np.array([FPS] * 3),
    }

  return run_chase(data, SPEED*3)

def warm_flicker(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
          [
            [30, 18, 9],
            [50, 50, 10],
            [0, 0, 0],
            [30, 18, 9],
          ],
          [
            [0, 0, 0],
            [30, 18, 9],
            [30, 18, 9],
            [50, 50, 10],
          ],
        ],
      'current_target_idx': 0,
      'at_target': np.array([False] * 4),
      'change_delay': 1,
      'change_delays': np.array(0 * 4),
    }

  return run_steps(data, 255)


def silver_purple(data, new=False):
  global mode_state
  if new:
    mode_state = {
      'pattern': [
          [
            [18, 9, 30],
            [150, 80, 255],
            [18, 9, 30],
            [5, 5, 5],
          ],
          [
            [5, 0, 5],
            [30, 0, 18],
            [200, 0, 150],
            [40, 0, 20],
          ],
        ],
      'current_target_idx': 0,
      'at_target': np.array([False] * 4),
      'change_delay': FPS / 4,
      'change_delays': np.array([FPS] * 4),
    }

  return run_steps(data, SPEED*4)

###################
# UTILS
###################

def run_chase(data, speed, all_must_match=True):
  # change the current value
  global mode_state
  num_vals = len(mode_state['pattern'])
  for idx in range(num_vals): 
    target_idx = mode_state['current_target_idx'][idx]
    target = mode_state['pattern'][target_idx]
    val = np.copy(data[idx::num_vals][0])
    # fade
    new_val = [
      fade(val[0], target[0], speed),
      fade(val[1], target[1], speed),
      fade(val[2], target[2], speed)
      ]

    #print "new val", new_val
    # update with new val
    data[idx::num_vals] = new_val

    # at target? - change target for this one
    #print "target", target, ", new", new_val, ", match", np.allclose(target, new_val)
    if np.allclose(target, new_val):
      #print "idx", idx, " target col matches new col"
      mode_state['at_target'][idx] = True

      if not all_must_match:
        # do delay?
        if mode_state['change_delays'][idx] > 0:
          mode_state['change_delays'][idx] -= 1
        else:
          # reset delay
          mode_state['change_delays'][idx] = mode_state['change_delay']
          # change target
          mode_state['current_target_idx'][idx] = loop(target_idx, 1, minimum=0, maximum=num_vals-1)
    # otherwise - not at target
    else:
      mode_state['at_target'][idx] = False
  
  # change target for all
  #print "all at target?", np.all(mode_state['at_target'])
  if all_must_match and np.all(mode_state['at_target']):
    
    # first check delay?
    if not np.allclose(np.array([0 * num_vals]), mode_state['change_delays']):
      mode_state['change_delays'] -= 1
      print "DELAY", mode_state['change_delays']
    
    # then change target colour
    else:
      #print "old targets:", mode_state['current_target_idx']
      for idx in range(num_vals):
        this_target_idx = mode_state['current_target_idx'][idx]
        mode_state['current_target_idx'][idx] = loop(this_target_idx, 1, minimum=0, maximum=num_vals-1)
        mode_state['at_target'][idx] = False

      print "new targets:", mode_state['current_target_idx']
      
      # reset target & delay flags
      mode_state['at_target'] = np.array([False]*num_vals)
      mode_state['change_delays'] = np.array([mode_state['change_delay']] * num_vals)
      print "delays reset:", mode_state['change_delays']
      #print "reset at target:", mode_state['at_target']
  
  return data

def run_steps(data, speed):
  # change the current value
  global mode_state
  num_vals = len(mode_state['pattern'][0])
  target_idx = mode_state['current_target_idx']
  target_colour_list = mode_state['pattern'][target_idx]
  print "steps colors idx:", target_idx
  for idx in range(num_vals): 
    val = np.copy(data[idx::num_vals][0])
    target = target_colour_list[idx]
    # fade
    new_val = [
      fade(val[0], target[0], speed),
      fade(val[1], target[1], speed),
      fade(val[2], target[2], speed)
      ]

    #print "new val", new_val
    # update with new val
    data[idx::num_vals] = new_val

    # at target? - change target for this one
    #print "target", target, ", new", new_val, ", match", np.allclose(target, new_val)
    if np.allclose(target, new_val):
      #print "idx", idx, " target col matches new col"
      mode_state['at_target'][idx] = True

    # otherwise - not at target
    else:
      mode_state['at_target'][idx] = False
  
  # change target for all
  #print "all at target?", np.all(mode_state['at_target'])
  if np.all(mode_state['at_target']):
    
    # first check delay?
    if not np.allclose(np.array([0 * num_vals]), mode_state['change_delays']):
      mode_state['change_delays'] -= 1
      print "DELAY", mode_state['change_delays']
    
    # then change target colour
    else:
      #print "old targets:", mode_state['current_target_idx']
      
      # inc target pattern, reset if gone too far
      mode_state['current_target_idx'] += 1
      if mode_state['current_target_idx'] >= len(mode_state['pattern']):
        mode_state['current_target_idx'] = 0

      print "new target:", mode_state['current_target_idx']
      
      # reset target & delay flags
      mode_state['at_target'] = np.array([False]*num_vals)
      mode_state['change_delays'] = np.array([mode_state['change_delay']] * num_vals)
      print "delays reset:", mode_state['change_delays']
      #print "reset at target:", mode_state['at_target']
  
  return data

def fade(current_val, target, speed, maximum=255):
  # already there
  if current_val == target and not loop:
    return current_val

  if current_val < target:
    new_val = current_val + speed
    if new_val > target:
      new_val = target
  else:
    new_val = current_val - speed
    if new_val < target:
      new_val = target

  return new_val

def loop(current_val, speed, minimum=0, maximum=255):
  new_val = current_val + speed
 
  #print "current_val", current_val, ", new_val", new_val
  
  if new_val > maximum:
    new_val = minimum

  #print "new_val fixed", new_val
  return new_val

####################
# Control
####################
def heardEnter():
    i,o,e = select.select([sys.stdin],[],[],0.0001)
    for s in i:
        if s == sys.stdin:
            if sys.stdin.readline():
              return True
    return False


def DmxSent(state):
  # early exit if QUIT is set
  if QUIT:
    end()
    
  # get command from queue
  queues = dict(QUEUE_POLLER.poll(0)) # we use 0 to specify immediate time out
  if QUEUE in queues and queues[QUEUE] == zmq.POLLIN:
    command = QUEUE.recv()
    process_command(command)

  # end if [ENTER] on stdin
  if heardEnter():
    blackout_end()    

  # end if failed to send DMX
  if not state.Succeeded():
    blackout_end()

def change_mode(new_mode):
  print "try to change mode to", new_mode, "..."
  global CURRENT_MODE
  if new_mode in MODES:
    print "YES"
    CURRENT_MODE = new_mode
    # update the status file
    statusfile.seek(0)
    statusfile.write(CURRENT_MODE)
    statusfile.truncate()

  else:
    print "NO"

def blackout_end():
  global BLACKOUT
  BLACKOUT = True
  global BLACKOUT_DONE
  BLACKOUT_DONE = False
  global QUIT
  QUIT = True

def end():
  print "END"
  wrapper.Stop()

def SendDMXFrame():
  # early exit if blackout
  if BLACKOUT:
    print "IS BLACKOUT"
    wrapper.Client().SendDmx(UNIVERSE, np.zeros(NUM_LEDS * 3, np.uint8), DmxSent)
    BLACKOUT_DONE = True
    return

  # schdule another frame call in TICK_INTERVAL ms
  # we do this first in case the frame computation takes a long time.
  wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)

  # get mode method
  #print ("mode:", MODE_NUM, "modes", MODES)
  mode_fn_name = CURRENT_MODE
  mode_fn = globals()[mode_fn_name]

  # mode changed? - then send new flag and reset loop count
  global loop_count
  global data
  global old_mode_fn
  if not mode_fn_name == old_mode_fn:
    old_mode_fn = mode_fn_name
    data = mode_fn(data, new=True)
    loop_count = 0
  # otherwise - normal
  else:
    data = mode_fn(data)

  #print ("data", data)
  
  # inc loop count
  loop_count += 1

  # send DMX data
  wrapper.Client().SendDmx(UNIVERSE, data.ravel(), DmxSent)

################
# CONTROL
################

def process_command(cmd):
  # split to type and options
  parts = cmd.split(':')
  cmd_type = parts[0]
  options = parts[1:]

  if cmd:
    print "GOT COMMAND", cmd
   
    # QUIT
    if cmd_type == 'QUIT':
      print "QUITING!!"
      blackout_end()

    # MODE
    if cmd_type == 'mode':
      print "COMMAND Change mode", cmd
      change_mode(':'.join(options))



#################
# MAIN
#################

if __name__ == '__main__':
  # setup message queue
  context = zmq.Context()
  QUEUE = context.socket(zmq.SUB)
  QUEUE.setsockopt(zmq.SUBSCRIBE, '')
  QUEUE.connect('tcp://localhost:5555')

  QUEUE_POLLER = zmq.Poller()
  QUEUE_POLLER.register(QUEUE, zmq.POLLIN)

  # set inital mode
  change_mode(DEFAULT_MODE)

  # start the OLA client
  wrapper = ClientWrapper()
  wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)
  # run until recevie quit command...
  wrapper.Run()
  
  # ... must have gotten a quit. So...
  # TIDY UP
  # close status file
  statusfile.close()
  