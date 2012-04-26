"""
Wrap the API in the standard API interface

The rest of the files here define a fully featured manufacturer's API while this file wraps it in a simplified generic interface
"""

from .. import interface
from base import Enum

import importlib
import os.path
import platform
import win32com.client.gencache
import pythoncom

WIAAPIMode = Enum()
WIAAPIMode.Tethered = 1 #: Shoot tethered
WIAAPIMode.Manual = 2 #: Shoot manually and use WIA events to detect new images and transfer them
WIAAPIMode.ManualScan = 3 #: Shoot manually and poll for new image in a particular path on the WIA device

wia = win32com.client.constants #: shortcut for WIA constants

CFG_WIA_DEVICE_IMAGE_PATH = ['DCIM','Camera'] #: This would used if we ever need to implement ManualScan mode in which case it should be user-configurable on a per-camera basis 


class API(interface.API):
	""" 
	A standard API wrapper class around the WIA API
	
	This wraps WIA via ActiveX (pythonwin's win32com) directly rather than having in intermediate API as with most other backends
	""" 
	
	def __init__(self,*args,**kargs):
		super(API,self).__init__(*args,**kargs)
		self.opened = False
	
	
	def getName(self):
		return 'Windows Image Acquisition (WIA)'
		
		
	def getId(self):
		return 'wia'
		
		
	def getCameras(self):
		return self.cameras


	def open(self):
		
		if self.opened:
			return
		
		api = self
		class WIAEvents:
			def OnEvent(self,eventID,deviceID,imageID):
				if eventID == wia.wiaEventItemCreated:
					camera = {camera.deviceInfo.DeviceID:camera for camera in api.cameras if camera.opened}[deviceID]
					camera.captureImage(imageID)
			
		win32com.client.gencache.EnsureDispatch('WIA.DeviceManager')
		self.dm = win32com.client.DispatchWithEvents('WIA.DeviceManager',WIAEvents)
		
		self.cameras = []
		for di in self.dm.DeviceInfos:
			self.cameras.append(Camera(deviceInfo=di,api=self))
		
		self.dm.RegisterEvent(wia.wiaEventItemCreated,'*')
		
		self.opened = True


	def close(self):
		return
	
	
	
class Camera(interface.Camera):

	def __init__(self,api,deviceInfo):
		super(Camera,self).__init__(api)
		self.deviceInfo = deviceInfo
		self.mode = None
		self.wiaItemsSeen = {}
		self.opened = False
		

	def getName(self):	
		return '%s %s'%(self.deviceInfo.Properties('Name').Value,self.deviceInfo.Properties('Unique Device ID').Value)
		
		
	def open(self):
		if self.opened:
			return
		
		self.dev = self.deviceInfo.Connect()
		#if self.dev.Properties.Exists('Format'):
		#	self.dev.Properties('Format').Value = wia.wiaFormatJPEG # Shoot JPEG rather than RAW
		
		if wia.wiaCommandTakePicture in [i.CommandID for i in self.dev.Commands]:
			self.mode = WIAAPIMode.Tethered
		else:
			self.mode = WIAAPIMode.Manual
		
		self.properties = []
		for i in self.api.propertyClasses:
			if self.dev.Properties.Exists(i.propertyId):
				self.properties.append(i(camera=self))

		if self.mode == WIAAPIMode.ManualScan:
			self.rootItemId = self.traverse(CFG_WIA_DEVICE_IMAGE_PATH).ItemID
			for item in self.dev.GetItem(self.rootItemId).Items:
				self.wiaItemsSeen[item.ItemID] = True
	
		self.opened = True

	
	def hasViewfinder(self):
		return False


	def hasCapture(self):
		return self.mode == WIAAPIMode.Tethered
	
	
	def capture(self):
		self.dev.ExecuteCommand(wia.wiaCommandTakePicture)
		self.captureNewImages()
	
	
	def getProperties(self):
		return self.properties

	
	def close(self):
		self.camera.close()

	
	def ontimer(self):
		"""
		If we're running in manual mode, periodically check for new items on the device, fetch them, and fire a capture event
		"""
		pythoncom.PumpWaitingMessages()
		if self.mode == WIAAPIMode.ManualScan:
			self.captureNewImages()
		
		
	#
	# Non-interface methods
	#

	def traverse(self,path):
		""" 
		Traverse a path on the WIA device and return the WIA Item at that location 
		
		@param path: sequence of strings
		@return: WIA Item
		"""
		here = self.dev.Items[0]
		while path:
			ident = path[0]
			path = path[1:]
			itemID = {i.Properties('Item Name').Value:i.ItemID for i in here.Items}[ident]
			here = self.dev.GetItem(itemID)
		return here


	def captureNewImages(self):
		"""
		Search the WIA device for new items and fire a captureComplete event for each new item
		
		@return: None
		"""
		root = self.dev.GetItem(self.rootItemId)
		for item in root.Items:
			if item.ItemID in self.wiaItemsSeen:
				continue
			self.wiaItemsSeen[item.ItemID] = True
			image = item.Transfer(wia.wiaFormatJPEG)
			data = image.FileData.BinaryData.tobytes()
			e = interface.CaptureCompleteEvent(self,data)
			self.captureComplete.fire(e)


	def captureImage(self,imageID):
		"""
		Download the image from the WIA device and fire it off as a captureComplete event 
		
		@param imageID: WIA ImageID for the newly captured image
		@return: None
		"""
		item = self.dev.GetItem(imageID)
		self.wiaItemsSeen[item.ItemID] = True
		image = item.Transfer(wia.wiaFormatJPEG)
		data = image.FileData.BinaryData.tobytes()
		e = interface.CaptureCompleteEvent(self,data)
		self.captureComplete.fire(e)
			


