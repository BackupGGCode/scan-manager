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
	
	def __init__(self,**kargs):
		self.__dict__['_data'] = kargs
		self.__dict__['_errors'] = collections.OrderedDict()
	
	
	def _setValue(self,k,v):
		self._data[k] = v
	
	
	def _setError(self,k,v):
		self._errors[k] = v
	
		
	def _pp(self,indent=''):
		s = ''
		s += indent + '<%s>\n'%self.__class__.__name__
		for k,v in self._items():
			if isinstance(v,FormData):
				s += indent + '  %s:\n'%k
				s += v._pp(indent + '	')
			else:
				error = ''
				if k in self._errors:
					 error = '[%s]'%self._errors[k]
				s += indent + '  %s=%r %s\n'%(k,v,error)
		return s
	
	def _items(self):
		return self._data.items()

	def __getattr__(self,k):
		return self._data[k]
	
	def __setattr__(self,k,v):
		if k not in self._data:
			raise AttributeError(k)
		self._data[k] = v 



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
		
		expandedArgs = self.expandArgs(args)
		
		for propertyFactory in expandedArgs:
			property = propertyFactory(field,self)
			if property.name in self.contents:
				raise Exception('Property %s already exists in %s'%(property.name,self.field.__class__.__name__))
			self.contents[property.name] = property
			
			
	def expandArgs(self,args):
		"""
		If any L{Properties} objects are included in args expand them into a set of L{Property} objects
		"""
		out = []
		for i in args:
			if isinstance(i,Properties):
				out += self.expandArgs(i.args)
			else:
				out.append(i)
		return out

	
	def keys(self):
		return self.contents.keys()
	
	
	def values(self):
		return self.contents.values()
	
	
	def items(self):
		return self.contents.items()
	
	
	def getDefaultEvent(self):
		for i in self.contents.values():
			if isinstance(i,_EventProperty) and getattr(i,'isDefault',None):
				return i


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

		if getattr(self,'type',None) is not callable and not isinstance(v,Factory):
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
			
		# Validate the value type (if a type was specified)
		if hasattr(self,'type'):
			# special shortcuts for certain Qt types 
			if self.type is QtCore.QSize and type(v) is tuple:
				v = QtCore.QSize(*v)
			elif self.type is QtCore.QMargins and type(v) is tuple:
				v = QtCore.QMargins(*v)
			elif self.type is QtGui.QIcon and type(v) in (str,unicode):
				v = QtGui.QIcon(v)
			
			# check base type
			if self.type in (unicode,str):
				if type(v) not in (unicode,str):
					self.configurationError('must be a string/unicode value')
			elif self.type is callable:
				if not callable(v):
					self.configurationError('must be a callable object')
			elif not isinstance(v,self.type):
				self.configurationError('must be of type %r'%self.type)
			
			# check sub-type for lists/tuples
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
							self.configurationError('item at index %d should be of type %r'%(index,self.subType))
							
		if hasattr(self,'options'):
			if v not in self.options:
				self.configurationError('must be one of %r'%self.options)

		# Store the value
		self.value = v
	
	def get(self):
		return self.value
	
	def configurationError(self,text):
			raise ConfigurationError('%s in %s object %s %s'%(self.name,self.properties.field.__class__.__name__[1:],getattr(self.properties.field,'name',self.properties.field),text))

	def __repr__(self):
		valueS = ', '.join(['name=%s.%s'%(self.field.name,self.name)] + ['%s=%r'%(k,v) for k,v in self.__dict__.items() if k != 'name'])
		return '<%s %s>'%(self.__class__.__name__,valueS)
	
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
				if i.endswith('()'):
					q = getattr(q,i[:-2])()
				else:
					q = getattr(q,i)
		if hasattr(self,'setter'):
			k = self.setter
		else:
			n = self.name.split('_')[-1]
			k = 'set%s%s'%(n[0].upper(),n[1:])
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
		
		if getattr(self,'target',None):
			for i in self.target.split('.'):
				if i.endswith('()'):
					q = getattr(q,i[:-2])()
				else:
					q = getattr(q,i)
					
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

		for property in self._properties.values():
			v = kargs.get(property.name,NOTSET)
			if v is NOTSET and hasattr(property,'default') and property.default is not NOTSET:
				v = property.default
			if v is NOTSET:
				continue
			property.set(v,firstTime=True) # firstTime is set so don't calculate any calculated properties
			if property.recalculable:
				self.recalculable.append(property)
				
		for k,v in kargs.items():
			if k not in self._properties:
				raise ConfigurationError('Unknown property %s=%r in %r'%(k,v,self))


	def recalculate(self,propertyName=None):
		if propertyName:
			toDo = [self._properties[propertyName]]
		else:
			toDo = self.recalculable
		
		for property in toDo:
			if property.name not in self.kargs:
				raise ConfigurationError('Trying to recalculate property %s.%s but property has not been set'%(getattr(self,'name',repr(self)),property.name))
			property.set(self.kargs[property.name])
			#if isinstance(property,_QtProperty):
			#	property.toQt(self._qt)
			
	
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
		
		
	def __repr__(self):
		return '<%s %s>'%(self.__class__.__name__[1:],self.name)

