from .common import *

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
	


