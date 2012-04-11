"""
Wrap the API in the standard API interface

The rest of the files here define a fully featured libgphoto2's API while this file wraps it in a simplified generic interface
"""

from base import Enum, smBasePath
from backend import interface

import os.path
import platform
import time


class API(interface.API):
	""" 
	A standard API wrapper class around the WIA API
	
	This wraps WIA via ActiveX (pythonwin's win32com) directly rather than having in intermediate API as with most other backends
	""" 
	
	def __init__(self,*args,**kargs):
		super(API,self).__init__(*args,**kargs)
		self.opened = False
	
	
	def getName(self):
		return 'libgphoto2'
		
		
	def open(self):
		
		if self.opened:
			return
		
		if platform.system().lower() == 'windows':
			from .remote import client
			self.client = client.GPhotoClient()
			self.client.open(basePath=os.path.join(smBasePath(),'backend','libgphoto2'))
			self.api = self.client.api
		else:
			from . import api
			self.api = api.API()
			self.api.open()
		
		self.opened = True


	def getCameras(self):
		out = []
		apiCameras = self.api.getCameras()
		for apiCamera in apiCameras:
			camera = Camera(self,apiCamera)
			out.append(camera)
		return out


	def close(self):
		return
	
	
	
class Camera(interface.Camera):

	def __init__(self,api,camera):
		super(Camera,self).__init__(api)
		self.camera = camera
		self.opened = False
		

	def getName(self):	
		return '%s %s'%(self.camera.getModel(),self.camera.getPort())
		
		
	def open(self):
		if self.opened:
			return
		self.camera.init()
		self.opened = True

	
	def hasViewfinder(self):
		return True


	def hasCapture(self):
		return True
	
	
	def capture(self):
		captured = self.camera.captureImage()
	
	
	def getProperties(self):
		return []

	
	def close(self):
		self.camera.close()

	
	def ontimer(self):
		"""
		If we're running in manual mode, periodically check for new items on the device, fetch them, and fire a capture event
		"""
		pass
	
	def handleViewfinderData(self,data):
		e = interface.ViewfinderFrameEvent(self,data=data)
		self.viewfinderFrame.fire(e)



	
class ViewfinderCaptureThread(object):
	
	def __init__(self,camera):
		self.camera = camera
		self.stopped = False
		
	def run(self):
		while 1:
			if self.stopped:
				break
			
		previewFile = self.camera.capturePreview()
		
		
	def stop(self):
		self.stopped = True
		
		
		