#
# Common properties
#

Properties.core = Properties(
	# Core properies
	Property(name='name',type=str,required=True),
	Property(name='label',type=str),
	Property(name='depends'),
	Property(name='klass',type=type),
	Property(name='labelIcon',type=QtGui.QIcon),

	# Layout-related properties
	Property(name='row',type=int),
	Property(name='col',type=int),
	Property(name='rowSpan',type=int),
	Property(name='colSpan',type=int),
	Property(name='cellAlignment',type=int,flags=[
		Qt.AlignLeft,Qt.AlignRight,Qt.AlignHCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignTop,Qt.AlignBottom,Qt.AlignVCenter,Qt.AlignCenter,
		Qt.AlignAbsolute,Qt.AlignLeading,Qt.AlignTrailing]
	),
)
	
Properties.widget = Properties(
	# General widget properties
	QtProperty(name='styleSheet',type=str),
	QtProperty(name='enabled',type=bool),
	QtProperty(name='hidden',type=bool,getter='_get_hidden',setter='_set_hidden',target='_field'),
	QtProperty(name='font',type=QtGui.QFont),
	QtProperty(name='visible',type=object),
	QtProperty(name='graphicsEffect',type=object),
	QtProperty(name='inputMethodHints',type=object,
		options=[Qt.ImhDialableCharactersOnly,Qt.ImhDigitsOnly,Qt.ImhEmailCharactersOnly,Qt.ImhExclusiveInputMask,
				 Qt.ImhFormattedNumbersOnly,Qt.ImhHiddenText,Qt.ImhLowercaseOnly,Qt.ImhNoAutoUppercase,Qt.ImhNoPredictiveText,
				 Qt.ImhPreferLowercase,Qt.ImhPreferNumbers,Qt.ImhPreferUppercase,Qt.ImhUppercaseOnly,Qt.ImhUrlCharactersOnly]),
	QtProperty(name='whatsThis',type=str),
	QtProperty(name='toolTip',type=str),

	# General widget properties (size)
	QtProperty(name='fixedSize',type=QtCore.QSize),
	QtProperty(name='fixedWidth',type=int),
	QtProperty(name='fixedHeight',type=int),
	QtProperty(name='minimumSize',type=QtCore.QSize),
	QtProperty(name='minimumWidth',type=int),
	QtProperty(name='minimumHeight',type=int),
	QtProperty(name='maximumSize',type=QtCore.QSize),
	QtProperty(name='maximumWidth',type=int),
	QtProperty(name='maximumHeight',type=int),
)


Properties.valueField = Properties(
	# General value-field properties
	Property(name='type'),
	Property(name='default'),
	Property(name='validate',type=callable),
	Property(name='required',type=bool),
)		


