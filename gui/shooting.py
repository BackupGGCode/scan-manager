from .common import *
from .thumbnails import ThumbnailItem, ThumbnailView, CapturedImageManager, CapturedImagePair
from . import cameracontrols
from .dialogs import ProgressDialog
from . import imageviewer
import log


try:
	from . import calibrate
except:
	log.logException('Unable to import calibration tools',log.WARNING)
	calibrate = None

### 3.0
# import queue
import Queue as queue
import threading


class LiveView(BaseWidget,QtGui.QLabel):
	""" Widget to display camera viewfinder live view """
	
	doRescale = True 
	
	def init(self):
		self.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
		self.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
		self._pm = QtGui.QPixmap()

	
	def resizeEvent(self,e):
		if not self.doRescale:
			return 
		if not hasattr(self,'_pm') or self._pm.isNull():
			return
		self.setPixmap(self._pm.scaled(e.size(),Qt.KeepAspectRatio))


	def load(self,image):
		self._pm.load(image)
		if self.doRescale:
			self.setPixmap(self._pm.scaled(self.size(),Qt.KeepAspectRatio))
		else:
			self.setPixmap(self._pm)
		
	def loadFromData(self,data):
		if isinstance(data,QtGui.QPixmap):
			self._pm = data
		else:
			self._pm.loadFromData(data)
		if self.doRescale:
			self.setPixmap(self._pm.scaled(self.size(),Qt.KeepAspectRatio))
		else:
			self.setPixmap(self._pm)
		


class CameraControls(BaseWidget,QtGui.QTabWidget):

	def setup(self,camera):
		self.camera = camera
		self.controls = []
		self.tabs = {}

		tab = GeneralTab(self)
		self.addTab(tab,'General')
		self.tabs['General'] = tab
		
		for property in camera.getProperties():
			
			section = property.getSection()
			if section not in self.tabs:
				tab = CameraControlsTab(self)
				self.addTab(tab,section)
				self.tabs[section] = tab
				tab._up = self 
				
			tab = self.tabs[section]
			cls = cameracontrols.controlTypeToClass[property.getControlType()]
			control = cls(qtparent=tab.CameraControlsTabScroll.CameraControlsTabMainArea,cameraProperty=property)
			self.controls.append(control)

		self.refreshFromCamera()
		
		for tab in self.tabs.values():
			tab.CameraControlsTabScroll.CameraControlsTabMainArea.adjustSize()
		
	def refreshFromCamera(self):
		for control in self.controls:
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
			self.setContentsMargins(0,0,0,0)
			
		class CameraControlsTabMainArea(BaseWidget,QtGui.QWidget):
			
			class Layout(BaseLayout,QtGui.QFormLayout):
				def init(self):
					self._up.setLayout(self)
		
			def init(self):
				self.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
				self._up.setWidget(self)



class GeneralTab(CameraControlsTab):

	class CameraControlsTabScroll(CameraControlsTab.CameraControlsTabScroll):
			
		class CameraControlsTabMainArea(CameraControlsTab.CameraControlsTabScroll.CameraControlsTabMainArea):
			
			def init(self):
				CameraControlsTab.CameraControlsTabScroll.CameraControlsTabMainArea.init(self)
				
			class CalbrationStateLabel(BaseWidget,QtGui.QLabel):
				
				def init(self):
					self._up.Layout.addRow(self)
					self.update()
					self.app.calibrationDataChanged.connect(self.update)
					
				def update(self):
					cameraIndex = self.app.cameras.index(self._up._up._up._up.camera)+1
					if self.app.calibrators[cameraIndex] and self.app.calibrators[cameraIndex].isReady():
						self.setText(self.tr('<p>Calibration active</p>'))
					else:
						self.setText(self.tr('<p>No calibration configured</p>'))


			class CorrectCheckbox(BaseWidget,QtGui.QCheckBox):
				def init(self):
					self._up.Layout.addRow(self)
					self.setText(self.tr('Correct images using calibration data'))
					self.app.calibrationDataChanged.connect(self.update)
					cameraIndex = self.app.cameras.index(self._up._up._up._up.camera)+1
					if self.app.calibrators[cameraIndex] and self.app.calibrators[cameraIndex].isActive():
						self.setChecked(True)
					else:
						self.setChecked(False) 
					
					
				def onstateChanged(self):
					cameraIndex = self.app.cameras.index(self._up._up._up._up.camera)+1
					if self.app.calibrators[cameraIndex]:
						self.app.calibrators[cameraIndex].setActive(self.isChecked())
						

				def update(self):
					cameraIndex = self.app.cameras.index(self._up._up._up._up.camera)+1
					if self.app.calibrators[cameraIndex] and self.app.calibrators[cameraIndex].isReady():
						self.show()
					else:
						self.hide()

				
			class CalibrateButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addRow(self)
					self.setText(self.tr('Calibrate with current iamge'))
					
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
					if self.app.Preview1._pm.isNull():
						return
					dialog = calibrate.CalibrateDialog(self)
					dialog.setModal(True)
					dialog.open()
					dialog.go(self.app.Preview1._pm)


			class CropCheckbox(BaseWidget,QtGui.QCheckBox): 
				def init(self):
					self._up.Layout.addRow(self)
					self.setText(self.tr('Crop images'))
					
				def onstateChanged(self):
					if self.isChecked():
						self.app.Preview1.cropBox.show()
						self.app.Preview2.cropBox.show()
					else:
						self.app.Preview1.cropBox.hide()
						self.app.Preview2.cropBox.hide()
				


