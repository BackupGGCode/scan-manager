from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from .core import BaseLayout, BaseWidget

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



#
# Fields
#

class BaseField(object):
	""" Base class for all control fields """
		
	def __init__(self,parent,**kargs):
		
		self.parent = parent
		
		self.error = None
		
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
			
	
	def recalculate(self,propertyName=None):
		if propertyName:
			toDo = [self._properties[propertyName]]
		else:
			toDo = self.recalculable
		
		for property in toDo:
			property.set(self.kargs[property.name])
			if isinstance(property,_QtProperty):
				property.toQt(self._qt)
			
	
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
	
		
	def __setattr__(self,k,v):
		if '_properties' in self.__dict__:
			if k in self._properties:
				self._properties[k].set(v)
				return
		self.__dict__[k] = v


	@property
	def form(self):
		return self.parent.form


	@property
	def group(self):
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
			if isinstance(p,_Form):
				break
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

#
# Common properties
#

Properties.core = Properties(
	# Core properies
	Property(name='name',type=str,required=True),
	Property(name='label',type=str),
	Property(name='depends',type=list,subType=str),
)
	
Properties.widget = Properties(
	# General widget properties
	QtProperty(name='styleSheet',type=str),
	QtProperty(name='enabled',type=bool),
	QtProperty(name='font',type=object),
	QtProperty(name='visible',type=object),
	QtProperty(name='graphicsEffect',type=object),
	QtProperty(name='inputMethodHints',type=object,
		options=[Qt.ImhDialableCharactersOnly,Qt.ImhDigitsOnly,Qt.ImhEmailCharactersOnly,Qt.ImhExclusiveInputMask,
				 Qt.ImhFormattedNumbersOnly,Qt.ImhHiddenText,Qt.ImhLowercaseOnly,Qt.ImhNoAutoUppercase,Qt.ImhNoPredictiveText,
				 Qt.ImhPreferLowercase,Qt.ImhPreferNumbers,Qt.ImhPreferUppercase,Qt.ImhUppercaseOnly,Qt.ImhUrlCharactersOnly]),
	QtProperty(name='whatsThis',type=str),
	QtProperty(name='toolTip',type=str),

	# General widget properties (size)
	QtProperty(name='fixedWidth',type=object),
	QtProperty(name='fixedHeight',type=object),
	QtProperty(name='minimumWidth',type=object),
	QtProperty(name='minimumHeight',type=object),
)


Properties.valueField = Properties(
	# General value-field properties
	Property(name='type'),
	Property(name='default'),
	Property(name='validate'),
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
)



#
# Concrete fields
#

		
class _Form(_AbstractGroup):
	Name = 'Form'

	QtClass = QtGui.QWidget

	Properties = Properties(
		Properties.formLayout,
		Properties.widget,
				
		Property(name='name',type=str,required=True),
		Property(name='contents',required=True),
	)
	

	def __init__(self,parent,**kargs):
		super(_Form,self).__init__(parent,**kargs)
		self.groupData = True
		
	
	def registerObject(self,field):
		self.fields[field.name] = field
		
		
	@property
	def form(self):
		return self

class Form(Factory):
	klass = _Form



class _LineEdit(BaseWidgetField):
	Name = 'LineEdit'
	QtClass = QtGui.QLineEdit
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,

		# Line-edit specific properties
		QtProperty(name='inputMask',type=str),
		QtProperty(name='maxLength',type=int),
		QtProperty(name='readOnly',type=bool,getter='isReadOnly'),
		QtProperty(name='placeholderText',type=str),
		QtProperty(name='alignment',type=int,
			flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
		),
		QtProperty(name='echoMode',type=int,
			options=[QtGui.QLineEdit.Normal,QtGui.QLineEdit.NoEcho,QtGui.QLineEdit.Password,QtGui.QLineEdit.PasswordEchoOnEdit]
		),
		QtProperty(name='completer',type=object),
		QtProperty(name='margins',type=tuple,subType=(int,int,int,int)),

		# Special properties for pysidline.forms
		Property(name='validator',type=callable),
	
		EventProperty(name='textEdited'),
		EventProperty(name='textChanged'),
	)
	
	def init(self):
		self.initValidator()
	
	def getValue(self):
		error,value = self.qtToValue(self._qt.text())
		self.setError(error)
		return value
		
	def setValue(self,v):
		if type(v) is int:
			v = unicode(v)
		self._qt.setText(v)

class LineEdit(Factory):
	klass = _LineEdit
	

	
