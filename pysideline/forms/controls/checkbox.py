from .common import *

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
		if v == NOTSET:
			self.clear()
			
		if v is True:
			v = Qt.Checked
		elif v is False:
			v = Qt.Unchecked
		elif v is None:
			v = Qt.PartiallyChecked
		else:
			raise Exception('Invalid value for a checkbox %r (must be True, False or None)'%v)
		self._qt.setCheckState(v)


	def clear(self):
		self._qt.setCheckState(Qt.Unchecked)

class CheckBox(Factory):
	klass = _CheckBox



