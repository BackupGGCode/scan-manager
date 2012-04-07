import ctypes
import sys

nikon = ctypes.windll.NkdPTP
d80 = ctypes.windll.LoadLibrary('D80_Mod.md3')


class NikonError(Exception):
	pass

class NikonWarning(Exception):
	pass

class UnkownError(NikonError):
	pass

class ENotSupported(NikonError):
	ident = -127

class EUnexpectedDataType(NikonError):
	ident = -126

class EValueOutOfBounds(NikonError):
	ident = -125

class EBufferSize(NikonError):
	ident = -124

class EAborted(NikonError):
	ident = -123

class ENoMedia(NikonError):
	ident = -122

class ENoEventProc(NikonError):
	ident = -121

class ENoDataProc(NikonError):
	ident = -120

class EZombieObject(NikonError):
	ident = -119
	
class EOutOfMemory(NikonError):
	ident = -118

class EUnexpectedError(NikonError):
	ident = -117

class EHardwareError(NikonError):
	ident = -116

class EMissingComponent(NikonError):
	ident = -115

#
# Warnings
#
class WPending(NikonWarning):
	ident = 1

class WOrphanedChildren(NikonWarning):
	ident = 2
	
#
# D80-specific
#

class EApertureFEE(NikonError):
	ident 					= 128
class EBufferNotReady(NikonError):
	ident 				= 129
class ENormalTTL(NikonError):
	ident 						= 130
class EMediaFull(NikonError):
	ident 						= 131
class EInvalidMedia(NikonError):
	ident 					= 132
class EEraseFailure(NikonError):
	ident 					= 133
class ECameraNotFound(NikonError):
	ident 				= 134
class EBatteryDontWork(NikonError):
	ident 				= 135
class EShutterBulb(NikonError):
	ident 					= 136
class EOutOfFocus(NikonError):
	ident 					= 137
class EProtected(NikonError):
	ident 						= 138
class EFileExists(NikonError):
	ident 					= 139
class ESharingViolation(NikonError):
	ident 				= 140
class EDataTransFailure(NikonError):
	ident 				= 141
class ESessionFailure(NikonError):
	ident 				= 142
class EFileRemoved(NikonError):
	ident 					= 143
class EBusReset(NikonError):
	ident 						= 144
class ENonCPULens(NikonError):
	ident 					= 145
class EReleaseButtonPressed(NikonError):
	ident 			= 146
class EBatteryExhausted(NikonError):
	ident 				= 147
class ECaptureFailure(NikonError):
	ident = 148
class EInvalidString(NikonError):
	ident = 149
class ENotInitialized(NikonError):
	ident = 150
class ECaptureDisable(NikonError):
	ident = 151
class EDeviceBusy(NikonError):
	ident = 152
class ECaptureDustFailure(NikonError):
	ident = 153
class EICADown(NikonError):
	ident = 154


Errors = [
	ENotSupported,
	EUnexpectedDataType,
	EValueOutOfBounds,
	EBufferSize,
	EAborted,
	ENoMedia,
	ENoEventProc,
	ENoDataProc,
	EZombieObject,
	EOutOfMemory,
	EUnexpectedError,
	EHardwareError,
	EMissingComponent,
	WPending,
	WOrphanedChildren,
	EApertureFEE,
	EBufferNotReady,
	ENormalTTL,
	EMediaFull,
	EInvalidMedia,
	EEraseFailure,
	ECameraNotFound,
	EBatteryDontWork,
	EShutterBulb,
	EOutOfFocus,
	EProtected,
	EFileExists,
	ESharingViolation,
	EDataTransFailure,
	ESessionFailure,
	EFileRemoved,
	EBusReset,
	ENonCPULens,
	EReleaseButtonPressed,
	EBatteryExhausted,
	ECaptureFailure,
	EInvalidString,
	ENotInitialized,
	ECaptureDisable,
	EDeviceBusy,
	ECaptureDustFailure,
	EICADown,
]


ErrorD = {}
for i in Errors:
	ErrorD[i.ident] = i

def checkError(rc):
	if rc == 0:
		return
	if rc in ErrorD:
		raise ErrorD[rc]
	else:
		raise UnkownError(rc)

Result_NoError = 0


class Enum(object):

	def _get_reverseDict(self):
		
		if not hasattr(self,'_rd'):
			self._rd = {}
			for k,v in self.__class__.__dict__.items():
				self._rd[v] = k
			
		return self._rd
	
	def __getitem__(self,k):
		rd = self._get_reverseDict()
		return rd[k]

	def __contains__(self,k):
		rd = self._get_reverseDict()
		return k in rd