class _TextEdit(BaseWidgetField):
	Name = 'TextEdit'
	QtClass = QtGui.QTextEdit
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,

		# Text-edit specific properties
		QtProperty(name='acceptRichText',type=bool),
		QtProperty(name='autoFormatting',type=int,flags=[QtGui.QTextEdit.AutoNone,QtGui.QTextEdit.AutoBulletList,QtGui.QTextEdit.AutoAll]),
		QtProperty(name='cursorWidth',type=bool),
		QtProperty(name='documentTitle',type=str),
		QtProperty(name='lineWrapColumnOrWidth',type=int),
		QtProperty(name='lineWrapMode',type=int,options=[QtGui.QTextEdit.NoWrap,QtGui.QTextEdit.WidgetWidth,QtGui.QTextEdit.FixedPixelWidth,QtGui.QTextEdit.FixedColumnWidth]),
		QtProperty(name='overwriteMode',type=bool),
		QtProperty(name='readOnly',type=bool,getter='isReadOnly'),
		QtProperty(name='textInteractionFlags',type=int,flags=[
			Qt.NoTextInteraction,Qt.TextSelectableByMouse,Qt.TextSelectableByKeyboard,Qt.LinksAccessibleByMouse,Qt.LinksAccessibleByKeyboard,Qt.TextEditable,
			Qt.TextEditorInteraction,Qt.TextBrowserInteraction]
		),
		QtProperty(name='undoRedoEnabled',type=bool,getter='isUndoRedoEnabled'),
		QtProperty(name='wordWrapMode',type=int,options=[QtGui.QTextOption.NoWrap,QtGui.QTextOption.WordWrap,QtGui.QTextOption.ManualWrap,QtGui.QTextOption.WrapAnywhere,
			QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere]
		),

		# Special properties for pysidline.forms
		Property(name='useHTML',type=bool,default=False),
		
		# Events
		EventProperty(name='textChanged'),
	)
	
	def getValue(self):
		if self.useHTML:
			return self._qt.toHtml()
		else:
			return self._qt.toPlainText()
		
	def setValue(self,v):
		if self.useHTML:
			return self._qt.setHtml(v)
		else:
			return self._qt.setPlainText(v)

class TextEdit(Factory):
	klass = _TextEdit
	


class _ComboOptions(_QtProperty):
	def toQt(self,q):
		if self.value is NOTSET:
			return
		q.clear()
		for ndx,item in enumerate(self.value):
			if type(item) != tuple:
				q.addItem(item)
			elif len(item) == 1:
				q.addItem(item[0])
			elif len(item) == 2:
				q.addItem(item[1],item[0])
			elif len(item) == 3:
				icon = QtGui.QIcon(item[3])
				q.addItem(icon,item[1],item[0])
			else:
				raise self._properties['options'].configurationError('invalid item at index %d'%ndx)

class ComboOptions(Factory):
	klass = _ComboOptions
	

	
class _ComboBox(BaseWidgetField):
	Name = 'ComboBox'
	QtClass = QtGui.QComboBox
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		
		ComboOptions(name='options'),
		
		# Combo-box specific properties
		QtProperty(name='editable',type=bool,getter='isEditable'),
		QtProperty(name='duplicatesEnabled',type=bool,getter='isEditable'),
		QtProperty(name='frame',type=bool,getter='hasFrame'),
		QtProperty(name='iconSize',type=QtCore.QSize),
		QtProperty(name='insertPolicy',type=int,options=[
			QtGui.QComboBox.NoInsert,QtGui.QComboBox.InsertAtTop,QtGui.QComboBox.InsertAtCurrent,QtGui.QComboBox.InsertAfterCurrent,QtGui.QComboBox.InsertBeforeCurrent,
			QtGui.QComboBox.InsertAlphabetically]
		),
		QtProperty(name='maxCount',type=int),
		QtProperty(name='maxVisibleItems',type=int),
		QtProperty(name='minimumContentsLength',type=int),
		QtProperty(name='sizeAdjustPolicy',type=int,options=[
			QtGui.QComboBox.AdjustToContents,QtGui.QComboBox.AdjustToContentsOnFirstShow,QtGui.
			QComboBox.AdjustToMinimumContentsLength,QtGui.QComboBox.AdjustToMinimumContentsLengthWithIcon]
		),
						
		# pysideline.forms specific properties
		Property(name='textAsValue',type=bool,default=False),
		Property(name='validator',type=callable),
		
		# Events
		EventProperty(name='currentIndexChanged'),
		EventProperty(name='editTextChanged'),
	)
	
	def init(self):
		self.initValidator()
	
	
	def getValue(self):
		if self.textAsValue:
			return self._qt.currentText()
		else:
			index = self._qt.currentIndex()
			data = self._qt.itemData(index)
			return data
	
		
	def setValue(self,v):
		if self.textAsValue:
			self._qt.lineEdit().setText(v)
		else:
			index = self._qt.findData(v)
			if index == -1:
				raise KeyError(v)
			self._qt.setCurrentIndex(index)

class ComboBox(Factory):
	klass = _ComboBox