Properties.formLayout = Properties(
	# Form layout properties
	QtProperty(name='fieldGrowthPolicy',target='Layout',options=[
		QtGui.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow,
		QtGui.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
		QtGui.QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint,
	]),
	QtProperty(name='formAlignment',target='Layout',type=int,
		flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
	),
	QtProperty(name='horizontalSpacing',target='Layout',type=int),
	QtProperty(name='labelAlignment',target='Layout',type=int,
		flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
	),
	QtProperty(name='rowWrapPolicy',target='Layout',options=[
		QtGui.QFormLayout.RowWrapPolicy.DontWrapRows,
		QtGui.QFormLayout.RowWrapPolicy.WrapAllRows,
		QtGui.QFormLayout.RowWrapPolicy.WrapLongRows,
	]),
	QtProperty(name='spacing',type=int,target='Layout'),
	QtProperty(name='verticalSpacing',type=int,target='Layout'),
	QtProperty(name='contentsMargins',type=QtCore.QMargins,target='Layout',setter='setContentsMargins'),
)


Properties.abstractSpinBox = Properties(
	# Spin-box specific properties
	
	# Abstract spin box
	QtProperty(name='accelerated',type=bool,getter='isAccelerated'),
	QtProperty(name='alignment',type=int,flags=[
		Qt.AlignLeft,Qt.AlignRight,Qt.AlignHCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignTop,Qt.AlignBottom,Qt.AlignVCenter,Qt.AlignCenter,
		Qt.AlignAbsolute,Qt.AlignLeading,Qt.AlignTrailing]
	),
	QtProperty(name='buttonSymbols',options=[QtGui.QAbstractSpinBox.UpDownArrows,QtGui.QAbstractSpinBox.PlusMinus,QtGui.QAbstractSpinBox.NoButtons]),
	QtProperty(name='correctionMode',type=int,options=[QtGui.QAbstractSpinBox.CorrectToPreviousValue,QtGui.QAbstractSpinBox.CorrectToNearestValue]),
	QtProperty(name='frame',type=bool,getter='hasFrame'),
	QtProperty(name='keyboardTracking',type=bool),
	QtProperty(name='readOnly',type=bool,getter='isReadOnly'),
	QtProperty(name='specialValueText',type=str),
	QtProperty(name='wrapping',type=bool),

)


Properties.spinBox = Properties(

	Properties.abstractSpinBox,
	
	# Spin box
	QtProperty(name='suffix',type=str),
	QtProperty(name='prefix',type=str),
	QtProperty(name='minimum'),
	QtProperty(name='maximum'),
	QtProperty(name='singleStep'),
		
	# Abstract spin box events (but not present in other child classes)
	EventProperty(name='valueChanged',isDefault=True),
	
	# Spin box events
	EventProperty(name='editingFinished'),
)


