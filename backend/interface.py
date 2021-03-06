from base import Enum, BaseSettings

from PySide.QtCore import Signal, QObject

ControlType = Enum()
ControlType.Combo = 1
ControlType.Slider = 2
ControlType.Button = 3
ControlType.Static = 4
ControlType.LineEdit = 5
ControlType.Checkbox = 6
ControlType.TwinButton = 7

ImageDataFormat = Enum()
ImageDataFormat.JPEG = 1



class AbstractException(Exception):
	pass


def abstract(f):
	""" Decorator for abstract methods """
	def raiser(*args,**kargs):
		raise AbstractException('Abstract function must be overridden by a child class before being called')
	return raiser



class Info(object):
	"""
	A single Info class should be defined in each backend's __init__.py which returns details via a set of class methods (it is never instantiated)  
	"""
	@classmethod	
	@abstract
	def getName(self):
		"""
		Return the display name of this API
		
		@return: str
		"""
	
	@classmethod	
	@abstract
	def isAvailable(self):
		"""
		Return True if this API can be used on this platfor

		@return: bool
		"""



class APISettings(BaseSettings):
	""" Basic object for storing generic, API-specific settings that the API wants to be kept persistently """
	def __init__(self,**kargs):
		if 'cameraSettings' not in kargs:
			kargs['cameraSettings'] = {}
		super(APISettings,self).__init__(**kargs)


class CameraSettings(BaseSettings):
	""" Basic object for storing generic, camera-specific settings that the API wants to be kept persistently """



class API(object):
	"""
	Main wrapper class for the API
	
	Instantiated/opened once for all cameras connected via this API
	"""
	
	def __init__(self,db):
		self.db = db
	
	@abstract
	def getName(self):
		"""
		Return the display name of this API
		
		@return: str
		"""

		
	@abstract
	def getId(self):
		"""
		Return the display a short identifier for this API
		
		@return: str
		"""

		
	@abstract	
	def getCameras(self):
		"""
		Return a list of L{Camera} objects (may or may not be in an opened state) 
		"""
	
	
	@abstract
	def open(self):
		"""
		Start the API including importing any necessary modules and loading any dlls/shared libraries
		"""
	
	
	@abstract
	def close(self):
		"""
		Stop the API
		"""

	
	def loadSettings(self):
		""" Load persistent settings from the app's settings db """
		key = 'APISettings:%s'%(self.getId())
		if key in self.db:
			self._settings = self.db[key]
		else:
			self._settings = APISettings()


	def saveSettings(self):
		""" Save persistent settings from the app's settings db """
		if self.opened:
			for camera in self.getCameras():
				if camera.opened:
					camera.saveSettings()
		if not getattr(self,'_settings',None):
			return
		key = 'APISettings:%s'%(self.getId())
		self.db[key] = self._settings


	@property
	def settings(self):
		"""
		API-specific settings are automatically persisted by the application
		"""
		if not getattr(self,'_settings',None):
			self.loadSettings()
		return self._settings



class CameraEvent(object):
	""" An event to be passed through a camera signal """



class ViewfinderFrameEvent(CameraEvent):
	""" A framefull of live viewfinder data is available for processing """
	def __init__(self,camera,data):
		self.camera = camera
		self.data = data
	def getData(self):
		"""
		@return: frame jpeg string data
		"""
		return self.data



class CaptureCompleteEvent(CameraEvent):
	def __init__(self,camera,data,auxFiles=[]):
		self.camera = camera
		self.data = data
		self.auxFiles = auxFiles
	def getData(self):
		"""
		Return file data as byte string
		@return: bytes
		"""
		return self.data
	
	def getAuxFiles(self):
		"""
		Return a list of filenames of pre-downloaded auxiliary files that are to be managed with the main image
		
		Aux files should each have a unique extension
		
		@return: [str,...] 
		"""
		return self.auxFiles


class PropertiesChangedEvent(CameraEvent):
	def __init__(self,camera,properties):
		self.camera = camera
		self.properties = properties
	def getProperties(self):
		"""
		@return: [L{CameraProperty},...]
		"""
		return self.properties



class CameraSignal(object):
	"""
	To be used in case we're using these wrappers outside a Qt application and can't use Qt's Signal handling
	"""
	
	def __init__(self,*args):
		self.types = args
		self.listeners = []
		
		
	def emit(self,event):
		""" fire a given event off to anyone listening at this signal """
		for f in self.listeners:
			f(event)
			
			
	def connect(self,listener):
		self.listeners.append(listener)
		
		
	def disconnect(self,listener):
		ndx = self.listeners.index(listener)
		if ndx == -1:
			return False
		del(self.listeners[ndx])
		return True
	


