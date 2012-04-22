#
# Based on: piggyphoto.py which is Copyright (C) 2010 Alex Dumitrache
#
import os
import ctypes
import time
import sys
import weakref

import structures
from constants import *
from ptp import *

WIN32 = (sys.platform == 'win32' or sys.platform == 'cygwin')
PTR = ctypes.pointer

retries = 1

# This is run if gp_camera_init returns -60 (Could not lock the device) and retries >= 1.
unmount_cmd = 'gvfs-mount -s gphoto2'



class CheckedTracedFunction(object):
	
	def __init__(self,api,f,checked=False,traced=False):
		self.api = api
		self.f = f
		self.checked = checked
		self.traced = traced
	
	def __call__(self,*args,**kargs):
		if self.traced: self.api.traceDLLCallStart(self.f,args,kargs)
		result = self.f(*args,**kargs)
		if self.traced: self.api.traceDLLCallEnd(self.f,args,kargs,result)
		if self.checked: self.api.check(result)
		return result
	
	def _getRestype(self):
		return self.f.restype
	def _setRestype(self,v):
		self.f.restype = v
	restype = property(_getRestype,_setRestype)


class CheckedTracedDLL(object):
	
	def __init__(self,api,dll,checked=False,traced=False):
		self.api = api
		self.dll = dll
		self.checked = checked
		self.traced = traced
		
	def __getattr__(self,k):
		f = getattr(self.dll,k)
		return CheckedTracedFunction(self.api,f,checked=self.checked,traced=self.traced)
		
	def __hasattr__(self,k):
		return hasattr(self.dll,k)
	

class API(object):
	
	def __init__(self):
		self.portInfoList = None
		self.cameraAbilitiesList = None
		self.objects = weakref.WeakValueDictionary()
	
	def open(self,dllDir='.',trace=False):
		
		global gp, context, PortInfo

		if WIN32:
			libgphoto2dll = r'cyggphoto2-2.dll'
			libgphoto2portdll = r'cyggphoto2_port-0.dll'
			os.environ['PATH'] += r';%s'%dllDir + '\\' 
			os.environ['IOLIBS'] = os.path.join(dllDir,'iolibs')
			os.environ['CAMLIBS'] = os.path.join(dllDir,'camlibs')
		else:
			libgphoto2dll = 'libgphoto2.so'
			libgphoto2portdll = 'libgphoto2_port-0.so'
		
		gp = ctypes.CDLL(libgphoto2dll)
		gpp = ctypes.CDLL(libgphoto2portdll)
		if trace:
			self.gp = CheckedTracedDLL(self,gp,checked=False,traced=False)
			self.gpp = CheckedTracedDLL(self,gpp,checked=False,traced=True)
			self.checkedGP = CheckedTracedDLL(self,gp,checked=True,traced=True)
			self.checkedGPP = CheckedTracedDLL(self,gpp,checked=True,traced=True)
		else:
			self.gp = gp
			self.gpp = gpp
			self.checkedGP = CheckedTracedDLL(self,gp,checked=True,traced=False)
			self.checkedGPP = CheckedTracedDLL(self,gpp,checked=True,traced=False)
		self.context = self.gp.gp_context_new()


	def getVersion(self,verbose=True):
		self.gp.gp_library_version.restype = ctypes.POINTER(ctypes.c_char_p)
		if not verbose:
			arrText = self.gp.gp_library_version(GP_VERSION_SHORT)
			return arrText[0]
		else:
			arrText = self.gp.gp_library_version(GP_VERSION_VERBOSE)
			out = []
			for s in arrText:
				if s is None:
					break
				out.append(s)
			return out
	
	def getPortInfoList(self):
		if not self.portInfoList:
			self.portInfoList = PortInfoList(self)
			self.register(self.portInfoList)
		return self.portInfoList
	
	def getCameraAbilitiesList(self):
		if not self.cameraAbilitiesList:
			self.cameraAbilitiesList = CameraAbilitiesList(self)
			self.register(self.cameraAbilitiesList)
		return self.cameraAbilitiesList
	
	
	def getCameras(self):
		portInfoList = self.getPortInfoList()
		cameraAbilitiesList = self.getCameraAbilitiesList()
		cameraList = CameraList(self)
		cameraAbilitiesList.detect(portInfoList,cameraList)
		
		out = []
		for i,(model,port) in enumerate(cameraList):
			camera = Camera(self,autoInit=False)
			camera.model = model
			camera.port = port
			abilities = cameraAbilitiesList[model]
			self.checkedGP.gp_camera_set_abilities(camera.c,abilities.c)
		
			portInfo = portInfoList.lookupPath(port)
			self.checkedGP.gp_camera_set_port_info(camera.c,portInfo)
			
			self.register(camera)
			out.append(camera)
		return out


	def getByAddress(self,address):
		return self.objects[address]
			

	def register(self,o):
		if not hasattr(o,'c'):
			return
		try: 
			address = ctypes.addressof(o.c)
		except:
			return
		self.objects[address] = o

	
	def check(self,result):
		if result < 0:
			self.gp.gp_result_as_string.restype = ctypes.c_char_p
			message = self.gp.gp_result_as_string(result)
			raise Exception('GPhoto Error - %s (%s)'%(message,result))


	def log(self,text):
		print 'libgphoto API WARNING:',text


	def traceDLLCallStart(self,function,args,kargs):
		sArgs = ['%r'%i for i in args]
		sArgs += ['%s=%r'%(k,v) for k,v in kargs.items()]
		s = '%s(%s)'%(function.__name__,','.join(sArgs))
		print s
		
		
	def traceDLLCallEnd(self,function,args,kargs,result):
		sArgs = ['%r'%i for i in args]
		sArgs += ['%s=%r'%(k,v) for k,v in kargs.items()]
		s = '%s(%s) -> %r'%(function.__name__,','.join(sArgs),result)
		print s
		
		


