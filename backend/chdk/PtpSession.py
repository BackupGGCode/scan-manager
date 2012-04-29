# Based on code from the pyptp project (http://code.google.com/p/pyptp/) 

from PtpAbstractTransport import PtpRequest, PtpResponse
import PtpValues
import struct


class PtpUnpacker:
	
	def __init__(self, raw):
		self.raw = raw
		self.offset = 0
		
		if struct.pack('<h', 1) == struct.pack('=h', 1):
			self.endian = "L"
		else:
			self.endian = "B"

	def unpack(self, fmt):
		fmtsize = struct.calcsize(fmt)
		
		result = struct.unpack(fmt, self.raw[self.offset:self.offset + fmtsize])
		self.offset += fmtsize
		return result

	def unpack_string(self):
		strLen = ord(self.raw[self.offset])
		self.offset += 1
		
		result = self.raw[self.offset:self.offset + (strLen * 2)].decode('UTF-16-LE')
		self.offset += strLen * 2
		if result[-1:] == '\0':
			result = result[:-1]
		return result
	
	def unpack_array(self, fmt):
		(arrayCount, ) = struct.unpack("<I", self.raw[self.offset:self.offset + 4])
		self.offset += 4
		
		fmtsize = struct.calcsize(fmt)
		result = struct.unpack("<%i%s" % (arrayCount, fmt), self.raw[self.offset:self.offset + (fmtsize * arrayCount)])
		self.offset += arrayCount * fmtsize
		return result
	
	def convert_endian(self, bytes):
		if self.endian == "L":
			return bytes[::-1]
		else:
			return bytes

	def decode_uint128(self, bytes):
		return reduce(lambda acc,v: (acc << 8) | (v & 0xff), self.convert_endian(bytes))

	def decode_int128(self, bytes):
		tmp = reduce(lambda acc,v: (acc << 8) | (v & 0xff), self.convert_endian(bytes))
		if tmp & 2**127:
			tmp = -(((~tmp)+1) & ((2**128)-1))
		return tmp

	def unpack_simpletype(self, is_array, fmt):
		if not is_array:
			if fmt == "_INT128":
				return self.decode_int128(self.unpack_array("16B"))
			
			elif fmt == "_UINT128":
				return self.decode_uint128(self.unpack_array("16B"))

			elif fmt == "_STR":
				return self.unpack_string()
			
			else:
				return self.unpack("<" + fmt)[0]
			
		else:
			if fmt == "_INT128":
				tmp = [self.decode_int128(item) for item in self.unpack_array("16B")]

			elif fmt == "_UINT128":
				tmp = [self.decode_uint128(item) for item in self.unpack_array("16B")]
				
			elif fmt == "_STR":
				(arrayCount, ) = struct.unpack("<I", self.raw[self.offset:self.offset + 4])
				self.offset += 4
				
				result = ()
				while arrayCount:
					result += self.unpack_string()
					arrayCount -= 1
				return result
			
			else:
				return self.unpack_array(fmt)


class PtpPacker:
	
	def __init__(self):
		self.raw = ""
		
		if struct.pack('<h', 1) == struct.pack('=h', 1):
			self.endian = "L"
		else:
			self.endian = "B"

	def pack(self, fmt, *params):
		self.raw += struct.pack(fmt, *params)

	def pack_string(self, string):
		self.raw += struct.pack("<B", len(string) + 1)
		self.raw += string.encode('UTF-16-LE')
		self.raw += u'\u0000'
	
	def pack_array(self, fmt, data):
		self.raw += struct.pack("<I", len(data))
		self.raw += struct.pack("<%i%s" % (len(data), fmt), data)
	
	def convert_endian(self, bytes):
		if self.endian == "L":
			return bytes[::-1]
		else:
			return bytes

	def encode_uint128(self, value):
		tmp = ""
		for i in range(0, 16):
			tmp += chr(value & 0xff)
			value >>= 8
		return self.convert_endian(tmp)

	def encode_int128(self, value):
		return self.encode_uint128(self, value)

	def pack_simpletype(self, is_array, fmt, value):
		if not is_array:
			if fmt == "_INT128":
				raw += self.encode_int128(value)
			
			elif fmt == "_UINT128":
				raw += self.encode_uint128(value)

			elif fmt == "_STR":
				self.pack_string(value)
			
			else:
				self.pack("<" + fmt, value)
			
		else:
			if fmt == "_INT128":
				self.pack_array("16B", [self.encode_int128(item) for item in value])

			elif fmt == "_UINT128":
				self.pack_array("16B", [self.encode_uint128(item) for item in value])

			elif fmt == "_STR":
				self.pack("<I", len(value))
				for str in value:
					self.pack_string(str)

			else:
				return self.pack_array(fmt, value)



