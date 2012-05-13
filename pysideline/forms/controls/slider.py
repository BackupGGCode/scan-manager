from .common import *

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



