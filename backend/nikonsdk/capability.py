from .base import *


class EnumValue(object):
	
	def __init__(self,info,array):
		self.defaultIndex = info.default
		if info.default < len(array):
			self.default = array[info.default]
		else:
			self.default = None
		self.items = array
		self.valueIndex = info.value
		if info.value < len(array):
			self.value = array[info.value]
		else:
			self.value = None
	
	def __repr__(self):
		sItems = []
		for item in self.items:
			sItem = repr(item)
			if item == self.default and item == self.value:
				sItem += '(selected,default)'
			else:
				if item == self.default:
					sItem += '(selected)'
				if item == self.value:
					sItem += '(default)'
			sItems.append(sItem)
		return '<EnumValue %s>'%(', '.join(sItems))


class Capability(object):

	def __init__(self,obj,capInfo):
		self.obj = obj
		self.id = capInfo.id
		self.type = capInfo.type
		self.visibility = capInfo.visibility
		self.operations = capInfo.operations
		self.description = capInfo.description
		
		
	def __reprlong__(self,indent=''):
		s = ''
		s += indent + '<Capability %s>\n'%self.description
		s += indent + '  pyid: %s\n'%self.pyid
		s += indent + '  id: %d\n'%self.id
		s += indent + '  type: %s\n'%CapType[self.type]
		s += indent + '  visibility: %s\n'%' | '.join(CapVisibility[self.visibility])
		s += indent + '  operations: %s\n'%' | '.join(CapOperation[self.operations])
		return s

	def __repr__(self):
		return '<Capability %s>'%self.description
	

	def _get_pyid(self):
		d = self.description
		d = d.replace(' ','')
		d = d.replace('(','')
		d = d.replace(')','')
		d = d.replace('-','')
		d = d.replace('/','')
		return d
	pyid = property(_get_pyid)


	def set(self,data,dataType=None):

		assert self.operations & CapOperation.Set, 'Capability does not support set operations'
		
		if dataType is None:
			if self.type == CapType.Boolean:
				local = ctypes.c_int(data)
				dataType = DataType.BooleanPtr
			elif self.type == CapType.Integer:
				local = ctypes.c_int(data)
				dataType = DataType.IntegerPtr
			elif self.type == CapType.Unsigned:
				local = ctypes.c_uint(data)
				dataType = DataType.UnsignedPtr
			elif self.type == CapType.Float:
				local = ctypes.c_float(data)
				dataType = DataType.FloatPtr
			elif self.type == CapType.Point:
				local = MAIDPoint()
				local.x = data[0]
				local.y = data[1]
				dataType = DataType.PointPtr
			elif self.type == CapType.Size:
				local = MAIDSize()
				local.w = data[0]
				local.h = data[1]
				dataType = DataType.SizePtr
			elif self.type == CapType.Rect:
				local = MAIDRect()
				local.x = data[0]
				local.y = data[1]
				local.w = data[2]
				local.h = data[3]
				dataType = DataType.RectPtr
			elif self.type == CapType.String:
				local = MAIDString()
				local.str = data
				dataType = DataType.StringPtr
			#elif self.type == CapType.DateTime:
			#	local = MAIDDateTime()
			#	dataType = DataType.DateTimePtr
			#elif self.type == CapType.Range:
			#	local = MAIDRange()
			#	local.start? = data[0]
			#	local.end? = data[1]
			#	dataType = DataType.RangePtr
			#elif self.type == CapType.Enum:
			#	return self.getEnumValue()
			#elif self.type == CapType.Array:
			#	return self.setArrayValue()
			else:
				raise Exception('Unsupported captype for set, %d'%self.type)
			
			rc = self.obj.call(
				command = Command.CapSet,
				param = self.id,
				dataType = dataType,
				data = local,
			)
			checkError(rc)
		
		else:

			rc = self.obj.call(
				command = Command.CapSet,
				param = self.id,
				dataType = dataType,
				data = data,
			)
			checkError(rc)
		
	
	def start(self,cFun=None,cRef=None):
	
		obj = self.obj.struct

		rc = self.obj.call(
			command = Command.CapStart,
			param = self.id,
			cFun = cFun,
			cRef = cRef,
		)
		checkError(rc)


	def getArrayValue(self):
		
		obj = self.obj.struct
	
		assert self.type == CapType.Array, 'Non-array capability'
		assert self.operations & CapOperation.GetArray, 'Capability does not support array operations'
	
		localArray = MAIDArray()
	
		# get size
		rc = self.obj.call(
			command = Command.CapGet,
			param = self.id,
			dataType = DataType.ArrayPtr,
			data = localArray,
		)
		checkError(rc)
		
		localData = ArrayInfoToCType(localArray)()
		
		localArray.data = ctypes.addressof(localData)
	
		rc = self.obj.call(
			command = Command.CapGetArray,
			param = self.id,
			dataType = DataType.ArrayPtr,
			data = localArray,
		)
		checkError(rc)
		
		if localArray.type == ArrayType.PackedString:
			return str(localData[:]).split('\x00')[:-1]
			
		return localData

	def getEnumValue(self):
	
		obj = self.obj.struct

		assert self.type == CapType.Enum, 'Non-enum capability'
		assert self.operations & CapOperation.Get, 'Capability does not support get operations'
		assert self.operations & CapOperation.GetArray, 'Capability does not support get operations'
	
		localEnum = MAIDEnum()
	
		# get size
		rc = self.obj.call(
			command = Command.CapGet,
			param = self.id,
			dataType = DataType.EnumPtr,
			data = localEnum,
		)
		checkError(rc)
		
		localData = ArrayInfoToCType(localEnum)()
		
		localEnum.data = ctypes.addressof(localData)
		
		rc = self.obj.call(
			command = Command.CapGetArray,
			param = self.id,
			dataType = DataType.EnumPtr,
			data = localEnum,
		)
		checkError(rc)

		if localEnum.type == ArrayType.PackedString:
			items = str(localData[:]).split('\x00')[:-1]
		else:
			items = localData[:]
		
		return EnumValue(localEnum,items)


	def get(self):
		assert self.operations & CapOperation.Get, 'Capability does not support get operations'
		
		if self.type == CapType.Boolean:
			local = ctypes.c_int()
			dataType = DataType.BooleanPtr
		elif self.type == CapType.Integer:
			local = ctypes.c_int()
			dataType = DataType.IntegerPtr
		elif self.type == CapType.Unsigned:
			local = ctypes.c_uint()
			dataType = DataType.UnsignedPtr
		elif self.type == CapType.Float:
			local = ctypes.c_float()
			dataType = DataType.FloatPtr
		elif self.type == CapType.Point:
			local = MAIDPoint()
			dataType = DataType.PointPtr
		elif self.type == CapType.Size:
			local = MAIDSize()
			dataType = DataType.SizePtr
		elif self.type == CapType.Rect:
			local = MAIDRect()
			dataType = DataType.RectPtr
		elif self.type == CapType.String:
			local = MAIDString()
			dataType = DataType.StringPtr
		elif self.type == CapType.DateTime:
			local = MAIDDateTime()
			dataType = DataType.DateTimePtr
		elif self.type == CapType.Range:
			local = MAIDRange()
			dataType = DataType.RangePtr
		elif self.type == CapType.Enum:
			return self.getEnumValue()
		elif self.type == CapType.Array:
			return self.getArrayValue()
		else:
			raise Exception('Unsupported captype for get, %d'%self.type)
		
		rc = self.obj.call(
			command = Command.CapGet,
			param = self.id,
			dataType = dataType,
			data = local,
		)
		
		checkError(rc)

		return local


	def issueProcess(self,cFun=None,cRef=None):
		self.start(cFun=cFun, cRef=cRef)
		self.obj.idleLoop()

	def __call__(self,*args,**kargs):
		return self.start(*args,**kargs)

	

