import Pyro4
import ctypes
import struct
import os
import sys
import imp
#import Pyro4.utils.flame

#Pyro4.config.COMMTIMEOUT = 0.1

basePath = sys.argv[2]

sys.path = [basePath] + sys.path
import api

class RemoteAPI(api.API):
	
	def __init__(self,*args,**kargs):
		self.stopped = False
		api.API.__init__(self,*args,**kargs)
	
	def stop(self):
		print 'stopping'
		self.stopped = True
	
	def notStopped(self):
		return not self.stopped
	
	def register(self,o):
		daemon.register(o)

apiObject = RemoteAPI()
	
daemon = Pyro4.Daemon()
uri = daemon.register(apiObject)

uriPath = os.path.join(basePath,'remote','uri.txt') 

f = open(uriPath,'wb')
f.write(str(uri))
f.close()
#Pyro4.utils.flame.start(daemon)

print uri
daemon.requestLoop(loopCondition=apiObject.notStopped)
print 'exitted'
sys.exit()