class PortInfoList(object):

	def __init__(self,api):
		self.api = api
		self.c = ctypes.c_void_p()
		self.cache = {}
		self.api.checkedGPP.gp_port_info_list_new(PTR(self.c))
		self.api.checkedGPP.gp_port_info_list_load(self.c)


	def __len__(self):
		return self.api.checkedGPP.gp_port_info_list_count(self.c)


	def lookupPath(self,path):
		index = self.api.checkedGPP.gp_port_info_list_lookup_path(self.c, path)
		if index == -1:
			raise KeyError(path)
		return self[index]


	def lookupName(self,name):
		index = self.api.checkedGPP.gp_port_info_list_lookup_name(self.c, name)
		if index == -1:
			raise KeyError(name)
		return self[index]


	def __iter__(self):
		for i in range(len(self)):
			yield self[i]


	def __getitem__(self,index):
		if index not in self.cache:
			if self.api.getVersion() < '2.4.99':
				info = structures.PortInfo()
			else:
				info = structures.PortInfoNew()
			self.api.checkedGPP.gp_port_info_list_get_info(self.c, index, PTR(info))
			self.cache[index] = info
			self.api.register(info)
			self.cache[index] = info
		return self.cache[index]
	
	
	def __del__(self):
		self.api.checkedGP.gp_port_info_list_free(self.c)
	
	#
	# For remote invokers who can't do __getitem__ etc.
	#
	def count(self):
		return len(self)
	
	def get(self,index):
		return self[index]



