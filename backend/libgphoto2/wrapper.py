"""
Wrap the API in the standard API interface

The rest of the files here define a fully featured libgphoto2's API while this file wraps it in a simplified generic interface
"""

from base import smBasePath, smDataPath
from backend import interface

import os.path
import platform
import threading
import constants
import log
import tempfile

EVENTTYPE_TO_NAME = {
	constants.GPEvent.UNKNOWN: 'constants.GPEvent.UNKNOWN',
	constants.GPEvent.TIMEOUT: 'constants.GPEvent.TIMEOUT',
	constants.GPEvent.FILE_ADDED: 'constants.GPEvent.FILE_ADDED',    
	constants.GPEvent.FOLDER_ADDED: 'constants.GPEvent.FOLDER_ADDED', 
	constants.GPEvent.CAPTURE_COMPLETE: 'constants.GPEvent.CAPTURE_COMPLETE',
}


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
		return 'GPhoto (libgphoto2)'
		
		
	def getId(self):
		return 'libgphoto2'
		
	
	def open(self):
		
		if self.opened:
			return
		
		if platform.system().lower() == 'windows':
			from .remote import client
			self.api = client.GPhotoClient()
			self.opened = True
			self.api.open(workingDir=smDataPath(),basePath=os.path.join(smBasePath(),'backend','libgphoto2'))
		else:
			from . import api
			self.api = api.API()
			self.opened = True
			self.api.open()
		

	def getCameras(self):
		if self.cameras:
			return self.cameras
		out = []
		apiCameras = self.api.getCameras()
		for apiCamera in apiCameras:
			camera = Camera(self,apiCamera)
			out.append(camera)
		self.cameras = out
		return out


	def close(self):
		if self.cameras:
			for camera in self.cameras:
				try: camera.close()
				except: pass
		if self.opened:
			self.api.close()
		
	
	
