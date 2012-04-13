import Pyro4
import ctypes
import struct
import os
import sys
import imp
#import Pyro4.utils.flame

Pyro4.config.COMPRESSION = False
Pyro4.config.DETAILED_TRACEBACK = True
Pyro4.config.HMAC_KEY = "gphotoremote"
Pyro4.config.AUTOPROXY = True

basePath = sys.argv[2]

sys.path = [basePath] + sys.path
import api

#
# Monkey patch for Pyro4 (it doesn't want to exit its main loop when stopped unless you set a COMMITTIMEOUT and if you do that then long
#  running operations tend to time out -- yuck!)
#
from Pyro4.socketserver.threadpoolserver import SocketServer_Threadpool
import select, socket
class MySocketServer_Threadpool(SocketServer_Threadpool):
	def events(self, eventsockets):
		"""used for external event loops: handle events that occur on one of the sockets of this server"""
		# we only react on events on our own server socket.
		# all other (client) sockets are owned by their individual threads.
		assert self.sock in eventsockets
		try:
			sR,sW,sX = select.select(eventsockets,eventsockets,eventsockets,0.2)
			if not (sR or sW or sX):
				return
			csock, caddr=self.sock.accept()
			if Pyro4.config.COMMTIMEOUT:
				csock.settimeout(Pyro4.config.COMMTIMEOUT)
			self.threadpool.growIfNeeded()
			self.workqueue.put((csock, caddr))
		except socket.timeout:
			pass  # just continue the loop on a timeout on accept


Pyro4.core.SocketServer_Threadpool = MySocketServer_Threadpool



class RemoteAPI(api.API):
	
	def __init__(self,*args,**kargs):
		self.stopped = False
		api.API.__init__(self,*args,**kargs)
	
	def stop(self):
		self.stopped = True
	
	def loopCondition(self):
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
	
	daemon.requestLoop(loopCondition=apiObject.loopCondition)
finally:
	try: os.remove(uriPath)
	except: pass
	sys.exit()