Properties.dateTimeEdit = Properties(

	Properties.abstractSpinBox,

	QtProperty(name='calendarPopup',type=bool),
	QtProperty(name='displayFormat',type=str),
	QtProperty(name='displayedSections',flags=[
		QtGui.QDateTimeEdit.NoSection,QtGui.QDateTimeEdit.AmPmSection,QtGui.QDateTimeEdit.MSecSection,QtGui.QDateTimeEdit.SecondSection,
		QtGui.QDateTimeEdit.MinuteSection,QtGui.QDateTimeEdit.HourSection,QtGui.QDateTimeEdit.DaySection,QtGui.QDateTimeEdit.MonthSection,QtGui.QDateTimeEdit.YearSection]
	),
	QtProperty(name='minimumDate',type=QtCore.QDate),
	QtProperty(name='maximumDate',type=QtCore.QDate),
	QtProperty(name='minimumTime',type=QtCore.QTime),
	QtProperty(name='maximumTime',type=QtCore.QTime),
	QtProperty(name='minimumDateTime',type=QtCore.QDateTime),
	QtProperty(name='maximumDateTime',type=QtCore.QDateTime),
	QtProperty(name='timeSpec',options=[Qt.LocalTime,Qt.UTC,Qt.OffsetFromUTC]),
	
	# Date time edit
	QtProperty(name='suffix',type=str),
	QtProperty(name='prefix',type=str),
	QtProperty(name='minimum'),
	QtProperty(name='maximum'),
	QtProperty(name='singleStep'),
		
	# Spin box events
	EventProperty(name='editingFinished'),
)


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
			depends = [depends]
			
		for item in depends:
			if '=' in item:
				# "myProperty=myOtherField.someEvent" or "myProperty=myOtherField" 
				propertyName = item.split('=')[0]
				item = item.split('=')[1]
			else:
				# "myOtherField.someEvent" or "myOtherField"
				propertyName = None
			if '.' in item:
				fieldName,eventName = item.split('.')
				field = self.form.getField(fieldName)
				event = field._properties[eventName]
			else:
				field = self.form.getField(item)
				event = field._properties.getDefaultEvent()
				if event is None:
					raise self._properties['depends'].configurationError('dependency %r -- field %s (%s) has no default event'%(item,field.name,field.__class__.__name__[1:]))
				
			event.notify(self.name,propertyName)
			
		
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
		
		klass = getattr(self,'klass',NOTSET) or self.QtClass 
		
		self._qt = klass()
		self._qt._field = self
		self._qt.setParent(qparent)

		for property in self._properties:
			if isinstance(property,_QtProperty):
				if not property.recalculable: 
					property.toQt(self._qt)
			if isinstance(property,_EventProperty):
				property.connect(self._qt)

		if hasattr(self._qt,'afterCreate'):
			self._qt.afterCreate()
			
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
		
	
	def rawToValue(self,v):
		type = getattr(self,'type',None)
		error = None
		value = None
		if type is int:
			if v and type(v) is not int:
				try:
					value = int(v)
				except:
					error = "must be an integer"
		elif type is float:
			if v and type(v) is not float:
				try:
					value = float(v)
				except:
					error = "must be an number" 
		elif type is unicode:
			if v and type(v) is not unicode:
				try:
					value = unicode(v)
				except:
					error = "could not convert to unicode"
		elif type is str:
			if v and type(v) is not str:
				value = str(v)
		else:
			value = v
		
		if getattr(self,'required',False) and not value:
			error = 'a value is required'

		return error,value


	def valueToRaw(self,v):
		return v
	
	
	def getValue(self):
		error,value = self.getValueAndError(mark=False)
		if error:
			return NOTSET
		else:
			return value
	
	
	def getValueAndError(self,mark=True):
		qtValue = self.getRawValue()
		error,value = self.rawToValue(qtValue)
		if not error and getattr(self,'validate',None):
			error = self.validate(value)
		
		if mark:
			if error:
				self.markError(error)
			else:
				self.clearError()
		return error,value


	def setValue(self,v):
		self.setRawValue(self.valueToRaw(v))

	
	def markError(self,error):
		if getattr(self,'_label',None):
			self._label.setStyleSheet('.%s { color: red; }'%self._label.__class__.__name__)
		#self._qt.setStyleSheet('.%s { background: #FF9999; }'%self._qt.__class__.__name__)

	
	def clearError(self):
		if getattr(self,'_label',None):
			self._label.setStyleSheet('')
		#self._qt.setStyleSheet('')
		
	
	def _set_hidden(self,v):
		self._qt.setHidden(v)
		if getattr(self,'_label',None):
			self._label.setHidden(v)
		self.form._qt.adjustSize()
		self.form._qt.parent().adjustSize()
			
			
	def _get_hidden(self):
		return self._qt.isHidden()
		