class PtpDeviceInfo:
	
	def __init__(self, raw):
		unpacker = PtpUnpacker(raw)

		(self.StandardVersion, self.VendorExtensionID, self.VendorExtensionVersion) = unpacker.unpack("<HIH")
		self.VendorExtensionDesc = unpacker.unpack_string()
		(self.FunctionalMode, ) = unpacker.unpack("<H")
		self.OperationsSupported = unpacker.unpack_array("H")
		self.EventsSupported = unpacker.unpack_array("H")
		self.DevicePropertiesSupported = unpacker.unpack_array("H")
		self.CaptureFormats = unpacker.unpack_array("H")
		self.ImageFormats = unpacker.unpack_array("H")
		self.Manufacturer = unpacker.unpack_string()
		self.Model = unpacker.unpack_string()
		self.DeviceVersion = unpacker.unpack_string()
		self.SerialNumber = unpacker.unpack_string()		


class PtpStorageInfo:
	
	def __init__(self, raw):
		unpacker = PtpUnpacker(raw)
		
		(self.StorageType, self.FilesystemType, self.AccessCapability, self.MaxCapacity, self.FreeSpaceInBytes, self.FreeSpaceInImages) = unpacker.unpack("<HHHQQI")
		self.StorageDescription = unpacker.unpack_string()
		self.VolumeLabel = unpacker.unpack_string()



class PtpObjectInfo:
	
	def __init__(self, raw):
		unpacker = PtpUnpacker(raw)
		
		(self.StorageId, self.ObjectFormat, self.ProtectionStatus, self.ObjectCompressedSize, 
		 self.ThumbFormat, self.ThumbCompressedSize, self.ThumbPixWidth, self.ThumbPixHeight,
		 self.ImagePixWidth, self.ImagePixHeight, self.ImageBitDepth, self.ParentObjectHandle,
		 self.AssociationType, self.AssociationDesc, self.SequenceNumber) = unpacker.unpack("<IHHIHIIIIIIIHII")
		self.Filename = unpacker.unpack_string()
		self.CaptureDate = unpacker.unpack_string()
		self.ModificationDate = unpacker.unpack_string()
		self.Keywords = unpacker.unpack_string()


class PtpDevicePropertyInfo:
	
	def __init__(self, raw):
		unpacker = PtpUnpacker(raw)
		
		(self.PropertyCode, self.DataType, self.GetSet) = unpacker.unpack("<HHB")
		
		(name, (id, is_array, fmt)) = PtpValues.SimpleTypeDetailsById(self.DataType)
		self.FactoryDefaultValue = unpacker.unpack_simpletype(is_array, fmt)
		self.CurrentValue = unpacker.unpack_simpletype(is_array, fmt)
		(form, ) = unpacker.unpack("<B")
		self.MinimumValue = None
		self.MaximumValue = None
		self.StepSize = None
		self.Enumeration = None
		if form == 1:
			self.MinimumValue = unpacker.unpack_simpletype(is_array, fmt)
			self.MaximumValue = unpacker.unpack_simpletype(is_array, fmt)
			self.StepSize = unpacker.unpack_simpletype(is_array, fmt)
		elif form == 2:
			(count, ) = unpacker.unpack("<H")
			self.Enumeration = ()
			while count:
				tmp = unpacker.unpack_simpletype(is_array, fmt)
				self.Enumeration += (tmp, )
				count-=1
 

