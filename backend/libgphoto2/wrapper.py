"""
Wrap the API in the standard API interface

The rest of the files here define a fully featured libgphoto2's API while this file wraps it in a simplified generic interface
"""

from base import Enum, smBasePath
from backend import interface

import os.path
import platform
import time
import threading


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
			self.api = client.GPhotoClient()
			self.opened = True
			self.api.open(basePath=os.path.join(smBasePath(),'backend','libgphoto2'))
		else:
			from . import api
			self.api = api.API()
			self.opened = True
			self.api.open()
		

	def getCameras(self):
		out = []
		apiCameras = self.api.getCameras()
		for apiCamera in apiCameras:
			camera = Camera(self,apiCamera)
			out.append(camera)
		return out


	def close(self):
		'call close on libgphoto2 wrapper api object'
		self.api.close()
		
	
	
class Camera(interface.Camera):

	def __init__(self,api,camera):
		super(Camera,self).__init__(api)
		self.camera = camera
		self.viewfinderThread = None
		self.opened = False
		

	def getName(self):	
		return '%s %s'%(self.camera.getModel(),self.camera.getPort())
		
		
	def open(self):
		if self.opened:
			return
		self.camera.init()
		self.opened = True
		self.properties = []
		for property in self.api.propertyClasses:
			self.properties.append(property(self))

	
	def hasViewfinder(self):
		return True


	def hasCapture(self):
		return True
	
	
	def capture(self):
		captured = self.camera.captureImage()
		data = captured.getData()
		e = interface.CaptureCompleteEvent(self,data=data)
		self.captureComplete.fire(e)
	
	
	def getProperties(self):
		return self.properties

	
	def close(self):
		self.camera.close()

	
	def ontimer(self):
		"""
		If we're running in manual mode, periodically check for new items on the device, fetch them, and fire a capture event
		"""
		pass

	#
	# Non-interface
	#
	
	def startViewfinder(self):
		if self.viewfinderThread and not self.viewfinderThread.stopped:
			return 
		self.viewfinderThread = ViewfinderCaptureThread(self)
		self.viewfinderThread.start() 

	def stopViewfinder(self):
		self.viewfinderThread.stopped = True

	
class ViewfinderCaptureThread(threading.Thread):
	
	def __init__(self,camera):
		super(ViewfinderCaptureThread,self).__init__()
		self.camera = camera
		self.stopped = False
		
	def run(self):
		while 1:
			if self.stopped:
				break
			
			previewFile = self.camera.camera.capturePreview()
			data = previewFile.getData()
			e = interface.ViewfinderFrameEvent(self.camera,data=data)
			self.camera.viewfinderFrame.fire(e)
		
	def stop(self):
		self.stopped = True
		
		
		
class GPhotoCameraButton(interface.CameraValueProperty):

	def __init__(self,camera):
		self.camera = camera
		self.sdkCamera = camera.camera
	
	def getName(self):
		return self.name
	
	def getIdent(self):
		return self.propertyId

	def getControlType(self):
		return self.controlType
		
	def getRawValue(self):
		return True


class StartViewfinder(GPhotoCameraButton):
	propertyId = '_START_VIEWFINDER'
	name = 'Start viewfinder'
	controlType = interface.ControlType.Button
	def go(self):
		self.camera.startViewfinder()

		
class StopViewfinder(GPhotoCameraButton):
	propertyId = '_STOP_VIEWFINDER'
	name = 'Stop viewfinder'
	controlType = interface.ControlType.Button
	def go(self):
		self.camera.stopViewfinder()
		

API.propertyClasses = [StartViewfinder,StopViewfinder]