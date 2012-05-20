"""
WORK IN PROGRESS
"""


from pysideline.forms import NOTSET
import collections


class SettingsMetaclass(type): 
	def __new__(cls, name, bases, dct):
		d = {}
		d['_contents'] = {}
		for k,v in dct.items():
			if type(v) is SettingsMetaclass or isinstance(v,quick):
				d['_contents'][k] = v
			else:
				d[k] = v
		return super(SettingsMetaclass, cls).__new__(cls, name, bases, d)



class quick(object):
	def __init__(self,**base):
		self.base = base
		
	def __call__(self,*args,**kargs):
		d = dict()
		d.update(self.base)
		d.update(kargs)
		return Value(*args,**d)
			
			
			
class BaseSetting(object):
	
	__metaclass__ = SettingsMetaclass



class Settings(BaseSetting):
	
	def __init__(self,parent=None,name=None):
		self.__dict__['_parent'] = parent
		self.__dict__['_name'] = name
		self.__dict__['_children'] = collections.OrderedDict()
		
		for k,v in self._contents.items():
			self._children[k] = v(parent=self,name=k)
	
	def __getattr__(self,k):
		if k not in self._children:
			raise AttributeError(k)
		
		return self._children[k]._getValue()
	
	def __setattr__(self,k,v):
		if k not in self._children:
			raise AttributeError(k)
		
		return self._children[k]._setValue(v)
		
	
	def _getValue(self):
		return self
	
	
	def _setValue(self,v):
		if v == NOTSET:
			for k,v in self._children:
				v._setValue(v)
			return
		
		for k,v in v.items():
			self._children[k]._setValue(v)
	
	
	def _update(self,d):
		for k,v in d.items():
			self._childern[k]._setValue(v)
		
	
	def _activate(self,app):
		for v in self._children.values():
			v._activate(app=app)
		


class SettingsDict(Settings):
	
	def __init__(self,parent,name):
		self.__dict__['_parent'] = parent
		self.__dict__['_name'] = name
		self.__dict__['_data'] = dict()
		
		
	def __setitem__(self,k,v):
		nv = self._contents['value'](name='value',parent=self)
		nv._setValue(v)
		
		self._data[k] = nv
		
		
	def __getitem__(self,k):
		return self._data[k]

	
	def __contains__(self,k):
		return k in self._data
	
	
	def __len__(self):
		return len(self._data)
	
	
	def _setValue(self,v):
		self._data = dict()

		if v == NOTSET:
			return
		
		self.update(v)
	
	
	def items(self):
		return self.k.items()


	def udpate(self,d):
		for k,v in d:
			self[k] = v


	def new(self,k):
		nv = self._contents['value'](name='value',parent=self)
		self._data[k] = nv
		return nv


	def __delitem__(self,k):
		del(self._data[k])


	def _activate(self,app):
		if not isinstance(self._contents['value'],Settings):
			return
		for v in self._data.values():
			v._activate(app=app)
		


class SettingsList(SettingsDict):
	def __init__(self,parent,name):
		Settings.__init__(self,parent=parent,name=name)
		self.__dict__['_data'] = list()

	
	def append(self,v=None):
		nv = self._contents['value'](name='value',parent=self)
		if v is not None:
			nv._setValue(v)
		self._data.append(nv)
		return nv

		
	def _setValue(self,v):
		self._data = dict()

		if v == NOTSET:
			return
		
		for i in v:
			self.append(i)
	
	def _activate(self,app):
		if not isinstance(self._contents['value'],Settings):
			return
		for i in self._data:
			i._activate(app=app)
	


class Value(BaseSetting):
	
	def __init__(self,name,parent,type=None,default=NOTSET):
		self.name = name
		self.parent = parent
		self.type = type
		self.default = default
		if default != NOTSET:
			self.value = self.default

		
	def _getValue(self):
		if not hasattr(self,'value'):
			raise Exception('%s has not been set'%self.name)
		return self.value

		
	def _setValue(self,v):
		if v == NOTSET:
			delattr(self,'value')
		if self.type is not None:
			if not isinstance(v,self.type):
				raise Exception('%s expects values of type %s'%(self.name,self.type))
		self.value = v


	def _activate(self,app):
		return
			
			

class SMSettings(Settings):
	
	class application(Settings):
		pass
	
		
	class project(Settings):
		outputDirectory = quick(type=unicode)
		class thumbnailSize(Settings):
			width = value(type=int,default=100) 
			height = value(type=int,default=100) 

		
	class camera(SettingsDict):
		
		class value(Settings):
			apiName = quick(type=unicode)
			cameraName = quick(type=unicode)
			rotate = quick(type=int,default=0)

			class pipelineSettings(Settings):			
				undistort = quick(type=object,default=None)
				class crop(Settings):
					top = quick(type=int,default=0)
					left = quick(type=int,default=0)
					bottom = quick(type=int,default=0)
					right = quick(type=int,default=0)
				
			@property
			def camera(self):
				return self.app.getCameraByName(self.apiName,self.cameraName)
		
		
		
if __name__ == '__main__':
	s = SMSettings()
	s.current.cameras.new(0)
	print s.current.cameras[0]
	print s.current.cameras[0].crop
	s.current.cameras[0].rotate = 11
	print s.current.cameras[0].rotate
	