class CameraList(object):
	
	def __init__(self,api):
		self.api = api
		self.c = ctypes.c_void_p()
		self.api.checkedGP.gp_list_new(PTR(self.c))


	def ref(self):
		self.api.checkedGP.gp_list_ref(self.c)

	def unref(self):
		self.api.checkedGP.gp_list_unref(self.c)

	def reset(self):
		self.api.checkedGP.gp_list_reset(self.c)

	def append(self, name, value):
		self.api.checkedGP.gp_list_append(self.c, name, value)

	def sort(self):
		self.api.checkedGP.gp_list_sort(self.c)
		
	def count(self):
		return len(self)
	
	def get(self,k):
		return self[k]

	def __len__(self):
		return self.api.checkedGP.gp_list_count(self.c)
		
	def __iter__(self):
		for i in range(len(self)):
			yield self[i]

	def find(self, name):
		index = ctypes.c_int()
		self.api.checkedGP.gp_list_find_by_name(self.c, PTR(index), name)
		return index.value

	def setName(self, index, name):
		self.api.checkedGP.gp_list_set_name(self.c, index, name)

	def __getitem__(self,k):
		value = ctypes.c_char_p()
		name = ctypes.c_char_p()
		if type(k) is str:
			name.value = k
			index = ctypes.c_int()
			self.api.checkedGP.gp_list_find_by_name(self.c, PTR(index), str(name))
			return self[index.value]
		else:
			self.api.checkedGP.gp_list_get_value(self.c, k, PTR(value))
			self.api.checkedGP.gp_list_get_name(self.c, k, PTR(name))
			return (name.value,value.value)

	def __setitem__(self,k,v):
		index = self.find(k)
		if index == -1:
			self.append(k,v)
		if type(k) in (int,long):
			self.api.checkedGP.gp_list_set_name(self.c, index, v[0])
			self.api.checkedGP.gp_list_set_value(self.c, index, v[1])
		else:
			self.api.checkedGP.gp_list_set_value(self.c, index, v)
		
	def __contains__(self,k):
		return self.find(k) != -1
		
	def items(self):
		name = ctypes.c_char_p()
		value = ctypes.c_char_p()
		out = []
		for i in range(len(self)):
			self.api.checkedGP.gp_list_get_name(self.c, i, PTR(name))
			self.api.checkedGP.gp_list_get_value(self.c, i, PTR(value))
			out.append((name.value,value.value))
		return out
	
	def values(self):
		return [i[1] for i in self.items()]
			
	def keys(self):
		return [i[1] for i in self.items()]
			
	def __del__(self):
		self.api.checkedGP.gp_list_free(self.c)

	def __repr__(self):
		return '<%s %r>'%(self.__class__.__name__,self.items())



class CameraAbilitiesList(object):

	def __init__(self,api):
		self.api = api
		self.c = ctypes.c_void_p()
		self.api.checkedGP.gp_abilities_list_new(PTR(self.c))
		self.api.checkedGP.gp_abilities_list_load(self.c, self.api.context)
		self._cache = {}

	def __del__(self):
		self.api.checkedGP.gp_abilities_list_free(self.c)

	def detect(self, portInfoList, cameraList):
		self._cache = {}
		self.api.checkedGP.gp_abilities_list_detect(self.c, portInfoList.c, cameraList.c, self.api.context)

	def findModel(self, model):
		return self.api.checkedGP.gp_abilities_list_lookup_model(self.c, model)

	def __len__(self):
		return self.api.checkedGP.gp_abilities_list_count(self.c)

		
	def __getitem__(self,k):
		if type(k) is (str):
			k = self.findModel(k)
			if k == -1:
				raise KeyError(k)
		if k >= len(self):
			raise IndexError(k)
		if k in self._cache:
			return self._cache[k]
		else:
			ab = CameraAbilities(self.api)
			self.api.checkedGP.gp_abilities_list_get_abilities(self.c, k, PTR(ab.c))
			self.api.register(ab)
			self._cache[k] = ab
			return ab

	def __repr__(self):
		return '<%s 0x%X len=%d>'%(self.__class__.__name__,id(self),len(self))



