"""
xmasweb.py
-------
Dan Seagrave
A webserver for controlling xmasd.py
"""

import sys, zmq
from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
import xmasd
from mpd import MPDClient

app = Flask(__name__)
app.debug = True

MUISC_ENABLED = True

VALID_MODES = xmasd.MODES
#["red_green_jump", "red_green_fade", "red_green_trail", "rainbow", "rainbow2", "red_blue_fade", "silver_twinkle"]

context = zmq.Context()
QUEUE = context.socket(zmq.PUB)

# connect to music deamon
music = MPDClient()               # create MPD client object
music.timeout = 10                # network timeout in seconds (floats allowed), default: None
music.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None
music.connect("localhost", 6600)  # connect to localhost:6600
music.consume(1)  # make sure items fall out of queue when finished

# status file
statusfile = open('xmasd-status', 'r')

@app.route('/static/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('static', path))

@app.route("/")
def default():
    #return "HELLO"
    return render_template('xmas.html')

@app.route("/quit")
def quit():
    #return "HELLO"
    return render_template('quit.html')

@app.route('/command', methods=['POST'])
def process_command():
  command = request.form['command']


  # convert to plain ascii (zmq doesnt like unicode)
  if command:
    command = command.encode('ascii','ignore')


  print "command", command
  if command == "QUIT":
    QUEUE.send(command)
    shutdown_server()

  else:
    # split to type and options
    parts = command.split(':')
    cmd_type = parts[0]
    options = parts[1:]

    # process here for some commands
    if cmd_type == 'music':
      process_music_command(options)
    # otherwise forward the whole thing to xmasd
    else:
      QUEUE.send(command)

  return jsonify(status='ok')

@app.route('/get-mode-commands')
def get_commands():
  return jsonify(modes=VALID_MODES)

@app.route('/get-current-mode')
def get_current_mode():
  statusfile.seek(0)
  mode = statusfile.readline()
  return jsonify(mode=mode)

@app.route('/get-music')
def get_music():
  available_music = music.listallinfo()
  return jsonify(music_enabled=MUISC_ENABLED, music=available_music)

@app.route('/get-playlist')
def get_playlist():
  playlist = music.playlistinfo()
  return jsonify(playlist=playlist)

def process_music_command(options):
  print "MUSIC COMMAND: ", options
  action = options[0]
  if action == 'play':
    music.play()
  elif action == 'pause':
    music.pause()
  elif action == 'stop':
    music.stop()
  elif action == 'next':
    music.next()
  elif action == 'add':
    if options[1]:
      music.add(options[1])


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

if __name__ == "__main__":
    QUEUE.bind('tcp://*:5555')


    app.run(host='0.0.0.0', use_reloader=False)

    statusfile.close()

    # close MPD connection
    music.close()
    music.disconnect()     