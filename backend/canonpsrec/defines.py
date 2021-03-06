from ctypes import *

class ENUM(object):

	def __init__(self):
		self.__dict__['name2value'] = {}
		self.__dict__['value2name'] = {}
		self.__dict__['name2comment'] = {}
		self.__dict__['nameOrder'] = []

	
	def __setattr__(self,k,v):
		if k in self.name2value:
			raise Exception('%s already set to %s (trying to reset with %s)'%(k,self.name2value[k],v))
		self.nameOrder.append(k)
		if type(v) is tuple:
			self.name2value[k] = v[0]
			self.value2name[v[0]] = k
			self.name2comment[k] = v[1]
		else:
			self.name2value[k] = v
			self.value2name[v] = k

	
	def __getattr__(self,k):
		if k in self.name2value:
			return self.name2value[k]
		else:
			raise AttributeError(k)

	
	def __getitem__(self,v):
		if type(v) is int:
			return self.value2name[v]
		else:
			return self.name2value[v]


	def __contains__(self,v):
		if type(v) is int:
			return v in self.value2name
		else:
			return v in self.name2value
		

	def describe(self,v):
		if type(v) is int:
			name = self.value2name[v]
		else:
			name = v
		if name in self.name2comment:
			return '%s (%s)'%(name,self.name2comment[name])
		else:
			return name


	def getName(self,v):
		return self.value2name[v]
	
	
	def getDescription(self,v):
		if type(v) is int:
			return self.name2comment.get(self.value2name[v])
		else:
			return self.name2comment[v]
	
		
	def __iter__(self):
		for k in self.nameOrder:
			yield (self.name2value[k],k,self.name2comment.get(k,None))
		

class ENUMException(Exception):
	enum = None	
	def __init__(self,rc):
		if rc in self.enum:
			Exception.__init__(self,self.enum.describe(rc))
		else:
			Exception.__init__(self,'Unknown error %s (0x%X)'%(rc,rc))


#
# Error code masks
#
ERROR_COMPONENTID_MASK					= 0x00F00000
ERROR_ERRORID_MASK						= 0x0000FFFF

#
# PRSDK Base Component IDs
#
ErrorComponentID = ENUM()
ErrorComponentID.PTP                              = (0x00100000,'PTP operation errors')
ErrorComponentID.PRSDK                            = (0x00200000,'PRSDK Internal Error')
ErrorComponentID.WIA_STI                          = (0x00300000,'Errors generated by the Windows WIA/STI')
ErrorComponentID.WINDOWS                          = (0x00400000,'Errors generated by the GetLastError() function in WIN32 API')
ErrorComponentID.COMIF                            = (0x00500000,'Windows COM I/F errors')


#
# PTP Operation Error IDs
#
Response = ENUM()
Response.OK                                       = 0x00000000
Response.Undefined                                = 0x00002000
Response.GeneralError                             = 0x00002002
Response.SessionNotOpen                           = 0x00002003
Response.InvalidTransactionID                     = 0x00002004
Response.OperationNotSupported                    = 0x00002005
Response.ParameterNotSupported                    = 0x00002006
Response.IncompleteTransfer                       = 0x00002007
Response.InvalidStorageID                         = 0x00002008
Response.InvalidObjectHandle                      = 0x00002009
Response.DevicePropNotSupported                   = 0x0000200A
Response.InvalidObjectFormatCode                  = 0x0000200B
Response.StoreFull                                = 0x0000200C
Response.ObjectWriteProtected                     = 0x0000200D
Response.StoreRead_Only                           = 0x0000200E
Response.AccessDenied                             = 0x0000200F
Response.NoThumbnailPresent                       = 0x00002010
Response.SelfTestFailed                           = 0x00002011
Response.PartialDeletion                          = 0x00002012
Response.StoreNotAvailable                        = 0x00002013
Response.SpecificationByFormatUnsupported         = 0x00002014
Response.NoValidObjectInfo                        = 0x00002015
Response.InvalidCodeFormat                        = 0x00002016
Response.UnknownVendorCode                        = 0x00002017
Response.CaptureAlreadyTerminated                 = 0x00002018
Response.DeviceBusy                               = 0x00002019
Response.InvalidParentObject                      = 0x0000201A
Response.InvalidDevicePropFormat                  = 0x0000201B
Response.InvalidDevicePropValue                   = 0x0000201C
Response.InvalidParameter                         = 0x0000201D
Response.SessionAlreadyOpen                       = 0x0000201E
Response.TransactionCancelled                     = 0x0000201F
Response.SpecificationOfDestinationUnsupported    = 0x00002020
# Vendor Extension Error IDs
#Response.Undefined                                = 0x0000A000
Response.UnknownCommandReceived                   = 0x0000A001
Response.MemAllocFailed                           = 0x0000A002
Response.InternalError                            = 0x0000A003
Response.DirIOError                               = 0x0000A004
Response.RefusedByOtherProcess                    = 0x0000A005
Response.CoverClosed                              = 0x0000A006
Response.NoRelease                                = 0x0000A007
Response.DeviceIsHot                              = 0x0000A008
Response.LowBattery                               = 0x0000A009
Response.AlreadyExit                              = 0x0000A00A


