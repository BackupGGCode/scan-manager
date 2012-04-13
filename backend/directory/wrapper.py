"""
This wrapper actually implements the backend since it's so simple
"""

from .. import interface

import os
import os.path



class API(interface.API):
	""" 
	A standard API wrapper class around the WIA API
	
	This wraps WIA via ActiveX (pythonwin's win32com) directly rather than having in intermediate API as with most other backends
	""" 
	
	def __init__(self,*args,**kargs):
		super(API,self).__init__(*args,**kargs)
		self.opened = False
	
	
	def getName(self):
		return 'Dummy (simply scans a directory for new files)'

	
	def getId(self):
		return 'directory'
		
	
	def getCameras(self):
		return self.cameras


	def open(self):
		if self.opened:
			return
		Camera1 = Camera(self,'Directory-scanner dummy camera 1')
		Camera2 = Camera(self,'Directory-scanner dummy camera 2')
		self.cameras = [Camera1,Camera2]
	

	def close(self):
		return


	
class Camera(interface.Camera):

	def __init__(self,api,name):
		super(Camera,self).__init__(api)
		self.name = name
		self.seen = {}
		if 'directory' not in self.settings:
			self.settings.directory = ''
		if self.settings.directory:
			self.ignoreExisting()
		self.opened = False
		

	def getName(self):	
		return self.name
		
		
	def open(self):
		if self.opened:
			return
		self.properties = []
		for cls in [DirectoryProperty,CaptureExistingProperty]:
			self.properties.append(cls(self))
		
	
	def hasViewfinder(self):
		return False

	
	def hasCapture(self):
		return False
	
	
	def getProperties(self):
		return self.properties

	
	def close(self):
		return

	
	def ontimer(self):
		"""
		Periodically check for new files in the device directory, fetch them, and fire a capture event
		"""
		if self.settings.directory:
			self.captureNewImages()
			

	def ignoreExisting(self):
		if self.settings.directory and os.path.isdir(self.settings.directory):
			names = os.listdir(self.settings.directory)
			for name in names:
				self.seen[name] = True


	def includeExisting(self):
		self.seen = {}
		
	
	def captureNewImages(self):
		"""
		Search the directory for new items and fire a captureComplete event for each new item
		
		@return: None
		"""
		if not (self.settings.directory and os.path.isdir(self.settings.directory)):
			return
		names = os.listdir(self.settings.directory)
		names = [name for name in names if name not in self.seen]
		for name in names:
			self.seen[name] = True
			if not name.lower().endswith('.jpg') or name.lower().endswith('.jpeg'):
				continue
			filename = os.path.join(self.settings.directory,name)
			data = open(filename,'rb').read()
			e = interface.CaptureCompleteEvent(self,data)
			self.captureComplete.fire(e)
			


class DirectoryProperty(interface.CameraProperty):
	"""
	Class for representing an input field from into which a directory can be entered
	"""
	
	def __init__(self,camera):
		self.camera = camera
		
	def getName(self):
		return 'Directory to scan'
	
	def getIdent(self):
		return 'directory'
	
	def isSupported(self):
		return True
		
	def isReadOnly(self):
		return False
	
	def getControlType(self):
		return interface.ControlType.LineEdit
	
	def rawToDisplay(self,rawValue):
		return rawValue
		
	def displayToRaw(self,displayValue):
		return displayValue
	
	def getRawValue(self):
		return self.camera.settings.directory

	def setRawValue(self,raw):
		if os.path.isdir(raw):
			if raw != self.camera.settings.directory:
				self.camera.settings.directory = raw
				self.camera.ignoreExisting()
		else:
			return 'Not a valid directory'


class CaptureExistingProperty(interface.CameraProperty):
	"""
	A button that forces the camera to recapture pre-existing files 
	"""
	
	def __init__(self,camera):
		self.camera = camera
		
	def getName(self):
		return 'Capture existing images'
	
	def getIdent(self):
		return 'captureExisting'
	
	def isSupported(self):
		return True
		
	def isReadOnly(self):
		return False
	
	def getControlType(self):
		return interface.ControlType.Button
	
	def getRawValue(self):
		if self.camera.settings.directory:
			return True
		else:
			return False

	def go(self):
		self.camera.includeExisting()
		