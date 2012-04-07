from ctypes import *
from .defines import *
from .properties import properties
import time
import os.path



class Sequential(object):

	def __init__(self,address):
		self.address = address
		self.ptr = address
	
	
	def read(self,cType):
		v = cType.from_address(self.ptr) 
		self.ptr += sizeof(v)
		return v.value
	
	
	def readArray(self,valueCType=c_uint16,indexCType=c_uint32): 
		v = indexCType.from_address(self.ptr)
		self.ptr += sizeof(v)
		v = (valueCType * v.value).from_address(self.ptr) 
		self.ptr += sizeof(v)
		return [i for i in v]


	def readString(self,indexCType=c_uint8,valueCType=c_wchar): 
		v = indexCType.from_address(self.ptr)
		self.ptr += sizeof(v)
		v = (valueCType * v.value).from_address(self.ptr) 
		self.ptr += sizeof(v)
		return v.value


	def write(self,value,cType):
		v = cType.from_address(self.ptr)
		v.value = value
		self.ptr += sizeof(v)


	def writeString(self,s):
		self.write(len(s),c_uint8)
		self.write((c_wchar*len(s)),s)

	
	def writeArray(self,l,valueCType=c_uint16,indexCType=c_uint32):
		self.write(len(l),indexCType)
		v = (valueCType * len(l)).from_address(self.ptr)
		for index,value in enumerate(l):
			v[index] = value
		
		


class SDK(object):
	
	
	def __init__(self,dllpath=None):
		
		self.closed = False

		self.cameras = []
		
		if dllpath:
			dllname = os.path.join(dllpath,'PRSDK.dll')
		else:
			dllname = 'PRSDK.dll'
		self.dll = windll.LoadLibrary(dllname)
		rc = self.dll.PR_StartSDK()
		if rc: raise SDKError(rc)
		
		self.devlist = DeviceList()
		bSize = c_ulong()
		bSize.value = sizeof(self.devlist)
		
		rc = self.dll.PR_GetDeviceList(pointer(bSize),pointer(self.devlist))
		if rc: raise SDKError(rc)
		
		for i in range(self.devlist.NumList):
			d = self.devlist.DeviceInfo[i]
			camera = Camera(sdk=self,deviceInfo=d)
			self.cameras.append(camera)


	def getDLLVersions(self):
		
		info = DllsVerInfo()
		bSize = c_ulong()
		bSize.value = sizeof(info)

		rc = self.dll.PR_GetDllsVersion(pointer(bSize),pointer(info))
		if rc: raise SDKError(rc)
		
		for i in range(info.Entry):
			x = info.VerInfo[i]
			print('Module name: %r'%x.ModuleName)
			print('Version: %r'%x.Version)
			print()


	def close(self):
		for camera in self.cameras:
			camera.close()
		rc = self.dll.PR_FinishSDK()
		if rc: raise SDKError(rc)
		self.closed = True

		
	def __del__(self):
		if not self.closed:
			self.close()



def readArray(base,size,ptr):
	items = (size-10)//sizeof(base)
	return (base * items).from_address(ptr)
	
def readString(size,ptr):
	return (c_wchar * size).from_address(ptr)