class Capabilities(object):

	def __init__(self,caps):
		self.__dict__['caps'] = caps
		self.__dict__['capD'] = {}
		for cap in caps:
			self.capD[cap.pyid.lower()] = cap
		
		self.caps.sort(key=lambda a: a.description)
		
	def __getattr__(self,k):
		cap = self.capD[k.lower()]
		if cap.operations & CapOperation.Start:
			return cap
		else:
			return cap.get()

	def __getitem__(self,k):
		return self.capD[k.lower()]

	def __setattr__(self,k,v):
		self.capD[k].set(v)
	
	def __contains__(self,k):
		return k.lower() in self.capD
	
	def __repr__(self):
		l = [cap.description for cap in self.caps]
		l.sort()
		return '<Capabilities %s>'%(', '.join(l))

	def __reprlong__(self,indent=''):
		s = ''
		s += '<Capabilities 0x%x>\n'%id(self)
		for cap in self.caps:
			s += cap.__reprlong__(indent=indent+'  ') + '\n'
		return s
	
	


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
		else:
			raise Exception('Invalid integer bytes %s'%ai.physicalBytes)
	elif ai.type == ArrayType.Unsigned:
		if ai.physicalBytes == 1:
			return ctypes.c_ubyte * ai.elements
		elif ai.physicalBytes == 2:
			return ctypes.c_uint16 * ai.elements
		elif ai.physicalBytes == 4:
			return ctypes.c_uint32 * ai.elements
		else:
			raise Exception('Invalid unsigned bytes %s'%ai.physicalBytes)
	elif ai.type == ArrayType.Float:
		return ctypes.c_float * ai.elements
	elif ai.type == ArrayType.PackedString:
		return ctypes.c_char * ai.elements
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
	


