from PySide import QtCore, QtGui
from PySide.QtCore import Qt
from pysideline import *


class ImageViewer(BaseWidget,QtGui.QWidget):
	
	
	def init(self):
		self._pm = QtGui.QPixmap()
		self.scaleFactor = 1.0
		#self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
		self.createActions()
		self.fitToWindowAct.setEnabled(True)
		
	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.LeftToRight,)
		def init(self):
			self._up.setLayout(self)
			self.setContentsMargins(0,0,0,0)
			self.addWidget(self._up.ScrollArea,1)
		
	class ScrollArea(BaseWidget,QtGui.QScrollArea):
		def init(self):
			self.setBackgroundRole(QtGui.QPalette.Dark)
			
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
		else:
			self.ScrollArea.ImageLabel.adjustSize()
			self.updateActions()


	def zoomIn(self):
		self.scaleImage(1.25)


	def zoomOut(self):
		self.scaleImage(0.8)


	def normalSize(self):
		self.ScrollArea.ImageLabel.adjustSize()
		self.scaleFactor = 1.0


	def fitToWindow(self):
		scaledSize = self.ScrollArea.ImageLabel.pixmap().size()
		scaledSize.scale(self.ScrollArea.contentsRect().size(), Qt.KeepAspectRatio)
		self.ScrollArea.ImageLabel.resize(scaledSize)
		
	
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
		self.zoomInAct = QtGui.QAction("Zoom &In (25%)", self,
				shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)

		self.zoomOutAct = QtGui.QAction("Zoom &Out (25%)", self,
				shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)

		self.normalSizeAct = QtGui.QAction("&Normal Size", self,
				shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)

		self.fitToWindowAct = QtGui.QAction("&Fit to Window", self,
				enabled=False, checkable=True, shortcut="Ctrl+F",
				triggered=self.handleFitToWindow)

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


	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.ScrollArea.ImageLabel.resize(self.scaleFactor * self.ScrollArea.ImageLabel.pixmap().size())

		self.adjustScrollBar(self.ScrollArea.horizontalScrollBar(), factor)
		self.adjustScrollBar(self.ScrollArea.verticalScrollBar(), factor)

		self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
		self.zoomOutAct.setEnabled(self.scaleFactor > 0.05)


	def adjustScrollBar(self, scrollBar, factor):
		scrollBar.setValue(int(factor * scrollBar.value()
								+ ((factor - 1) * scrollBar.pageStep()/2)))
