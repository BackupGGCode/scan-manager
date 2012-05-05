from .common import *
from .thumbnails import ThumbnailView
from .imagemanager import CapturedImageManager
from .dialogs import ProgressDialog
from . import imageviewer
from . import processing
from .cameraui import CameraControls
import log

import threading
import Queue
import time



class CaptureThread(threading.Thread):
	"""
	A capture thread waits for its capture() method to be called then, in a separate thread of control, causes the camera to capture an image
	
	It also makes sure captures are queued serially and do not overlap (it waits for a captureComplete signal before deciding a capture is finished)
	"""
	
	def __init__(self,camera):
		threading.Thread.__init__(self)
		self.camera = camera
		self.captureQueue = Queue.Queue()
		self.doneEvent = threading.Event()
		
	def stop(self):
		self.doneEvent.set()
		self.captureQueue.put(True)
		
	def capture(self):
		self.captureQueue.put(False)
	
	def done(self):
		self.doneEvent.set()
	
	def run(self):
		while 1:
			if self.captureQueue.get():
				# a normal capture puts a False on the queue; a stop call puts a True on the queue
				return
			
			viewfinderActive = self.camera.isViewfinderStarted()

			if viewfinderActive:				
				self.camera.stopViewfinder()

			self.camera.capture()
			
			if not self.doneEvent.wait(15.0):
				log.error('capture failed (took longer than 15s) -- resetting capture thread')
			self.doneEvent.clear()

			if viewfinderActive:
				self.camera.startViewfinder()



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
	


class PreviewTab(BaseWidget,QtGui.QWidget):

	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self._up.setLayout(self)
			self.setSpacing(0)
			self.setContentsMargins(0,0,0,0)
			self.addWidget(self._up.PreviewImage,1)
			
	class PreviewImage(imageviewer.ImageViewer):
		tabNames = ['raw','processed'] 
		


class Preview(BaseWidget,QtGui.QTabWidget):
	
	def init(self):
		self.addTab(self.PreviewRaw,self.tr('Raw'))
		self.addTab(self.PreviewProcessed,self.tr('Processed'))
		self.raw = self.PreviewRaw.PreviewImage
		self.processed = self.PreviewProcessed.PreviewImage

	class PreviewRaw(PreviewTab):
		pass

	class PreviewProcessed(PreviewTab):
		pass
	
	def showCropBox(self):
		self.processed.cropBox.show()

	def hideCropBox(self):
		self.processed.cropBox.hide()

	

