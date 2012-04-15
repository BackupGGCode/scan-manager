from .common import *

from . import imageviewer
from .dialogs import ProgressDialog
import backend

import base
import log

import calibrator
import numpy as np


class CalibrateDialog(BaseDialog,QtGui.QDialog):
	
	
	def init(self):
		self.setWindowTitle(self.tr('ScanManager - calibration'))
		self.resize(600,600)
	
	def go(self,pm,cameraIndex=1):
		
		self.cameraIndex = cameraIndex
		
		if self.app.settings.calibrators[cameraIndex]:
			self.calibrator = self.app.settings.calibrators[cameraIndex]
			self.realSizeMM = list(self.calibrator.realSizeMM)
			self.chessboardSize = list(self.calibrator.boardSize)
		else:
			self.calibrator = calibrator.QTCalibrator()
			self.realSizeMM=[254.0,170.0]
			self.chessboardSize=[25,17]
			
		self.app.settings.calibrators[cameraIndex] = self.calibrator
			
		self.Viewers.CalibrateBefore.loadFromData(pm)
		self.original = pm
		
		if self.calibrator.isReady():
			self.Controls.Buttons.CorrectButton.show()
			
		self.toForm()
			
	def toForm(self):
		self.Controls.Width.setValue(self.chessboardSize[0])
		self.Controls.Height.setValue(self.chessboardSize[1])
		self.Controls.RealWidth.setText(str(self.realSizeMM[0]))
		self.Controls.RealHeight.setText(str(self.realSizeMM[1]))
		if hasattr(self.calibrator,'dpi'):
			self.Controls.CalculatedDPI.setText('%.1f'%self.calibrator.dpi)
		else:
			self.Controls.CalculatedDPI.setText('')
		
	def fromForm(self):
		self.chessboardSize[0] = int(self.Controls.Width.value())
		self.chessboardSize[1] = int(self.Controls.Height.value())
		self.realSizeMM[0] = float(self.Controls.RealWidth.text() or '254.0')
		self.realSizeMM[1] = float(self.Controls.RealHeight.text() or '170.0')
		
	def doCancel(self):
		self.close()
		
	def doClear(self):
		self.app.settings.calibrators[self.cameraIndex] = None
		self.app.calibrationDataChanged.emit()
		self.close()
		
	def doCalibrate(self):
		self.fromForm()

		progress = ProgressDialog(parent=self.app.MainWindow,text='Calculating image distortion',minimum=0,maximum=100)
		progress.setValue(30)
		progress.open()
		
		success = self.calibrator.calibrate(self.original,realSizeMM=self.realSizeMM,chessboardSize=self.chessboardSize,returnAnnotatedImage=True)
		if success is False:
			e = QtGui.QMessageBox.critical(
				self.app.SetupWindow,
				self.tr('Error'),
				self.tr("""
					<p>No chessboard pattern was found. Make sure you entered correct values for chessboard size. 
					The size is the number of <i>internal corners</i>, not the number of squares, so on normal
					chessboards (the ones you play chess on!) are 7 corners wide and 7 corners high.</p>
					<p><center><img src=":/chessboard-howto.png"/><center></p> 
				""")
			)
		else:
			progress.setValue(70)
			
			annotated = success
			self.Viewers.CalibrateBefore.loadFromData(annotated)
			corrected = self.calibrator.correct(self.original)
			self.Viewers.CalibrateAfter.loadFromData(corrected)
			self.Controls.Buttons.ApplyButton.show()
			self.Controls.Buttons.CorrectButton.hide()
			self.Controls.CalculatedDPI.setText(str(getattr(self.calibrator,'dpi','')))
			
		progress.close()
		
	def doCorrect(self):
		corrected = self.calibrator.correct(self.original)
		self.Viewers.CalibrateAfter.loadFromData(corrected)

	def doApply(self):
		self.app.calibrationDataChanged.emit()
		self.close()

						
	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self._up.setLayout(self)


	class Viewers(BaseWidget,QtGui.QWidget):
		def init(self):
			self._up.Layout.addWidget(self)
		
		
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				self._up.setLayout(self)
	
		
		class CalibrateBefore(imageviewer.ImageViewer):
			def init(self):
				imageviewer.ImageViewer.init(self)
				self._up.Layout.addWidget(self,1)
	
		
		class CalibrateAfter(imageviewer.ImageViewer):
			def init(self):
				imageviewer.ImageViewer.init(self)
				self._up.Layout.addWidget(self,1)
		
		
	class Controls(BaseWidget,QtGui.QWidget):
		
		def init(self):
			self._up.Layout.addWidget(self)
		
		class Layout(BaseLayout,QtGui.QFormLayout):
			def init(self):
				self._up.setLayout(self)
				
				
		class Label1(BaseWidget,QtGui.QLabel):
			def init(self):
				self.setTextFormat(Qt.RichText)
				self.setText(self.tr("""
					<p>These sizes are the number of <i>internal corners</i>, not the number of squares, so on normal
					chessboards (the ones you play chess on!) are 7 corners wide and 7 corners high.</p> 
				"""))
				self._up.Layout.addRow(self)
			
			
		class Width(BaseWidget,QtGui.QSpinBox):
			def init(self):
				self._up.Layout.addRow(self.tr('Chessboard corners (horizontal):'),self)
				self.setMinimum(1)
				self.setMaximum(99)

				
		class Height(BaseWidget,QtGui.QSpinBox):
			def init(self):
				self._up.Layout.addRow(self.tr('Chessboard corners (vertical):'),self)
				self.setMinimum(1)
				self.setMaximum(99)


		class Label2(BaseWidget,QtGui.QLabel):
			def init(self):
				self.setTextFormat(Qt.RichText)
				self.setText(self.tr("""
					<p>These measurements (in mm) give the size of the chessboard from <i>inside</i> the first row/column</p> 
				"""))
				self._up.Layout.addRow(self)
			
			
		class RealWidth(BaseWidget,QtGui.QLineEdit):
			def init(self):
				self._up.Layout.addRow(self.tr('Chessboard inside width:'),self)
				self.setValidator(QtGui.QDoubleValidator())
				
				
		class RealHeight(BaseWidget,QtGui.QLineEdit):
			def init(self):
				self._up.Layout.addRow(self.tr('Chessboard inside height:'),self)
				self.setValidator(QtGui.QDoubleValidator())
				
				
		class CalculatedDPI(BaseWidget,QtGui.QLabel):
			def init(self):
				self._up.Layout.addRow(self.tr('Calculated DPI:'),self)
				
				
				
		class Buttons(BaseWidget,QtGui.QWidget):
			
			def init(self):
				self._up.Layout.addRow(self)

			class Layout(BaseLayout,QtGui.QHBoxLayout):
				def init(self):
					self._up.setLayout(self)
		
			class CalibrateButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText(self.tr('Calibrate from this image'))
					
				def onclicked(self):
					self._up._up._up.doCalibrate()
					
			class CorrectButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText(self.tr('Correct with current data'))
					self.hide()
					
				def onclicked(self):
					self._up._up._up.doCorrect()
					
			class ClearButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText(self.tr('Clear data and exit'))
					
				def onclicked(self):
					self._up._up._up.doClear()
					
			class ApplyButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.hide()
					self.setText(self.tr('Save and exit'))
					
				def onclicked(self):
					self._up._up._up.doApply()
					
			class CancelButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText(self.tr('Cancel'))
					
				def onclicked(self):
					self._up._up._up.doCancel()
			