#
# Exception class for PTP errors
#
class PTPError(ENUMException):
	enum = Response


#
# PRSDK Internal Error IDs
#
SDKErrorCode = ENUM()
# Miscellaneous errors
SDKErrorCode.UNIMPLEMENTED                            = 0x00000001
SDKErrorCode.INTERNAL_ERROR                           = 0x00000002
SDKErrorCode.MEM_ALLOC_FAILED                         = 0x00000003
SDKErrorCode.MEM_FREE_FAILED                          = 0x00000004
SDKErrorCode.OPERATION_CANCELLED                      = 0x00000005
SDKErrorCode.INCOMPATIBLE_VERSION                     = 0x00000006
SDKErrorCode.NOT_SUPPORTED                            = 0x00000007
SDKErrorCode.UNEXPECTED_EXCEPTION                     = 0x00000008
SDKErrorCode.PROTECTION_VIOLATION                     = 0x00000009
SDKErrorCode.MISSING_SUBCOMPONENT                     = 0x0000000A
SDKErrorCode.SELECTION_UNAVAILABLE                    = 0x0000000B
# Function Parameter errors 
SDKErrorCode.INVALID_PARAMETER                        = 0x00000021
SDKErrorCode.INVALID_HANDLE                           = 0x00000022
# ...
SDKErrorCode.INVALID_FN_CALL                          = 0x00000061
SDKErrorCode.WAIT_TIMEOUT_ERROR                       = 0x00000062
SDKErrorCode.INSUFFICIENT_BUFFER                      = 0x00000063
SDKErrorCode.EVENT_CALLBACK_EXIST                     = 0x00000064

#
# Generic exception class for SDK errors and PTP response errors
#
class SDKError(ENUMException):
	def __init__(self,rc):
		componentID = rc & ERROR_COMPONENTID_MASK
		errorId = rc & ERROR_ERRORID_MASK
		
		if componentID in ErrorComponentID and errorId in SDKErrorCode:
			componentName = ErrorComponentID[componentID]
			Exception.__init__(self,'%s in %s'%(SDKErrorCode.describe(errorId),componentName))
		elif errorId in Response:
			Exception.__init__(self,Response.describe(errorId))
		else:
			if componentID in ErrorComponentID:
				componentName = ErrorComponentID[componentID]
				Exception.__init__(self,'Unknown error 0x%X (or error 0x%X in %s)'%(rc,errorId,componentName))
			else:
				Exception.__init__(self,'Unknown error 0x%X'%(rc))


DATA_BUFFER_SIZE = (1024*1024)


# Definition of Operation Code
#  prUInt16
OperationCode = ENUM()
OperationCode.INITIATE_RELEASE_CONTROL				= 0x9008
OperationCode.TERMINATE_RELEASE_CONTROL				= 0x9009
OperationCode.RC_INITIATE_VIEW_FINDER				= 0x900B
OperationCode.RC_TERMINATE_VIEW_FINDER				= 0x900C
OperationCode.RC_RELEASE_DO_AE_AF_AWB				= 0x900D
OperationCode.RC_FOCUS_LOCK							= 0x9014
OperationCode.RC_FOCUS_UNLOCK						= 0x9015
OperationCode.RC_CAPTURE							= 0x901A
OperationCode.RC_GET_CHANGED_RELEASE_PARAMS_LIST	= 0x9020