class _SpinBox(BaseWidgetField):
	Name = 'SpinBox'
	QtClass = QtGui.QSpinBox 
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		
		# Spin-box specific properties
		QtProperty(name='accelerated',type=bool,getter='isAccelerated'),
		QtProperty(name='alignment',type=int,flags=[
			Qt.AlignLeft,Qt.AlignRight,Qt.AlignHCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignTop,Qt.AlignBottom,Qt.AlignVCenter,Qt.AlignCenter,
			Qt.AlignAbsolute,Qt.AlignLeading,Qt.AlignTrailing]
		),
		QtProperty(name='correctionMode',type=int,options=[QtGui.QAbstractSpinBox.CorrectToPreviousValue,QtGui.QAbstractSpinBox.CorrectToNearestValue]),
		QtProperty(name='keyboardTracking',type=bool),
		QtProperty(name='specialValueText',type=str),
		QtProperty(name='wrapping',type=bool),
		QtProperty(name='minimum',type=int),
		QtProperty(name='maximum',type=int),
		QtProperty(name='singleStep',type=int),
		QtProperty(name='suffix',type=str),
		QtProperty(name='prefix',type=str),
		
		# Events
		EventProperty(name='valueChanged'),
		EventProperty(name='editingFinished'),
	)
	
	def getValue(self):
		return self._qt.value()
	
		
	def setValue(self,v):
		self._qt.setValue(v)

class SpinBox(Factory):
	klass = _SpinBox



class _Slider(BaseWidgetField):
	Name = 'Slider'
	QtClass = QtGui.QSlider 
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		
		# QAbstractSlider specific properties
		QtProperty(name='invertedAppearance',type=bool),
		QtProperty(name='invertedControls',type=bool),
		QtProperty(name='maximum',type=int),
		QtProperty(name='minimum',type=int),
		QtProperty(name='orientation',options=[Qt.Horizontal,Qt.Vertical]),
		QtProperty(name='pageStep',type=int),
		QtProperty(name='singleStep',type=int),
		QtProperty(name='tracking',type=bool,getter='hasTracking'),

		# QSlider specific properties
		QtProperty(name='tickInterval',type=int),
		QtProperty(name='tickPosition',options=[QtGui.QSlider.NoTicks,QtGui.QSlider.TicksBothSides,QtGui.QSlider.TicksAbove,
			QtGui.QSlider.TicksBelow,QtGui.QSlider.TicksLeft,QtGui.QSlider.TicksRight]
		),
		
		
		# Events
		EventProperty(name='valueChanged'),
		EventProperty(name='rangeChanged'),
		EventProperty(name='sliderMoved'),
		EventProperty(name='sliderPressed'),
		EventProperty(name='sliderReleased'),
	)
	
	def getValue(self):
		return self._qt.value()
	
		
	def setValue(self,v):
		self._qt.setValue(v)

class Slider(Factory):
	klass = _Slider



class _GroupBox(_AbstractGroup):
	Name = 'GroupBox'
	QtClass = QtGui.QGroupBox 
	
	Properties = Properties(
		
		_AbstractGroup.Properties,
		Properties.core,
		Properties.widget,
		Properties.formLayout,

		QtProperty(name='title',type=str),
		QtProperty(name='flat',type=bool,getter='isFlat'),
		QtProperty(name='checkable',type=bool,getter='isCheckable'),
		QtProperty(name='checked',type=bool,getter='isChecked'),
		QtProperty(name='alignment',type=int,
			flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
		),
		
	)

	def getValue(self):
		v = super(_GroupBox,self).getValue()
		if self.checkable:
			v.setValue('checked',self.checked)
		return v
	
class GroupBox(Factory):
	klass = _GroupBox



class TableModel(QtCore.QAbstractTableModel):

	def __init__(self,columns=None,data=None,parent=None):
		super(TableModel, self).__init__(parent)
		if data is None:
			data = []
		if columns is None:
			columns = []
		self.columns = columns
		self.data = data

	def rowCount(self, index=QtCore.QModelIndex()):
		return len(self.data)

	def columnCount(self, index=QtCore.QModelIndex()):
		return len(self.columns)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if not 0 <= index.row() < len(self.data):
			return None

		if role != Qt.DisplayRole:
			return None
		
		column = self.columns[index.column()]
		return self.data[column.name]

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role != Qt.DisplayRole:
			return None

		if orientation != Qt.Horizontal:
			return None
		
		return self.columns[section].label

	def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
		self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)

		for row in range(rows):
			self.data.insert(position + row, dict())

		self.endInsertRows()
		return True

	def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
		self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows - 1)

		del self.data[position:position+rows]

		self.endRemoveRows()
		return True

	def setData(self, index, value, role=Qt.EditRole):
		if role != Qt.EditRole:
			return False

		if not index.isValid():
			return False
		
		if not (0 <= index.row() < len(self.addresses)):
			return False
		
		datum = self.data[index.row()]
		
		if index.column() < 0  or index.column() >= len(self.columns):
			return True
		
		column = self.columns[index.column()]
		datum[column.name] = value

		self.dataChanged.emit(index, index)
		return True

	def flags(self, index):
		if not index.isValid():
			return Qt.ItemIsEnabled
		return Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable)