class Camera(QObject):
	""" Generic interface for cameras """

	### N.B. do not simply switch these to CameraSignal -- those need to be instantiated in the __init__ method!
	#viewfinderFrame = Signal(object) #: signal(ViewfinderFrameEvent)
	#captureComplete = Signal(object) #: signal(CaptureCompleteEvent)
	#propertiesChanged = Signal(object) #: signal(PropertiesChangedEvent)
	
	def __init__(self,api):
		self.viewfinderFrame = CameraSignal(object) #: signal(ViewfinderFrameEvent)
		self.captureComplete = CameraSignal(object) #: signal(CaptureCompleteEvent)
		self.propertiesChanged = CameraSignal(object) #: signal(PropertiesChangedEvent)
		super(Camera,self).__init__()
		self.api = api
		
	@abstract
	def open(self):
		""" 
		Connect to the camera using the camera API 
		
		Calling L{open} for an already opened camera should not raise an exception (the camera should simply remain open)
		@return: None
		"""
	@abstract
	def capture(self):
		""" 
		Shoot a frame
		
		This returns immediately and emits a L{captureComplete} signal when the frame is ready
		@return: None
		"""  
	@abstract
	def hasViewfinder(self):
		"""
		Returns true if live view is supported
		@return: bool 
		"""
	@abstract
	def hasCapture(self):
		"""
		Returns true if the camera supports remote capture
		@return: bool 
		"""
	@abstract
	def startViewfinder(self,callback):
		""" 
		Start the live view feature
		
		Once started live view will emit a L{liveViewFrame} signal when the each frame is ready
		@return: None
		"""  
	@abstract
	def stopViewfinder(self):
		"""
		Stop capturing live view frames
		"""
	@abstract
	def isViewfinderStarted(self):
		"""
		Return True if the viewfinder is currently active
		@return: bool
		"""
	@abstract
	def close(self):
		"""
		Disconnect the camera from the API
		
		N.B. camera APIs should call this automatically on __del__ 
		@return: None
		"""
	@abstract
	def getProperties(self):
		""" Return a list of CameraProperty objects which this camera supports and which we want to be controllable """

	def ontimer(self):
		""" This method is executed periodically on each active camera so it can take care of any periodic activities """
		pass

	def saveSettings(self):
		""" This method is called for all cameras when the API is closing to allow the camera time to save any settings it needs to save """
		pass 
	
	@property
	def settings(self):
		if self.getName() not in self.api.settings.cameraSettings:
			self.api.settings.cameraSettings[self.getName()] = CameraSettings()
		return self.api.settings.cameraSettings[self.getName()]	
	


class CameraProperty(QObject):
	""" Generic interface for cameras """
	
	section = 'General'
	
	@abstract
	def getControlType(self):
		""" 
		Return ControlType.XXX
		
		@return: L{ControlType} 
		"""
	@abstract
	def getName(self):
		""" 
		Return a displayable name for this camera property 
		
		@return: str
		"""
	@abstract
	def getIdent(self):
		""" 
		Return the camera API's internal identifier string for this property (should be prefixed with the name of the camera API so as to make it unique)
		
		@return: str
		"""
	@abstract
	def isSupported(self):
		""" Return True if this property is supported for the currently connected camera """
	@abstract
	def isReadOnly(self):
		""" Return False if this value can be set """

	def getCamera(self):
		"""
		Return the wrapper L{Camera} to which this property 
		"""
		return self.camera 
	
	def getSection(self):
		"""
		Return the name of a section (if controls are to be organised by sections/tabs) or None to put it in a default section
		"""
		return self.section


class CameraValueProperty(CameraProperty):
	@abstract
	def getRawValue(self):
		""" Return the current value of this property from the camera """
	@abstract
	def setRawValue(self):
		""" Write a new value of this property to the camera """
	@abstract
	def rawToDisplay(self,rawValue):
		""" Convert a raw value to a displayable string """ 
	@abstract
	def displayToRaw(self,rawValue):
		""" Convert a raw value to a displayable string """



class CameraRangeProperty(CameraValueProperty):
	@abstract
	def getMax(self):
		""" Get the CURRENT maximum (raw) value for this item (only relevant if this is a min-max range item rather than a possibleValues item) """
	@abstract
	def getMin(self):
		""" Get the CURRENT minimum (raw) value for this item (only relevant if this is a min-max range item rather than a possibleValues item) """
	@abstract
	def getStep(self):
		""" Get the CURRENT step (raw) value for this item (only relevant if this is a min-max-step range item rather than a possibleValues item) """



class CameraSelectionProperty(CameraValueProperty):
	@abstract
	def getPossibleValues(self):
		""" 
		Return a list of two-tuples possible values
		
		@return: C{[(<raw_value>,<display_label>),...]} 
		"""