class MaskEnum(Enum):
	
	def __getitem__(self,k):
		out = []
		for i in range(32):
			bit = 2**i
			if k & bit:
				out.append(Enum.__getitem__(self,bit))
		return out


class Command(Enum):
	Async = 0			# process asynchronous operations
	Open = 1			# opens a child object
	Close = 2			# closes a previously opened object
	GetCapCount = 3	# get number of capabilities of an object
	GetCapInfo = 4		# get capabilities of an object
	CapStart = 5		# starts capability
	CapSet = 6			# set value of capability
	CapGet = 7			# get value of capability
	CapGetDefault = 8	# get default value of capability
	CapGetArray = 9	# get data for array capability
	Mark = 10				# insert mark in the command queue
	AbortToMark = 11	# abort asynchronous commands to mark
	Abort = 12			# abort current asynchronous command
	EnumChildren = 13	# requests 'add' events for all child IDs
	GetParent = 14		# gets previously opened parent for object
	ResetToDefault = 15	# resets all capabilities to their default value
Command = Command()

class DataType(Enum):
	Null = 0
	Boolean = 1			# passed by value, set only
	Integer = 2			# signed 32 bit int, passed by value, set only
	Unsigned = 3		# unsigned 32 bit int, passed by value, set only
	BooleanPtr = 4		# pointer to single byte boolean value(s)
	IntegerPtr = 5	   # pointer to signed 4 byte value(s)
	UnsignedPtr = 6		# pointer to unsigned 4 byte value(s)
	FloatPtr = 7		# pointer to DOUB_P value(s)
	PointPtr = 8		# pointer to NkMAIDPoint structure(s)
	SizePtr = 9			# pointer to NkMAIDSize structure(s)
	RectPtr = 10		# pointer to NkMAIDRect structure(s)
	StringPtr = 11		# pointer to NkMAIDString structure(s)
	DateTimePtr = 12	# pointer to NkMAIDDateTime structure(s)
	CallbackPtr = 13	# pointer to NkMAIDCallback structure(s)
	RangePtr = 14		# pointer to NkMAIDRange structure(s)
	ArrayPtr = 15  		# pointer to NkMAIDArray structure(s)
	EnumPtr = 16			# pointer to NkMAIDEnum structure(s)
	ObjectPtr = 17		 # pointer to NkMAIDObject structure(s)
	CapInfoPtr = 18		# pointer to NkMAIDCapInfo structure(s)
	GenericPtr = 19		# pointer to generic data
DataType = DataType()

class ObjectType(Enum):
	Module = 1
	Source = 2
	Item = 3
	DataObj = 4
ObjectType = ObjectType()

class CapType(Enum):
	Process = 0				# a process that can be started
	Boolean = 1				# single byte boolean value
	Integer = 2				# signed 4 byte value
	Unsigned = 3			# unsigned 4 byte value
	Float = 4				# DOUB_P value
	Point = 5				# NkMAIDPoint structure
	Size = 6				# NkMAIDSize structure
	Rect = 7				# NkMAIDRect structure
	String = 8				# NkMAIDString structure
	DateTime = 9			# NkMAIDDateTime structure
	Callback = 10			# NkMAIDCallback structure
	Array = 11				# NkMAIDArray structure
	Enum = 12				# NkMAIDEnum structure
	Range = 13				# NkMAIDRange structure
	Generic = 14			# generic data
	BoolDefault = 15		# Reserved
CapType = CapType()

class CapOperation(MaskEnum):
	Start			= 0x0001
	Get				= 0x0002
	Set				= 0x0004
	GetArray		= 0x0008
	GetDefault		= 0x0010
CapOperation = CapOperation()

class CapVisibility(MaskEnum):
	Hidden			= 0x0001
	Advanced		= 0x0002
	Vendor			= 0x0004
	Group			= 0x0008
	GroupMember		= 0x0010
	Invalid			= 0x0020
CapVisibility = CapVisibility()

class ArrayType(Enum):
	Boolean = 0			# 1 byte per element
	Integer = 1			# signed value that is 1, 2 or 4 bytes per element
	Unsigned = 2			# unsigned value that is 1, 2 or 4 bytes per element
	Float = 3				# DOUB_P elements
	Point = 4				# NkMAIDPoint structures
	Size = 5				# NkMAIDSize structures
	Rect = 6				# NkMAIDRect structures
	PackedString = 7		# packed array of strings
	String = 8			# NkMAIDString structures
	DateTime = 9			# NkMAIDDateTime structures
ArrayType = ArrayType()

