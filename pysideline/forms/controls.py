from . import base
from .base import *

#
# Concrete fields
#

		
class _Form(base._AbstractGroup):

	QtClass = QtGui.QWidget

	Properties = Properties(
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.formLayout,
		Properties.widget,
	)

	def __init__(self,parent,**kargs):
		super(_Form,self).__init__(parent,**kargs)
		self.groupData = True

		
	@property
	def form(self):
		return self

class Form(Factory):
	klass = _Form



class _TabbedForm(_Form):

	QtClass = QtGui.QTabWidget

	Properties = Properties(
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.widget,
		
		QtProperty(name='documentMode',type=bool),
		QtProperty(name='moveable',type=bool),
		QtProperty(name='tabsClosable',type=bool),
		QtProperty(name='usesScrollButtons',type=bool),
		QtProperty(name='elideMode',options=[
			Qt.ElideLeft,Qt.ElideMiddle,Qt.ElideNone,Qt.ElideRight
		]),
		QtProperty(name='iconSize',type=QtCore.QSize),
		QtProperty(name='tabPosition',options=[
			QtGui.QTabWidget.North,QtGui.QTabWidget.South,QtGui.QTabWidget.East,QtGui.QTabWidget.West
		]),
		QtProperty(name='tabShape',options=[
			QtGui.QTabWidget.Rounded,QtGui.QTabWidget.Triangular
		]),
	)

	def layoutChildren(self):
		for field in self._children.values():
			icon = field.icon
			if icon:
				if not isinstance(field.icon,QtGui.QIcon):
					icon = QtGui.QIcon(icon)
				self._qt.addTab(field._qt,icon,field.label)
			else:
				self._qt.addTab(field._qt,field.label)

class TabbedForm(Factory):
	klass = _TabbedForm



class _Tab(base._AbstractGroup):
	
	QtClass = QtGui.QWidget 
	
	Properties = Properties(
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.formLayout,
		Properties.widget,
		
		Property(name='icon',type=object)
	)

class Tab(Factory):
	klass = _Tab



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
		if v is NOTSET or v is None:
			self._qt.clear()
			return
		if type(v) in (int,float):
			v = unicode(v)
		self._qt.setText(v)
		
	def clear(self):
		self._qt.clear()

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

	def clear(self):
		self._qt.clear()

class TextEdit(Factory):
	klass = _TextEdit
	


class _ComboOptions(base._QtProperty):
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
		QtProperty(name='duplicatesEnabled',type=bool),
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

	def clear(self):
		self._qt.clear()

class ComboBox(Factory):
	klass = _ComboBox


Properties.spinBox = Properties(
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
	QtProperty(name='suffix',type=str),
	QtProperty(name='prefix',type=str),

	QtProperty(name='minimum'),
	QtProperty(name='maximum'),
	QtProperty(name='singleStep'),
		

	# Events
	EventProperty(name='valueChanged'),
	EventProperty(name='editingFinished'),
)


class _SpinBox(BaseWidgetField):
	Name = 'SpinBox'
	QtClass = QtGui.QSpinBox 
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		Properties.spinBox,
		
	)
	
	def getValue(self):
		return self._qt.value()
	
		
	def setValue(self,v):
		if v is NOTSET or v is None:
			self._qt.clear()
		else:
			self._qt.setValue(v)

	def clear(self):
		self._qt.clear()

class SpinBox(Factory):
	klass = _SpinBox



class _DoubleSpinBox(BaseWidgetField):
	Name = 'DoubleSpinBox'
	QtClass = QtGui.QDoubleSpinBox 
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		Properties.spinBox,
		
		QtProperty(name='decimals',type=int),
	)
	
	def getValue(self):
		return self._qt.value()
	
		
	def setValue(self,v):
		if v is NOTSET or v is None:
			self._qt.clear()
		else:
			self._qt.setValue(v)

	def clear(self):
		self._qt.clear()

class DoubleSpinBox(Factory):
	klass = _DoubleSpinBox



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

	def clear(self):
		self._qt.setValue(self._qt.minimum())

class Slider(Factory):
	klass = _Slider



class _GroupBox(base._AbstractGroup):
	Name = 'GroupBox'
	QtClass = QtGui.QGroupBox 
	
	Properties = Properties(
		
		base._AbstractGroup.Properties,
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
	
	def clear(self):
		return
	
class GroupBox(Factory):
	klass = _GroupBox
