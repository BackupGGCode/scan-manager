from .common import *

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
				q.addItem(item[0],item[1])
			elif len(item) == 3:
				icon = QtGui.QIcon(item[3])
				q.addItem(icon,item[0],item[1])
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
		if self.textAsValue:
			if v is NOTSET or v is None:
				self._qt.lineEdit().clear()
			else:
				self._qt.lineEdit().setText(v)
		else:
			if v is NOTSET or v is None:
				self._qt.setCurrentIndex(0)
				return
			index = self._qt.findData(v)
			if index == -1:
				raise KeyError(v)
			self._qt.setCurrentIndex(index)

	def clear(self):
		self._qt.setCurrentIndex(0)
		self._qt.clearEditText()

class ComboBox(Factory):
	klass = _ComboBox