class CameraProperty(object):

	DATA_TYPES = {
		0x0001: c_byte,
		0x0002: c_ubyte,
		0x0003: c_short,
		0x0004: c_ushort,
		0x0005: c_int,
		0x0006: c_uint,
		0x0007: c_longlong,
		0x0008:	c_ulonglong,
	}

	
	def makeReader(self,sequential):
		if self.dataType == 0xFFFF:
			reader = lambda: sequential.readString()
		elif self.dataType & 0x4000:
			cType = self.DATA_TYPES[self.dataType ^ 0x4000] 
			reader = lambda: sequential.readArray(cType)
		else:
			cType = self.DATA_TYPES[self.dataType] 
			reader = lambda: sequential.read(cType)
		return reader


	def makeWriter(self,sequential):
		if self.dataType == 0xFFFF:
			reader = lambda v: sequential.writeString(v)
		elif self.dataType & 0x4000:
			cType = self.DATA_TYPES[self.dataType ^ 0x4000] 
			reader = lambda v: sequential.writeArray(v,cType)
		else:
			cType = self.DATA_TYPES[self.dataType] 
			reader = lambda v: sequential.write(v,cType)
		return reader


	def getValue(self):
		bSize = c_ulong()
		propValue = DevicePropValue()	
		bSize.value = sizeof(propValue)
		
		rc = self.dll.PR_GetDevicePropValue(self.camera.handle,self.propCode,pointer(bSize),pointer(propValue))
		if rc: raise SDKError(rc)
			
		r = Sequential(addressof(propValue))
		reader = self.makeReader(r)
		
		self.value = reader() 
		
		return self.value
		
	
	def setValue(self,value):
		bSize = c_ulong()
		propValue = DevicePropValue()	
		bSize.value = sizeof(propValue)

		r = Sequential(addressof(propValue))
		self.makeWriter(r)(value)
		
		rc = self.dll.PR_SetDevicePropValue(self.camera.handle,self.propCode,bSize,pointer(propValue))
		if rc: raise SDKError(rc)
		
		self.value = value


	def update(self):
		self.getValue()
	
	
	def __init__(self,camera,propDesc):

		self.camera = camera
		self.sdk = camera.sdk
		self.dll = camera.sdk.dll

			
		r = Sequential(addressof(propDesc))
		
		self.propCode = r.read(c_uint16)
		self.dataType = r.read(c_uint16)

		pc = self.propCode
		if pc in DevicePropCode:
			self.name = DevicePropCode.getName(pc)
			self.description = DevicePropCode.getDescription(pc)
		else:
			self.name = ''
			self.description = ''
		if pc in properties:
			self.description = properties.getDescription(pc)

		getSet = r.read(c_uint8)
		self.readOnly = not getSet
		
		if self.dataType == 0:
			self.supported = False
			return
		else:
			self.supported = True
		
		reader = self.makeReader(r)
		
		self.factoryDefault = reader()
		self.value = reader()
		
		self.formFlag = r.read(c_uint8)
		
		if self.formFlag == 1:
			self.min = reader()
			self.max = reader()
			self.step = reader()
		elif self.formFlag == 2:
			items = r.read(c_uint16)
			self.values = []
			for i in range(items):
				self.values.append(reader())
		elif self.formFlag:
			raise Exception('Invalid value 0x%X for formFlag'%self.formFlag)


	def pformatValue(self,value):
		if self.name in properties:
			return '0x%X=%s'%(value,properties.getValueName(self.name,value))
		else:
			return repr(value)
		
		
	def pformat(self,short=False,indent=''):
		if short:
			return '<%s 0x%X %s %s>'%(self.__class__.__name__,self.propCode,self.name,self.pformatValue(self.value))
		else:
			s = ''
			s += indent + '<%s 0x%X %s>\n'%(self.__class__.__name__,self.propCode,self.name)
			if self.description:
				s += indent + '    description: %s'%self.description
			if self.readOnly:
				s += indent + '    readOnly'
			s += indent + '  factoryDefault: %s'%self.pformatValue(self.factoryDefault)
			s += indent + '  value: %s'%self.pformatValue(self.value)
			if hasattr(p,'values'):
				s += indent + '  values: %s'%(', '.join([self.pformatValue(i) for i in self.values]))
			if hasattr(p,'min'):
				s += indent + '  min: %s'%self.pformatValue(self.min)
				s += indent + '  max: %s'%self.pformatValue(self.max)
				s += indent + '  step: %r'%self.step
			return s
		
	def __repr__(self):
		return self.pformat(short=True)



