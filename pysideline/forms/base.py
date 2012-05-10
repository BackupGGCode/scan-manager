from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from pysideline.core import BaseLayout, BaseWidget

import types
import collections
import inspect


class __NOTSET(object):
	def __nonzero__(self):
		return False
NOTSET = __NOTSET()

class __NOTSTORED(object):
	def __nonzero__(self):
		return False
NOTSTORED = __NOTSTORED()



class ConfigurationError(Exception):
	pass


class FormData(object):
	
	def __init__(self):
		pass
	
	
	def setValue(self,k,v):
		self.__dict__[k] = v
	
		
	def __setattr__(self,k,v):
		raise AttributeError(k)


	def _pp(self,indent=''):
		s = ''
		s += indent + '<%s>\n'%self.__class__.__name__
		for k,v in self.items():
			if isinstance(v,FormData):
				s += indent + '  %s:\n'%k
				s += v._pp(indent + '	')
			else:
				s += indent + '  %s=%r\n'%(k,v)
		return s
	
	def items(self):
		return self.__dict__.items()


class Factory(object):
	
	def __init__(self,*args,**kargs):
		self.args = args
		self.kargs = kargs

		
	def __call__(self,*args):
		return self.klass(*(args+self.args),**self.kargs)



class _Properties(object):
	
	def __init__(self,field,*args):
		self.field = field
		self.contents = collections.OrderedDict()
		
		expandedArgs = []
		for i in args:
			# if any L{Properties} objects are included in args expand them into a set of L{Property} objects
			if isinstance(i,Properties):
				expandedArgs += i.args
			else:
				expandedArgs.append(i)
		
		for propertyFactory in expandedArgs:
			property = propertyFactory(field,self)
			self.contents[property.name] = property

	
	def keys(self):
		return self.contents.keys()
	
	
	def values(self):
		return self.contents.values()
	
	
	def items(self):
		return self.contents.items()


	def __getitem__(self,k):
		return self.contents[k]

	
	def __contains__(self,k):
		return k in self.contents
	
	
	def __len__(self):
		return len(self.contents)
	
	
	def __iter__(self):
		for i in self.contents.itervalues():
			yield i
	
class Properties(Factory):
	klass = _Properties


def getNumArgs(v):
	while 1:
		if hasattr(v,'func_code'):
			v = v.func_code
			break
		if hasattr(v,'__call__'):
			v = v.__call__
		if hasattr(v,'im_func'):
			v = v.im_func
		if hasattr(v,'func_code'):
			v = v.func_code
		break
	if type(v) is not types.CodeType:
		return None
	return len(inspect.getargs(v).args)


class _Property(object):
	
	def __init__(self,field,properties,**kargs):
		self.field = field
		self.properties = properties
		self.value = NOTSET
		self.required = False
		self.recalculable = False
		self.__dict__.update(kargs)
		if not hasattr(self,'name'):
			raise Exception('no name') ### TODO: TEMP

	def set(self,v=NOTSET,firstTime=False):
		
		# Validate value 
		if v is NOTSET and self.required:
			raise self.configurationError('require %s to be set'%self.name)
		
		if getattr(self,'type',None) is not callable:
			numArgs = getNumArgs(v)
			if numArgs is not None:
				self.recalculable = True
				if firstTime:
					self.value = getattr(self,'default',NOTSET)
					return
				numArgs = getNumArgs(v)
				args = (self.field.form,self.field,self)
				v = v(*(args[:numArgs]))
			else:
				self.recalculable = False
		else:
			self.recalculable = False
			
		# Validate the property supplied
		if hasattr(self,'type'):
			if self.type is str and type(v) not in (unicode,str):
				self.configurationError('must be a string/unicode value')
			elif self.type is callable:
				if not callable(v):
					self.configurationError('must be a callable object')
			elif not isinstance(v,self.type):
				self.configurationError('must be of type %r'%self.type)
			if self.type in (tuple,list) and hasattr(self,'subType'):
				if type(self.subType) in (tuple,list):
					if len(self.subType) != len(v):
						self.configurationError('must be of type %r'%self.subType)
					for i in range(len(self.subType)):
						if not isinstance(v[i],self.subType[i]):
							self.configurationError('must be of type %r'%self.subType)
				else:
					for index,i in enumerate(v):
						if not isinstance(i,self.subType):
							self.configurationError('index %d should be of type %r'%(index,self.subType))
							
		if hasattr(self,'options'):
			if v not in self.options:
				self.configurationError('must be one of %r'%self.options)
				
		# Store the value
		self.value = v
	
	def get(self):
		return self.value
	
	def configurationError(self,text):
			raise ConfigurationError('%s in %s object %s %s'%(self.name,self.properties.field.__class__.__name__[1:],getattr(self.properties.field,'name',self.properties.field),text))

