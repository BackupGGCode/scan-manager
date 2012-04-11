import Pyro4
import Pyro4.utils.flame
import subprocess
import time

import os


class GPhotoClient(object):

	startupTimeout = 5.0

	def __init__(self):
		pass
		
	def open(self,basePath='',dllDir=None):
		
		if dllDir is None:
			dllDir = os.path.join(basePath,'win32')
	
		self.basePath = basePath

		uriPath = os.path.join(basePath,'remote','uri.txt')
	
		if os.path.exists(uriPath):
			os.remove(uriPath)

		process = subprocess.Popen((os.path.join(basePath,'remote','bin','gphotoremote.exe'),os.path.join(basePath,'remote','server.py'),basePath))
		self.opened = True

		start = time.time()
		while not os.path.exists(uriPath):
			if time.time() - start > self.startupTimeout:
				raise Exception('libgphoto2 Cygwin PRC server took too long to start up')
			time.sleep(0.05)

		uri = open(uriPath,'rb').read()
		self.api = Pyro4.Proxy(uri)
		self.api.open(dllDir=dllDir)

	def close(self):
	
		if not self.opened:
			return
		
		try: self.api.close()
		except: pass
			
		try: self.api.stop()
		except: pass
		
		try: process.terminate()
		except: pass
		
		try:
			uriPath = os.path.join(self.basePath,'uri.txt')
			if os.path.exists(uriPath):
				os.remove(uriPath)
		except:
			pass

if __name__ == '__main__':
	client = GPhotoClient()
	client.open()
	api = client.api
	cameras = api.getCameras()