class ReleaseInfo(object):
	def __init__(self,
		retrieveImage=True,
		retrieveThumb=False,
		imageFileName=None,
		thumbFileName=None,
		keepImageBuffer=True,
		keepThumbBuffer=False,
		imageCompleteCallback=None,
		thumbCompleteCallback=None,
		imageProgressCallback=None,
		chunkSize=1024*1024,
	):
		self.imageFileName = imageFileName
		self.thumbFileName = thumbFileName
		self.retrieveImage = retrieveImage or imageFileName
		self.retrieveThumb = retrieveThumb or thumbFileName
		self.keepImageBuffer = keepImageBuffer
		self.keepThumbBuffer = keepThumbBuffer
		self.imageCompleteCallback = imageCompleteCallback
		self.thumbCompleteCallback = thumbCompleteCallback
		self.imageProgressCallback = imageProgressCallback
		self.chunkSize = chunkSize
		
		self.doneImage = False
		self.doneThumb = False
		self.imageBuffer = None
		self.thumbBuffer = None
		self.fImage = None
		self.fThumb = None
		self.percentDone = 0
		self.bytesDone = 0
		
		if self.imageFileName:
			self.fImage = open(self.imageFileName,'wb')
		if self.thumbFileName:
			self.fThumb = open(self.thumbFileName,'wb')
		if self.keepImageBuffer:
			self.imageBuffer = b''
		if self.keepThumbBuffer:
			self.thumbBuffer = b''
		

	def handleEvent(self,progress,isThumb):
		progress = progress.contents
		status = progress.Status
		message = progress.Message
		percent = progress.PercentComplete
		offset = progress.Offset
		length = progress.Length
		
		self.percentDone = percent
		self.bytesDone = offset + length
		
		if isThumb:
			f = self.fThumb
			keepBuffer = self.keepThumbBuffer
			completeCallback = self.thumbCompleteCallback
		else:
			f = self.fImage
			keepBuffer = self.keepImageBuffer
			completeCallback = self.imageCompleteCallback
		
		if message == ProgressMessage.TERMINATION:
			if f:
				f.close()
				if isThumb: self.fThumb = None 
				else: self.fImage = None
			if isThumb: self.doneThumb = True
			else: self.doneImage = True
			if completeCallback:
				completeCallback(self)
		elif length:
			data = string_at(progress.Data,length)
			if f:
				f.write(data)
			if keepBuffer:
				if isThumb: self.thumbBuffer += data
				else: self.imageBuffer += data
			if not isThumb and self.imageProgressCallback:
				self.imageProgressCallback(self)


	def __del__(self):
		if self.fImage: self.fImage.close()
		if self.fThumb: self.fThumb.close()

		