class Property(Factory):
	klass = _Property



class _QtProperty(_Property):
	
	def get(self):
		if getattr(self.field,'_qt',None):
			self.fromQt(self.field._qt)
		return self.value
		
	def set(self,v,firstTime=False):
		_Property.set(self,v,firstTime)
		if getattr(self.field,'_qt',None):
			self.toQt(self.field._qt)
	
	def toQt(self,q):
		if self.value is NOTSET:
			return
		if getattr(self,'target',None):
			for i in self.target.split('.'):
				q = getattr(q,i)
		if hasattr(self,'setter'):
			k = self.setter
		else:
			k = 'set%s%s'%(self.name[0].upper(),self.name[1:])
		setter = getattr(q,k)
		setter(self.value)

	def fromQt(self,q):
		if getattr(self,'target',None):
			for i in self.target.split('.'):
				q = getattr(q,i)
		if hasattr(self,'getter'):
			k = self.getter
		else:
			k = self.name
		getter = getattr(q,k)
		self.value = getter()

class QtProperty(Factory):
	klass = _QtProperty



class _DescriptorProperty(_Property):
	
	def get(self):
		return self.value
		
	def set(self,v,firstTime=False):
		self.value = v(None)
	
class DescriptorProperty(Factory):
	klass = _DescriptorProperty



class EventPropertyHandler(object):
	
	def __init__(self,property,field):
		self.property = property
		self.field = field
		self.toSignal = []
		v = self.property.value
		if not v:
			return
		
		if type(v) not in (list,tuple):
			v = v.split(',')
			
		for item in v:
			if '.' in item:
				# "myOtherField.someProperty"
				self.toSignal.append(tuple(item.split('.')))
			else:
				# "myOtherField"
				self.toSignal.append((item,None))
	
	
	def __call__(self,*args):
		for fieldName,propertyName in self.toSignal:					
			field = self.field.form.getField(fieldName)
			if propertyName:
				field.recalculate(propertyName)
			else:
				field.recalculate()



class _EventProperty(_Property):
	
	def connect(self,q):
		signalName = getattr(self,'signal',None)
		if not signalName:
			signalName = self.name
		signal = getattr(q,signalName)
		self.handler = EventPropertyHandler(self,self.field)
		signal.connect(self.handler)


	def notify(self,fieldName,propertyName):
		self.handler.toSignal.append((fieldName,propertyName))
	
class EventProperty(Factory):
	klass = _EventProperty



class Configurable(object):
	""" Base class for objects configurable via properties """
		
	def __init__(self,**kargs):
		
		self._properties = self.Properties(self)
		
		self.kargs = kargs
		self.recalculable = []

		for k,v in kargs.items():
			if k not in self._properties:
				raise ConfigurationError('Unknown property %s=%r in %r'%(k,v,self))
			property = self._properties[k]
			property.set(v,firstTime=True) # firstTime is set so don't calculate any calculated properties
			if property.recalculable:
				self.recalculable.append(property)


	def recalculate(self,propertyName=None):
		if propertyName:
			toDo = [self._properties[propertyName]]
		else:
			toDo = self.recalculable
		
		for property in toDo:
			property.set(self.kargs[property.name])
			if isinstance(property,_QtProperty):
				property.toQt(self._qt)
			
	
	def __getattr__(self,k):
		if '_properties' in self.__dict__ and k in self._properties:
			# used for every field
			return self._properties[k].get()
		else:
			raise AttributeError(k)
	
		
	def __setattr__(self,k,v):
		if '_properties' in self.__dict__:
			if k in self._properties:
				self._properties[k].set(v)
				return
		self.__dict__[k] = v

#
# Fields
#

class BaseField(Configurable):
	""" Base class for all control fields """
		
	def __init__(self,parent,**kargs):
		
		self.parent = parent
		self.error = None
		
		super(BaseField,self).__init__(**kargs)

		if self.group:
			self.group.registerObject(self)


	def connectDependencies(self):		
		depends = self.depends
		if depends is NOTSET:
			return
		if type(depends) not in (list,tuple):
			depends= [depends]
		for item in depends:
			if '=' in item:
				# "myProperty=myOtherField.someEvent"
				propertyName = item.split('=')[0]
				rest = item.split('=')[1]
				fieldName,eventName = rest.split('.')
			else:
				# "myOtherField.someEvent"
				propertyName = None
				fieldName,eventName = item.split('.')
				
			field = self.form.getField(fieldName)
			event = field._properties[eventName]
			event.notify(self.name,propertyName)
			
		
	def setError(self,error):
		self.error = error
		
	
	def __getattr__(self,k):
		if '_properties' in self.__dict__ and k in self._properties:
			# used for every field
			return self._properties[k].get()
		elif '_children' in self.__dict__ and k in self._children:
			# used for all field containers
			return self._children[k]
		elif '_fields' in self.__dict__ and k in self._fields:
			# used for forms
			return self._fields[k]
		else:
			raise AttributeError(k)
	
		
	@property
	def form(self):
		if not self.parent:
			return None
		return self.parent.form


	@property
	def group(self):
		if not self.parent:
			return None
		return self.parent.group



