"""
Wrap the CHDK PTP API in the standard API interface

The rest of the files here define a fully featured CHDK PTP API while this file wraps it in a simplified generic interface
"""

from base import smBasePath, smDataPath
from backend import interface

from .PtpUsbTransport import PtpUsbTransport
from .PtpSession import PtpException
from . import PtpCHDK
from . import PtpValues
from .chdkconstants import *

import os.path
import platform
import threading
import log
import tempfile
import time
from contextlib import contextmanager

from PySide import QtGui

class CHDKError(Exception):
	pass

class LUAError(CHDKError):
	pass

class LUACompileError(LUAError):
	pass

class LUARuntimeError(LUAError):
	pass


class API(interface.API):
	""" 
	A standard API wrapper class around the WIA API
	
	This wraps WIA via ActiveX (pythonwin's win32com) directly rather than having in intermediate API as with most other backends
	""" 
	
	def __init__(self,*args,**kargs):
		super(API,self).__init__(*args,**kargs)
		self.opened = False
		self.cameras = None
	
	
	def getName(self):
		return 'CHDK-PTP (for CHDK-equipped cameras)'
		
		
	def getId(self):
		return 'chdk'
		
	
	def open(self):
		
		if self.opened:
			return
		

	def getCameras(self):
		if self.cameras is not None:
			return self.cameras
		ptps = PtpUsbTransport.findptps()
		
		self.cameras = []
		for ptp in ptps:
			camera = Camera(self,ptp)
			self.cameras.append(camera)
			
		return self.cameras


	def close(self):
		if self.cameras:
			for camera in self.cameras:
				try: camera.close()
				except: pass
		if self.opened:
			self.api.close()
		
	
	
class Camera(interface.Camera):

	def __init__(self,api,ptpLocation):
		self.opened = False
		self.afterOpened = False
		self.viewfinderThread = None
		super(Camera,self).__init__(api)

		self.ptpLocation = ptpLocation
		self.ptpTransport = PtpUsbTransport(self.ptpLocation)
		self.ptpSession = PtpCHDK.PtpCHDKSession(self.ptpTransport)
		
		self.vendorId = PtpValues.Vendors.STANDARD
		
		self.ptpSession.OpenSession()
		self.deviceInfo = self.ptpSession.GetDeviceInfo()
		
		self.vendorId = self.deviceInfo.VendorExtensionID
		


	def getName(self):	
		return '%s %s'%(self.deviceInfo.Model,self.deviceInfo.SerialNumber)
	
	
	def open(self):
		if self.opened:
			return
		
		self.opened = True
		
		self.version = self.ptpSession.GetVersion()
		
		self.execute('switch_mode_usb(1)')
		
		self.createProperties()
		
		self.afterOpened = True


	def hasViewfinder(self):
		return self.version >= (2,2)


	def hasCapture(self):
		return True
	
	
	def capture(self):
		self.execute("shoot()")
	
	
	def getProperties(self):
		return self.properties

	
	def close(self):
		if not self.opened:
			return
		try:
			self.viewfinderThread.stopped = True
		except: 
			pass
		
		### TODO: TEMP: uncomment this!
		#try:
		#	self.execute('switch_mode_usb(0)')
		#except:
		#	pass

	
	def ontimer(self):
		"""
		If we're running in manual mode, periodically check for new items on the device, fetch them, and emit a capture event
		"""
		
		if not self.afterOpened:
			return
		
		
	def startViewfinder(self):
		if self.viewfinderThread and not self.viewfinderThread.stopped:
			return 
		self.viewfinderThread = ViewfinderCaptureThread(self)
		self.viewfinderThread.start()


	def stopViewfinder(self):
		if self.viewfinderThread:
			self.viewfinderThread.stopped = True
			self.viewfinderThread.join()


	def isViewfinderStarted(self):
		if self.viewfinderThread and not self.viewfinderThread.stopped:
			return True
		else:
			return False
	
	#
	# Non-interface
	#
	
	@contextmanager
	def viewfinderDisabled(self):
		viewfinderStarted = self.isViewfinderStarted()
		if viewfinderStarted:
			self.stopViewfinder()
		try:
			yield
		finally:
			if viewfinderStarted:
				self.startViewfinder()
	

	def execute(self,script,expectMessages=False,blind=False,messageCallback=None,*args):

		with self.viewfinderDisabled():
		
			scriptId,rc = self.ptpSession.ExecuteScript(script)
			
			if blind:
				return scriptId
			
			rc = self.ptpSession.GetScriptStatus(scriptId=scriptId)
			if rc == ScriptStatusFlag.RUN:
				for arg in args:
					rc = self.ptpSession.WriteScriptMessage(scriptId=scriptId,message=arg)
					if rc == ScriptMessageStatus.OK:
						continue
					elif rc == ScriptMessageStatus.NOTRUN:
						raise CHDKError('Trying to write a CHDK message to a LUA script but the script has stopped')
					elif rc == ScriptMessageStatus.QFULL:
						raise CHDKError('Message queue full while trying to write a CHDK PTP message to a LUA script')
					elif rc == ScriptMessageStatus.BADID:
						raise CHDKError('Trying to write a CHDK message to a LUA script but the script ID is invalid')
					else:
						raise CHDKError('Unknown return value %r'%rc)
			
			messages = []
			toReturn = None
			
			while 1:
				rc = self.ptpSession.GetScriptStatus(scriptId=scriptId)
				if rc == ScriptStatusFlag.DONE:
					break
				elif rc == ScriptStatusFlag.RUN:
					time.sleep(0.01)
					continue
				elif rc == ScriptStatusFlag.MSG:
					msg = self.ptpSession.ReadScriptMessage(scriptId=scriptId)
					if msg.type == ScriptMessageType.NONE:
						# no message
						continue
					if messageCallback:
						messageCallback(msg)
					if msg.type == ScriptMessageType.ERR:
						if msg.subType == ScriptErrorMessageType.COMPILE:
							raise LUACompileError(msg.value)
						elif msg.subType == ScriptErrorMessageType.RUN: 
							raise LUARuntimeError(msg.value)
						else:
							raise LUAError(msg.value)
					elif msg.type == ScriptMessageType.USER:
						if not expectMessages:
							raise CHDKError('Unexpected message %r sent by Lua script'%msg)
						messages.append(msg.value)
					elif msg.type == ScriptMessageType.RET:
						toReturn = msg.value
					else:
						raise CHDKError('Unknown message type %r'%msg.type)
			
			if expectMessages:
				return toReturn,messages
			else:
				return toReturn
			
	
	def createProperties(self):
		self.properties = []
		for property in self.api.propertyClasses:
			self.properties.append(property(self,None))
	
	
	
