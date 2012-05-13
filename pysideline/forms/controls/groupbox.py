from .common import *

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