class CameraAbilities(object):
	
	_attrs = [i[0] for i in structures.CameraAbilities._fields_]
	
	def __init__(self,api):
		self.api = api
		self.c = structures.CameraAbilities()

	def __getattr__(self,k):
		if k.startswith('get'):
			canonical = k[3].lower() + k[4:]
			if canonical in self._attrs:
				return lambda: getattr(self.c,canonical)
		raise KeyError(k)
	

	def pprint(self,indent=''):
		out = ''
		out += indent + '<%s 0x%X>\n'%(self.__class__.__name__,id(self))
		for k in self._attrs:
			if k.startswith('reserved'):
				continue
			v = getattr(self.c,k)
			out += indent + '  %s: %r\n'%(k,v)
		return out



class Camera(object):

	def __init__(self,api,autoInit=True):
		self.api = api
		self.c = ctypes.c_void_p()
		self.initialized = False
		self.api.checkedGP.gp_camera_new(PTR(self.c))
		if autoInit:
			self.init()

	def init(self):
		if self.initialized:
			return
		for i in range(1 + retries):
			rc = self.api.gp.gp_camera_init(self.c, self.api.context)
			if rc == 0:
				break
			elif rc == -60:
				if not WIN32:
					os.system(unmount_cmd)
				time.sleep(1)
				self.api.log('retrying camera initialisation')
		self.api.check(rc)
		self.initialized = True


	def reinit(self):
		self.api.checkedGP.gp_camera_unref(self.c)
		self.initialized = False
		self.init()

	def __del__(self):
		try:
			self.exit()
		finally:
			self.api.checkedGP.gp_camera_free(self.c)

	def ref(self):
		self.api.checkedGP.gp_camera_ref(self.c)

	def unref(self):
		self.api.checkedGP.gp_camera_unref(self.c)

	def exit(self):
		self.api.checkedGP.gp_camera_exit(self.c, self.api.context)

	def getSummary(self):
		txt = structures.CameraText()
		self.api.checkedGP.gp_camera_get_summary(self.c, PTR(txt), self.api.context)
		return txt.text
	
	def getManual(self):
		txt = structures.CameraText()
		self.api.checkedGP.gp_camera_get_manual(self.c, PTR(txt), self.api.context)
		return txt.text

	def getAbout(self):
		txt = structures.CameraText()
		self.api.checkedGP.gp_camera_get_about(self.c, PTR(txt), self.api.context)
		return txt.text

	def captureImage(self):
		path = structures.CameraFilePath()

		rc = 0
		for i in range(1 + retries):
			rc = self.api.gp.gp_camera_capture(self.c, GP_CAPTURE_IMAGE, PTR(path), self.api.context)
			if rc == 0:
				break
			else: 
				self.api.log('retrying image capture')
		self.api.check(rc)

		cfile = CameraFile(self.api,self,path.folder,path.name)
		return cfile.getData()

	def capturePreview(self, destpath = None):
		path = structures.CameraFilePath()
		cfile = CameraFile(self.api,self)

		rc = 0
		for i in range(1 + retries):
			rc = self.api.gp.gp_camera_capture_preview(self.c, cfile.c, self.api.context)
			if rc == 0:
				break
			else:
				self.api.log('retrying image capture preview')
		self.api.check(rc)

		if destpath:
			cfile.save(destpath)
		else:
			return cfile.getData()

	def downloadFile(self, srcfolder, srcfilename, destpath):
		cfile = CameraFile(self,srcfolder,srcfilename)
		cfile.save(destpath)
		self.api.checkedGP.gp_file_unref(cfile.c)

	def triggerCapture(self):
		self.api.checkedGP.gp_camera_trigger_capture(self.c, self.api.context)

	def getConfig(self):
		window = CameraWindow(self.api,self)
		self.api.checkedGP.gp_camera_get_config(self.c, PTR(window.c), self.api.context)
		self.api.register(window)
		self.window = window
		return window
	def setConfig(self, window):
		self.api.checkedGP.gp_camera_set_config(self.c, window.c, self.api.context)
		
		
	def getConfiguration(self):

		def widgetToDict(widget):
			type = widget.getType()
			readonly = widget.getReadonly()
			value = widget.getValue()
			out = dict(
				id = widget.getId(),
				name = widget.getName(),
				label = widget.getLabel(),
				type = type,
				info = widget.getInfo(),
				value = value,
				readonly = readonly,
				changed = 0,
				children = [],
			)
			if type in (GP_WIDGET_MENU,GP_WIDGET_RADIO):
				out['choices'] = widget.getChoices()
			elif type == GP_WIDGET_RANGE:
				out['range'] = widget.getRange()
			elif type in (GP_WIDGET_WINDOW,GP_WIDGET_SECTION):
				for child in widget.getChildren():
					out['children'].append(widgetToDict(child))
			return out
		
		self.getConfig()
		return widgetToDict(self.window)
			

	def setConfiguration(self,window):
		if not hasattr(self,'window'):
			self.getConfig()
		realWindow = self.window
		for section in window['children']:
			realSection = None
			for widget in section['children']:
				if widget['changed']:
					if not realSection:
						realSection = realWindow.getChildByName(section['name'])
					realWidget = realSection.getChildByName(widget['name'])
					realWidget.setValue(widget['value'])
		self.setConfig(realWindow)
					

	def getAbilities(self):
		ab = CameraAbilities()
		self.api.checkedGP.gp_camera_get_abilities(self.c, PTR(ab.c))
		self.api.register(ab)
		return ab
	def setAbilities(self, ab):
		self.api.checkedGP.gp_camera_set_abilities(self.c, ab.c)
	abilities = property(getAbilities, setAbilities)

	def getModel(self):
		return self.model

	def getPort(self):
		return self.port



