from .common import *

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
		value = self._qt.text()
		return value
		
	def setRawValue(self,v):
		if v == NOTSET or v is None:
			self._qt.clear()
			return
		if type(v) in (int,float):
			v = unicode(v)
		self._qt.setText(v)
		
	def clear(self):
		self._qt.clear()

class LineEdit(Factory):
	klass = _LineEdit
	

	