from .common import *
from . import cameracontrols
from . import imageviewer
from . import processing 
import log
import time

try:
	import chdkconsole
except:
	pass 


try:
	from . import calibrate
except:
	log.logException('Unable to import calibration tools',log.WARNING)
	calibrate = None



class CameraControls(BaseWidget,QtGui.QTabWidget):

	def setup(self,camera):
		self.camera = camera
		self.controls = {}
		self.tabs = {}

		tab = GeneralTab(self)
		self.addTab(tab,'General')
		self.tabs['General'] = tab
		
		toDo = []
		if 'config' in camera.settings and camera.settings.config.cameraControls:
			# use camera controls specified in configuration
			toDo = camera.settings.config.cameraControls
		else:
			# show all camera controls arranged into their default tabs
			toDo = [dict(ident=p.getIdent(),section=p.getSection()) for p in camera.getProperties()]
			
		propertyByIdent = {p.getIdent():p for p in camera.getProperties()}
		
		for item in toDo:
			
			if item['ident'] not in propertyByIdent:
				continue 
			property = propertyByIdent[item['ident']]
			section = item['section']
			
			if section not in self.tabs:
				tab = CameraControlsTab(self)
				self.addTab(tab,section)
				self.tabs[section] = tab
				tab._up = self 
				
			tab = self.tabs[section]
			cls = cameracontrols.controlTypeToClass[property.getControlType()]
			control = cls(qtparent=tab.CameraControlsTabScroll.CameraControlsTabMainArea,cameraProperty=property)
			self.controls[property] = control

		self.refreshFromCamera()
		
		for tab in self.tabs.values():
			tab.CameraControlsTabScroll.CameraControlsTabMainArea.adjustSize()
			
		self.camera.propertiesChanged.connect(self.onProperiesChanged)
		
		if self.camera.api.getId() == 'chdk':
			console = chdkconsole.CHDKConsole(camera=camera,parent=self)
			self.addTab(console,'CHDK console')


	def onProperiesChanged(self,event):
		properties = event.getProperties()
		for property in properties:
			self.controls[property].fromCamera()
			

	def refreshFromCamera(self):
		for control in self.controls.values():
			control.fromCamera()



class CameraControlsTab(BaseWidget,QtGui.QWidget):
	
	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self._up.setLayout(self)
			self.setSpacing(0)
			self.setContentsMargins(0,0,0,0)
			
	class CameraControlsTabScroll(BaseWidget,QtGui.QScrollArea):
		def init(self):
			self._up.Layout.addWidget(self,1)
			self.setWidgetResizable(False)
			self.setContentsMargins(0,0,0,0)
			
		class CameraControlsTabMainArea(BaseWidget,QtGui.QWidget):
			
			class Layout(BaseLayout,QtGui.QFormLayout):
				def init(self):
					self.setFieldGrowthPolicy(QtGui.QFormLayout.FieldsStayAtSizeHint)
					self._up.setLayout(self)
		
			def init(self):
				self._up.setWidget(self)