class MainWindow(BaseWidget,QtGui.QMainWindow):
	
	def init(self):
		self.hide()
		self.setCentralWidget(self.ShootingView)
		self.resize(900,600)
		self.setWindowTitle(self.tr('ScanManager %s - shooting')%smGetVersion())
		self.setCorner(Qt.TopRightCorner,Qt.RightDockWidgetArea)
		self.setCorner(Qt.BottomRightCorner,Qt.RightDockWidgetArea)
		
		self.viewMenu = self.menuBar().addMenu('&View')
		self.actAbout = self.viewMenu.addAction(
			QtGui.QAction('&About',self,triggered=self.doAbout,checkable=False)
		)
		
		self.captureShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+P"),self) 
		self.captureShortcut.setContext(Qt.ApplicationShortcut)
		self.captureShortcut.activated.connect(self.doCapture)

		
	def doCapture(self):
		self.startCaptureThreads()
		for t in self.app.captureThreads.values():
			t.capture()

		
	def startShooting(self):
		"""
		Setup stuff that needs to be organised just before we start shooting frames
		"""
		
		solo = (self.app.setup.mode == Mode.Flat) #: solo is True if we're using single rather than paired images (N.B. that this is NOT the same as only have one camera) 

		if solo:
			self.app.cameraIndices = [1]
		else:
			self.app.cameraIndices = [1,2]
		
		# override default thumbnail sizes using user-selected sizes
		if 'thumbnailSize' in self.app.setup:
			self.app.Thumbnails.thumbnailWidth = self.app.setup.thumbnailSize[0]
			self.app.Thumbnails.thumbnailHeight = self.app.setup.thumbnailSize[1]

		if solo:
			self.app.ThumbnailDock.setMinimumWidth((self.app.setup.thumbnailSize[0]*1)+37)
		else:
			self.app.ThumbnailDock.setMinimumWidth((self.app.setup.thumbnailSize[0]*2)+37)
			
		# set up the image manager to manage captured images and control the thumbnail view 
		self.app.imageManager = CapturedImageManager(path=self.app.setup.outputDirectory,view=self.app.Thumbnails,solo=solo)
		self.app.Thumbnails.solo = solo
		progress = ProgressDialog(parent=self.app.MainWindow,text='Thumbnailing existing images',minimum=0,maximum=100)
		
		# the the image manager with any pre-existing images in the target directory
		progress.open()
		self.app.imageManager.fillFromDirectory(progressCallback=lambda total,done: progress.setValue(int((float(done)/float(total))*100.0)))
		progress.close()
		# for solo mode
		if self.app.setup.mode != Mode.V:
			self.app.Camera2Dock.hide()
			self.app.Preview2.hide()
			self.app.previews = self.app.previews[:2]
		
		# give controls for each camera a change to do their own initialisation (mainly reading initial data from the camera)
		for ndx,camera in enumerate(self.app.cameras):
			cc = getattr(self.app,'Camera%dControls'%(ndx+1))
			cc.setup(camera)

		# hide the capture button if neither camera supports it			
		if not (self.app.cameras[0].hasCapture() or self.app.cameras[0].hasCapture()):
			self.app.CaptureButton.hide()

		# start the processing thread
		self.app.processingThread = processing.ProcessingThread(app=self.app)
		self.app.processingThread.start()

		# start per-camera viewfinder threads
		self.app.captureThreads = {}
		self.startCaptureThreads()


	def startCaptureThreads(self):
		""" start the per-camera capture threads as needed """
		for camera in self.app.cameras:
			if camera in self.app.captureThreads:
				if self.app.captureThreads[camera].isAlive():
					continue
			log.debug('starting capture thread for %s'%camera.getName())
			thread = CaptureThread(camera)
			self.app.captureThreads[camera] = thread
			thread.start()
			
		
	class ShootingView(BaseWidget,QtGui.QWidget):
		def init(self):
			self.setMinimumHeight(200)
			self.app.previews = [None,self.Preview1,self.Preview2] # add a none at the start so we can index directly by cameraIndex
	
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				self._up.setLayout(self)
				self.setContentsMargins(0,0,0,0)
				self.setSpacing(0)
				self.addWidget(self._up.Preview1,1)
				self.addWidget(self._up.Preview2,1)
		
		class Preview1(Preview):
				pass
		
		class Preview2(Preview):
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
				self.setStretchFactor(0,1)
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
				self.setStretchFactor(0,1)
				self.setStretchFactor(1,1)
			
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
					self.app.MainWindow.doCapture()

			
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
				#self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
				
			class Thumbnails(ThumbnailView):
				pass

	def doAbout(self):
		QtGui.QMessageBox.about(self,'About scan manager',
			"""
			<p>The <b>scan manager</b> automates the use of USB-tethered cameras with book scanners
			(see <a href="http://www.diybookscanner.org">www.diybookscanner.org<a>)</p>
			<p>This software and its associated source code is provided for free under the LGPL v3.0 license (full text <a href="http://www.gnu.org/copyleft/lesser.html">here</a>)</p> 
			<p>The libgphoto2 backend is currently GPL rather than LGPL because of its dependency on Cygwin</a></p> 
			<p>For more information please contact Oren Goldschmidt at <a href="mailto:og200@hotmail.com">og200@hotmail.com</a></p> 
			"""
		)
		
	#
	# Shooting window methods
	#
	
	captureComplete = QtCore.Signal(object)
	viewfinderFrame = QtCore.Signal(object)

	def captureCompleteCallback(self,event):
		# we have to do this via a signal because you can't have a non-gui thread doing gui stuff in Qt (this mainly affects PS-ReC drivers)
		# TODO: this may not be necessary now the interface uses QT signals
		self.app.captureThreads[event.camera].done()
		self.captureComplete.emit(event)

		
	def oncaptureComplete(self,event):
		cameraIndex = self.app.cameras.index(event.camera) + 1
		pm = QtGui.QPixmap()
		pm.loadFromData(event.data)
		
		# rotation for preview only
		angle = self.app.settings.rotate[cameraIndex]
		if angle:
			transform = QtGui.QTransform()
			transform.rotate(angle)
			pm = pm.transformed(transform)
			
		image = self.app.imageManager.addFromData(pm=pm,cameraIndex=cameraIndex,withPreview=True)
		for fn in event.getAuxFiles():
			image[cameraIndex].addAuxFromFile(fn)
		self.app.processingQueue.put(processing.PostCaptureJob(app=self.app,image=image,cameraIndex=cameraIndex,pm=pm))

	
	def viewfinderFrameCallback(self,event):
		# we have to do this via a signal because you can't have a non-gui thread doing gui stuff in Qt (this mainly affects PS-ReC drivers)
		self.viewfinderFrame.emit(event)


	def onviewfinderFrame(self,event):
		cameraIndex = self.app.cameras.index(event.camera) + 1
		viewfinder = getattr(self.app,'Viewfinder%d'%(cameraIndex))

		pm = QtGui.QPixmap()
		pm.loadFromData(event.data)
		
		if viewfinder.isHidden():
			viewfinder.resize(pm.size())
			viewfinder.show()
			
		# rotation
		angle = self.app.settings.rotate[cameraIndex]
		if angle:
			transform = QtGui.QTransform()
			transform.rotate(angle)
			pm = pm.transformed(transform)
			
		# correction
		#if self.app.settings.calibrators[cameraIndex] and self.app.settings.calibrators[cameraIndex].isActive():
		#	pm = self.app.settings.calibrators[cameraIndex].correct(pm)
			
		viewfinder.loadFromData(pm)


	#
	# Background processing of captured frames
	#
	
	processingCompleted = QtCore.Signal(object)
	
	def onprocessingCompleted(self,item):
		item.oncompletion()
		
		
		
	class Timer(BaseWidget,QtCore.QTimer):
		
		def init(self):
			self.setInterval(100)
			self.start()
			
		def ontimeout(self):
			if not self._up.isVisible():
				return
			for camera in self.app.cameras:
				camera.ontimer()