class CameraFile(object):
	def __init__(self,api,cam=None,srcfolder=None,srcfilename=None):
		self.api = api
		self.c = ctypes.c_void_p()
		self.api.checkedGP.gp_file_new(PTR(self.c))
		if cam and srcfolder and srcfilename:
			try:
				self.api.checkedGP.gp_camera_file_get(cam.c,srcfolder,srcfilename,GP_FILE_TYPE_NORMAL,self.c,self.api.context)
			except:
				self.unref()
				raise

	def open(self, filename):
		self.api.checkedGP.gp_file_open(PTR(self.c), filename)

	def save(self, filename=None):
		if filename is None: filename = self.name
		self.api.checkedGP.gp_file_save(self.c, filename)

	def ref(self):
		self.api.checkedGP.gp_file_ref(self.c)

	def unref(self):
		self.api.checkedGP.gp_file_unref(self.c)

	def clean(self):
		self.api.checkedGP.gp_file_clean(self.c)

	def copy(self, source):
		self.api.checkedGP.gp_file_copy(self.c, source.c)

	def __del__(self):
		self.api.checkedGP.gp_file_free(self.c)

	def getName(self):
		name = ctypes.c_char_p()
		self.api.checkedGP.gp_file_get_name(self.c, PTR(name))
		return name.value
	
	def setName(self, name):
		self.api.checkedGP.gp_file_set_name(self.c, name)
		
	def getData(self):
		datap = ctypes.c_void_p()
		size = ctypes.c_ulong()
		self.api.checkedGP.gp_file_get_data_and_size(self.c,PTR(datap),PTR(size))
		if not size.value:
			return None
		data = ctypes.cast(datap,ctypes.POINTER(ctypes.c_char*size.value))
		return str(data.contents.raw)

	def __repr__(self):
		return '<%s %s>'%(self.__class__.__name__,self.getName())




