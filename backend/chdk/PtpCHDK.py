# Based on code from the pyptp project (http://code.google.com/p/pyptp/) 

from PtpSession import *

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


# Control flags for determining which data block to transfer
LV_TFR_VIEWPORT = 0x01
LV_TFR_BITMAP = 0x04
LV_TFR_PALETTE = 0x08

# Live view aspect ratios
LV_ASPECT_4_3 = 0
LV_ASPECT_16_9 = 1


class CHDKMessage(object):
	def __init__(self,type,subType,data):
		self.type = type
		self.subType = subType
		self.data = data


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
	
	
	def chdkRequest(self,params):
		if type(params) is int:
			params = (params,)
			
		request = PtpRequest(PTP_OC_CHDK, self.sessionid, self.NewTransaction(), params)
		
		self.transport.send_ptp_request(request)
		response = self.transport.get_ptp_response(request)
		if response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(response.respcode)
		return response
	

	def chdkRequestWithSend(self,params,fmt=None,args=None,buffer=None):
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

		self.transport.send_ptp_request(request)
		self.transport.send_ptp_data(request, tx_data)
		response = self.transport.get_ptp_response(request)
		if response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(response.respcode)
		return response


	def chdkRequestWithReceive(self,params,stream=None):
		if type(params) is int:
			params = (params,)
			
		request = PtpRequest(PTP_OC_CHDK, self.sessionid, self.NewTransaction(), params)
		
		# send the tx
		rx_data = None
		response = None
		
		self.transport.send_ptp_request(request)
		if stream:
			self.transport.get_ptp_data(request,stream)
		else:
			data = self.transport.get_ptp_data(request)
		response = self.transport.get_ptp_response(request)
		if response.respcode != PtpValues.StandardResponses.OK:
			raise PtpException(response.respcode)
		if not stream:
			response.data = data
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

