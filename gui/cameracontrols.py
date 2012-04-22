from pysideline import *
from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import Qt
from backend import interface


class AbstractCameraControl(object):
	
	noLabel = False
	
	def __init__(self,qtparent,cameraProperty):
		self.cameraProperty = cameraProperty
		controlType = self.cameraProperty.getControlType()
		self.field = self.Field(qtparent,self)
		if self.noLabel:
			qtparent.Layout.addRow(self.field)
		else:
			qtparent.Layout.addRow(self.cameraProperty.getName() + ':',self.field)

		
	def fromCamera(self):
		"""
		Read a value from the camera into the field
		
		@return: None
		"""
		raise NotImplementedError
	
	
	def toCamera(self):
		"""
		Write a value from the field into the camera
		
		@return: None
		"""
		raise NotImplementedError
	


	def processSetResult(self,rc):
		"""
		Check the return value from setRawValue on the camera property and display an appropriate error if this value is invalid  
		"""
		if not rc:
			self.field._up._up._up.app.cameraPropertiesChanged(self.cameraProperty.getCamera())
			return
		else:
			### TODO: do something with this error string
			pass

class CameraControlFieldWidget(BaseWidget):
		def __init__(self,parent,cameraControl):
			self.cameraControl = cameraControl
			super(CameraControlFieldWidget,self).__init__(parent)


class CameraSliderControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QWidget):
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				self._up.setLayout(self)
			
		class Slider(BaseWidget,QtGui.QSlider):
			def init(self):
				self._up.Layout.addWidget(self,1)
				self.setOrientation(Qt.Horizontal)
			def onvalueChanged(self,raw):
				self._up.cameraControl.toCamera()

	
		class Text(BaseWidget,QtGui.QLabel):
			def init(self):
				self._up.Layout.addWidget(self,0)
				
	
	def fromCamera(self):
		self.field.Slider.blockSignals(True)
		self.field.Slider.setMaximum(self.cameraProperty.getMax())
		self.field.Slider.setMinimum(self.cameraProperty.getMin())
		self.field.Slider.setSingleStep(self.cameraProperty.getStep())
		self.field.Slider.setPageStep(self.cameraProperty.getStep())
		raw = self.cameraProperty.getRawValue()
		if raw is not None:
			self.field.Slider.setSliderPosition(raw)
		self.field.Text.setText(str(self.cameraProperty.rawToDisplay(raw)))
		if self.cameraProperty.isReadOnly():
			self.field.Slider.setEnabled(False)
		else:
			self.field.Slider.setEnabled(True)
		self.field.Slider.blockSignals(False)

	def toCamera(self):
		raw = self.field.Slider.sliderPosition()
		self.processSetResult(self.cameraProperty.setRawValue(raw))


	
class CameraStaticControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QLineEdit):
		def init(self):
			self.setReadOnly(True)

	def fromCamera(self):
		raw = self.cameraProperty.getRawValue()
		display = self.cameraProperty.rawToDisplay(raw)
		self.field.setText(unicode(display))

	def toCamera(self):
		return


		
class CameraLineEditControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QLineEdit):
		def oneditingFinished(self):
			if not self.cameraControl.cameraProperty.isReadOnly():
				self.cameraControl.toCamera()

	def fromCamera(self):
		self.field.blockSignals(True)
		raw = self.cameraProperty.getRawValue()
		display = self.cameraProperty.rawToDisplay(raw)
		self.field.setText(unicode(display))
		if self.cameraProperty.isReadOnly():
			self.field.setReadOnly(True)
		else:
			self.field.setReadOnly(False)
		self.field.blockSignals(False)

	def toCamera(self):
		display = self.field.text()
		raw = self.cameraProperty.displayToRaw(display)
		self.processSetResult(self.cameraProperty.setRawValue(raw))


		
class CameraComboControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QComboBox):
		def init(self):
			self.setEditable(False)
		def onactivated(self,event):
			self.cameraControl.toCamera()

	def fromCamera(self):
		self.field.blockSignals(True)
		self.field.clear()
		for raw,display in self.cameraProperty.getPossibleValues():
			self.field.addItem(str(display),raw)
		raw = self.cameraProperty.getRawValue()
		self.field.setCurrentIndex(self.field.findData(raw))
		if self.cameraProperty.isReadOnly():
			self.field.setEnabled(False)
		else:
			self.field.setEnabled(True)
		self.field.blockSignals(False)

	def toCamera(self):
		index = self.field.currentIndex()
		raw = self.field.itemData(index)
		self.processSetResult(self.cameraProperty.setRawValue(raw))



class CameraCheckboxControl(AbstractCameraControl):
	
	noLabel = True
	
	class Field(CameraControlFieldWidget,QtGui.QCheckBox):
		def init(self):
			self.setText(self.cameraControl.cameraProperty.getName())
		def onclicked(self):
			self.cameraControl.toCamera()
			
	def fromCamera(self):
		self.field.blockSignals(True)
		raw = self.cameraProperty.rawToDisplay(self.cameraProperty.getRawValue())
		if raw is None:
			self.field.setCheckState(Qt.PartiallyChecked)
		elif raw:
			self.field.setCheckState(Qt.Checked)
		else:
			self.field.setCheckState(Qt.Unchecked)
		self.field.blockSignals(False)
		
	def toCamera(self):
		state = self.field.checkState()
		if state == Qt.PartiallyChecked:
			self.processSetResult(self.cameraProperty.setRawValue(self.cameraProperty.displayToRaw(None)))
		elif state == Qt.Checked:
			self.processSetResult(self.cameraProperty.setRawValue(self.cameraProperty.displayToRaw(True)))
		else:
			self.processSetResult(self.cameraProperty.setRawValue(self.cameraProperty.displayToRaw(False)))


class CameraButtonControl(AbstractCameraControl):

	noLabel = True
	
	class Field(CameraControlFieldWidget,QtGui.QPushButton):
		def init(self):
			self.setText(self.cameraControl.cameraProperty.getName())
		def onpressed(self):
			self.cameraControl.processSetResult(self.cameraControl.cameraProperty.go())
	
	def fromCamera(self):
		self.field.blockSignals(True)
		if self.cameraProperty.isReadOnly():
			self.field.setEnabled(False)
		else:
			self.field.setEnabled(True)
		self.field.blockSignals(False)

	def toCamera(self):
		return


class CameraTwinButtonControl(AbstractCameraControl):

	noLabel = True

	class Field(CameraControlFieldWidget,QtGui.QWidget):
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				self._up.setLayout(self)
			
		class On(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self._up.cameraControl.cameraProperty.getName() + self.tr(' on'))
			def onpressed(self):
				self._up.cameraControl.processSetResult(self._up.cameraControl.cameraProperty.setRawValue(1))
	
		class Off(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self._up.cameraControl.cameraProperty.getName() + self.tr(' off'))
				
			def onpressed(self):
				self._up.cameraControl.processSetResult(self._up.cameraControl.cameraProperty.setRawValue(0))
	
	def fromCamera(self):
		self.field.blockSignals(True)
		if self.cameraProperty.isReadOnly():
			self.field.On.setEnabled(False)
			self.field.Off.setEnabled(False)
		else:
			self.field.On.setEnabled(True)
			self.field.Off.setEnabled(True)
		self.field.blockSignals(False)

	def toCamera(self):
		return



controlTypeToClass = {
	interface.ControlType.Combo: CameraComboControl,
	interface.ControlType.Slider: CameraSliderControl,
	interface.ControlType.Button: CameraButtonControl,
	interface.ControlType.Static: CameraStaticControl,
	interface.ControlType.LineEdit: CameraLineEditControl,
	interface.ControlType.Checkbox: CameraCheckboxControl,
	interface.ControlType.TwinButton: CameraTwinButtonControl,
}


def getControlClass(property):
	cls = controlTypeToClass[property.getControlType()]
	
		