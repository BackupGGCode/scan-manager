import Pyro4
import ctypes
import struct
import os
import sys
import imp
#import Pyro4.utils.flame

#Pyro4.config.COMMTIMEOUT = 0.1
Pyro4.config.POLLTIMEOUT = 0.1
Pyro4.config.COMPRESSION = False
Pyro4.config.SERVERTYPE = "multiplex"
Pyro4.config.DETAILED_TRACEBACK = True
Pyro4.config.HMAC_KEY = "gphotoremote"

basePath = sys.argv[2]

sys.path = [basePath] + sys.path
import api

class RemoteAPI(api.API):
	
	def __init__(self,*args,**kargs):
		self.stopped = False
		api.API.__init__(self,*args,**kargs)
	
	def stop(self):
		self.stopped = True
	
	def notStopped(self):
		return not self.stopped
	
	def register(self,o):
		super(RemoteAPI,self).register(o)
		daemon.register(o)

try:
	apiObject = RemoteAPI()
		
	daemon = Pyro4.Daemon()
	uri = daemon.register(apiObject)
	
	uriPath = os.path.join(basePath,'remote','uri.txt')
	
	f = open(uriPath,'wb')
	f.write(str(uri))
	f.close()
	#Pyro4.utils.flame.start(daemon)
	
	daemon.requestLoop(loopCondition=apiObject.notStopped)
finally:
	sys.exit()