class Camera(interface.Camera):

	def __init__(self,api,camera):
		super(Camera,self).__init__(api)
		self.camera = camera
		self.viewfinderThread = None
		self.opened = False
		self.afterOpened = False
		self.config = None
		self.configWidgets = {} 
		self.capturedData = None
		self.capturedAuxFiles = []
		
		self.hasCaptureEvents = None #: None means automatically guess whether capture events are supported
		
		self.name = '%s %s'%(self.camera.getModel(),self.camera.getPort())

		
	def getName(self):
		return self.name
	
	
	def open(self):
		if self.opened:
			return
		
		self.opened = True
		self.camera.init()
		self.properties = []
		self.nameToProperty = {}

		# fetch current camera config
		self.configurationFromCamera()
		
		# try to wake the camera up so we get a complete set of properties to work with
		changed = False
		if 'capture' in self.configWidgets and self.configWidgets['capture']['value'] != 1:
			self.configWidgets['capture']['value'] = 1
			self.configWidgets['capture']['changed'] = True
			changed = True
		if changed:
			self.configurationToCamera()
			self.configurationFromCamera()

		if 'savedProperties' in self.settings:
			self.restoreProperties()
			self.configurationToCamera()
			"""
			try:
				self.restoreProperties()
				self.configurationToCamera()
			except:
				log.logException('Error attempting to restore properties:\n%s'%'\n'.join('  %s=%s'%(name,value) for name,value in self.settings.savedProperties),log.ERROR)
			"""

		# now create new CameraProperty instances in self.properties based on the configuration we just retrieved
		self.createProperties()
		
		self.afterOpened = True


	def hasViewfinder(self):
		return True


	def hasCapture(self):
		return True
	
	
	def capture(self):
		data = self.camera.captureImage()
		self.capturedData = data
		if not self.hasCaptureEvents:
			e = interface.CaptureCompleteEvent(self,data=data,auxFiles=[])
			self.captureComplete.emit(e)
	
	
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
			if 'capture' in self.configWidgets and self.configWidgets['capture']['value'] != 0: 
				self.configWidgets['capture']['value'] = 0
				self.configWidgets['capture']['changed'] = True
				self.configurationToCamera()
		except:
			log.logException('unable to turn off capture mode', log.WARNING)
		self.opened = False
		self.camera.exit()
			
	
	def ontimer(self):
		
		if not self.afterOpened:
			return
		
		while 1:
			eventType,data = self.camera.waitForEvent(timeout=0)
			if eventType == constants.GPEvent.TIMEOUT:
				return
			if self.hasCaptureEvents is None:
				if (eventType == constants.GPEvent.UNKNOWN and data.startswith('PTP Property')) or eventType == constants.GPEvent.FILE_ADDED or eventType == constants.GPEvent.CAPTURE_COMPLETE: 
					### TEMP: if we get any valid event we guess that the camera supports PTP end capture events -- not ideal!  
					self.hasCaptureEvents = True
			if not eventType == constants.GPEvent.UNKNOWN and data.startswith('PTP Property'):
				# log everything except timeouts and PTP property change events
				log.debug('%s %r'%(EVENTTYPE_TO_NAME[eventType],data))  
			if eventType == constants.GPEvent.UNKNOWN and data.startswith('PTP Property'):
				changed = self.configurationFromCamera()
				if not changed:
					continue
				changedProperties = [self.getPropertyByName(widget['name']) for widget in changed]
				event = interface.PropertiesChangedEvent(self,changedProperties)
				self.propertiesChanged.emit(event)
			elif eventType == constants.GPEvent.FILE_ADDED:
				path,fn = data
				tempFn = os.path.join(tempfile.gettempdir(),tempfile.gettempprefix()+fn)
				self.camera.downloadFile(path,fn,tempFn)
				self.capturedAuxFiles.append(tempFn)
			elif eventType == constants.GPEvent.CAPTURE_COMPLETE:
				e = interface.CaptureCompleteEvent(self,data=self.capturedData,auxFiles=self.capturedAuxFiles)
				self.capturedAuxFiles = []
				self.captureComplete.emit(e)
				
				
	def startViewfinder(self):
		if 'output' in self.configWidgets and 'LCD' in self.configWidgets['output']['choices'] and self.configWidgets['output']['value'] != 'LCD': 
			self.configWidgets['output']['value'] = 'LCD'
			self.configWidgets['output']['changed'] = True
			self.configurationToCamera()
		if self.viewfinderThread and not self.viewfinderThread.stopped:
			return 
		self.viewfinderThread = ViewfinderCaptureThread(self)
		self.viewfinderThread.start() 


	def stopViewfinder(self):
		if self.viewfinderThread:
			self.viewfinderThread.stopped = True


	def isViewfinderStarted(self):
		if self.viewfinderThread and not self.viewfinderThread.stopped:
			return True
		else:
			return False 

	#
	# Non-interface
	#
	
	def configurationToCamera(self):
		n = 0
		toClear = []
		for section in self.config['children']:
			for widget in section['children']:
				n += 1
				if widget['changed']:
					toClear.append(widget)
		if toClear:
			s = ', '.join(['%s (%s)=%r'%(i['name'],i['label'],i['value']) for i in toClear])
			try:
				self.camera.setConfiguration(self.config)
			except:
				log.logException('Failed setting camera properties %s'%s,log.WARNING)
			else:
				log.debug('Successfully changed camera properties %s'%s)
				
			for i in toClear:
				i['changed'] = False
			
				
	def configurationFromCamera(self):
		old = dict()
		old.update(self.configWidgets)
		changed = []
		
		self.config = self.camera.getConfiguration()
		for section in self.config['children']:
			for widget in section['children']:
				self.configWidgets[widget['name']] = widget
				if (widget['name'] in old) and (widget['value'] != old[widget['name']]['value']):
					changed.append(widget)
		
		if changed:
			changedString = '\n        '.join(['%s (%s)=%r'%(i['name'],i['label'],i['value']) for i in changed])
		
		return changed
	
	
	def getWidget(self,id):
		return self.configWidgets[id]
	
	
	def createProperties(self):
		self.nameToProperty = {}	
		for section in self.config['children']:
			for widget in section['children']:
				if widget['type'] == constants.GPWidget.BUTTON:
					property = GPhotoCameraButton(self,widget['name']) 
				else: 
					property = GPhotoCameraValueProperty(self,widget['name'])
				property.section = section['label']
				self.properties.append(property)
				self.nameToProperty[widget['name']] = property
	
		for property in self.api.propertyClasses:
			self.properties.append(property(self,None))
	
	
	def getPropertyByName(self,name):
		return self.nameToProperty[name]
	
	
	def saveSettings(self):
		saved = []
		if 'config' in self.settings:
			savedProperties = [i['control'] for i in self.settings.config.savedProperties]
			for name in savedProperties:
				if name not in self.configWidgets:
					continue
				value = self.configWidgets[name]['value']
				saved.append((name,value))
		self.settings.savedProperties = saved
		
		
	def restoreProperties(self):
		if 'savedProperties' not in self.settings:
			return
		saved = list(self.settings.savedProperties)
		saved.reverse()
		for name,value in saved:
			if name not in self.configWidgets:
				log.warning('could not find property %s to restore'%name)
				continue
			self.configWidgets[name]['value'] = value
			self.configWidgets[name]['changed'] = True
		
	
	
	