class PtpSession:
	"Class implementing a session over an underlying PTP transport"
	
	def __init__(self, transport):
		self.transport = transport
		self.sessionid = 0
		self.__transactionid = 0

	def __del__(self):
		"""Cleanup a PtpSession structure (does not delete underlying transport)."""
		
		try:
			self.CloseSession()
		except:
			pass
		
	def NewTransaction(self):
		"""Allocate a new transactionid.
		
		Returns: The new id."""
		
		self.__transactionid += 1
		if self.__transactionid == 0xffffffff:
			self.__transactionid = 1
		return self.__transactionid

	def CheckForEvent(self, timeout=None):
		"""Check if the device has sent an event.
		
		Arguments:
		timeout -- If set, timeout in milliseconds, or None to wait forever.
		
		Returns: 
		PtpEvent instance, or None if no event was received."""
		
		return self.transport.check_ptp_event(self.sessionid, timeout)
	
	def OpenSession(self):
		"""Open a new session to a PTP device."""
		
		self.sessionid = self.transport.NewSession()
		self.__transactionid = 0
		ptp_request = PtpRequest(PtpValues.StandardOperations.OPEN_SESSION, 0, 0, (self.sessionid, ))
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)

	def CloseSession(self):
		"""Close the PTP session."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.CLOSE_SESSION, self.sessionid, self.NewTransaction())
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)

	def GetDeviceInfo(self):
		"""Get Device info from a PTP device.
		
		Returns: A PtpDeviceInfo instance."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_DEVICE_INFO, self.sessionid, self.NewTransaction())
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return PtpDeviceInfo(rx[1])

	def GetStorageIDs(self):
		"""Get list of storages a PTP device.
		
		Returns: A tuple of IDs."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_STORAGE_IDS, self.sessionid, self.NewTransaction())
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		
		unpacker = PtpUnpacker(rx[1])
		return unpacker.unpack_array("I")
	
	def GetStorageInfo(self, storageId):
		"""Get information about a storage on a PTP device.
		
		Returns: A PtpStorageInfo instance."""
	
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_STORAGE_INFO, self.sessionid, self.NewTransaction(), (storageId, ))
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return PtpStorageInfo(rx[1])

	def FormatStore(self, storageId, fsType=None):
		"""Format a store on a PTP device.
		
		Returns:"""
		
		params = (storageId, )
		if fsType != None:
			params += (fsType, )
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.FORMAT_STORE, self.sessionid, self.NewTransaction(), params)
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=False)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)

	def GetDevicePropValue(self, propertyId, is_array, fmt):
		"""Get the value of a device property.
		
		Returns: The value ."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_DEVICE_PROP_VALUE, self.sessionid, self.NewTransaction(), (propertyId,))
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)

		unpacker = PtpUnpacker(rx[1])
		return unpacker.unpack_simpletype(is_array, fmt)

	def SetDevicePropValue(self, propertyId, is_array, fmt, value):
		"""Set the value of a device property.
		
		Returns:"""
		
		packer = PtpPacker()
		packer.pack_simpletype(is_array, fmt, value)

		ptp_request = PtpRequest(PtpValues.StandardOperations.SET_DEVICE_PROP_VALUE, self.sessionid, self.NewTransaction(), (propertyId,))
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, tx_data = packer.raw)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)

	def GetDevicePropInfo(self, propertyId):
		"""Get the description of a device property.
		
		Returns: A string of bytes."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_DEVICE_PROP_DESC, self.sessionid, self.NewTransaction(), (propertyId,))
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return PtpDevicePropertyInfo(rx[1])
	
	def GetNumObjects(self, storageId=0xffffffff, objectFormatId=None, associationId=None):
		"""Get the number of objects.
		
		Returns: The number of objects."""
		
		params = (storageId, )
		if objectFormatId != None:
			params += (objectFormatId, )
		if associationId != None:
			if objectFormatId == None:
				params += (0, )
			params += (associationId, )
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_NUM_OBJECTS, self.sessionid, self.NewTransaction(), params)
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=False)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return ptp_response.params[0]

	def GetObjectHandles(self, storageId=0xffffffff, objectFormatId=None, associationId=None):
		"""Get the object handles.
		
		Returns: Tuple of object handles."""
		
		params = (storageId, )
		if objectFormatId != None:
			params += (objectFormatId, )
		if associationId != None:
			if objectFormatId == None:
				params += (0, )
			params += (associationId, )
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_OBJECT_HANDLES, self.sessionid, self.NewTransaction(), params)
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		
		unpacker = PtpUnpacker(rx[1])
		return unpacker.unpack_array("I")

	def GetObjectInfo(self, objectHandle):
		"""Get information about an object on a PTP device.
		
		Returns: A PtpObjectInfo instance."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_OBJECT_INFO, self.sessionid, self.NewTransaction(), (objectHandle, ))
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=True)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return PtpObjectInfo(rx[1])
	
	def GetObject(self, objectHandle, stream=None):
		"""Get an object on a PTP device.
		
		Returns: A tuple of (object length, and object data (or None if stream was not None))."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_OBJECT, self.sessionid, self.NewTransaction(), (objectHandle, ))
		self.transport.send_ptp_request(ptp_request)
		rx_data = self.transport.get_ptp_data(ptp_request, stream)
		ptp_response = self.transport.get_ptp_response(ptp_request)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return rx_data
	
	def GetThumb(self, objectHandle, stream=None):
		"""Get a thumbnail on a PTP device.
		
		Returns: A tuple of (object length, and object data (or None if stream was not None))."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_THUMB, self.sessionid, self.NewTransaction(), (objectHandle, ))
		self.transport.send_ptp_request(ptp_request)
		rx_data = self.transport.get_ptp_data(ptp_request, stream)
		ptp_response = self.transport.get_ptp_response(ptp_request)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return rx_data

	def GetPartialObject(self, objectHandle, offset=0, count=0xffffffff, stream=None):
		"""Get a partial object on a PTP device.
		
		Returns: A tuple of (object length, and object data (or None if stream was not None))."""
		
		ptp_request = PtpRequest(PtpValues.StandardOperations.GET_PARTIAL_OBJECT, self.sessionid, self.NewTransaction(), (objectHandle, offset, count))
		self.transport.send_ptp_request(ptp_request)
		rx_data = self.transport.get_ptp_data(ptp_request, stream)
		ptp_response = self.transport.get_ptp_response(ptp_request)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		return rx_data

	def DeleteObject(self, objectHandle, objectFormatId=None):
		"""Delete an object from a PTP device.
		
		Returns:"""

		params = (objectHandle, )
		if objectFormatId != None:
			params += (objectFormatId, )

		ptp_request = PtpRequest(PtpValues.StandardOperations.DELETE_OBJECT, self.sessionid, self.NewTransaction(), params)
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=False)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)

	def InitiateCapture(self, storageId=None, objectFormatId=None):
		"""Trigger an image capture.
		
		Returns:"""

		params = ()
		if storageId != None:
			params += (storageId, )
		if objectFormatId != None:
			if len(params) == 0:
				params += (0, )
			params += (objectFormatId, )

		ptp_request = PtpRequest(PtpValues.StandardOperations.INITIATE_CAPTURE, self.sessionid, self.NewTransaction(), params)
		(ptp_response, rx) = self.transport.ptp_simple_transaction(ptp_request, receiving=False)
		if ptp_response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(ptp_response.respcode)
		
	def GetBatteryLevel(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.BATTERY_LEVEL, False, "B")
	
	def GetImageSize(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.IMAGE_SIZE, False, "_STR")
	
	def SetImageSize(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.IMAGE_SIZE, False, "_STR", value)

	def GetCompressionSetting(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.COMPRESSION_SETTING, False, "B")

	def SetCompressionSetting(self, value):
		return self.GetDevicePropValue(PtpValues.StandardProperties.COMPRESSION_SETTING, False, "B", value)

	def GetWhiteBalance(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.WHITE_BALANCE, False, "H")

	def SetWhiteBalance(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.WHITE_BALANCE, False, "H", value)

	def GetFNumber(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.F_NUMBER, False, "H")

	def SetFNumber(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.F_NUMBER, False, "H", value)

	def GetFocalLength(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.FOCAL_LENGTH, False, "L")

	def GetFocusMode(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.FOCUS_MODE, False, "H")

	def GetExposureMeteringMode(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_METERING_MODE, False, "H")

	def SetExposureMeteringMode(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_METERING_MODE, False, "H",  value)

	def GetFlashMode(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.FLASH_MODE, False, "H")

	def SetFlashMode(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.FLASH_MODE, False, "H",  value)

	def GetExposureTime(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_TIME, False, "L")

	def SetExposureTime(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_TIME, False, "L",  value)

	def GetExposureProgramMode(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_PROGRAM_MODE, False, "H")

	def GetExposureIndex(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_INDEX, False, "H")

	def SetExposureIndex(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_INDEX, False, "H", value)

	def GetExposureBiasCompensation(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_BIAS_COMPENSATION, False, "h")

	def SetExposureBiasCompensation(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.EXPOSURE_BIAS_COMPENSATION, False, "h", value)

	def GetDateTime(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.DATE_TIME, False, "_STR")

	def SetDateTime(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.DATE_TIME, False, "_STR", value)

	def GetStillCaptureMode(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.STILL_CAPTURE_MODE, False, "H")

	def SetStillCaptureMode(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.STILL_CAPTURE_MODE, False, "H", value)

	def GetBurstNumber(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.BURST_NUMBER, False, "H")

	def SetBurstNumber(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.BURST_NUMBER, False, "H", value)

	def GetFocusMeteringMode(self):
		return self.GetDevicePropValue(PtpValues.StandardProperties.FOCUS_METERING_MODE, False, "H")

	def SetFocusMeteringMode(self, value):
		return self.SetDevicePropValue(PtpValues.StandardProperties.FOCUS_METERING_MODE, False, "H", value)



