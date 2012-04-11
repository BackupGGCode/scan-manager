#
# Based on: piggyphoto.py which is Copyright (C) 2010 Alex Dumitrache
#

import os
import ctypes
import time
import sys

sys.path = ['.'] + sys.path

import structures
from constants import *
from ptp import *

WIN32 = (sys.platform == 'win32' or sys.platform == 'cygwin')
PTR = ctypes.pointer

retries = 1

# This is run if gp_camera_init returns -60 (Could not lock the device) and retries >= 1.
unmount_cmd = 'gvfs-mount -s gphoto2'



class GPhotoError(Exception):
	def __init__(self, result, message):
		self.result = result
		self.message = message
	def __str__(self):
		return '%s (%s)'%(self.message,self.result)
	


class CheckedDLL(object):
	
	def __init__(self,api,dll):
		self.api = api
		self.dll = dll
		
	def __getattr__(self,k):
		function = getattr(self.dll,k)

		def withCheck(*args,**kargs):
			result = function(*args,**kargs)
			self.api.check(result)
			return result
		
		return withCheck
		
	def __hasattr__(self,k):
		return hasattr(self.dll,k)
	
	

class API(object):
	
	def __init__(self):
		self.portInfoList = None
		self.cameraAbilitiesList = None
	
	def open(self,dllDir='.'):
		
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
			
		self.gp = ctypes.CDLL(libgphoto2dll)
		self.gpp = ctypes.CDLL(libgphoto2portdll)
		self.checkedGP = CheckedDLL(self,self.gp)
		self.checkedGPP = CheckedDLL(self,self.gpp)
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


	def register(self,o):
		pass

	
	def check(self,result):
		if result < 0:
			self.gp.gp_result_as_string.restype = ctypes.c_char_p
			message = self.gp.gp_result_as_string(result)
			raise GPhotoError(result,message)



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
	

	def getCamera(self):
		raise Exception('not done')
		camera = Camera(self.api,autoInit=False)
		
		
		#self.api.checkedGP.gp_camera_set_port_info(camera.c,portInfo)
		self.api.checkedGP.gp_camera_set_abilities(camera.c,self.c)
		camera.init()
		return camera
	
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
			rc = self.api.checkedGP.gp_camera_init(self.c, self.api.context)
			if rc == 0:
				break
			elif rc == -60:
				os.system(unmount_cmd)
				time.sleep(1)
				self.api.log('retrying camera initialisation')
		self.api.check(rc)
		self.initialized = True

	def reinit(self):
		self.api.checkedGP.gp_camera_free(self.c)
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

	def captureImage(self,destpath=None):
		path = structures.CameraFilePath()

		rc = 0
		for i in range(1 + retries):
			rc = self.api.gp.gp_camera_capture(self.c, GP_CAPTURE_IMAGE, PTR(path), self.api.context)
			if rc == 0: 
				break
			else: 
				self.api.log('retrying image capture')
		self.api.check(rc)

		if destpath:
			self.download_file(path.folder, path.name, destpath)
		else:
			return (path.folder, path.name)

	def capturePreview(self, destpath = None):
		path = structures.CameraFilePath()
		cfile = CameraFile()

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
			return cfile

	def downloadFile(self, srcfolder, srcfilename, destpath):
		cfile = CameraFile(self,srcfolder,srcfilename)
		cfile.save(destpath)
		self.api.checkedGP.gp_file_unref(cfile.c)

	def triggerCapture(self):
		self.api.checkedGP.gp_camera_trigger_capture(self.c, self.api.context)

	def getConfig(self):
		window = CameraWidget(GP_WIDGET_WINDOW)
		self.api.checkedGP.gp_camera_get_config(self.c, PTR(window.c), self.api.context)
		window.populateChildren()
		return window



class CameraFile(object):
	def __init__(self,cam=None,srcfolder=None,srcfilename=None):
		self.c = ctypes.c_void_p()
		self.api.checkedGP.gp_file_new(PTR(self.c))
		if cam:
			try:
				self.api.checkedGP.gp_camera_file_get(cam,srcfolder,srcfilename,GP_FILE_TYPE_NORMAL,self.c,self.api.context)
			except:
				self.unref()

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

	def __repr__(self):
		return '<%s %s>'%(self.__class__.__name__,self.getName())




