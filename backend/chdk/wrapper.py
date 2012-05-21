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
		self.filesDownloaded = {}
		super(Camera,self).__init__(api)

		self.ptpLocation = ptpLocation
		self.ptpTransport = PtpUsbTransport(self.ptpLocation)
		self.ptpSession = PtpCHDK.PtpCHDKSession(self.ptpTransport)
		
		self.vendorId = PtpValues.Vendors.STANDARD
		
		self.ptpSession.OpenSession()
		self.deviceInfo = self.ptpSession.GetDeviceInfo()
		
		self.vendorId = self.deviceInfo.VendorExtensionID
		
		self.executeLock = threading.Lock()


	def getName(self):	
		return '%s %s'%(self.deviceInfo.Model,self.deviceInfo.SerialNumber)
	
	
	def open(self):
		if self.opened:
			return
		
		self.opened = True
		
		self.version = self.ptpSession.GetVersion()
		
		self.lastCheck = str(self.execute('switch_mode_usb(1)\nreturn os.time()'))
		
		self.createProperties()
		
		self.afterOpened = True
		
		if 'config' in self.api.settings and self.api.settings.config.downloadMode == 'background':
			self.downloadThread = DownloadThread(self)
			self.downloadThread.start()


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
		
		try:
			self.downloadThread.stopped = True
		except: 
			pass
		
		try:
			self.execute('switch_mode_usb(0)')
		except:
			pass

	
	def ontimer(self):
		"""
		If we're running in manual mode, periodically check for new items on the device, fetch them, and emit a capture event
		"""
		
		if not self.afterOpened:
			return
		
		
	def startViewfinder(self):
		if self.isViewfinderStarted():
			return
		self.viewfinderThread = ViewfinderCaptureThread(self)
		self.viewfinderThread.start()


	def stopViewfinder(self):
		if self.isViewfinderStarted():
			self.viewfinderThread.stop()


	def isViewfinderStarted(self):
		if self.viewfinderThread and self.viewfinderThread.isAlive():
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
	

	def downloadNewImages(self):
		
		script = self.api.settings.config.listNewFilesScript
		script = script.replace('##LASTTIME##',self.lastCheck)
		
		rc = self.execute(script)
		
		startTimeForCurrent = str(rc['started'])
		del(rc['started'])
		
		if not rc:
			return 

		self.lastCheck = startTimeForCurrent
		
		toRemove = []
		for file in rc.values():
			if file in self.filesDownloaded:
				continue
			toRemove.append(file)
			self.filesDownloaded[file] = True
			data = self.ptpSession.Download(file)
			e = interface.CaptureCompleteEvent(self,data=data,auxFiles=[])
			self.captureComplete.emit(e)
			
		self.execute('\n'.join(['os.remove("%s")'%file for file in toRemove]))


	def execute(self,script,expectMessages=False,blind=False,messageCallback=None,*args):

		with self.viewfinderDisabled(),self.executeLock:
		
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
					if msg is None:
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
			
		if 'config' not in self.api.settings:
			return
		
		config = self.api.settings.config
		
		for control in config.chdkControls:
			property = CHDKCameraValueProperty(camera=self,config=control)
			property.setup()
			self.properties.append(property)
	
	
	
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



class DownloadThread(threading.Thread):
	
	def __init__(self,camera):
		super(DownloadThread,self).__init__()
		self.camera = camera
		self.stopped = False
		self.paused = False
		self.lastCheck = str(self.camera.execute('return os.time()'))
		self.done = {}

		
	def run(self):
		while 1:
			while self.paused:
				if self.stopped:
					break
				time.sleep(0.1)
			
			if self.stopped:
				break
			
			self.camera.downloadNewImages()
										
			time.sleep(1.0)
			
			
	def stop(self):
		self.stopped = True
		self.join(10.0)
		
		
	def pause(self):
		self.paused = True
		
		
	def unpause(self):
		self.paused = True



def tolua(value):
	if type(value) is unicode:
		return repr(str(value))
	elif type(value) is dict:
		return '{%s}'%(','.join(['%s=%s'%(k,tolua(i)) for k,i in value.items()]))
	elif type(value) is list:
		return '{%s}'%(','.join([tolua(i) for i in value]))
	else:
		return repr(value)


class CHDKCameraValueProperty(interface.CameraValueProperty):
	
	def __init__(self,camera,config):
		super(CHDKCameraValueProperty,self).__init__()
		self.camera = camera
		self.config = config
		self.options = []
		self.range = dict(min=0,max=10,step=1)
		self.readOnly = False

	def getName(self):
		return self.config['label']
	
	def getIdent(self):
		return self.config['name']

	def getControlType(self):
		return self.config['controlType']
		
	def getRawValue(self):
		return self.execute(self.config['getValueScript'])
	
	def setRawValue(self,v):
		script = self.config['setValueScript']
		script = script.replace('##VALUE##',tolua(v))
		return self.execute(script)
		
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
		return self.config['tab']
	
	def go(self):
		return self.execute(self.config['executeScript'],'executeScript')
			
	#
	# Non-interface
	#
	def execute(self,script,scriptName='<unknown>'):
		try:
			return self.camera.execute(script)
		except CHDKError:
			log.logException('LUA script error in %s->%s'%(self.getName(),scriptName), log.ERROR)
		
	
	def setup(self):
		
		ct = self.getControlType()
		
		if ct != interface.ControlType.Static and self.config['readOnlyScript']:
			self.readOnly = self.execute(self.config['readOnlyScript'],'readOnlyScript')
			
		if ct == interface.ControlType.Combo:
			if self.config['optionsScriptType'] == 'fixed':
				options = self.config['optionsFixedValue'].strip().replace('\r','').split('\n')
				self.options = [(i,i) for i in options]
			else:
				options = self.execute(self.config['optionsScript'],'optionsScript')
				if options is None:
					return
				self.options = [None] * len(options)
				for k,v in options.items():
					self.options[k] = (v,v)
		elif ct == interface.ControlType.Slider:
			if self.config['rangeScriptType'] == 'fixed':
				try:
					l = self.config['rangeFixedValue'].strip().split(',')
					self.range = dict(min=int(l[0]),max=int(l[1]),step=int(l[2]))
				except:
					raise Exception('Invalid fixed range string for CHDK control %s'%self.getName())
			else:
				if not self.config['rangeScript']:
					raise Exception('You must supply a range script for CHDK control %s'%self.getName())
				range = self.execute(self.config['rangeScript'],'rangeScript')
				if range is None:
					return
				self.range = dict(min=int(range['min']),max=int(range['max']),step=int(range['step']))
		else:
			return
	

class SpecialCameraButton(interface.CameraValueProperty):

	def __init__(self,camera,property):
		super(SpecialCameraButton,self).__init__()
		self.camera = camera
		self.property = property
	
	def getName(self):
		return self.name
	
	def getIdent(self):
		return self.propertyId

	def getControlType(self):
		return self.controlType
		
	def getRawValue(self):
		return True
	
	def isReadOnly(self):
		return False
	
class DownloadNewImages(SpecialCameraButton):
	propertyId = 'downloadNewImages'
	name = 'Download new images'
	section = 'Capture Settings'
	controlType = interface.ControlType.Button
	def go(self):
		self.camera.downloadNewImages()


API.propertyClasses = [DownloadNewImages]