class PtpException(Exception):

	def __init__(self, responsecode, vendorId=None):
		self.responsecode = responsecode
		self.vendorId = vendorId
		
	def __repr__(self):
		if self.vendorId:
			return PtpValues.ResponseNameById(self.responsecode, self.vendorId)
		else:
			return self.responsecode



PTP_CHDK_Version = 0
PTP_CHDK_GetMemory = 1
PTP_CHDK_SetMemory = 2
PTP_CHDK_CallFunction = 3
PTP_CHDK_TempData = 4
PTP_CHDK_UploadFile = 5
PTP_CHDK_DownloadFile = 6
PTP_CHDK_ExecuteScript = 7
PTP_CHDK_ScriptStatus = 8
PTP_CHDK_ScriptSupport = 9
PTP_CHDK_ReadScriptMsg = 10
PTP_CHDK_WriteScriptMsg = 11
PTP_CHDK_GetLiveData = 12

PTP_OC_CHDK = 0x9999 

# data types as used by ReadScriptMessage
PTP_CHDK_TYPE_UNSUPPORTED = 0 # type name will be returned in data
PTP_CHDK_TYPE_NIL = 1
PTP_CHDK_TYPE_BOOLEAN = 2
PTP_CHDK_TYPE_INTEGER = 3
PTP_CHDK_TYPE_STRING = 4 # Empty strings are returned with length=0
PTP_CHDK_TYPE_TABLE = 5  # tables are converted to a string by usb_msg_table_to_string, the string may be empty for an empty table