class GeneralTab(CameraControlsTab):

	class CameraControlsTabScroll(CameraControlsTab.CameraControlsTabScroll):
			
		class CameraControlsTabMainArea(CameraControlsTab.CameraControlsTabScroll.CameraControlsTabMainArea):
			
			def init(self):
				CameraControlsTab.CameraControlsTabScroll.CameraControlsTabMainArea.init(self)

			def getCameraIndex(self):
				return self.app.cameras.index(self._up._up._up.camera)+1
			
			class StartViewfinder(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addRow(self)
					self.setText(self.tr('Start viewfinder'))
					if not self.aq.camera.hasViewfinder():
						self.hide()
					
				def onclicked(self):
					self.aq.camera.startViewfinder()
				
					
			class StopViewfinder(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addRow(self)
					self.setText(self.tr('Stop viewfinder'))
					if not self.aq.camera.hasViewfinder():
						self.hide()
					
				def onclicked(self):
					self.aq.camera.stopViewfinder()
					viewfinder = getattr(self.app,'Viewfinder%d'%(self._up.getCameraIndex()))
					viewfinder.hide()
				
					
			class Rotate(BaseWidget,QtGui.QComboBox):
				
				def init(self):
					self._up.Layout.addRow(self.tr('Rotation (for new images):'),self)
					self.blockSignals(True)
					self.addItem(self.tr('No rotation'),0)
					self.addItem(self.tr('90 CW'),90)
					self.addItem(self.tr('180'),180)
					self.addItem(self.tr('90 CCW'),270)
					if 'rotate' in self.aq.camera.settings:
						self.setCurrentIndex(self.findData(self.aq.camera.settings.rotate))
					self.blockSignals(False)
				def oncurrentIndexChanged(self,index):
					angle = self.itemData(index)
					self.aq.camera.settings.rotate = angle
			
					
			class CalibrationControlsBox(BaseWidget,QtGui.QGroupBox):
				
				def init(self):
					self._up.Layout.addRow(self)
	
				class Layout(BaseLayout,QtGui.QFormLayout):
					def init(self):
						self.setFieldGrowthPolicy(QtGui.QFormLayout.FieldsStayAtSizeHint)
						self._up.setLayout(self)
			
				class CalbrationStateLabel(BaseWidget,QtGui.QLabel):
					
					def init(self):
						self._up.Layout.addRow(self)
						self.update()
						self.app.calibrationDataChanged.connect(self.update)
						
					def update(self):
						if self.aq.camera.settings.get('undistort',None) and self.aq.camera.settings.undistort.isReady():
							self.setText(self.tr('<p>Calibration configured</p>'))
							self._up.CorrectCheckbox.setEnabled(True)
						else:
							self.setText(self.tr('<p>No calibration configured</p>'))
							self._up.CorrectCheckbox.setChecked(False)
							self._up.CorrectCheckbox.setEnabled(False)
	
	
				class CorrectCheckbox(BaseWidget,QtGui.QCheckBox):
					def init(self):
						self._up.Layout.addRow(self)
						self.setText(self.tr('Correct images using calibration data'))
						self.app.calibrationDataChanged.connect(self.update)
						if 'undistort' in self.aq.camera.settings and self.aq.camera.settings.undistort.isActive():
							self.setChecked(True)
						else:
							self.setChecked(False) 
						
						
					def onstateChanged(self):
						if 'undistort' in self.aq.camera.settings:
							self.aq.camera.settings.undistort.setActive(self.isChecked())
							
	
					def update(self):
						if 'undistort' in self.aq.camera.settings and self.aq.camera.settings.undistort.isReady():
							self.show()
						else:
							self.hide()
	
					
				class CalibrateButton(BaseWidget,QtGui.QPushButton):
					def init(self):
						self._up.Layout.addRow(self)
						self.setText(self.tr('Calibrate with current image'))
						if 'undistort' in self.aq.camera.settings and self.aq.camera.settings.undistort.isActive():
							self.setChecked(True)
						
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
						
						if not preview.hasImage('raw'):
							return
						
						dialog = calibrate.CalibrateDialog(self)
						dialog.setModal(True)
						dialog.open()
						dialog.go(preview.pixmaps['raw'],camera=self.aq.camera)
	
	
			class CropControlsBox(BaseWidget,QtGui.QGroupBox):
				
				def init(self):
					if 'crop' not in self.aq.camera.settings:
						self.aq.camera.settings.crop = BaseSettings()
					self._up.Layout.addRow(self)

	
				class Layout(BaseLayout,QtGui.QFormLayout):
					def init(self):
						self.setFieldGrowthPolicy(QtGui.QFormLayout.FieldsStayAtSizeHint)
						self._up.setLayout(self)
			
	
				class CropCheckbox(BaseWidget,QtGui.QCheckBox): 
					def init(self):
						self.blockSignals(True)
						self._up.Layout.addRow(self)
						self.setText(self.tr('Crop images'))
						if 'crop' in self.aq.camera.settings:
							self.setChecked(self.aq.camera.settings.crop.get('enabled',False))
						self.blockSignals(False)
						
					def onstateChanged(self):
						if self.isChecked():
							self._up.CropSpinners.update()
							self.aq.camera.settings.crop.enabled = True
						else:
							self.aq.camera.settings.crop.enabled = False
					
					
				class CropSpinners(BaseWidget,QtGui.QWidget):
					def init(self):
						self._up.Layout.addRow(self)
						
						if 'crop' in self.aq.camera.settings and self.aq.camera.settings.crop.get('coords',None):
							self.load()

						ndx = self.aq.getCameraIndex()
						preview = self.app.previews[ndx]
						preview.cropBoxChanged.connect(self.cropBoxChanged)
						preview.pixmapChanged.connect(self.pixmapChanged)
	
					def cropBoxChanged(self,rect):
						coords = self.rectToCoords(rect)
						if coords:
							self.aq.camera.settings.crop.coords = coords
							self.load()
						
					
					def pixmapChanged(self,rect):
						ndx = self.aq.getCameraIndex()
						preview = self.app.previews[ndx]
						if not preview.cropBox.isVisible():
							return
						else:
							self.update()
						
					
					def load(self):
						self.blockSignals(True)
						for i in self.Left,self.Top,self.Right,self.Bottom:
							i.blockSignals(True)
							
						c = self.aq.camera.settings.crop.coords
						self.Left.setValue(c[0])
						self.Top.setValue(c[1])
						self.Right.setValue(c[2])
						self.Bottom.setValue(c[3])
						
						self.blockSignals(False)
						for i in self.Left,self.Top,self.Right,self.Bottom:
							i.blockSignals(False)
						
					def update(self):
						self.aq.camera.settings.crop.coords = (self.Left.value(),self.Top.value(),self.Right.value(),self.Bottom.value())
						ndx = self.aq.getCameraIndex()
						preview = self.app.previews[ndx]
						
						rect = self.coordsToRect(self.aq.camera.settings.crop.coords)
						
						if rect is not None:
							preview.cropBox.setRect(rect)
						
					def coordsToRect(self,c=None):
						if c is None: 
							c = self.aq.camera.settings.crop.coords
						
						ndx = self.aq.getCameraIndex()
						preview = self.app.previews[ndx]
						
						pm = preview.pixmaps.get('undistorted',None)
						if pm is None or pm.isNull():
							return None
						
						size = pm.size()

						return QtCore.QRect(
							min(size.height(),c[0]),
							min(size.width(),c[1]),
							max(0,size.width()-(c[0]+c[2])),
							max(0,size.height()-(c[1]+c[3]))
						)
						
					def rectToCoords(self,rect):

						ndx = self.aq.getCameraIndex()
						preview = self.app.previews[ndx]
						
						pm = preview.pixmaps.get('undistorted',None)
						if pm is None or pm.isNull():
							return None
						
						size = pm.size()

						c = (
							rect.left(),
							rect.top(),
							size.width()-(rect.left()+rect.width()),
							size.height()-(rect.top()+rect.height())
						)

						return c
						
					class Layout(BaseLayout,QtGui.QGridLayout):
						def init(self):
							self.setContentsMargins(0,0,0,0)
							self._up.setLayout(self)
						
					class Top(BaseWidget,QtGui.QSpinBox):
						def init(self):
							self.blockSignals(True)
							self.setAccelerated(True)
							self.setMinimum(0)
							self.setMaximum(99999)
							self.localInit()
							self.blockSignals(False)
						def onvalueChanged(self):
							self._up.update()
						def localInit(self):
							self._up.Layout.addWidget(self,0,1)
							
					class Left(Top):
						def localInit(self):
							self._up.Layout.addWidget(self,1,0)
							
					class Right(Top):
						def localInit(self):
							self._up.Layout.addWidget(self,1,2)
							
					class Bottom(Top):
						def localInit(self):
							self._up.Layout.addWidget(self,2,1)
	
				
			class ReprocessButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addRow(self)
					self.setText(self.tr('Re-process current image'))
					
				def onclicked(self):
					ndx = self._up.getCameraIndex()
					image = self.app.imageManager.selected
					self.app.processingQueue.put(processing.PostCaptureJob(self.app,image,ndx))

					
 