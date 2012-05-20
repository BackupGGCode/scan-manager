from .common import *

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
		if v == NOTSET or v is None:
			self._qt.clear()
		else:
			self._qt.setValue(v)

	def clear(self):
		self._qt.clear()

class DoubleSpinBox(Factory):
	klass = _DoubleSpinBox