class MainWindow(BaseWidget,QtGui.QMainWindow):
	
	def __init__(self,*args,**kargs):
		super(MainWindow,self).__init__(*args,**kargs)
		self.viewfinderEventQ = queue.Queue()
		self.captureCompleteEventQ = queue.Queue()

	def init(self):
		self.setCentralWidget(self.ShootingView)
		self.resize(900,600)
		self.setWindowTitle(self.tr('ScanManager - shooting'))
		self.setCorner(Qt.TopRightCorner,Qt.RightDockWidgetArea)
		self.setCorner(Qt.BottomRightCorner,Qt.RightDockWidgetArea)
		
		self.viewMenu = self.menuBar().addMenu('&View')
		self.actAbout = self.viewMenu.addAction(
			QtGui.QAction('&About',self,triggered=self.doAbout,checkable=False)
		)

		
	def startShooting(self):
		"""
		Setup stuff that needs to be organised just before we start shooting frames
		"""
		
		solo = (self.app.settings.mode == Mode.Flat) #: solo is True if we're using single rather than paired images (N.B. that this is NOT the same as only have one camera) 
		
		# override default thumbnail sizes using user-selected sizes
		if 'thumbnailSize' in self.app.settings:
			self.app.Thumbnails.thumbnailWidth = self.app.settings.thumbnailSize[0]
			self.app.Thumbnails.thumbnailHeight = self.app.settings.thumbnailSize[1]
			
		# set up the image manager to manage captured images and control the thumbnail view 
		self.app.imageManager = CapturedImageManager(path=self.app.settings.outputDirectory,view=self.app.Thumbnails,solo=solo)
		progress = ProgressDialog(parent=self.app.MainWindow,text='Thumbnailing existing images',minimum=0,maximum=100)
		
		# the the image manager with any pre-existing images in the target directory
		progress.open()
		self.app.imageManager.fillFromDirectory(progressCallback=lambda total,done: progress.setValue(int((float(done)/float(total))*100.0)))
		progress.close()
		# for solo mode
		if self.app.settings.mode != Mode.V:
			self.app.Camera2Dock.hide()
			self.app.Preview2.hide()
		
		# give controls for each camera a change to do their own initialisation (mainly reading initial data from the camera)
		for ndx,camera in enumerate(self.app.cameras):
			cc = getattr(self.app,'Camera%dControls'%(ndx+1))
			cc.setup(camera)

		# hide the capture button if neither camera supports it			
		if not (self.app.cameras[0].hasCapture() or self.app.cameras[0].hasCapture()):
			self.app.CaptureButton.hide()

		
	class ShootingView(BaseWidget,QtGui.QWidget):
		def init(self):
			self.setMinimumHeight(200)
	
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				self._up.setLayout(self)
				self.setContentsMargins(0,0,0,0)
				self.setSpacing(0)
				self.addWidget(self._up.Preview1,1)
				self.addWidget(self._up.Preview2,1)
		
		class Preview1(imageviewer.ImageViewer):
				pass
		
		class Preview2(imageviewer.ImageViewer):
				pass
		
		
	class Camera1Dock(BaseWidget,QtGui.QDockWidget):
		
		def init(self):
			self.setWindowTitle(self.tr('Camera 1 controls'))
			self._up.addDockWidget(Qt.BottomDockWidgetArea,self)
			self.setWidget(self.CameraControls)
			self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)

		class CameraControls(BaseWidget,QtGui.QSplitter):
			
			def init(self):
				self.addWidget(self.Viewfinder1)
				self.addWidget(self.Camera1Controls)
				self.setFrameStyle(QtGui.QFrame.StyledPanel)
				self.setLineWidth(1)
				self.setStretchFactor(0,10000)
				self.setStretchFactor(1,1)
			
			class Viewfinder1(LiveView):
				def init(self):
					LiveView.init(self)
					self.setMinimumSize(QtCore.QSize(100,100))
					self.hide()
			
			class Camera1Controls(CameraControls):
				def init(self):
					CameraControls.init(self)


	class Camera2Dock(BaseWidget,QtGui.QDockWidget):
		
		def init(self):
			self.setWindowTitle(self.tr('Camera 2 controls'))
			self._up.addDockWidget(Qt.BottomDockWidgetArea,self)
			self.setWidget(self.CameraControls)
			self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)

		class CameraControls(BaseWidget,QtGui.QSplitter):
			
			def init(self):
				self.addWidget(self.Viewfinder2)
				self.addWidget(self.Camera2Controls)
				self.setFrameStyle(QtGui.QFrame.StyledPanel)
				self.setLineWidth(1)
			
			class Viewfinder2(LiveView):
				def init(self):
					LiveView.init(self)
					self.setMinimumSize(QtCore.QSize(100,100))
					self.hide()
			
			class Camera2Controls(CameraControls):
				def init(self):
					CameraControls.init(self)


	class CommonControlsDock(BaseWidget,QtGui.QDockWidget):
		
		def init(self):
			self.setWindowTitle(self.tr('Common controls'))
			self._up.addDockWidget(Qt.RightDockWidgetArea,self)
			self.setWidget(self.CommonControls)
			self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)
			self.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)

		class CommonControls(BaseWidget,QtGui.QFrame):
			
			class Layout(BaseLayout,QtGui.QVBoxLayout):
				def init(self):
					self._up.setLayout(self)
					self.setContentsMargins(5,5,5,5)
					self.setSpacing(5)
					
			class LeftOrRight(BaseWidget,QtGui.QWidget):
				def init(self):
					self._up.Layout.addWidget(self)
					self.hide()
				class Layout(BaseLayout,QtGui.QHBoxLayout):
					def init(self):
						self._up.setLayout(self)
						self.setContentsMargins(0,0,0,0)
						self.setSpacing(0)
				class Left(BaseWidget,QtGui.QRadioButton):
					def init(self):
						self.setText(self.tr('Left'))
						self._up.Layout.addWidget(self)
				class Right(BaseWidget,QtGui.QRadioButton):
					def init(self):
						self.setText(self.tr('Right'))
						self._up.Layout.addWidget(self)
					
			class CaptureButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText(self.tr('Capture'))
					self.setIcon(QtGui.QIcon(':/camera-24.png'))
					self.setIconSize(QtCore.QSize(24,24))
					
				def onclicked(self):
					captureThreads = []
					for camera in reversed(self.app.cameras):
						captureThreads.append(threading.Thread(target=camera.capture))
					for thread in captureThreads:
						thread.start()

			
	class ThumbnailDock(BaseWidget,QtGui.QDockWidget):
		def init(self):
			self.setWindowTitle(self.tr('Thumbnails'))
			self._up.addDockWidget(Qt.RightDockWidgetArea,self)
			self.setWidget(self.ThumbnailScrollArea)
			self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)

		class ThumbnailScrollArea(BaseWidget,QtGui.QScrollArea):
			def init(self):
				self.setWidget(self.Thumbnails)
				self.setWidgetResizable(True)
				
			class Thumbnails(ThumbnailView):
				pass

	def doAbout(self):
		QtGui.QMessageBox.about(self,'About scan manager',
			"""
			<p>The <b>scan manager</b> automates the use of USB-tethered cameras with book scanners
			(see <a href="http://www.diybookscanner.org">www.diybookscanner.org<a>)</p>
			<p>This software and its associated source code is provided for free under the LGPL v3.0 license (full text <a href="http://www.gnu.org/copyleft/lesser.html">here</a>)</p> 
			<p>The libgphoto2 backend is currently GPL rather than LGPL because of its dependency on Cygwin</a>)</p> 
			<p>For more information please contact Oren Goldschmidt at <a href="mailto:og200@hotmail.com">og200@hotmail.com</a></p> 
			"""
		)
		
	#
	# Shooting window methods
	#
	
	captureComplete = QtCore.Signal()
	viewfinderFrame = QtCore.Signal()

	def captureCompleteCallback(self,event):
		# we have to do this via a signal because you can't have a non-gui thread doing gui stuff in Qt
		self.captureCompleteEventQ.put(event)
		self.captureComplete.emit()

		
	def oncaptureComplete(self):
		while 1:
			try:
				event = self.captureCompleteEventQ.get(False)
			except queue.Empty:
				break
			ndx = self.app.cameras.index(event.camera) + 1
			if self.app.calibrators[ndx] and self.app.calibrators[ndx].isReady():
				self.app.calibrators[ndx].correct() 
			self.app.imageManager.addFromData(event.data,cameraIndex=ndx,withPreview=True)

	
	def viewfinderFrameCallback(self,event):
		# we have to do this via a signal because you can't have a non-gui thread doing gui stuff in Qt
		self.viewfinderEventQ.put(event)
		self.viewfinderFrame.emit()


	def onviewfinderFrame(self):
		while 1:
			try:
				event = self.viewfinderEventQ.get(False)
			except queue.Empty:
				break
			ndx = self.app.cameras.index(event.camera)
			preview = getattr(self.app,'Viewfinder%d'%(ndx+1))
			if preview.isHidden():
				pm = QtGui.QPixmap()
				pm.loadFromData(event.data)
				preview.resize(pm.size())
				preview.show()
			preview.loadFromData(event.data)
