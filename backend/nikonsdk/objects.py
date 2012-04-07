import ctypes
import sys
import time

from .base import *
from .capability import *

nikon = ctypes.windll.NkdPTP
d80 = ctypes.windll.LoadLibrary('D80_Mod.md3')

class Object(object):
	
	def __init__(self,parent=None,childId=None):

		self.procs = []

		self.d80 = d80
		self.parent = parent
		self.struct = MAIDObject()
		oClient = MAIDClient()
		self.struct.client = oClient
		
		self.open(childId)
		self.setCallbacks()


	def call(self,command,param=0,dataType=DataType.Null,data=None,cFun=None,cRef=None):
		
		if data is not None:
			data = ctypes.byref(data)
			
		return d80.MAIDEntryPoint(
			ctypes.byref(self.struct),
			command,
			param,
			dataType,
			data,
			cFun,
			cRef,
		)


	def open(self,childId):

		if self.parent:
			parentStruct = self.parent.struct
		else:
			parentStruct = None

		rc = d80.MAIDEntryPoint(
			byref(parentStruct),
			Command.Open,
			childId,
			DataType.ObjectPtr,
			byref(self.struct),
			None,
			0
		)
		checkError(rc)
		

	def close(self):
		self.call(command=Command.Close)

		
	def __del__(self):
		self.call(command=Command.Close)
		
	
	def getCapCount(self):

		obj = self.struct

		localCapCount = ctypes.c_ulong()
		
		rc = self.call(
			command = Command.GetCapCount,
			dataType = DataType.UnsignedPtr,
			data = localCapCount,
		)
		checkError(rc)
		
		return localCapCount.value


	def _getCaps(self):
		
		if not hasattr(self,'_caps'):
	
			obj = self.struct
	
			count = self.getCapCount()
			localInfo = (MAIDCapInfo * count)()
			while 1:
				try:
					rc = self.call(
						command = Command.GetCapInfo,
						param = count,
						dataType = DataType.UnsignedPtr,
						data = localInfo,
					)
					checkError(rc)
				except EBufferSize:
					continue
				else:
					break
			
			out = []
			for item in localInfo:
				out.append(Capability(self,item))
	
			self._caps = Capabilities(out)
		
		return self._caps

	caps = property(_getCaps)
	

	def setProc(self,cap,proc):
		#print 'SetProc on %s, cap=%s'%(self.caps.name.str,cap.description)
		localProc = MAIDCallback()
		localProc.proc = ctypes.cast(proc,CEventProc)
		self.procs.append(localProc)
		cap.set(dataType=DataType.CallbackPtr,data=localProc)

	def setCallbacks(self):

		if self.struct.type == ObjectType.Module:
			if 'progressProc' in self.caps:
				# Data event proc
				self.setProc(self.caps['progressProc'],ProgressProc())
			if 'eventProc' in self.caps:
				self.setProc(self.caps['eventProc'],EventProc())
			if 'uiRequestProc' in self.caps:
				self.setProc(self.caps['uiRequestProc'],UIRequestProc())

		elif self.struct.type == ObjectType.Source:
			if 'eventProc' in self.caps:
				# Source event proc
				self.setProc(self.caps['eventProc'],EventProc())
		
		elif self.struct.type == ObjectType.Item:
			if 'eventProc' in self.caps:
				# Item event proc
				self.setProc(self.caps['eventProc'],EventProc())
			
		elif self.struct.type == ObjectType.DataObj:
			if 'progressProc' in self.caps:
				# Data event proc
				self.setProc(self.caps['progressProc'],ProgressProc())
			if 'eventProc' in self.caps:
				# Data event proc
				self.setProc(self.caps['eventProc'],EventProc())
		
		else:
			raise Exception('Unkown object type %s'%self.struct.type)


	def commandAsync(self):

		rc = self.call(Command.Async)
		
		if rc == WPending.ident:
			return True
		else:
			checkError(rc)
			return False
		

	def idleLoop(self):
		while 1:
			rc = self.commandAsync()
			if not rc:
				break
			time.sleep(0.01)

	def __repr__(self):
		name = ''
		if 'name' in self.caps:
			name = str(self.caps.name.str).strip()
			if name:
				name = 'name=\'%s\' '%name
		return '<Object %s %sid=%s>'%(
			ObjectType[self.struct.type],
			name,
			self.struct.id,
		)
	

def ArrayInfoToCType(ai):
	if ai.type == ArrayType.Boolean:
		return ctypes.c_ubyte * ai.physicalBytes
	elif ai.type == ArrayType.Integer:
		if ai.physicalBytes == 1:
			return ctypes.c_byte * ai.elements
		elif ai.lphysicalBytes == 2:
			return ctypes.c_int16 * ai.elements
		elif ai.physicalBytes == 4:
			return ctypes.c_int32 * ai.elements
	elif ai.type == ArrayType.Unsigned:
		if ai.physicalBytes == 1:
			return ctypes.c_ubyte * ai.elements
		elif ai.physicalBytes == 2:
			return ctypes.c_uint16 * ai.elements
		elif ai.physicalBytes == 4:
			return ctypes.c_uint32 * ai.elements
	elif ai.type == ArrayType.Float:
		return ctypes.c_float * ai.elements
	else:
		raise Exception('as yet unimplemented type %s'%ai.type)

"""	
ArrayType.Integer = 1			# signed value that is 1, 2 or 4 bytes per element
ArrayType.Unsigned = 2			# unsigned value that is 1, 2 or 4 bytes per element
ArrayType.Float = 3				# DOUB_P elements
ArrayType.Point = 4				# NkMAIDPoint structures
ArrayType.Size = 5				# NkMAIDSize structures
ArrayType.Rect = 6				# NkMAIDRect structures
ArrayType.PackedString = 7		# packed array of strings
ArrayType.String = 8			# NkMAIDString structures
ArrayType.DateTime = 9			# NkMAIDDateTime structures
"""
	

