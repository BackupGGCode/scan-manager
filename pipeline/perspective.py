from .common import *


class Perspective(PipelineStage):
	
	def __init__(self,calibrator):
		self.calibrator = calibrator
	
	def getName(self):
		return 'Perspective'
	
	def getId(self):
		return 'perspective'
	
	def process(self,pixmap):
		return self.correctPerspective(pixmap)

		

class CalibrationControlsBox(BaseWidget,QtGui.QGroupBox):
	
	def init(self):
		self._up.Layout.addRow(self)

	class Layout(BaseLayout,QtGui.QFormLayout):
		def init(self):
			self._up.setLayout(self)

	class CalbrationStateLabel(BaseWidget,QtGui.QLabel):
		
		def init(self):
			self._up.Layout.addRow(self)
			self.update()
			self.app.calibrationDataChanged.connect(self.update)
			
		def update(self):
			cameraIndex = self._up._up.getCameraIndex()
			if self.aq.camera.settings.undistort[cameraIndex] and self.aq.camera.settings.undistort[cameraIndex].isReady():
				self.setText(self.tr('<p>Calibration configured</p>'))
			else:
				self.setText(self.tr('<p>No calibration configured</p>'))


	class CorrectCheckbox(BaseWidget,QtGui.QCheckBox):
		def init(self):
			self._up.Layout.addRow(self)
			self.setText(self.tr('Correct images using calibration data'))
			self.app.calibrationDataChanged.connect(self.update)
			cameraIndex = self._up._up.getCameraIndex()
			if self.aq.camera.settings.undistort[cameraIndex] and self.aq.camera.settings.undistort[cameraIndex].isActive():
				self.setChecked(True)
			else:
				self.setChecked(False) 
			
			
		def onstateChanged(self):
			cameraIndex = self._up._up.getCameraIndex()
			if self.aq.camera.settings.undistort[cameraIndex]:
				self.aq.camera.settings.undistort[cameraIndex].setActive(self.isChecked())
				

		def update(self):
			cameraIndex = self._up._up.getCameraIndex()
			if self.aq.camera.settings.undistort[cameraIndex] and self.aq.camera.settings.undistort[cameraIndex].isReady():
				self.show()
			else:
				self.hide()

		
	class CalibrateButton(BaseWidget,QtGui.QPushButton):
		def init(self):
			self._up.Layout.addRow(self)
			self.setText(self.tr('Calibrate with current image'))
			self.setChecked(self.app.settings.crop.get('enabled',False))
			
		def onclicked(self):
			if calibrate is None:
				e = QtGui.QMessageBox.critical(
					self.app.SetupWindow,
					self.tr('Error'),
					self.tr("""
						<p>Calibration is not available on your system. If you're <i>not</i> running on Windows check that you have
						OpenCV 2.3 for Python and NumPy installed and that the OpenCV Python bindings are on your Python path.</p> 
					""")
				)
				return
			
			cameraIndex = self._up._up.getCameraIndex()
			preview = self.app.previews[cameraIndex]
			
			if not preview.raw.hasImage():
				return
			
			dialog = calibrate.CalibrateDialog(self)
			dialog.setModal(True)
			dialog.open()
			dialog.go(preview.raw._pm,cameraIndex=cameraIndex)


