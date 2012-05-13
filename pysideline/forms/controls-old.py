"""
TODO:

-- enhancements
	File: create the QFileDialog ourselves and have a full set of properties for it
	EventProperty can be marked as 'default' which means it is used if none is specified

-- extra fields, e.g.
	QDateTimeEdit based field
	QDateEdit based field
	QTimeEdit based field
	RadioButtons: dynamically creates QRadioButtons in a QButtonGroup based on options
	Color field using QColorDialog
	? QTreeView based field (perhaps as a property editor)
	? QColumnView based field
	? QCalenderWidget based field
	? Font field using QFontDialog
	? QLCDNumber based field
	? Syntax highlighting for TextEdit fields
	? Add a QWhatsThis button to forms
"""

from . import base
from .base import *
import os

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
	
	def init(self):
		self._qt.setIconSize(QtCore.QSize(10,10))

	def layoutChildren(self):
		for field in self._children.values():
			icon = getattr(field,'labelIcon',None)
			if icon:
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
		
		Property(name='icon',type=QtGui.QIcon)
	)

	def markError(self,error):
		tabIndex = self._qt.parent().parent().indexOf(self._qt)
		self._qt.parent().parent().setTabIcon(tabIndex,QtGui.QIcon(':/error-16.png'))

	
	def clearError(self):
		tabIndex = self._qt.parent().parent().indexOf(self._qt)
		self._qt.parent().parent().setTabIcon(tabIndex,QtGui.QIcon())

class Tab(Factory):
	klass = _Tab



class _LineEdit(BaseWidgetField):

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
		EventProperty(name='textChanged',isDefault=True),
	)
	
	def init(self):
		self.initValidator()
	
	def getRawValue(self):
		error,value = self.qtToValue(self._qt.text())
		return value
		
	def setRawValue(self,v):
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
		QtProperty(name='wordWrapMode',options=[QtGui.QTextOption.NoWrap,QtGui.QTextOption.WordWrap,QtGui.QTextOption.ManualWrap,QtGui.QTextOption.WrapAnywhere,
			QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere]
		),

		# Special properties for pysidline.forms
		Property(name='useHTML',type=bool,default=False),
		
		# Events
		EventProperty(name='textChanged',isDefault=True),
	)
	
	def getRawValue(self):
		if self.useHTML:
			return self._qt.toHtml()
		else:
			return self._qt.toPlainText()
		
	def setRawValue(self,v):
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
		EventProperty(name='currentIndexChanged',isDefault=True),
		EventProperty(name='editTextChanged'),
	)
	
	def init(self):
		self.initValidator()
	
	
	def getRawValue(self):
		if self.textAsValue:
			return self._qt.currentText()
		else:
			index = self._qt.currentIndex()
			data = self._qt.itemData(index)
			return data
	
		
	def setRawValue(self,v):
		if v is NOTSET:
			self.clear()
			return
		if self.textAsValue:
			self._qt.lineEdit().setText(v)
		else:
			index = self._qt.findData(v)
			if index == -1:
				raise KeyError(v)
			self._qt.setCurrentIndex(index)

	def clear(self):
		self._qt.setCurrentIndex(0)
		self._qt.clearEditText()

class ComboBox(Factory):
	klass = _ComboBox


class _SpinBox(BaseWidgetField):

	QtClass = QtGui.QSpinBox 
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		Properties.spinBox,
		
	)
	
	def getRawValue(self):
		return self._qt.value()
	
		
	def setRawValue(self,v):
		if v is NOTSET or v is None:
			self._qt.clear()
		else:
			self._qt.setValue(v)

	def clear(self):
		self._qt.clear()

class SpinBox(Factory):
	klass = _SpinBox



class _DoubleSpinBox(BaseWidgetField):

	QtClass = QtGui.QDoubleSpinBox 
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		Properties.spinBox,
		
		QtProperty(name='decimals',type=int),
	)
	
	def getRawValue(self):
		return self._qt.value()
	
		
	def setRawValue(self,v):
		if v is NOTSET or v is None:
			self._qt.clear()
		else:
			self._qt.setValue(v)

	def clear(self):
		self._qt.clear()

class DoubleSpinBox(Factory):
	klass = _DoubleSpinBox



class _Slider(BaseWidgetField):

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
		EventProperty(name='valueChanged',isDefault=True),
		EventProperty(name='rangeChanged'),
		EventProperty(name='sliderMoved'),
		EventProperty(name='sliderPressed'),
		EventProperty(name='sliderReleased'),
	)
	
	def getRawValue(self):
		return self._qt.value()
	
		
	def setRawValue(self,v):
		self._qt.setValue(v)

	def clear(self):
		self._qt.setValue(self._qt.minimum())

