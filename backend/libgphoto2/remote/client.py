import Pyro4
import Pyro4.utils.flame
import subprocess
import time

import os

if os.path.exists('uri.txt'):
	os.remove('uri.txt')

process = subprocess.Popen(('bin/gphotoremote.exe','main.py'))

time.sleep(1)
while not os.path.exists('uri.txt'):
	time.sleep(0.05)

try:
	uri = open('uri.txt','rb').read()
	
	api = Pyro4.Proxy(uri)
	api.open(r'..\win32')
	
	#port = uri.split(':')[-1]
	#flame = Pyro4.utils.flame.connect("localhost:%s"%port)
	#api = flame.module('api')
	#with flame.console() as console:
	#	console.interact()
	
	cameras = api.getCameras()
	for camera in cameras:
		print camera.captureImage()
	
	api.stop()
	time.sleep(0.1)
finally:
	try:
		process.terminate()
	except:
		pass
	process.wait()