class WIACameraValueProperty(interface.CameraValueProperty):
	"""
	Abstract base class for classes representing WIA properties that have a value
	"""
	
	dRawToDisplay = None #: A simple mapping of raw value -> displayable string for this property
	
	def __init__(self,camera):
		super(WIACameraValueProperty,self).__init__()
		self.camera = camera
		self.sdkCamera = camera.camera
		
	def getName(self):
		return self.name
	
	def getIdent(self):
		return self.propertyId
	
	def getRawValue(self):
		return self.prop.Value
	
	def setRawValue(self,v):
		self.prop.SetValue(v)
		
	def rawToDisplay(self,rawValue):
		""" Convert a raw value to a displayable string """ 
		if self.dRawToDisplay:
			return self.dRawToDisplay[rawValue]
		else:
			return rawValue
		
	def displayToRaw(self,displayValue):
		""" Convert a raw value to a displayable string """
		if self.dRawToDisplay:
			ndx = self.dRawToDisplay.values().index(displayValue)
			return self.dRawToDisplay.keys()[ndx]
		else:
			return displayValue
		
	def getMin(self):
		return self.prop.SubTypeMin
	
	def getMax(self):
		return self.prop.SubTypeMax
	
	def getStep(self):
		return self.prop.SubTypeStep
	
	def getPossibleValues(self):
		self.prop.SubTypeValues
		
	def isSupported(self):
		return self.sdkCamera.Properties.Exists(self.propertyId)
		
	def isReadOnly(self):
		return self.prop.IsReadOnly()
	
	def getControlType(self):
		return self.controlType
	
	#
	# Non-interface stuff
	#
	
	@property
	def prop(self):
		return self.sdkCamera.Properties[self.propertyId]
	
	@property
	def api(self):
		return self.camera.api



#
# Some standard WIA properties supported by some (by no means all) WIA cameras that support thethered shooting via WIA (e.g. Nikon DLSRs)  
#

class ExposureMode(WIACameraValueProperty):
	propertyId = 'Exposure Mode'
	name = 'Exposure mode'
	controlType = interface.ControlType.Combo
	
class ExposureCompensation(WIACameraValueProperty):
	propertyId = 'Exposure Compensation'
	name = 'Exposure compensaiton'
	controlType = interface.ControlType.Combo
	
class ExposureTime(WIACameraValueProperty):
	dRawToDisplay = {
		1:"6400",2:"4000",3:"3200",4:"2500",5:"2000",6:"1600",8:"1250",10:"1000",12:"800",15:"640",20:"500",25:"400",31:"320",40:"250",
		50:"200",62:"160",80:"125",100:"100",125:"80",166:"60",200:"50",250:"40",333:"30",400:"25",500:"20",666:"15",769:"13",1000:"10",
		1250:"8",1666:"6",2000:"5",2500:"4",3333:"3",4000:"2.5",5000:"2",6250:"1.6",7692:"1.3",10000:"1s",13000:"1.3s",16000:"1.6s",20000:"2s",
		25000:"2.5s",30000:"3s",40000:"4s",50000:"5s",60000:"6s",80000:"8s",100000:"10s",130000:"13s",150000:"15s",200000:"20s",250000:"25s",300000:"30s"
	}
	propertyId = 'Exposure Time'
	name = 'Exposure'
	controlType = interface.ControlType.Combo
	
class ISO(WIACameraValueProperty):
	propertyId = 'Exposure Index'
	name = 'ISO'
	controlType = interface.ControlType.Combo
	
class Aperture(WIACameraValueProperty):
	propertyId = 'F Number'
	name = 'Aperture'
	controlType = interface.ControlType.Combo
	
class WhiteBalance(WIACameraValueProperty):
	dRawToDisplay = {2:'Auto',4:'Daylight',5:'Fluorescent',6:'Incandescent',7:'Flash',32784:'Cloudy',32785:'Shade',32786:'Kelvin',32787:'Custom'}
	propertyId = 'White Balance'
	name = 'White blanace'
	controlType = interface.ControlType.Combo
	
API.propertyClasses = [ExposureMode,ExposureCompensation,ExposureTime,ISO,Aperture,WhiteBalance]