class CameraWidget(object):

	def __init__(self,api,type=None,label=''):
		self.api = api
		self.c = ctypes.c_void_p()
		self._childCache = {}
		self.created = False
		if type is not None:
			self.created = True
			self.api.checkedGP.gp_widget_new(type,label,PTR(self.c))
			self.api.checkedGP.gp_widget_ref(self.c)
			
	def ref(self):
		self.api.checkedGP.gp_widget_ref(self.c)

	def unref(self):
		self.api.checkedGP.gp_widget_unref(self.c)

	#def __del__(self):
	#	if self.created:
	#		self.api.checkedGP.gp_widget_unref(self.c)

	def getInfo(self):
		info = ctypes.c_char_p()
		self.api.checkedGP.gp_widget_get_info(self.c, PTR(info))
		return info.value
	def setInfo(self, info):
		self.api.checkedGP.gp_widget_set_info(self.c, info)
	info = property(getInfo,setInfo)

	def getName(self):
		name = ctypes.c_char_p()
		self.api.checkedGP.gp_widget_get_name(self.c, PTR(name))
		return name.value
	def setName(self, name):
		self.api.checkedGP.gp_widget_set_name(self.c, name)
	name = property(getName,setName)

	def getId(self):
		id = ctypes.c_int()
		self.api.checkedGP.gp_widget_get_id(self.c, PTR(id))
		return id.value
	id = property(getId)

	def setChanged(self, changed):
		self.api.checkedGP.gp_widget_set_changed(self.c, int(changed))
	def getChanged(self):
		return self.api.checkedGP.gp_widget_changed(self.c)
	changed = property(getChanged, setChanged)

	def getReadonly(self):
		readonly = ctypes.c_int()
		self.api.checkedGP.gp_widget_get_readonly(self.c, PTR(readonly))
		return readonly.value
	def setReadonly(self, readonly):
		self.api.checkedGP.gp_widget_set_readonly(self._w, int(readonly))
	readonly = property(getReadonly, setReadonly)

	def getType(self):
		type = ctypes.c_int()
		self.api.checkedGP.gp_widget_get_type(self.c, PTR(type))
		return type.value
	type = property(getType)

	def getTypeString(self):
		return widget_types[self.type]
	typeString = property(getTypeString)

	def getLabel(self):
		label = ctypes.c_char_p()
		self.api.checkedGP.gp_widget_get_label(self.c, PTR(label))
		return label.value
	def setLabel(self, label):
		self.api.checkedGP.gp_widget_set_label(self.c, label)
	label = property(getLabel,setLabel)

	def getValue(self):
		if self.type in (GP_WIDGET_WINDOW,GP_WIDGET_SECTION):
			return None
		value = ctypes.c_void_p()
		rc = self.api.checkedGP.gp_widget_get_value(self.c, PTR(value))
		if self.type in (GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT):
			value = ctypes.cast(value, ctypes.c_char_p)
			value = value.value
		elif self.type == GP_WIDGET_RANGE:
			if value.value is None:
				value = None
			else:
				value = ctypes.cast(ctypes.pointer(value), ctypes.POINTER(ctypes.c_float))
				value = value.contents.value
		elif self.type in (GP_WIDGET_TOGGLE,GP_WIDGET_DATE):
			if value.value is None:
				value = 0
			else:
				value = value.value
		elif self.type == GP_WIDGET_BUTTON:
			raise Exception('Getting a value for a GP_WIDGET_BUTTON should return a CameraWidgetCallback but we haven\'t built that yet')
		else:
			raise Exception('Unknown widget type %r'%self.type)
		self.api.check(rc)
		return value
	def setValue(self, value):
		if value is None:
			return
		if self.type in (GP_WIDGET_WINDOW,GP_WIDGET_SECTION):
			return None
		elif self.type in (GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT):
			v = ctypes.c_char_p(value)
		elif self.type == GP_WIDGET_RANGE:
			v = PTR(ctypes.c_float(float(value)))
		elif self.type in (GP_WIDGET_TOGGLE,GP_WIDGET_DATE):
			v = PTR(ctypes.c_int(int(value)))
		elif self.type == GP_WIDGET_BUTTON:
			v = structures.CameraWidgetCallback(
				lambda cameraAddress,widgetAddress,context: 
					value( self.api.getByAddress(cameraAddress), self.api.getByAddress(widgetAddress) )
			)
		else:
			raise Exception('Unknown widget type %r'%self.type)
		self.api.checkedGP.gp_widget_set_value(self.c,v)
	value = property(getValue, setValue)

	def append(self, child):
		self.api.checkedGP.gp_widget_append(self.c,child.c)

	def prepend(self, child):
		self.api.checkedGP.gp_widget_prepend(self.c, child.c)

	def countChildren(self):
		return self.api.gp.gp_widget_count_children(self.c)

	def getChild(self, child_number):
		if child_number not in self._childCache:
			w = CameraWidget(self.api)
			self.api.checkedGP.gp_widget_get_child(self.c, child_number, PTR(w.c))
			self.api.checkedGP.gp_widget_ref(w.c)
			self._childCache[child_number] = w
			#self.api.register(w)
		return self._childCache[child_number]

	def getChildByLabel(self, label):
		if label not in self._childCache:
			w = CameraWidget(self.api)
			self.api.checkedGP.gp_widget_get_child_by_label(self.c, label, PTR(w.c))
			self._childCache[label] = w
			#self.api.register(w)
		return self._childCache[label]

	def getChildById(self, id):
		if id not in self._childCache:
			w = CameraWidget(self.api)
			self.api.checkedGP.gp_widget_get_child_by_id(self.c, id, PTR(w.c))
			self._childCache[id] = w
			#self.api.register(w)
		return self._childCache[id]

	def getChildByName(self, name):
		if name not in self._childCache:
			w = CameraWidget(self.api)
			self.api.checkedGP.gp_widget_get_child_by_name(self.c, name, PTR(w.c))
			self._childCache[name] = w
			#self.api.register(w)
		return self._childCache[name]

	def __getitem__(self,k):
		if k < self.countChildren():
			return self.getChild(k)
		else:
			raise IndexError(k)
		
	def __iter__(self):
		for i in range(self.countChildren()):
			yield self.getChild(i)

	def getChildren(self):
		children = []
		for i in range(self.countChildren()):
			child = self.getChild(i)
			children.append(child)
		return children
	children = property(getChildren)

	def getParent(self):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_parent(self.c, PTR(w.c))
		#self.api.register(w)
		return w
	parent = property(getParent)

	def getRoot(self):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_root(self.c, PTR(w.c))
		#self.api.register(w)
		return w
	root = property(getRoot)

	def setRange(self, range):
		"""cameraWidget.range = (min, max, increment)"""
		float = ctypes.c_float
		min, max, increment = range
		self.api.checkedGP.gp_widget_set_range(self.c, float(min), float(max), float(increment))
	def getRange(self):
		"""cameraWidget.range => (min, max, increment)"""
		min, max, increment = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
		self.api.checkedGP.gp_widget_get_range(self.c, PTR(min), PTR(max), PTR(increment))
		return (min.value, max.value, increment.value)
	range = property(getRange,setRange)

	def addChoice(self, choice):
		self.api.checkedGP.gp_widget_add_choice(self.c,choice)

	def countChoices(self):
		return self.api.gp.gp_widget_count_choices(self.c)

	def getChoice(self, choice_number):
		choice = ctypes.c_char_p()
		self.api.checkedGP.gp_widget_get_choice(self.c, choice_number, PTR(choice))
		return choice.value
	
	def getChoices(self):
		out = []
		for index in range(self.countChoices()):
			out.append(self.getChoice(index))
		return out

	def __repr__(self):
		return '<%s name=%s label=%s info=%s type=%s value=%s>'%(self.__class__.__name__, self.name, self.label, self.info, self.typeString, self.value)




class CameraWidgetSimple(object):
	pass
class CameraWindow(CameraWidget):
	def __init__(self,api,camera):
		super(CameraWindow,self).__init__(api=api,type=GP_WIDGET_WINDOW)
		self.camera = camera
		
	def writeToCamera(self):
		self.camera.setConfig(self)