# TempData flags
PTP_CHDK_TD_DOWNLOAD = 0x1  # download data instead of upload
PTP_CHDK_TD_CLEAR = 0x2  # clear the stored data; with DOWNLOAD this means first download, then clear and without DOWNLOAD this means no uploading, just clear

# Script Languages - for execution only lua is supported for now
PTP_CHDK_SL_LUA = 0
PTP_CHDK_SL_UBASIC = 1

# bit flags for script status
PTP_CHDK_SCRIPT_STATUS_RUN = 0x1 # script running
PTP_CHDK_SCRIPT_STATUS_MSG = 0x2 # messages waiting

# bit flags for scripting support
PTP_CHDK_SCRIPT_SUPPORT_LUA = 0x1

# message types
PTP_CHDK_S_MSGTYPE_NONE = 0 # no messages waiting
PTP_CHDK_S_MSGTYPE_ERR = 1 # error message
PTP_CHDK_S_MSGTYPE_RET = 2 # script return value
PTP_CHDK_S_MSGTYPE_USER = 3 # message queued by script
# TODO chdk console data ?

# error subtypes for PTP_CHDK_S_MSGTYPE_ERR and script startup status
PTP_CHDK_S_ERRTYPE_NONE = 0
PTP_CHDK_S_ERRTYPE_COMPILE = 1
PTP_CHDK_S_ERRTYPE_RUN = 2