class ViewfinderCaptureThread(threading.Thread):
	
	def __init__(self,camera):
		super(ViewfinderCaptureThread,self).__init__()
		self.camera = camera
		self.stopped = False
		
	def run(self):
		while 1:
			if self.stopped:
				break
			
			data = self.camera.camera.capturePreview()
			e = interface.ViewfinderFrameEvent(self.camera,data=data)
			self.camera.viewfinderFrame.emit(e)
		
	def stop(self):
		self.stopped = True

		
WidgetToControlType = {
	constants.GPWidget.WINDOW: None,
	constants.GPWidget.SECTION: None,
	constants.GPWidget.TEXT: interface.ControlType.LineEdit,
	constants.GPWidget.RANGE: interface.ControlType.Slider,
	constants.GPWidget.TOGGLE: interface.ControlType.Checkbox,
	constants.GPWidget.RADIO: interface.ControlType.Combo,
	constants.GPWidget.MENU: interface.ControlType.Combo,
	constants.GPWidget.BUTTON: interface.ControlType.Button,
	constants.GPWidget.DATE: interface.ControlType.LineEdit, ### TODO: Add a date field
}

WidgetNameToControlType = {
	'focuslock': interface.ControlType.TwinButton,
}

def cached(f):
	def withCache(*args,**kargs):
		self = args[0]
		if f.__name__ not in self._cache:
			rc = f(*args,**kargs)
			self._cache[f.__name__] = rc
		return self._cache[f.__name__]
	return withCache


		
class GPhotoCameraValueProperty(interface.CameraValueProperty):
	
	def __init__(self,camera,widgetId):
		super(GPhotoCameraValueProperty,self).__init__()
		self.camera = camera
		self.widgetId = widgetId
		self.name = self.widget['label']

	def getName(self):
		return self.name
	
	def getIdent(self):
		return self.widget['name']

	def getControlType(self):
		if self.widget['name'] in WidgetNameToControlType:
			return WidgetNameToControlType[self.widget['name']]
		else:
			return WidgetToControlType[self.widget['type']]
		
	def getRawValue(self):
		return self.widget['value']
	
	def setRawValue(self,v):
		if self.widget['value'] != v:
			self.widget['value'] = v
			self.widget['changed'] = True
			self.camera.configurationToCamera()
			self.camera.configurationFromCamera()
		
	def rawToDisplay(self,rawValue):
		if self.widget['type'] == constants.GPWidget.TOGGLE:
			if rawValue == 0:
				return None
			elif rawValue == 1:
				return True
			elif rawValue == 2:
				return True
			else:
				log.warn('Unsupported raw value %r for camera toggle control %s'%(rawValue,self.getName()))
		else:
			return rawValue
		
	def displayToRaw(self,displayValue):
		if self.widget['type'] == constants.GPWidget.TOGGLE:
			if displayValue is None:
				return None
			elif displayValue is False:
				return 0
			elif displayValue is True:
				return 1
			else:
				log.warn('Unsupported display value %r for camera toggle control %s'%(displayValue,self.getName()))
		return displayValue
		
	def getMin(self):
		return self.widget['range'][0]
	
	def getMax(self):
		return self.widget['range'][1]
	
	def getStep(self):
		return self.widget['range'][2]
	
	def getPossibleValues(self):
		return [(i,i) for i in self.widget['choices']]
	
	def isSupported(self):
		return True
	
	def isReadOnly(self):
		return self.widget['readonly']
	
	def getSection(self):
		return self.section
	
	#
	# Non-interface
	#
	def getWidget(self):
		return self.camera.getWidget(self.widgetId)
	widget = property(getWidget)
	


class GPhotoCameraButton(GPhotoCameraValueProperty):

	def getRawValue(self):
		return True

	def go(self):
		self.setRawValue(1)
		self.camera.configurationFromCamera()
		

API.propertyClasses = []