# Based on code from the pyptp project (http://code.google.com/p/pyptp/) 

from PtpSession import PtpSession,PtpRequest,PtpPacker,PtpException
import PtpValues

import ctypes
import struct
import threading

import chdkimage

from chdkconstants import *

#
# Live view frame buffer data
#
class FramebufDesc(ctypes.Structure):
	_fields_ = [
		('logical_width',ctypes.c_int),
		('logical_height',ctypes.c_int),
		('buffer_width',ctypes.c_int),
		('buffer_logical_xoffset',ctypes.c_int),
		('buffer_logical_yoffset',ctypes.c_int),
		('visible_width',ctypes.c_int),
		('visible_height',ctypes.c_int),
		('data_start',ctypes.c_int),
	]

	def pp(self,indent=''):
		s = indent + '<%s>\n'%(self.__class__.__name__)
		for k,c in self._fields_:
			s += indent + '  %s: %r\n'%(k,getattr(self,k))
		return s

class LiveDataHeader(ctypes.Structure):
	_fields_ = [
		('version_major',ctypes.c_int),
		('version_minor',ctypes.c_int),
		('lcd_aspect_ratio',ctypes.c_int), # physical aspect ratio of LCD
		('palette_type',ctypes.c_int),
		('palette_data_start',ctypes.c_int),
		('viewport',FramebufDesc),
		('bitmap',FramebufDesc),
	]

	def pp(self,indent=''):
		s = indent + '<%s>\n'%(self.__class__.__name__)
		for k,c in self._fields_:
			v = getattr(self,k)
			if hasattr(v,'pp'):
				s += indent + '  %s:\n'%(k)
				s += v.pp(indent=indent+'    ')
			else:
				s += indent + '  %s: %r\n'%(k,v)
		return s

class LiveViewFrame(object):
	
	def __init__(self,raw):
		
		headerBuffer = ctypes.create_string_buffer(raw[:ctypes.sizeof(LiveDataHeader)])
		self.header = LiveDataHeader.from_buffer(headerBuffer)
		
		self.viewportRGB = chdkimage.dataToViewportRGB(raw,0)
		self.bitmapRGBA = chdkimage.dataToBitmapRGBA(raw,0)


class ScriptMessage(object):
	def __init__(self,type,subType,data=None,scriptId=None):
		self.type = type
		self.subType = subType
		self.data = data[1]
		self.scriptId = scriptId
	def __repr__(self):
		types = ScriptMessageType[self.type]
		if self.type == ScriptMessageType.ERR:
			subs = ScriptErrorMessageType[self.subType]
		elif self.type in (ScriptMessageType.RET,ScriptMessageType.USER):
			subs = ScriptMessageSubType[self.subType]
		elif self.type == ScriptMessageType.NONE:
			subs = 'N/A'
		else:
			subs = '[UNKNOWN]'
		ScriptMessageSubType
		s = '<%s type=%d (%s) subType=%d (%s) scriptId=%s value=%r>'%(self.__class__.__name__,self.type,types,self.subType,subs,self.scriptId,self.value)
		return s
	
	@property
	def value(self):
		if self.type == ScriptMessageType.USER or self.type == ScriptMessageType.RET:
			if self.subType == ScriptMessageSubType.INTEGER:
				return struct.unpack('i',self.data)[0]
			elif self.subType == ScriptMessageSubType.BOOLEAN:
				return bool(struct.unpack('i',self.data)[0])
			elif self.subType == ScriptMessageSubType.NIL:
				return None
			elif self.subType == ScriptMessageSubType.STRING:
				return self.data
			elif self.subType == ScriptMessageSubType.TABLE:
				return {k:v for k,v in [tuple(i.split('\t')) for i in self.data.split('\n')[:-1]]}
			elif self.subType == ScriptMessageSubType.UNSUPPORTED:
				raise Exception('Unsupported LUA type sent as a script message (data=%r)'%self.data)
		else:
			return self.data


class PtpCHDKSession(PtpSession):
	
	def __init__(self,*args,**kargs):
		super(PtpCHDKSession,self).__init__(*args,**kargs)
		self.lock = threading.Lock()

	
	def chdkRequest(self,params):
		with self.lock:
			if type(params) is int:
				params = (params,)
				
			request = PtpRequest(PTP_OC_CHDK, self.sessionid, self.NewTransaction(), params)
			
			self.transport.send_ptp_request(request)
			response = self.transport.get_ptp_response(request)
			if response.respcode != PtpValues.StandardResponses.OK:
				raise PtpException(response.respcode)
			return response
	

	def chdkRequestWithSend(self,params,fmt=None,args=None,buffer=None):
		with self.lock:
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
		with self.lock:
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
		response = self.chdkRequestWithReceive((Operation.GetMemory,start,num))
		return response.data

	def SetMemory(self,addr,buffer):
		self.chdkRequestWithSend((Operation.SetMemory,addr,len(buffer)),buffer=buffer)
		return True
	
	def CallFunction(self,args):
		response = self.chdkRequestWithSend(Operation.CallFunction,args=args,fmt='I'*len(args))
		return response.params

	def Upload(self,remoteFilename,data):
		self.chdkRequestWithSend(
			Operation.UploadFile,
			fmt = 'I',
			args = (len(remoteFilename),),
			buffer = remoteFilename+data,
		)
		return True

	def Download(self,remoteFilename,stream=None):
		self.chdkRequestWithSend(
			(Operation.TempData,0),
			buffer = remoteFilename,
		)
		response = self.chdkRequestWithReceive(
			Operation.DownloadFile,
			stream = stream
		)
		if stream is None:
			return response.data[1]

	def ExecuteScript(self,script):
		response = self.chdkRequestWithSend((Operation.ExecuteScript,ScriptLanguage.LUA,0),buffer=script+'\x00')
		return response.params

	def GetVersion(self):
		response = self.chdkRequest(Operation.Version)
		return response.params

	def GetScriptStatus(self,scriptId):
		response = self.chdkRequest(Operation.ScriptStatus)
		assert len(response.params) == 1
		return response.params[0]
	
	def GetScriptSupport(self,scriptId):
		response = self.chdkRequest(Operation.ScriptSupport)
		assert len(response.params) == 1
		return response.params[0]
	
	def WriteScriptMessage(self,scriptId,message):
		assert message
		response = self.chdkRequestWithSend((Operation.WriteScriptMsg,scriptId),buffer=message)
		assert len(response.params) == 1
		return response.params[0]
	
	def ReadScriptMessage(self,scriptId):
		response = self.chdkRequestWithReceive(Operation.ReadScriptMsg)
		sm = ScriptMessage(type=response.params[0],subType=response.params[1],scriptId=response.params[2],data=response.data)
		if sm.type == ScriptMessageType.NONE:
			return None
		else:
			return sm
	
	def GetLiveData(self,flags=LiveViewFlag.VIEWPORT|LiveViewFlag.BITMAP|LiveViewFlag.PALETTE):
		response = self.chdkRequestWithReceive((Operation.GetLiveData,flags))
		frame = LiveViewFrame(response.data[1])
		return frame