class CameraWidget(object):

	def __init__(self,api,type=None,label=''):
		self.api = api
		self.c = ctypes.c_void_p()
		if kind is not None:
			self.api.checkedGP.gp_widget_new(type,label,PTR(self.c))
			self.api.checkedGP.gp_widget_ref(self.c)

	def ref(self):
		self.api.checkedGP.gp_widget_ref(self.c)

	def unref(self):
		self.api.checkedGP.gp_widget_unref(self.c)

	def __del__(self):
		# TODO fix this or find a good reason not to
		#print "widget(%s) __del__" % self.name
		#check(gp.gp_widget_unref(self._w))
		pass

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
		self.api.checkedGP.gp_widget_set_changed(self.c, changed)
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
		value = ctypes.c_void_p()
		rc = self.api.gp.gp_widget_get_value(self.c, PTR(value))
		if self.type in [GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT]:
			value = ctypes.cast(value.value, ctypes.c_char_p)
		elif self.type == GP_WIDGET_RANGE:
			value = ctypes.cast(value.value, ctypes.POINTER(ctypes.c_float))
		elif self.type in [GP_WIDGET_TOGGLE, GP_WIDGET_DATE]:
			#value = ctypes.cast(value.value, ctypes.c_int_p)
			pass
		else:
			return None
		self.api.check(rc)
		return value.value
	def setValue(self, value):
		if self.type in (GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT):
			value = ctypes.c_char_p(value)
		elif self.type == GP_WIDGET_RANGE:
			value = ctypes.POINTER(ctypes.c_float)(value) # this line not tested
		elif self.type in (GP_WIDGET_TOGGLE, GP_WIDGET_DATE):
			value = PTR(ctypes.c_int(value))
		else:
			return None # this line not tested
		self.api.checkedGP.gp_widget_set_value(self.c, value)
	value = property(getValue, setValue)

	def append(self, child):
		self.api.checkedGP.gp_widget_append(self.c,child.c)

	def prepend(self, child):
		self.api.checkedGP.gp_widget_prepend(self.c, child.c)

	def countChildren(self):
		return self.api.gp_widget_count_children(self.c)

	def getChild(self, child_number):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_child(self.c, child_number, PTR(w.c))
		self.api.checkedGP.gp_widget_ref(w.c)
		return w

	def getChildByLabel(self, label):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_child_by_label(self.c, label, PTR(w.c))
		return w

	def getChildById(self, id):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_child_by_id(self.c, id, PTR(w.c))
		return w

	def getChildByName(self, name):
		w = CameraWidget()
		# this fails in 2.4.6 (Ubuntu 9.10)
		self.api.checkedGP.gp_widget_get_child_by_name(self.c, name, PTR(w.c))
		return w

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
			children.append(self.getChild(i))
		return children
	children = property(getChildren)

	def getParent(self):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_parent(self.c, PTR(w.c))
		return w
	parent = property(getParent)

	def getRoot(self):
		w = CameraWidget()
		self.api.checkedGP.gp_widget_get_root(self.c, PTR(w.c))
		return w
	root = property(getRoot)

	def setRange(self, range):
		"""cameraWidget.range = (min, max, increment)"""
		float = ctypes.c_float
		min, max, increment = range
		self.api.checkedGP.gp_widget_set_range(self.c, float(min), float(max), float(increment))
	def getRange(self, range):
		"""cameraWidget.range => (min, max, increment)"""
		min, max, increment = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
		self.api.checkedGP.gp_widget_set_range(self._w, PTR(min), PTR(max), PTR(increment))
		return (min.value, max.value, increment.value)
	range = property(getRange,setRange)

	def addChoice(self, choice):
		self.api.checkedGP.gp_widget_add_choice(self.c,choice)

	def countChoices(self, choice):
		return self.api.gp.gp_widget_count_choices(self.c)

	def getChoice(self, choice_number):
		choice = ctypes.c_char_p()
		self.api.checkedGP.gp_widget_add_choice(self.c, choice_number, PTR(choice))
		return choice.value

	def createdoc(self):
		label = "Label: " + self.label
		info = "Info: " + (self.info if self.info != "" else "n/a")
		type = "Type: " + self.typestr
		#value = "Current value: " + str(self.value)
		childs = []
		for c in self.children:
			childs.append("  - " + c.name + ": " + c.label)
		if len(childs):
			childstr = "Children:\n" + '\n'.join(childs)
			return label + "\n" + info + "\n" + type + "\n" + childstr
		else:
			return label + "\n" + info + "\n" + type

	def _pop(self, simplewidget):
		widget = self
		for c in widget.children:
			simplechild = CameraWidgetSimple()
			if c.countChildren():
				setattr(simplewidget, c.name, simplechild)
				simplechild.__doc__ = c.createdoc()
				c._pop(simplechild)
			else:
				setattr(simplewidget, c.name, c)

			#print c.name, simplewidget.__doc__
		#print dir(simplewidget)

	def populateChildren(self):
		simplewidget = CameraWidgetSimple()
		setattr(self, self.name, simplewidget)
		simplewidget.__doc__ = self.createdoc()
		self._pop(simplewidget)

	def __repr__(self):
		return "%s:%s:%s:%s:%s" % (self.label, self.name, self.info, self.typestr, self.value)



class CameraWidgetSimple(object):
	pass




if __name__ == '__main__':
	api = API()
	api.open('..\win32')
	
	cameras = api.getCameras()
	for camera in cameras:
		print camera.captureImage()

