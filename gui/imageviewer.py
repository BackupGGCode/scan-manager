from PySide import QtCore, QtGui
from PySide.QtCore import Qt
from pysideline import *
import math

MIN_SCALE = 0.05
MAX_SCALE = 2.00

class ImageViewer(BaseWidget,QtGui.QWidget):
	
	
	def init(self):
		self._pm = QtGui.QPixmap()
		self.scaleFactor = 1.0
		self.createActions()
		self.fitToWindowAct.setEnabled(True)
		self.fitToWindowAct.setChecked(True)
		self.Toolbar.Slider.setEnabled(False)
		
	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self._up.setLayout(self)
			self.setSpacing(0)
			self.setContentsMargins(0,0,0,0)
			self.addWidget(self._up.ScrollArea,1)
			self.addWidget(self._up.Toolbar,0)
		
	class ScrollArea(BaseWidget,QtGui.QScrollArea):
		def init(self):
			self.setBackgroundRole(QtGui.QPalette.Dark)
			self.setContentsMargins(0,0,0,0)
			
		class ImageLabel(BaseWidget,QtGui.QLabel):
			def init(self):
				self.setBackgroundRole(QtGui.QPalette.Base)
				self.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
				self.setScaledContents(True)
				self._up.setWidget(self)
				self.resize(0,0)
				
		
	def load(self,image):
		self._pm.load(image)
		self.loadFromData(self._pm)

		
	def loadFromData(self,data):
		if isinstance(data,QtGui.QPixmap):
			self._pm = data
		else:
			self._pm.loadFromData(data)
			
		self.ScrollArea.ImageLabel.setPixmap(self._pm)
		
		if self.fitToWindowAct.isChecked():
			self.fitToWindow()
			self.updateActions()
			self.updateSlider()
		else:
			self.ScrollArea.ImageLabel.adjustSize()
			self.updateActions()
			self.updateSlider()


	def zoomIn(self):
		self.scaleImage(1.25)
		self.updateSlider()


	def zoomOut(self):
		self.scaleImage(0.8)
		self.updateSlider()


	def normalSize(self):
		self.ScrollArea.ImageLabel.adjustSize()
		self.scaleFactor = 1.0
		self.updateSlider()


	def fitToWindow(self):
		if not self.ScrollArea.ImageLabel.pixmap():
			return
		if not self.fitToWindowAct.isChecked():
			self.fitToWindowAct.setChecked(True)
		scaledSize = self.ScrollArea.ImageLabel.pixmap().size()
		scaledSize.scale(self.ScrollArea.contentsRect().size(), Qt.KeepAspectRatio)
		self.ScrollArea.ImageLabel.resize(scaledSize)
		self.scaleFactor = float(self.ScrollArea.ImageLabel.size().width()) / float(self.ScrollArea.ImageLabel.pixmap().size().width())
		self.updateSlider()
		
	
	def handleFitToWindow(self):
		if self.fitToWindowAct.isChecked():
			self.fitToWindow()
		else:
			self.normalSize()
		self.updateActions()


	def resizeEvent(self,e):
		if not self.fitToWindowAct.isChecked():
			return 
		if not hasattr(self,'_pm') or self._pm.isNull():
			return
		scaledSize = self.ScrollArea.ImageLabel.pixmap().size()
		scaledSize.scale(self.ScrollArea.contentsRect().size(), Qt.KeepAspectRatio)
		self.ScrollArea.ImageLabel.resize(scaledSize)


	def createActions(self):
		self.zoomInAct = QtGui.QAction("Zoom &In (25%)", self, icon=QtGui.QIcon(':/zoom-in-16.png'), shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
		self.zoomOutAct = QtGui.QAction("Zoom &Out (25%)", self, icon=QtGui.QIcon(':/zoom-out-16.png'), shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
		self.normalSizeAct = QtGui.QAction("&Normal Size", self, icon=QtGui.QIcon(':/zoom-actual-16.png'), shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
		self.fitToWindowAct = QtGui.QAction("&Fit to Window", self, icon=QtGui.QIcon(':/zoom-fit-16.png'), enabled=False, checkable=True, shortcut="Ctrl+F", triggered=self.handleFitToWindow)
		self.Toolbar.addAction(self.zoomInAct)
		self.Toolbar.addAction(self.zoomOutAct)
		self.Toolbar.addAction(self.normalSizeAct)
		self.Toolbar.addAction(self.fitToWindowAct)

	class Toolbar(BaseWidget,QtGui.QToolBar):
		
		def init(self):
			self.setIconSize(QtCore.QSize(16,16))
			self.setContentsMargins(0,0,0,0)

		class Slider(BaseWidget,QtGui.QSlider):
			def init(self):
				self._up.addWidget(self)
				self.setOrientation(Qt.Horizontal)
				self.setMinimum(1)
				self.setMaximum(101)
				self.setSingleStep(2)
				self.setPageStep(10)
				
			def onsliderMoved(self):
				relativeFactor = (self.getValueAsFactor()) / self._up._up.scaleFactor
				self._up._up.scaleImage(relativeFactor)
				
			def setValueFromFactor(self,v):
				bottom = math.log(MIN_SCALE)
				top = math.log(MAX_SCALE)
				srange = float(self.maximum()-self.minimum())
				v = ((math.log(v) - bottom)/(top-bottom))*srange
				self.setValue(int(v))
				
			def getValueAsFactor(self):
				v = self.value()
				bottom = math.log(MIN_SCALE)
				top = math.log(MAX_SCALE)
				srange = float(self.maximum()-self.minimum())
				return math.exp(bottom + (v/srange)*(top-bottom))
				

	def contextMenuEvent(self,event):
		menu = QtGui.QMenu(self)
		menu.addAction(self.zoomInAct)
		menu.addAction(self.zoomOutAct)
		menu.addAction(self.fitToWindowAct)
		menu.exec_(event.globalPos())

	def updateActions(self):
		self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
		self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
		self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())
		self.Toolbar.Slider.setEnabled(not self.fitToWindowAct.isChecked())


	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.ScrollArea.ImageLabel.resize(self.scaleFactor * self.ScrollArea.ImageLabel.pixmap().size())

		self.adjustScrollBar(self.ScrollArea.horizontalScrollBar(), factor)
		self.adjustScrollBar(self.ScrollArea.verticalScrollBar(), factor)

		self.zoomInAct.setEnabled(self.scaleFactor < MAX_SCALE)
		self.zoomOutAct.setEnabled(self.scaleFactor > MIN_SCALE)

			
	def updateSlider(self):
		self.Toolbar.Slider.setValueFromFactor(self.scaleFactor)


	def adjustScrollBar(self, scrollBar, factor):
		scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2)))