## Progress Message
ProgressMessage = ENUM()
ProgressMessage.DATA_HEADER							= 0x0001
ProgressMessage.DATA								= 0x0002
ProgressMessage.TERMINATION							= 0x0004

## Event Codes
##  prUInt16
EventCode = ENUM()
EventCode.DEVICE_PROP_CHANGED                     = (0x4006,'Deveice property has been changed.')
EventCode.CAPTURE_COMPLETE                        = (0x400D,'Capture has finished.')
EventCode.SHUTDOWN_CF_GATE_WAS_OPENED             = (0xC001,'The Device has shut down due to the opening of the SD card cover.')
EventCode.RESET_HW_ERROR                          = (0xC005,'The device has generated a hardware error.')
EventCode.ABORT_PC_EVF                            = (0xC006,'The Viewfinder mode has been cancelled.')
EventCode.ENABLE_PC_EVF                           = (0xC007,'The Viewfinder mode has been enablede.')
EventCode.FULL_VIEW_RELEASED                      = (0xC008,'Transfer timing of main image data')
EventCode.THUMBNAIL_RELEASED                      = (0xC009,'Transfer timing of thumbnail image data')
EventCode.CHANGE_BATTERY_STATUS                   = (0xC00A,'The power condition of the camera has changed.')
EventCode.PUSHED_RELEASE_SW                       = (0xC00B,'User has pressed the release swtich on camera.')
EventCode.RC_PROP_CHANGED                         = (0xC00C,'A group of properties relating to release control have been changed.')
EventCode.RC_ROTATION_ANGLE_CHANGED               = (0xC00D,'The angle of rotation of the camera has been changed.')
EventCode.RC_CHANGED_BY_CAM_UI                    = (0xC00E,'An operation control on the camera has been operated.')
EventCode.SHUTDOWN                                = (0xD001,'Shutdown')