class DataObjType(MaskEnum):
	Image			= 0x00000001
	Sound			= 0x00000002
	Video			= 0x00000004
	Thumbnail		= 0x00000008
	File			= 0x00000010
DataObjType = DataObjType()

class FileDataType(Enum):
	NotSpecified = 0
	JPEG = 1
	TIFF = 2
	FlashPix = 3
	NIF = 4
	QuickTime = 5
	UserType = 0x100
FileDataType = FileDataType()

class EventType(Enum):
	AddChild = 0
	RemoveChild = 1
	WarmingUp = 2
	WarmedUp = 3
	CapChange = 4
	OrphanedChildren = 5
	CapChangeValueOnly = 6
EventType = EventType()


class MAIDClient(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('x',ctypes.c_ulong)
	]

class MAIDObject(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('type', ctypes.c_ulong), # ObjectType_Module
		('id', ctypes.c_ulong), 
		('client', MAIDClient),
		('module', ctypes.c_void_p),
	]
	
class MAIDCapInfo(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('id', ctypes.c_ulong),
		('type', ctypes.c_ulong),
		('visibility', ctypes.c_ulong),
		('operations', ctypes.c_ulong),
		('description', ctypes.c_char * 256),
	]
	
class MAIDArray(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('type', ctypes.c_ulong),			# one of eNkMAIDArrayType
		('elements', ctypes.c_ulong),
		('dimSize1', ctypes.c_ulong),
		('dimSize2', ctypes.c_ulong),
		('dimSize3', ctypes.c_ulong),
		('physicalBytes', ctypes.c_uint),
		('logicalBits', ctypes.c_uint),
		('data', ctypes.c_void_p),
	]

class MAIDEnum(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('type', ctypes.c_ulong),			# one of eNkMAIDArrayType
		('elements', ctypes.c_ulong),
		('value', ctypes.c_ulong),
		('default', ctypes.c_ulong),
		('physicalBytes', ctypes.c_int16),
		('data', ctypes.c_void_p),
	]

class MAIDDateTime(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('year', ctypes.c_uint),		# ie 1997, 1998
		('month', ctypes.c_uint),		# 0-11 = Jan-Dec
		('day', ctypes.c_uint),			# 1-31
		('hour', ctypes.c_uint),		# 0-23
		('minute', ctypes.c_uint),		# 0-59
		('second', ctypes.c_uint),		# 0-59
		('subsecond', ctypes.c_ulong),	# module dependent
	]


class MAIDPoint(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('x', ctypes.c_long),		# ie 1997, 1998
		('y', ctypes.c_long),		# ie 1997, 1998
	]
	

class MAIDSize(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('w', ctypes.c_long),		# ie 1997, 1998
		('h', ctypes.c_long),		# ie 1997, 1998
	]
	

class MAIDRect(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('x', ctypes.c_long),		# ie 1997, 1998
		('y', ctypes.c_long),		# ie 1997, 1998
		('w', ctypes.c_ulong),		# ie 1997, 1998
		('h', ctypes.c_ulong),		# ie 1997, 1998
	]
	

class MAIDString(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('str', ctypes.c_char * 256),		# ie 1997, 1998
	]

	
class MAIDUIRequestInfo(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('type', ctypes.c_ulong),
		('default', ctypes.c_ulong),
		('sync', ctypes.c_ubyte),
		('prompt', ctypes.c_char_p),
		('detail', ctypes.c_char_p),
		('object', MAIDObject),
		('data', MAIDArray),
	]


class MAIDDataInfo(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('type', ctypes.c_ulong),
	]


class MAIDImageInfo(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('base', MAIDDataInfo),
		('totalPixels', MAIDSize),
		('colorSpace', ctypes.c_ulong),
		('rData', MAIDRect),
		('ulRowBytes', ctypes.c_ulong),
		('bits', ctypes.c_uint*4),
		('plane', ctypes.c_uint),
		('removeObject', ctypes.c_ubyte),
		
	]

class MAIDFileInfo(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('base', MAIDDataInfo),
		('fileDataType', ctypes.c_uint),
		('totalLength', ctypes.c_uint),
		('start', ctypes.c_uint),
		('length', ctypes.c_uint),
		('diskFile', ctypes.c_ubyte),
		('removeObject', ctypes.c_ubyte),
	]




