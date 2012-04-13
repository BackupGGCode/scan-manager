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

	class Field(CameraControlFieldWidget,QtGui.QSlider):
		def init(self):
			self.setOrientation(Qt.Horizontal)
		def onvalueChanged(self,raw):
			self.cameraControl.toCamera()

	def fromCamera(self):
		self.field.setMaximum(self.cameraProperty.getMax())
		self.field.setMinimum(self.cameraProperty.getMin())
		self.field.setSingleStep(self.cameraProperty.getStep())
		self.field.setPageStep(self.cameraProperty.getStep())
		raw = self.cameraProperty.getRawValue()
		if raw is not None:
			self.field.setSliderPosition(raw)

	def toCamera(self):
		raw = self.field.sliderPosition()
		self.processSetResult(self.cameraProperty.setRawValue(raw))


	
class CameraStaticControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QLineEdit):
		def init(self):
			self.setReadOnly(True)

	def fromCamera(self):
		raw = self.cameraProperty.getRawValue()
		display = self.cameraProperty.rawToDisplay(raw)
		self.field.setText(display)

	def toCamera(self):
		return


		
class CameraLineEditControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QLineEdit):
		def init(self):
			if self.cameraControl.cameraProperty.isReadOnly():
				self.setReadOnly(True)
		def oneditingFinished(self):
			if not self.cameraControl.cameraProperty.isReadOnly():
				self.cameraControl.toCamera()

	def fromCamera(self):
		raw = self.cameraProperty.getRawValue()
		display = self.cameraProperty.rawToDisplay(raw)
		self.field.setText(display)

	def toCamera(self):
		display = self.field.text()
		raw = self.cameraProperty.displayToRaw(display)
		self.processSetResult(self.cameraProperty.setRawValue(raw))


		
class CameraComboControl(AbstractCameraControl):

	class Field(CameraControlFieldWidget,QtGui.QComboBox):
		def onactivated(self,event):
			self.cameraControl.toCamera()

	def fromCamera(self):
		self.field.clear()
		for raw,display in self.cameraProperty.getPossibleValues():
			self.field.addItem(str(display),raw)
		raw = self.cameraProperty.getRawValue()
		self.field.setCurrentIndex(self.field.findData(raw))

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
		raw = self.cameraProperty.rawToDisplay(self.cameraProperty.getRawValue())
		if raw is None:
			self.field.setCheckState(Qt.PartiallyChecked)
		elif raw:
			self.field.setCheckState(Qt.Checked)
		else:
			self.field.setCheckState(Qt.Unchecked)
		
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
		if self.cameraProperty.getRawValue():
			self.field.setEnabled(True)
		else:
			self.field.setEnabled(False)
	
	def toCamera(self):
		return



controlTypeToClass = {
	interface.ControlType.Combo: CameraComboControl,
	interface.ControlType.Slider: CameraSliderControl,
	interface.ControlType.Button: CameraButtonControl,
	interface.ControlType.Static: CameraStaticControl,
	interface.ControlType.LineEdit: CameraLineEditControl,
	interface.ControlType.Checkbox: CameraCheckboxControl,
}


def getControlClass(property):
	cls = controlTypeToClass[property.getControlType()]
	
		