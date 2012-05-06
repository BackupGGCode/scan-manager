class Enum(object):
	
	def __iter__(self):
		for k,v in self.__dict__.items():
			yield (k,v)
	
	
	def __getitem__(self,i):
		for k,v in self.__dict__.items():
			if v == i:
				return k
		else:
			raise KeyError(i)



class Flags(object):
	
	def __iter__(self):
		for k,v in self.__dict__.items():
			yield (k,v)
	
	
	def __getitem__(self,i):
		for k,v in self.__dict__.items():
			if v == i:
				return k
		else:
			raise KeyError(i)


	def pp(self,flags):
		return '|'.join([k for k,v in self if v&flags])


Operation = Enum()
Operation.Version = 0
Operation.GetMemory = 1
Operation.SetMemory = 2
Operation.CallFunction = 3
Operation.TempData = 4
Operation.UploadFile = 5
Operation.DownloadFile = 6
Operation.ExecuteScript = 7
Operation.ScriptStatus = 8
Operation.ScriptSupport = 9
Operation.ReadScriptMsg = 10
Operation.WriteScriptMsg = 11
Operation.GetLiveData = 12

PTP_OC_CHDK = 0x9999 

# data types as used by ReadScriptMessage
ScriptMessageSubType = Enum()
ScriptMessageSubType.UNSUPPORTED = 0 # type name will be returned in data
ScriptMessageSubType.NIL = 1
ScriptMessageSubType.BOOLEAN = 2
ScriptMessageSubType.INTEGER = 3
ScriptMessageSubType.STRING = 4 # Empty strings are returned with length=0
ScriptMessageSubType.TABLE = 5  # tables are converted to a string by usb_msg_table_to_string, the string may be empty for an empty table

# TempData flags
TempDataFlag = Flags()
TempDataFlag.DOWNLOAD = 0x1  # download data instead of upload
TempDataFlag.CLEAR = 0x2  # clear the stored data; with DOWNLOAD this means first download, then clear and without DOWNLOAD this means no uploading, just clear

# Script Languages - for execution only lua is supported for now
ScriptLanguage = Enum()
ScriptLanguage.LUA = 0
ScriptLanguage.UBASIC = 1

# bit flags for script status
ScriptStatusFlag = Flags()
ScriptStatusFlag.DONE = 0x0 # OG: script completed
ScriptStatusFlag.RUN = 0x1 # script running
ScriptStatusFlag.MSG = 0x2 # messages waiting

# bit flags for scripting support
ScriptSupportFlag = Enum()
ScriptSupportFlag.LUA = 0x1

# message types
ScriptMessageType = Enum()
ScriptMessageType.NONE = 0 # no messages waiting
ScriptMessageType.ERR = 1 # error message
ScriptMessageType.RET = 2 # script return value
ScriptMessageType.USER = 3 # message queued by script
	# TODO chdk console data ?

# error subtypes for PTP_CHDK_S_MSGTYPE_ERR and script startup status
ScriptErrorMessageType = Enum()
ScriptErrorMessageType.NONE = 0
ScriptErrorMessageType.COMPILE = 1
ScriptErrorMessageType.RUN = 2

# message status
ScriptMessageStatus = Enum()
ScriptMessageStatus.OK = 0 # queued ok
ScriptMessageStatus.NOTRUN = 1 # no script is running
ScriptMessageStatus.QFULL = 2 # queue is full
ScriptMessageStatus.BADID = 3 # specified ID is not running


# Control flags for determining which data block to transfer
LiveViewFlag = Flags()
LiveViewFlag.VIEWPORT = 0x01
LiveViewFlag.BITMAP = 0x04
LiveViewFlag.PALETTE = 0x08

# Live view aspect ratios
LiveViewAspect = Enum()
LiveViewAspect.LV_ASPECT_4_3 = 0
LiveViewAspect.LV_ASPECT_16_9 = 1