class ViewfinderCaptureThread(threading.Thread):
	
	def __init__(self,camera):
		super(ViewfinderCaptureThread,self).__init__()
		self.camera = camera
		self.stopped = False
		
	def run(self):
		while 1:
			if self.stopped:
				break
			
			frame = self.camera.ptpSession.GetLiveData(flags=LiveViewFlag.VIEWPORT|LiveViewFlag.BITMAP|LiveViewFlag.PALETTE)
			
			qimage = QtGui.QImage(
				frame.viewportRGB,
				frame.header.bitmap.logical_width,
				frame.header.bitmap.logical_height,
				QtGui.QImage.Format_RGB888
			)
			pm = QtGui.QPixmap.fromImage(qimage)
			
			painter = QtGui.QPainter(pm)

			qimage = QtGui.QImage(
				frame.bitmapRGBA,
				frame.header.bitmap.logical_width,
				frame.header.bitmap.logical_height,
				QtGui.QImage.Format_ARGB32
			)
			overlay = QtGui.QPixmap.fromImage(qimage)
			
			painter.drawPixmap(0,0,overlay)
			
			e = interface.ViewfinderFrameEvent(self.camera,data=pm)
			self.camera.viewfinderFrame.emit(e)
		
	def stop(self):
		self.stopped = True



class CHDKCameraValueProperty(interface.CameraValueProperty):
	
	def __init__(self,camera,config):
		super(CHDKCameraValueProperty,self).__init__()
		self.camera = camera
		self.config = config
		self.options = []
		self.range = dict(min=0,max=1,step=1)
		self.readOnly = False

	def getName(self):
		return self.config.name
	
	def getIdent(self):
		return self.config.ident

	def getControlType(self):
		return self.config.controlType
		
	def getRawValue(self):
		return self.camera.execute(self.config.getValue)
	
	def setRawValue(self,v):
		self.camera.execute(self.config.setValue,str(v))
		
	def rawToDisplay(self,rawValue):
		return rawValue
		
	def displayToRaw(self,displayValue):
		return displayValue
		
	def getMin(self):
		return self.range['min']
	
	def getMax(self):
		return self.range['max']
	
	def getStep(self):
		return self.range['step'] or 1
	
	def getPossibleValues(self):
		return self.options
	
	def isSupported(self):
		return True
	
	def isReadOnly(self):
		return self.readOnly
	
	def getSection(self):
		return self.config.section
	
	#
	# Non-interface
	#
	
	def setup(self):
		ct = self.getControlType()
		if ct != interface.ControlType.Static:
			self.readOnly = self.camera.execute(self.config.readOnly)
		if ct == interface.ControlType.Combo:
			self.options = self.camera.execute(self.config.options)
		elif ct == interface.ControlType.Slider:
			self.range = self.camera.execute(self.config.getRange)
		else:
			return
	

API.propertyClasses = []