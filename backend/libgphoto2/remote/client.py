import Pyro4
import Pyro4.utils.flame
import subprocess
import time
import sys
import os
import atexit
import log
import glob

Pyro4.config.HMAC_KEY = "gphotoremote"

class GPhotoClient(object):

	startupTimeout = 5.0

	def __init__(self):
		self.opened = False
		
	def open(self,workingDir,basePath='',dllDir=None):
		
		if dllDir is None:
			dllDir = os.path.join(basePath,'win32')
			
		# remove any .pycs that might have been created with the wrong version of python (cygwin is running 2.6)
		for f in glob.glob(os.path.join(basePath,'*.pyc')) + glob.glob(os.path.join(basePath,'remote','*.pyc')):
			try: os.remove(f)
			except: pass
	
		self.basePath = basePath

		uriPath = os.path.join(workingDir,'uri.txt')
	
		if os.path.exists(uriPath):
			os.remove(uriPath)

		os.environ['CYGWIN'] = 'nodosfilewarning'
		self.opened = True
		atexit.register(self.close)
		si = subprocess.STARTUPINFO()
		si.dwFlags = subprocess.STARTF_USESHOWWINDOW
		si.wShowWindow = subprocess.SW_HIDE
		self.process = subprocess.Popen(
			(
				os.path.join(basePath,'remote','bin','gphotoremote.exe'),
				os.path.join(basePath,'remote','server.py'),
				uriPath,
				basePath,
			),
			startupinfo = si
		)

		start = time.time()
		while not os.path.exists(uriPath):
			if time.time() - start > self.startupTimeout:
				raise Exception('libgphoto2 Cygwin PRC server took too long to start up')
			time.sleep(0.05)

		time.sleep(0.1) # in case the file is in the process of being written (not pretty but it works; should really use a lock)
		uri = open(uriPath,'rb').read()
		self.api = Pyro4.Proxy(uri)
		self.api.open(dllDir=dllDir)


	def close(self):

		log.debug('closing down libgphoto2 client')
		
		if not self.opened:
			return
		
		log.debug('closing down gphotoremote.exe')
		
		try: 
			self.api.stop()
		except: 
			log.logException('failed trying to stop gphotoremote.exe main loop',log.WARNING)
		
		start = time.time()		
		while self.process.poll() is None and (time.time()-start) < 2:
			time.sleep(0.05)
		if self.process.poll():			
			log.warning('failed to shut down gphotoremote.exe -- trying to kill it')
			try:
				self.process.kill()
			except:
				log.logException('failed to kill gphotoremote.exe -- please kill the process manually using the Task Manager',log.ERROR)
		else:
			log.debug('gphotoremote.exe closed down cleanly')
			
		try:
			uriPath = os.path.join(self.basePath,'uri.txt')
			if os.path.exists(uriPath):
				os.remove(uriPath)
		except:
			pass
		
		self.opened = False
		
		
	def __getattr__(self,k):
		if 'api' in self.__dict__:
			return getattr(self.api,k)
		else:
			raise AttributeError(k)
	
	
	def __del__(self):
		try:
			self.close()
		except:
			pass

if __name__ == '__main__':
	client = GPhotoClient()
	client.open()
	api = client.api
	cameras = api.getCameras()