class _AbstractGroup(BaseWidgetField):
	
	Properties = Properties(
		Property(name='contents',required=True),
		Property(name='groupData',type=bool,default=False),
	)
	
	
	def __init__(self,parent,**kargs):
		self._fields = {}
		super(_AbstractGroup,self).__init__(parent=parent,**kargs)
		self._children = collections.OrderedDict([(i.name,i) for i in [fieldFactory(self) for fieldFactory in self.contents]])
		
		
	def registerObject(self,field):
		self._fields[field.name] = field
		p = self.parent
		while 1:
			if p is None:
				break
			if hasattr(p,'registerObject'):
				p.registerObject(field)
				break # other parents will be taken care of automatically now
			p = p.parent
		
		
	def getField(self,k):
		return self._fields[k]

	
	def create(self,qparent):
		
		# Create the main Qt widget
		
		klass = getattr(self,'klass',NOTSET) or self.QtClass 
		
		self._qt = klass()
		self._qt._field = self
		self._qt.setParent(qparent)

		# Now create the children and arrange them in a layout
		
		for field in self._children.values():
			field.create(self._qt)
		
		self.layoutChildren()
		
		# Set any generic Qt properties on the main widget and connect its events

		for property in self._properties:
			if isinstance(property,_QtProperty):
				if not property.recalculable: 
					property.toQt(self._qt)
			if isinstance(property,_EventProperty):
				property.connect(self._qt)

		# Exceute post-creation hooks

		if hasattr(self._qt,'afterCreate'):
			self._qt.afterCreate()

		# Initialize the control
			
		self.init()
		
		# Now hook up any dependencies and calculate the actual values of any properties that were passsed in as callable objects 
		# (we do this last to allow these functions to reference as many other fields/properties as possible) 

		for field in self._children.values():
			# must be done after everything is instantiated/registered
			field.connectDependencies()

		for field in self._children.values():
			field.recalculate()
			
		# And finally return the newly created object
		
		return self._qt

	
	def layoutChildren(self):
		self._qt.Layout = QtGui.QFormLayout()
		self._qt.setLayout(self._qt.Layout)
		
		for field in self._children.values():
			if getattr(field,'label',None):
				self._qt.Layout.addRow(field.label,field._qt)
				field._label = self._qt.Layout.labelForField(field._qt)
			else:
				self._qt.Layout.addRow(field._qt)
				field._label = None 

		
	def getValueAndError(self,mark=True):
		
		data = FormData()
		hasErrors = False
		
		for field in self._children.values():
			if field.hidden:
				continue
			error,value = field.getValueAndError(mark=mark)
			if value is NOTSTORED:
				continue
			if isinstance(value,FormData) and not field.groupData:
				data._data.update(value._data)
				data._errors.update(value._errors)
			else:
				data._setValue(field.name,value)
				if error:
					data._setError(field.name,error)
		
		if data._errors:
			hasErrors = True
		
		if mark:
			if hasErrors:
				self.markError(None)
			else:
				self.clearError()
		
		return hasErrors,data

		
	def setValue(self,v):
		if not self.groupData:
			raise Exception('Cannot set value for group (%s) unless groupData is True'%self.name)
		
		for k,v in v._items():
			self.getField(k).setValue(v)


	def clear(self):
		for child in self._children.values():
			child.clear()

	def markError(self,error):
		return

	
	def clearError(self):
		return

	@property
	def group(self):
		return self



class _AbstractGroupGrid(_AbstractGroup):
	
	def layoutChildren(self):
		self._qt.Layout = QtGui.QGridLayout()
		self._qt.setLayout(self._qt.Layout)
		
		for field in self._children.values():
			row = self._qt.Layout.rowCount()
			if getattr(field,'label',None):
				field._label = QtGui.QLabel()
				field._label.setText(field.label)
				field._label.setBuddy(field._qt)
				self._qt.Layout.addWidget(field._label,row,0)
				self._qt.Layout.addWidget(field._qt,row,1,getattr(field,'rowSpan',1),(2*getattr(field,'colSpan',1))-1)
			else:
				self._qt.Layout.addWidget(field._qt,row,0,getattr(field,'rowSpan',1),(2*getattr(field,'colSpan',1)))
				field._label = None