CCompletionProc = ctypes.WINFUNCTYPE(
	None,
	ctypes.c_void_p,	# LPNkMAIDObject	pObject,			// module, source, item, or data object
	ctypes.c_ulong,		# ULONG				ulCommand,		// Command, one of eNkMAIDCommand
	ctypes.c_ulong,		# ULONG				ulParam,			// parameter for the command
	ctypes.c_ulong,		# ULONG				ulDataType,		// Data type, one of eNkMAIDDataType
	ctypes.c_void_p,	# NKPARAM			data,				// Pointer or long integer
	ctypes.c_void_p,	# NKREF				ref,	// Reference set by client
	ctypes.c_long,		# NKERROR			nResult )		// One of eNkMAIDResult)
)
def CompletionProc(f=None):
	def pyCompletionProc(obj,command,param,dataType,data,reference,result):
		print('COMPLETION',(obj,command,param,dataType,data,reference,result))
		if f is not None:
			return f(obj=obj,command=command,param=param,dataType=dataType,data=data,reference=reference,result=result)
	return CCompletionProc(pyCompletionProc)


CProgressProc = ctypes.WINFUNCTYPE(
	None,
	ctypes.c_ulong,		# ULONG				ulCommand,		// Command, one of eNkMAIDCommand
	ctypes.c_ulong,		# ULONG				ulParam,			// parameter for the command
	ctypes.c_void_p,	# NKREF				ref,	// Reference set by client
	ctypes.c_ulong,		# ULONG				ulDone 		// Numerator
	ctypes.c_ulong,		# ULONG				ulTotal 		// Denominator
)
def ProgressProc(f=None):
	def pyProgressProc(command,param,ref,done,total):
		print('PROGRESS',(command,param,ref,done,total))
		if f is not None:
			return f(command=command,param=param,ref=ref,done=done,total=total)
	return CProgressProc(pyProgressProc)

	
CEventProc = ctypes.WINFUNCTYPE(
	None,
	ctypes.c_void_p,	# refProc
	ctypes.c_ulong,		# event
	ctypes.c_void_p,	# data
)
def EventProc(f=None):
	def pyEventProc(ref,event,data):
		print('EVENT ref=%s, event=%s, data=%s'%(ref,EventType[event],data))
		if f is not None:
			return f(ref=ref,event=event,data=data)
	return CEventProc(pyEventProc)


CUIRequestProc = ctypes.WINFUNCTYPE(
	ctypes.c_ulong,
	ctypes.c_void_p,	# refProc
	ctypes.POINTER(MAIDUIRequestInfo),	# LPNkMAIDUIRequestInfo pUIRequest
)
def UIRequestProc(f=None):
	def pyRequestProc(ref,info):
		print('UI REQUEST',(ref,info))
		if f is not None:
			return f(ref=ref,info=info)
	return CUIRequestProc(pyRequestProc)


CDataProc = ctypes.WINFUNCTYPE(
	ctypes.c_ulong,
	ctypes.c_void_p,	# refProc
	ctypes.POINTER(MAIDDataInfo),		# info
	ctypes.c_void_p,	# data
)
def DataProc(f=None):
	def pyDataProc(ref,info,data):
		print('DATA',(ref,info,data))
		if f is not None:
			return f(ref=ref,info=info,data=data)
		else:
			return 0
	return CDataProc(pyDataProc)


def byref(o):
	if o is None:
		return None
	return ctypes.byref(o)


class DataHandler(object):
	
	def __init__(self,baseFileName='image'):
		self.baseFileName = baseFileName
		self.file = None
		
	def __call__(self,ref,info,data):

		pinfo = info
		info = info.contents
		
		if info.type & DataObjType.File:

			n = ctypes.cast(pinfo,ctypes.POINTER(MAIDFileInfo)).contents
			sys.n = n
			
			fileDataType = n.fileDataType
			
			if fileDataType == FileDataType.JPEG:
				self.ext = 'jpg'
			elif fileDataType == FileDataType.TIFF:
				self.ext = 'tiff'
			elif fileDataType == FileDataType.FlashPix:
				self.ext = 'fp'
			elif fileDataType == FileDataType.NIF:
				self.ext = 'nef'
			elif fileDataType == FileDataType.QuickTime:
				self.ext = 'qt'
			else:
				self.ext = 'bin'
			
			if n.length:
				
				if self.file is None:
					self.fileName = self.baseFileName + '.' + self.ext
					self.file = open(self.fileName,'wb')
				
				data = ctypes.string_at(data,n.length)
				
				self.file.write(data)

			if n.start + n.length >= n.totalLength:
				self.file.close()
				self.completed()
					
		return 0

	def completed(self):
		pass

class MAIDCallback(ctypes.Structure):
	_pack_ = 2
	_fields_ = [
		('proc', CEventProc),
		('ref', ctypes.c_void_p),
	]

