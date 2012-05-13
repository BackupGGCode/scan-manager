from .common import *

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



