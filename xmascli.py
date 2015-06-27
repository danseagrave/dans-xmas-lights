"""
xmascli.py
-------
Dan Seagrave
A webserver for controlling xmasd.py
"""
import sys, pygame, zmq, os
from pygame.locals import *

key_map = {
    'q': "QUIT",
    '0': "red_green_jump",
    '1': "red_green_fade",
    '2': "red_green_trail",
    '3': "rainbow",
    '4': "red_blue_fade",
    '5': "silver_twinkle",
    '5': "silver_twinkle",
}

context = zmq.Context()
QUEUE = context.socket(zmq.PUB)
QUEUE.bind('tcp://*:5555')

while True:
    action = raw_input("Enter option:")
    if action in key_map:
        print "Sending", action
        QUEUE.send(key_map[action])

        if action == "q":
            sys.exit()