class Slider(Factory):
	klass = _Slider



class _GroupBox(base._AbstractGroup):

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

class GroupBox(Factory):
	klass = _GroupBox



class _Label(BaseWidgetField):

	QtClass = QtGui.QLabel
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		QtProperty(name='alignment',type=int,
			flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
		),
		QtProperty(name='scaledContents',type=bool,getter='hasScaledContents'),
		QtProperty(name='textFormat',options=[Qt.PlainText,Qt.RichText,Qt.AutoText,Qt.LogText]),
		QtProperty(name='textInteractionFlags',
			flags=[
				Qt.NoTextInteraction,Qt.TextSelectableByMouse,Qt.TextSelectableByKeyboard,Qt.LinksAccessibleByMouse,Qt.LinksAccessibleByKeyboard,
				Qt.TextEditable,Qt.TextEditorInteraction,Qt.TextBrowserInteraction
			],
		),
		QtProperty(name='wordWrap',type=bool),
		QtProperty(name='text',type=unicode),
		QtProperty(name='indent',type=int),
		QtProperty(name='margin',type=int),
		QtProperty(name='openExternalLinks',type=bool),
		QtProperty(name='pixmap',type=QtGui.QPixmap),
		QtProperty(name='picture',type=QtGui.QPicture),
		QtProperty(name='movie',type=QtGui.QMovie),
		
		# Convenience properties
		QtProperty(name='selectedText',setter=None),

		# Events
		EventProperty(name='linkActivated'),
		EventProperty(name='linkHovered'),
	)
	
	def getRawValue(self):
		return NOTSTORED

		
	def setRawValue(self,v):
		if v is NOTSET or v is None:
			self._qt.clear()
		else:
			self._qt.setText(v)


	def clear(self):
		self._qt.clear()

class Label(Factory):
	klass = _Label



class _CheckBox(BaseWidgetField):

	QtClass = QtGui.QCheckBox
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,
		Properties.valueField,
		
		# QCheckBox and QAbstractButton properties/settings
		QtProperty(name='tristate',type=bool,getter='isTristate'),
		QtProperty(name='text',type=unicode),
		QtProperty(name='shortcut',type=QtGui.QKeySequence),
		QtProperty(name='icon',type=QtGui.QIcon),
		QtProperty(name='iconSize',type=QtCore.QSize),
		
		# Events
		EventProperty(name='stateChanged'),
	)
	
	def getRawValue(self):
		cs = self._qt.checkState()
		if cs == Qt.Checked:
			return True
		elif cs == Qt.Unchecked:
			return False
		elif cs == Qt.PartiallyChecked:
			return None
	
		
	def setRawValue(self,v):
		if v is NOTSET:
			self.clear()
			
		if v is True:
			v = Qt.Checked
		elif v is False:
			v = Qt.Unchecked
		elif v is None:
			v = Qt.PartiallyChecked
		else:
			raise Exception('Invalid value for a checkbox %r (must be True, False or None)'%v)
		self._qt.setCheckedState(v)


	def clear(self):
		self._qt.setCheckedState(Qt.Unchecked)

class CheckBox(Factory):
	klass = _CheckBox



class _Dial(_Slider):

	QtClass = QtGui.QDial
	
	Properties = Properties(
		
		_Slider.Properties,
		
		# QDial properties
		QtProperty(name='notchSize',type=int),
		QtProperty(name='notchTarget',type=float),
		QtProperty(name='notchesVisible',type=bool),
		QtProperty(name='wrapping',type=bool),
	)
	
class Dial(Factory):
	klass = _Dial



class DirectoryField(BaseWidget,QtGui.QWidget):
	"""
	Input field + 'Browse...' button pair for selecting existing files/directories
	"""
	
	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.LeftToRight,)
		def init(self):
			self._up.setLayout(self)
			self.setContentsMargins(0,0,0,0)
			self.addWidget(self._up.Field)
			self.addWidget(self._up.Button)

	
	class Field(BaseWidget,QtGui.QLineEdit):
		pass


	class Button(BaseWidget,QtGui.QPushButton):
		def init(self):
			self.setText(self.tr('Browse...'))
			
		def onclicked(self):
			field = self._up._field
			mode = field.mode
			kargs = dict(parent=self,caption=field.caption or None,dir=field.directory or None,options=field.browserOptions or 0)
			if mode == FileMode.ExistingDirectory:
				out = QtGui.QFileDialog.getExistingDirectory(**kargs)
			elif mode == FileMode.OpenFileName:
				out,filter = QtGui.QFileDialog.getOpenFileName(**kargs)
			elif mode == FileMode.OpenFileNames:
				out,filter = QtGui.QFileDialog.getOpenFileNames(**kargs)
			elif mode == FileMode.SaveFileName:
				out,filter = QtGui.QFileDialog.getSaveFileName(**kargs)
			if out:
				self._up.Field.setText(out)