## Deveice Property Codes
#  prUint16
DevicePropCode = ENUM()
DevicePropCode.BUZZER                             = (0xD001,'Set on/off the device buzzer')
DevicePropCode.BATTERY_KIND                       = (0xD002,'Type of the battery')
DevicePropCode.BATTERY_STATUS                     = (0xD003,'Buttery Status')
DevicePropCode.COMP_QUALITY                       = (0xD006,'Image quality')
DevicePropCode.FULLVIEW_FILE_FORMAT               = (0xD007,'Image type')
DevicePropCode.IMAGE_SIZE                         = (0xD008,'Image size')
DevicePropCode.SELFTIMER                          = (0xD009,'Self-timer')
DevicePropCode.STROBE_SETTING                     = (0xD00A,'Strobe setting')
DevicePropCode.BEEP                               = (0xD00B,'Buzzer setting')
DevicePropCode.EXPOSURE_MODE                      = (0xD00C,'Exposure mode setting')
DevicePropCode.IMAGE_MODE                         = (0xD00D,'Image mode setting')
DevicePropCode.DRIVE_MODE                         = (0xD00E,'Drive mode')
DevicePropCode.EZOOM                              = (0xD00F,'Electonic zoom setting')
DevicePropCode.ML_WEI_MODE                        = (0xD010,'Metering method')
DevicePropCode.AF_DISTANCE                        = (0xD011,'Search range in the AF mode')
DevicePropCode.FOCUS_POINT_SETTING                = (0xD012,'Selection mode for focusing point')
DevicePropCode.WB_SETTING                         = (0xD013,'White balance setting')
DevicePropCode.SLOW_SHUTTER_SETTING               = (0xD014,'Slow Shutter setting')
DevicePropCode.AF_MODE                            = (0xD015,'Auto focus mode setting')
DevicePropCode.IMAGE_STABILIZATION                = (0xD016,'Image stabilization processing')
DevicePropCode.CONTRAST                           = (0xD017,'Contrast')
DevicePropCode.COLOR_GAIN                         = (0xD018,'Color Compensation')
DevicePropCode.SHARPNESS                          = (0xD019,'Sharpness')
DevicePropCode.SENSITIVITY                        = (0xD01A,'Sensitivity')
DevicePropCode.PARAMETER_SET                      = (0xD01B,'Development parameter setting')
DevicePropCode.ISO                                = (0xD01C,'ISO value')
DevicePropCode.AV                                 = (0xD01D,'Av value')
DevicePropCode.TV                                 = (0xD01E,'Tv value')
DevicePropCode.EXPOSURE_COMP                      = (0xD01F,'Exposure compensation value')
DevicePropCode.FLASH_COMP                         = (0xD020,'Flash exposure compensation value')
DevicePropCode.AEB_EXPOSURE_COMP                  = (0xD021,'AEB exposure compensation value')
DevicePropCode.AV_OPEN                            = (0xD023,'Open aperture value')
DevicePropCode.AV_MAX                             = (0xD024,'maximum aperture value')
DevicePropCode.FOCAL_LENGTH                       = (0xD025,'Value corresponding to the current focal distance multiplied by FocalLengthDenominator')
DevicePropCode.FOCAL_LENGTH_TELE                  = (0xD026,'Value corresponding to the telescopic focal distance multiplied by FocalLengthDenominator')
DevicePropCode.FOCAL_LENGTH_WIDE                  = (0xD027,'Value corresponding to the wide-angle focus distance multiplied by FocalLengthDenominator')
DevicePropCode.FOCAL_LENGTH_DENOMI                = (0xD028,'Focus information multiplier value')
DevicePropCode.CAPTURE_TRANSFER_MODE              = (0xD029,'Image transfer mode to be applied at caputre')
DevicePropCode.ZOOM_POS                           = (0xD02A,'Current zoom position')
DevicePropCode.SUPPORTED_SIZE                     = (0xD02C,'Support size')
DevicePropCode.SUPPORTED_THUMB_SIZE               = (0xD02D,'Thumbnail size supported by the device')
DevicePropCode.FIRMWARE_VERSION                   = (0xD031,'Version of the camera device firmware')
DevicePropCode.CAMERA_MODEL_NAME                  = (0xD032,'Camera model')
DevicePropCode.OWNER_NAME                         = (0xD033,'Owner name')
DevicePropCode.CAMERA_TIME                        = (0xD034,'Current time information in the device')
DevicePropCode.CAMERA_OUTPUT                      = (0xD036,'Destination of image signal output in the Viewfinder mode')
DevicePropCode.DISP_AV                            = (0xD037,'How to display the Av value')
DevicePropCode.AV_OPEN_APEX                       = (0xD038,'Open aperture value')
DevicePropCode.EZOOM_SIZE                         = (0xD039,'Horizontal size of image to be cut out from CCD image using electronic zoom')
DevicePropCode.ML_SPOT_POS                        = (0xD03A,'Spot metering positon')
DevicePropCode.DISP_AV_MAX                        = (0xD03B,'How to display the maximin Av value')
DevicePropCode.AV_MAX_APEX                        = (0xD03C,'minimum aperture value')
DevicePropCode.EZOOM_START_POS                    = (0xD03D,'Zoom position at which the electornic zoom range starts')
DevicePropCode.FOCAL_LENGTH_OF_TELE               = (0xD03E,'Focal distance at the optical telescopic end')
DevicePropCode.EZOOM_SIZE_OF_TELE                 = (0xD03F,'Horizontal size of image to be cut out from CCD image at the telescopic end of the electronic zoom range')
DevicePropCode.PHOTO_EFFECT                       = (0xD040,'Photo effect')
DevicePropCode.AF_LIGHT                           = (0xD041,'ON/OFF of AF assist light')
DevicePropCode.FLASH_QUANTITY                     = (0xD042,'Number of flash levels that can be set in the manual mode')
DevicePropCode.ROTATION_ANGLE                     = (0xD043,'Angle of rotation detected by the gravity sensor')
DevicePropCode.ROTATION_SENSE                     = (0xD044,'Whether the gravity sensor is enable or disable')
DevicePropCode.IMAGE_FILE_SIZE                    = (0xD048,'Image file size supported be the camera')
DevicePropCode.CAMERA_MODEL_ID                    = (0xD049,'Camera model ID')