class Camera(object):
	
	EVENT2HANDLER = {
		EventCode.DEVICE_PROP_CHANGED                     : 'onDevicePropChanged',
		EventCode.CAPTURE_COMPLETE                        : 'onCaptureComplete',
		EventCode.SHUTDOWN_CF_GATE_WAS_OPENED             : 'onShutdownCFGateWasOpened',
		EventCode.RESET_HW_ERROR                          : 'onResetHWError',
		EventCode.ABORT_PC_EVF                            : 'onAbortPCEVF',
		EventCode.ENABLE_PC_EVF                           : 'onEnablePCEVF',
		EventCode.FULL_VIEW_RELEASED                      : 'onFullViewReleased',
		EventCode.THUMBNAIL_RELEASED                      : 'onThumbnailReleased',
		EventCode.CHANGE_BATTERY_STATUS                   : 'onChangeBatteryStatus',
		EventCode.PUSHED_RELEASE_SW                       : 'onPushedReleaseSW',
		EventCode.RC_PROP_CHANGED                         : 'onPropChanged',
		EventCode.RC_ROTATION_ANGLE_CHANGED               : 'onRotationAngleChanged',
		EventCode.RC_CHANGED_BY_CAM_UI                    : 'onRCChangedByCamUI',
		EventCode.SHUTDOWN                                : 'onShutdown',
	}
	
	def __init__(self,sdk,deviceInfo):
		
		self.closed = False
		self.initiatedRC = False
		self.initiatedViewfinder = False
		
		self.sdk = sdk
		self.dll = sdk.dll

		self.name = deviceInfo.DeviceInternalName
		self.model = deviceInfo.ModelName
		self.generation = int(deviceInfo.Generation)
		self.modelId = int(deviceInfo.ModelID)
				
		self.handle = c_ulong()
		self.handle.value = 1 
		
		# Create the object
		rc = self.dll.PR_CreateCameraObject(pointer(deviceInfo),pointer(self.handle))
		if rc: raise SDKError(rc)
		
		# Connect to the camera
		rc = self.dll.PR_ConnectCamera(self.handle)
		if rc: raise SDKError(rc)

		# Set up event callbacks
		self.cEventCallback = EventCallback(self.eventCallback)
		rc = self.dll.PR_SetEventCallBack(self.handle,0,self.cEventCallback)
		if rc: raise SDKError(rc)
		
		# Update device information and available properties
		self.getDeviceInfo()
		self.getProperties()

		# Set up a callback pointer we can use later when getting image data
		self.cFileDataCallback = FileDataCallback(self.fileDataCallback)
		
		self.cViewfinderCallback = ViewfinderCallback(self.viewfinderCallback)
	
	
	def getDeviceInfo(self):
		
		info = DeviceInfo()
		bSize = c_ulong()
		bSize.value = sizeof(info)

		# Get device information
		rc = self.dll.PR_GetDeviceInfo(self.handle,pointer(bSize),pointer(info))
		if rc: raise SDKError(rc)
		
		r = Sequential(addressof(info))

		self.standardVersion = r.read(c_uint16)
		self.vendorExtensionId = r.read(c_uint32)
		self.vendorExtensionVersion = r.read(c_uint16)
		self.vendorExtensionDesc = r.readString()
		self.functionalMode = r.read(c_uint16)
		self.operationCodes = r.readArray()
		self.eventCodes = r.readArray()
		self.propCodes = r.readArray()
		self.captureFormats = r.readArray()
		self.imageFormats = r.readArray()
		self.manufacturer = r.readString()
		self.model = r.readString()
		self.deviceVersion = r.readString()
		self.serialNumber = r.readString()


	def pformat(self,short=False,indent=''):
		if short:
			return '<%s %s %s>'%(self.__class__.__name__,self.model,self.serialNumber)
		else:
			s = ''
			s += indent + '<%s %s %s>\n'%(self.__class__.__name__,self.model,self.serialNumber)
			s += indent + '  events: %s\n'%(', '.join([EventCode[i] for i in self.eventCodes if i in EventCode]))
			s += indent + '  properties: %s\n'%(', '.join([DevicePropCode[i] for i in self.propCodes if i in DevicePropCode]))
			s += indent + '  capture formats: %s\n'%(', '.join([EventCode[i] for i in self.eventCodes if i in EventCode]))
			s += indent + '  operation codes: %s\n'%(', '.join([OperationCode[i] for i in self.operationCodes if i in OperationCode]))
			return s


	def getProperties(self):
		
		self.properties = {}
		
		bSize = c_ulong()
		propDesc = DevicePropDesc()	
		
		for propCode in self.propCodes:
			bSize.value = sizeof(propDesc)
			rc = self.dll.PR_GetDevicePropDesc(self.handle,propCode,pointer(bSize),pointer(propDesc))
			if rc: raise SDKError(rc)
			
			prop = CameraProperty(camera=self,propDesc=propDesc)
			self.properties[prop.name or prop.propCode] = prop


	def updateSingleProperty(self,propCode):
		if isinstance(propCode,str):
			propCode = DevicePropCode[propCode]
		bSize = c_ulong()
		propDesc = DevicePropDesc()	
		bSize.value = sizeof(propDesc)
		rc = self.dll.PR_GetDevicePropDesc(self.handle,propCode,pointer(bSize),pointer(propDesc))
		if rc: raise SDKError(rc)
		
		prop = CameraProperty(camera=self,propDesc=propDesc)
		self.properties[prop.name or prop.propCode] = prop
		return property
			
			
	def startRemote(self,quick=False):	
		""" Put the camera in 'release control' mode (extends the lens etc.) """

		if self.initiatedRC:
			return
		
		rc = self.dll.PR_InitiateReleaseControl(self.handle)
		if rc: raise SDKError(rc)
		self.initiatedRC = True 

		if not quick:
			# Update available properties
			self.getDeviceInfo()
			self.getProperties()


	def stopRemote(self,quick=False):
		""" Stop release control mode (retract the lens etc.) """

		if not self.initiatedRC:
			return

		rc = self.dll.PR_TerminateReleaseControl(self.handle)
		if rc: raise SDKError(rc)
		self.initiatedRC = False

		if not quick:
			# Update available properties and events
			self.getDeviceInfo()
			self.getProperties()


	def startViewfinder(self,callback):
		"""
		Callback function is called with each viewfinder frame with one argument which is a string of JPEG bytes
		"""
		
		self.applicationVFCallback = callback
			
		if self.initiatedViewfinder:
			return
		
		if not self.initiatedRC:
			self.startRemote()
			
		rc = self.dll.PR_RC_StartViewFinder(self.handle,0,self.cViewfinderCallback)
		if rc: raise SDKError(rc)
		
		self.initiatedViewfinder = True


	def stopViewfinder(self):	
		if not self.initiatedViewfinder:
			return
			
		rc = self.dll.PR_RC_TermViewFinder(self.handle)
		if rc: raise SDKError(rc)
		self.initiatedViewfinder = False


	def viewfinderCallback(self,cameraHandle,context,size,dataPointer):
		self.vfData = bytes(string_at(dataPointer,size))
		self.applicationVFCallback(self.vfData)
		return 0


	def reset_AE_AF_AWB(self,AF=False,AE=False,AWB=False):
		if not self.initiatedViewfinder:
			raise Exception('Only works in Viewfinder mode')

		flag = 0
		if AF:
			flag |= AfAeResetFlag.AE
		if AE:
			flag |= AfAeResetFlag.AF
		if AWB:
			flag |= AfAeResetFlag.AWB
		
		rc = self.dll.PR_RC_DoAeAfAwb(self.handle,flag)
		if rc: raise SDKError(rc)


	def lockFocus(self):
		rc = self.dll.PR_RC_FocusLock(self.handle)
		if rc: raise SDKError(rc)

		
	def unlockFocus(self):
		rc = self.dll.PR_RC_FocusUnlock(self.handle)
		if rc: raise SDKError(rc)

		
	def release(self,**kargs):

		self.releaseInfo = ReleaseInfo(**kargs)

		rc = self.dll.PR_RC_Release(self.handle)
		if rc: raise SDKError(rc)

		if self.releaseInfo.retrieveImage:
			objectHandle = 2
			rc = self.dll.PR_RC_GetReleasedData(self.handle,objectHandle,EventCode.FULL_VIEW_RELEASED,self.releaseInfo.chunkSize,0,self.cFileDataCallback)
			if rc: raise SDKError(rc)
			
		if self.releaseInfo.retrieveThumb:
			objectHandle = 2
			rc = self.dll.PR_RC_GetReleasedData(self.handle,objectHandle,EventCode.THUMB_VIEW_RELEASED,self.releaseInfo.chunkSize,1,self.cFileDataCallback)
			if rc: raise SDKError(rc)
		

	def eventCallback(self,handle,context,data):
		"""
		Generic event callback function which dispatched events to the right self.on... handlers (see self.EVENT_HANDLERS)
		"""
		
		# Unpack the data structure and the parameters to pass to the event handler proper
		data = Sequential(data)
		length = data.read(c_uint32)
		reserved_containerType = data.read(c_uint16)
		eventCode = data.read(c_uint16)
		transactionId = data.read(c_uint32)
		nParameters = (length - 12) // 4
		parameters = []
		for i in range(nParameters):
			parameters.append(data.read(c_uint32))
			
		#print '*event -- 0x%X %s %s'%(eventCode,EventCode.getName(eventCode),EventCode.getDescription(eventCode))
		#print '  ',parameters
		
		handlerName = self.EVENT2HANDLER[eventCode]
		
		if hasattr(self,handlerName):
			handler = getattr(self,handlerName)
			rc = handler(*parameters)
			if rc is not None:
				return rc
		
		return 0

	
	def fileDataCallback(self,handle,objectHandle,context,progress):
		self.releaseInfo.handleEvent(progress,context)
		return 0
		

	def close(self):
		if self.closed:
			return
		if self.initiatedViewfinder:
			self.stopViewfinder()
		if self.initiatedRC:
			rc = self.dll.PR_TerminateReleaseControl(self.handle)
			if rc: raise SDKError(rc)
		rc = self.dll.PR_ClearEventCallBack(self.handle)
		if rc: raise SDKError(rc)
		rc = self.dll.PR_DisconnectCamera(self.handle)
		if rc: raise SDKError(rc)
		rc = self.dll.PR_DestroyCameraObject(self.handle)
		if rc: raise SDKError(rc)
		self.closed = True


	def __del__(self):
		if not self.closed:
			self.close()


	def __repr__(self):
		return self.pformat(short=True)
	
	
	def __setitem__(self,k,v):
		for i in self.properties.values():
			if i.name == k or i.propCode == k:
				i.setValue(v)
				return


	def __getitem__(self,k):
		for i in self.properties.values():
			if i.name == k or i.propCode == k:
				return i.getValue()

	

if __name__ == '__main__':
	
	sdk = SDK()

	if sdk.cameras:
		camera = sdk.cameras[0]

		for p in camera.properties.values():
			print(p.pformat(short=True))
			
		print()
		print()
		camera.startRemote()
		
		for p in camera.properties.values():
			print(p.pformat(short=True))
		
		camera.startViewfinder(lambda data:None)
		time.sleep(1.0)
		camera.release(imageFileName='test.jpg')
		time.sleep(1.0)
		camera.stopViewfinder()
		
	sdk.close()