class FileMode(object):
	ExistingDirectory = 1
	OpenFileName = 2
	OpenFileNames = 3
	SaveFileName = 4

class _File(BaseWidgetField):

	QtClass = DirectoryField
	
	Properties = Properties(
		Properties.core,
		Properties.widget,
		Properties.valueField,

		Property(name='caption',type=unicode),
		Property(name='directory',type=unicode),
		Property(name='filter',type=unicode),
		Property(name='selectedFilter',type=unicode),
		Property(name='browserOptions',type=int,flags=[
			QtGui.QFileDialog.ShowDirsOnly,QtGui.QFileDialog.DontResolveSymlinks,QtGui.QFileDialog.DontConfirmOverwrite,QtGui.QFileDialog.DontUseNativeDialog,
			QtGui.QFileDialog.ReadOnly,QtGui.QFileDialog.HideNameFilterDetails,QtGui.QFileDialog.DontUseSheet
		]),
		Property(name='mode',options=[FileMode.ExistingDirectory,FileMode.OpenFileName,FileMode.OpenFileNames,FileMode.SaveFileName],default=FileMode.OpenFileName),
	)
	
	def getRawValue(self):
		return self._qt.Field.text()

	def setRawValue(self,v):
		return self._qt.Field.setText(v)
	
	def defaultValidator(self,v):
		if not v:
			return None
		elif self.mode == FileMode.ExistingDirectory:
			if not os.path.isdir(v):
				return 'Must refer to an existing directory'
		elif self.mode == FileMode.OpenFileName:
			if not os.path.isfile(v):
				return 'Must refer to an existing file'
		elif self.mode == FileMode.SaveFileName:
			if not os.path.exists(os.path.split(v)[0]):
				return 'Must be a valid filename in an existing directory'
		return None
	
class File(Factory):
	klass = _File

		

class _DateTimeEdit(BaseWidgetField):

	QtClass = QtGui.QDateTimeEdit
	
	Properties = Properties(
						
		Properties.core,
		Properties.widget,
		Properties.valueField,

		Properties.dateTimeEdit,
		
		EventProperty(name='dateChanged'),
		EventProperty(name='dateTimeChanged',isDefault=True),
		EventProperty(name='timeChanged'),
	)
	
	def getRawValue(self):
		return self.getDateTime()
	
	def setRawValue(self):
		return self.dateTime()
	
	def valueToRaw(self,v):
		out = QtCore.QDateTime()
		out.setDate(v.date())
		out.setTime(v.time())
		return out

	def rawToValue(self,v):
		return v.toPython()
	
class DateTimeEdit(Factory):
	klass = _DateTimeEdit



class _DateEdit(BaseWidgetField):

	QtClass = QtGui.QDateEdit
	
	Properties = Properties(
						
		Properties.core,
		Properties.widget,
		Properties.valueField,

		Properties.dateTimeEdit,
		
		EventProperty(name='dateChanged',isDefault=True),
	)
	
	def getRawValue(self):
		return self.getDate()
	
	def setRawValue(self):
		return self.date()
	
	def valueToRaw(self,v):
		out = QtCore.QDateTime()
		out.setDate(v.date())
		return out.date()

	def rawToValue(self,v):
		return v.toPython()
	
class DateEdit(Factory):
	klass = _DateEdit



class _TimeEdit(BaseWidgetField):

	QtClass = QtGui.QDateEdit
	
	Properties = Properties(
						
		Properties.core,
		Properties.widget,
		Properties.valueField,

		Properties.dateTimeEdit,
		
		EventProperty(name='timeChanged',isDefault=True),
	)
	
	def getRawValue(self):
		return self.getTime()
	
	def setRawValue(self):
		return self.time()
	
	def valueToRaw(self,v):
		out = QtCore.QDateTime()
		out.setDate(v.date())
		return out.time()

	def rawToValue(self,v):
		return v.toPython()
	
class TimeEdit(Factory):
	klass = _TimeEdit



