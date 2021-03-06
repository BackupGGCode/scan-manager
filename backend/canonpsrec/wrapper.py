"""
Wrap the API in the standard API interface

The rest of the files here define a fully featured manufacturer's API while this file wraps it in a simplified generic interface
"""

from .. import interface
from base import smBasePath

import importlib
import os.path
import sys
import platform

from . import psrec 
from .properties import properties 

class API(interface.API):
	
	def __init__(self,*args,**kargs):
		super(API,self).__init__(*args,**kargs)
		self.opened = False
	
	
	def getName(self):
		return 'Canon PS-ReC (for older PowerShot cameras)'
	
		
	def getId(self):
		return 'canonpsrec'
		
		
	def getCameras(self):
		out = []
		for camera in self.sdk.cameras:
			out.append(Camera(camera=camera,api=self))
		return out

		
	def isAvailable(self):
		return platform.system() == 'windows'

		
	def open(self):
		if self.opened:
			return
		dllpath = os.path.join(smBasePath(),'backend','canonpsrec')
		self.sdk = psrec.SDK(dllpath=dllpath)
		self.opened = True

	def close(self):
		self.sdk.close()
	
	
	
class Camera(interface.Camera):

	def __init__(self,api,camera):
		super(Camera,self).__init__(api)
		self.camera = camera
		self.opened = False
		self.viewfinderStarted = False

	
	def open(self):
		if self.opened:
			return
		self.camera.startRemote()
		self.properties = [i(camera=self) for i in self.api.propertyClasses]
		self.opened = True
		
		
	def getName(self):
		return '%s %s %s %s'%(
			self.camera.manufacturer,
			self.camera.model,
			self.camera.deviceVersion,
			self.camera.serialNumber,
		)
		
	
	def hasCapture(self):
		return True
	
	
	def hasViewfinder(self):
		return True
	
	
	def startViewfinder(self):
		self.viewfinderStarted = True
		self.camera.startViewfinder(self.handleViewfinderData)

	
	def capture(self):
		self.camera.release(keepImageBuffer=True,imageCompleteCallback=self.handleCaptureComplete)

	
	def stopViewfinder(self):
		self.viewfinderStarted = False
		self.camera.stopViewfinder()


	def isViewfinderStarted(self):
		return self.viewfinderStarted

	
	def getProperties(self):
		return self.properties
	
	def close(self):
		self.camera.close()


	def handleViewfinderData(self,data):
		e = interface.ViewfinderFrameEvent(self,data=data)
		self.viewfinderFrame.emit(e)
		
		
	def handleCaptureComplete(self,releaseInfo):
		e = interface.CaptureCompleteEvent(self,releaseInfo.imageBuffer)
		self.captureComplete.emit(e)



class PSRECCameraValueProperty(interface.CameraValueProperty):
	
	def __init__(self,camera):
		super(PSRECCameraValueProperty,self).__init__()
		self.camera = camera
		self.sdkCamera = camera.camera
		
	def getName(self):
		return self.name
	
	def getIdent(self):
		return self.propertyId
	
	def getRawValue(self):
		return self.sdkCamera[self.propertyId]
	
	def setRawValue(self,v):
		if v is not None:
			try:
				self.sdkCamera[self.propertyId] = v
			except:
				print('failed to write camera property %r to %s'%(v,self.propertyId))
				raise
		
	def rawToDisplay(self,rawValue):
		""" Convert a raw value to a displayable string """ 
		if self.descriptor:
			return self.descriptor[rawValue]
		else:
			return rawValue
		
	def displayToRaw(self,displayValue):
		""" Convert a raw value to a displayable string """
		if self.descriptor:
			return self.descriptor[displayValue]
		else:
			return displayValue
		
	def getMin(self):
		return self.prop.min
	
	def getMax(self):
		return self.prop.max
	
	def getStep(self):
		return 1
	
	def getPossibleValues(self):
		out = []
		if getattr(self.prop,'values',None):
			for v in self.prop.values:
				out.append((v,self.descriptor[v]))
		else:
			for v,k in self.descriptor:
				out.append((k,v))
		return out
	
	def isSupported(self):
		return True
	def isReadOnly(self):
		return False
	
	def getControlType(self):
		return self.controlType
		
	#
	# Non-interface stuff
	#
	@property
	def descriptor(self):
		if self.propertyId in properties:
			return properties[self.propertyId]
		else:
			return None

	@property
	def prop(self):
		return self.sdkCamera.properties[self.propertyId]
	
	@property
	def api(self):
		return self.camera.api


		
class PSRECCameraButton(interface.CameraValueProperty):

	def __init__(self,camera):
		super(PSRECCameraButton,self).__init__()
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


class Zoom(PSRECCameraValueProperty):
	propertyId = 'ZOOM_POS'
	name = 'Zoom'
	section = 'Capture Settings'
	controlType = interface.ControlType.Slider
	
class ISO(PSRECCameraValueProperty):
	propertyId = 'ISO'
	name = 'ISO'
	section = 'Capture Settings'
	controlType = interface.ControlType.Combo
	
class ExposureMode(PSRECCameraValueProperty):
	propertyId = 'EXPOSURE_MODE'
	name = 'Exposure mode'
	section = 'Capture Settings'
	controlType = interface.ControlType.Combo
	
class Aperture(PSRECCameraValueProperty):
	propertyId = 'AV'
	name = 'Aperture'
	section = 'Capture Settings'
	controlType = interface.ControlType.Combo

class ShutterSpeed(PSRECCameraValueProperty):
	propertyId = 'TV'
	name = 'Shutter speed'
	section = 'Capture Settings'
	controlType = interface.ControlType.Combo

class FocusPoint(PSRECCameraValueProperty):
	propertyId = 'FOCUS_POINT_SETTING'
	name = 'Focus point'
	section = 'Capture Settings'
	controlType = interface.ControlType.Combo
	
class WhiteBalance(PSRECCameraValueProperty):
	propertyId = 'WB_SETTING'
	name = 'White balance'
	section = 'Capture Settings'
	controlType = interface.ControlType.Combo
	
class CameraOutput(PSRECCameraValueProperty):
	propertyId = 'CAMERA_OUTPUT'
	name = 'Camera output'
	section = 'Camera Settings'
	controlType = interface.ControlType.Combo
	
class CameraModel(PSRECCameraValueProperty):
	propertyId = 'CAMERA_MODEL_NAME'
	name = 'Camera model'
	section = 'Camera Settings'
	controlType = interface.ControlType.Static
	
class ResetAEAFAWB(PSRECCameraButton):
	propertyId = '_RESET_AE_AF_AWB'
	name = 'Reset AE/AF/AWB'
	section = 'Capture Settings'
	controlType = interface.ControlType.Button
	def go(self):
		self.sdkCamera.reset_AE_AF_AWB(AE=True,AF=True,AWB=True)

class LockFocus(PSRECCameraButton):
	propertyId = '_LOCK_FOCUS'
	name = 'Lock focus'
	section = 'Capture Settings'
	controlType = interface.ControlType.Button
	def go(self):
		self.sdkCamera.lockFocus()

class UnlockFocus(PSRECCameraButton):
	propertyId = '_UNLOCK_FOCUS'
	name = 'Unlock focus'
	section = 'Capture Settings'
	controlType = interface.ControlType.Button
	def go(self):
		self.sdkCamera.unlockFocus()

API.propertyClasses = [Zoom,ISO,ExposureMode,Aperture,ShutterSpeed,FocusPoint,WhiteBalance,CameraOutput,CameraModel,ResetAEAFAWB,LockFocus,UnlockFocus]