# message status
PTP_CHDK_S_MSGSTATUS_OK = 0 # queued ok
PTP_CHDK_S_MSGSTATUS_NOTRUN = 1 # no script is running
PTP_CHDK_S_MSGSTATUS_QFULL = 2 # queue is full
PTP_CHDK_S_MSGSTATUS_BADID = 3 # specified ID is not running


class PtpCHDKSession(PtpSession):
	
	def simpleRequest(self,params,fmt=None,args=None,buffer=None,receiving=True,stream=None):
		if type(params) is int:
			params = (params,)
			
		request = PtpRequest(PTP_OC_CHDK, self.sessionid, self.NewTransaction(), params)
		
		if fmt:
			assert args
			packer = PtpPacker()
			packer.pack(fmt,*args)
			tx_data = packer.raw
			if buffer:
				tx_data += buffer
		elif buffer:
			tx_data = buffer
		else:
			tx_data = None

		# send the tx
		rx_data = None
		response = None
		
		self.transport.send_ptp_request(request)
		if tx_data != None:
			self.transport.send_ptp_data(request, tx_data)
		if receiving:
			if stream:
				self.transport.get_ptp_data(request,stream)
			else:
				rx_data = self.transport.get_ptp_data(request)
			if isinstance(rx_data, PtpResponse):
				response = rx_data
				rx_data = None
		
		if response == None:
			response = self.transport.get_ptp_response(request)

		if response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(response.respcode)
		
		if receiving and rx_data is not None and not stream:
			return response, rx_data
		else:
			return response
	
	
	def GetMemory(self,start,num):
		response,rx = self.simpleRequest((PTP_CHDK_GetMemory,start,num),receiving=True)
		return rx

	def SetMemory(self,addr,buffer):
		response,rx = self.simpleRequest((PTP_CHDK_SetMemory,addr,len(buffer)),buffer=buffer,receiving=False)
		return True
	
	def CallFunction(self,args):
		response,rx = self.simpleRequest(PTP_CHDK_CallFunction,args=args,fmt='I'*len(args),receiving=True)
		return response.params[0]

	def Upload(self,remoteFilename,data):
		response = self.simpleRequest(
			PTP_CHDK_UploadFile,
			fmt = 'I',
			args = (len(remoteFilename),),
			buffer = remoteFilename+data,
			receiving = False
		)
		return True

	def Download(self,remoteFilename,stream=None):
		response = self.simpleRequest(
			(PTP_CHDK_TempData,0),
			buffer = remoteFilename,
			receiving = False
		)
		if stream:
			response = self.simpleRequest(
				PTP_CHDK_DownloadFile,
				receiving = True,
				stream = stream
			)
		else:
			response,rx = self.simpleRequest(
				PTP_CHDK_DownloadFile,
				receiving = True
			)
			return rx[1]

	def ExecuteScript(self,script):
		response = self.simpleRequest((PTP_CHDK_ExecuteScript,PTP_CHDK_SL_LUA,0),buffer=script+'\x00',receiving=True)
		return response.params

	def GetVersion(self):
		return self.simpleRequest(PTP_CHDK_Version,receiving=True).params

	def GetScriptStatus(self,scriptId):
		response = self.simpleRequest(PTP_CHDK_ScriptStatus,receiving=True)
		return response.params
	
	def GetScriptSupport(self,scriptId):
		response = self.simpleRequest(PTP_CHDK_ScriptSupport,receiving=True)
		return response.params[0]
	
	def WriteScriptMessage(self,scriptId,message):
		assert message
		response = self.simpleRequest((PTP_CHDK_WriteScriptMsg,scriptId),buffer=message,receiving=True)
		return response.params[0]
	
	def ReadScriptMessage(self,scriptId):
		response,rx = self.simpleRequest(PTP_CHDK_ReadScriptMsg,receiving=True)
		mType,mSubType,scriptId,size = response.params
		return mType,mSubType,scriptId,size,rx
	
	def GetLiveData(self,flags):
		response,rx = self.simpleRequest((PTP_CHDK_GetLiveData,flags),receiving=True)
		return rx