class QuickValidator(QtGui.QValidator):
	def __init__(self,parent,callable):
		self.callable = callable
		QtGui.QValidator.__init__(self,parent)
	
	def validate(self,s,pos):
		if getNumArgs(callable) == 1:
			rc = self.callable(s)
		elif getNumArgs(callable) == 2:
			rc = self.callable(s,pos)
		else:
			raise Exception('validator must take one or two arguments')
		if rc is True:
			return QtGui.QValidator.Acceptable
		elif rc is False:
			return QtGui.QValidator.Invalid
		elif rc is None:
			return QtGui.QValidator.Intermediate
		else:
			raise ConfigurationError('validator must return True, False or None')

	

class BaseWidgetField(BaseField):

	def create(self,qparent):
		
		self._qt = self.QtClass()
		self._qt._field = self
		self._qt.setParent(qparent)

		for property in self._properties:
			if isinstance(property,_QtProperty):
				if not property.recalculable: 
					property.toQt(self._qt)
			if isinstance(property,_EventProperty):
				property.connect(self._qt)

		self.init()
		
		return self._qt


	def init(self):
		pass


	def initValidator(self):
		if self.validator is None:
			return
		if self.validator is NOTSET:
			if self.type is int:
				validator = QtGui.QIntValidator(self._qt)
			elif self.type is float:
				validator = QtGui.QDoubleValidator(self._qt)
			else:
				return
		elif type(self.validator) in (str,unicode):
			validator = QtGui.QRegExpValidator(self.validator,self._qt)
		elif isinstance(self.validator,QtGui.QValidator):
			validator = self.validator
		elif callable(self.valdiator):
			validator = QuickValidator(self.field._qt,self.validator)
		else:
			raise self._properties['validator'].configurationError('invalid validator')
		self._qt.setValidator(validator)
		
	
	def qtToValue(self,v):
		### TODO: Not sure if this should handle errors at all -- user can supply a validator for it, but it is good to have a shortcut too...
		error = None
		value = None
		if self.type is int:
			if v:
				try:
					value = int(v)
				except:
					error = "must be an integer"
		if self.type is float:
			if v:
				try:
					value = float(v)
				except:
					error = "must be an number" 
		elif self.type is unicode:
			if v is not None:
				value = unicode(v)
		elif self.type is str:
			if v is not None:
				value = str(v)
		else:
			value = v
		
		return error,value
		


class _AbstractGroup(BaseWidgetField):
	
	Properties = Properties(
		Property(name='name',type=str,required=True),
		Property(name='contents',required=True),
		Property(name='groupData',type=bool,default=False),
	)
	
	
	def __init__(self,parent,**kargs):
		self.parent = parent
		self.fields = {}
		super(_AbstractGroup,self).__init__(parent=None,**kargs)
		self._children = collections.OrderedDict([(i.name,i) for i in [fieldFactory(self) for fieldFactory in self.contents]])
		
		
	def registerObject(self,field):
		self.fields[field.name] = field
		p = self.parent
		while 1:
			if p is None:
				break
			if hasattr(p,'registerObject'):
				p.registerObject(field)
			p = p.parent
		
		
	def getField(self,k):
		return self.fields[k]

	
	def create(self,qparent):
		
		super(_AbstractGroup,self).create(qparent)
		self._layout = QtGui.QFormLayout()
		self._qt.setLayout(self._layout)
		
		for field in self._children.values():
			field.create(self._qt)
			if getattr(field,'label',None):
				self._layout.addRow(field.label,field._qt)
			else:
				self._layout.addRow(field._qt)

		for field in self._children.values():
			# must be done after everything is instantiated/registered
			field.connectDependencies()

		for field in self._children.values():
			field.recalculate()
		
		return self._qt

		
	def getValue(self):
		
		data = FormData()
		
		for field in self._children.values():
			value = field.getValue()
			if value is NOTSTORED:
				continue
			if isinstance(value,FormData) and not field.groupData:
				for k,v in value.items():
					data.setValue(k,v)
			else:
				data.setValue(field.name,field.getValue())
		
		return data

		
	def setValue(self,v):
		if not self.groupData:
			raise Exception('Cannot set value for group (%s) unless groupData is True'%self.name)
		
		for k,v in v.items():
			self.getField(k).setValue(v)
		

	@property
	def group(self):
		return self