## AE,AF,AWB Reset flag */
##  prUInt32
AfAeResetFlag = ENUM()
AfAeResetFlag.AE  = (0x00000001,'AE Reset')
AfAeResetFlag.AF  = (0x00000002,'AF Reset')
AfAeResetFlag.AWB = (0x00000004,'AWB Reset')

## Port type 
##  prUInt16
PortType = ENUM()
PortType.WIA = 0x0001
PortType.STI = 0x0002

GENERATION_CAMERA_MASK = 0xff00
def SUB_GENERATION_CAMERA(gen):
	return ((gen&GENERATION_CAMERA_MASK)>>8)

## Object type
##  prUInt16
ObjectFormatCode = ENUM()
ObjectFormatCode.EXIF_JPEG = (0x3801,'EXIF JPEG')
ObjectFormatCode.PTP_CRW = (0xB101,'RAW')


c_uint32 = c_int
c_uint16 = c_ushort
c_uint8 = c_ubyte
c_int32 = c_int
c_int16 = c_short
c_int8 = c_byte


def cResize(array, new_size):
	resize(array, sizeof(array._type_)*new_size)
	return (array._type_*new_size).from_address(addressof(array))


#
# Structures
#

DevicePropDesc = c_char * (1024 * 16)
DevicePropValue = c_char * (1024 * 16)

class VerInfo(Structure):
	_pack_ = 1
	_fields_ = [
		('ModuleName',c_wchar*512),
		('Version',c_wchar*32),
	]




class DllsVerInfo(Structure):
	_pack_ = 1
	_fields_ = [
		('Entry',c_uint32),						# Number of modules included in this structure
		('VerInfo',VerInfo*50),					# Array of file version number information of PS-ReC SDK modules
	]


class DeviceInfoTable(Structure):
	_pack_ = 1
	_fields_ = [
		('DeviceInternalName',c_wchar*512),		# Internal devicve name (512 characters)
		('ModelName',c_wchar*32),				# Camera model name (32 characters) 
		('Generation',c_uint16),				# Camera generation number 
		('Reserved1',c_uint32),					# Reserved 
		('ModelID',c_uint32),					# Camera model ID 
		('Reserved2',c_uint16),					# Reserved 
		('PortType',c_uint16),					# Port type 0x01F WIA / 0x02 FSTI 
		('Reserved3',c_uint32),					# Reserved
	]


class PRString(Structure):
	_pack_ = 1
	_fields_ = [
		('DeviceInternalName',c_uint8),
		('DeviceInternalName',c_wchar*0),
	]


class DeviceInfo(Structure):
	_pack_ = 1
	_fields_ = [
		('StandardVersion',c_uint16),
		('VendorExtensionID',c_uint32),
		('VendorExtensionVersion',c_uint16),
		('data',c_uint8*8192),
	]


class DeviceList(Structure):
	_pack_ = 1
	_fields_ = [
		('NumList',c_uint32),					# Number of camera device information included in this structure */
		('DeviceInfo',DeviceInfoTable*50),		# Camera device information */
	]


class Progress(Structure):
	_pack_ = 1
	_fields_ = [
		('Message',c_int32),					# Message
		('Status',c_int32),						# Status
		('PercentComplete',c_uint32),			# The uint of this parameter is percent
		('Offset',c_uint32),					# Offset
		('Length',c_uint32),					# Size
		('Reserved',c_uint32),					# Reserved
		('ResLength',c_uint32),					# Reserved
		('Data',c_uint32),			# Pointer to the buffer in which the transferred data is stored.
	]





EventCallback = WINFUNCTYPE(c_int,c_uint32,c_uint32,c_uint32)
FileDataCallback = WINFUNCTYPE(c_int,c_uint32,c_uint32,c_uint32,POINTER(Progress))
ViewfinderCallback = WINFUNCTYPE(c_int,c_uint32,c_uint32,c_uint32,c_uint32)


