from PySide import QtCore, QtGui
from PySide.QtCore import Qt
from pysideline import *
import math

#
# Start Crop Stuff
#
linePen = QtGui.QPen(QtGui.QColor(133,133,255),1.0,Qt.DotLine,Qt.RoundCap,Qt.RoundJoin)
handleBrush = QtGui.QBrush(QtGui.QColor(133,133,255))

class CropHandle(QtGui.QGraphicsRectItem):
	def __init__(self,cropBox):
		QtGui.QGraphicsRectItem.__init__(self)
		self.cropBox = cropBox
		self.lines = [] 
		self.setBrush(handleBrush)
		self.setRect(0.0,0.0,8.0,8.0)
		self.setZValue(100)
		self.setFlags(Qt.ItemIsSelectable|QtGui.QGraphicsItem.ItemIsMovable|QtGui.QGraphicsItem.ItemIsFocusable|QtGui.QGraphicsItem.ItemSendsGeometryChanges|QtGui.QGraphicsItem.ItemIgnoresTransformations)

	def registerLine(self,line):
		self.lines.append(line)

	def itemChange(self,change,value):
		if change == self.ItemPositionChange:
			if value.x() < -(self.size/2.0):
				value.setX(-(self.size/2.0))
			if value.y() < -(self.size/2.0):
				value.setY(-(self.size/2.0))
			
			if self.cropBox.view._image and not self.cropBox.view._image.pixmap().isNull():
				size = self.cropBox.view._image.pixmap().size()
				maxX = size.width()-(self.size/2.0)
				maxY = size.height()-(self.size/2.0)
				if value.x() > maxX:
					value.setX(maxX)
				if value.y() > maxY:
					value.setY(maxY)
		
		elif change == self.ItemPositionHasChanged:
			pos = self.scenePos()
			if self is self.cropBox.tl:
				self.cropBox.bl.setX(pos.x())
				self.cropBox.tr.setY(pos.y())
			elif self is self.cropBox.tr:
				self.cropBox.br.setX(pos.x())
				self.cropBox.tl.setY(pos.y())
			elif self is self.cropBox.bl:
				self.cropBox.br.setY(pos.y())
				self.cropBox.tl.setX(pos.x())
			elif self is self.cropBox.br:
				self.cropBox.bl.setY(pos.y())
				self.cropBox.tr.setX(pos.x())
			for line in self.lines:
				line.handleMoved(self,self.getCenterPos())
			self.cropBox.rectChanged()
		
		return QtGui.QGraphicsRectItem.itemChange(self,change,value)
	
	def getCenterPos(self):
		pos = self.scenePos()
		pos.setX(pos.x()+(self.size/2.0))
		pos.setY(pos.y()+(self.size/2.0))
		return pos

	def setCenterPos(self,pos):
		pos = QtCore.QPointF(pos)
		pos.setX(pos.x()-(self.size/2.0))
		pos.setY(pos.y()-(self.size/2.0))
		self.setPos(pos)

	def setX(self,x):
		pos = self.scenePos()
		pos.setX(x)
		self.setPos(pos)
		
	def setY(self,y):
		pos = self.scenePos()
		pos.setY(y)
		self.setPos(pos)

	@property
	def size(self):
		return self.cropBox.view.transform().inverted()[0].mapRect(self.rect()).width()
	

	
class CropLine(QtGui.QGraphicsLineItem):
	def __init__(self,cropBox,handle1,handle2):
		QtGui.QGraphicsLineItem.__init__(self)
		self.cropBox = cropBox
		self.handle1 = handle1
		self.handle2 = handle2
		self.handle1.lines.append(self)
		self.handle2.lines.append(self)
		self.setPen(linePen)
		self.setZValue(100)
		self.setFlags(QtGui.QGraphicsItem.ItemIgnoresTransformations)
		
	def handleMoved(self,handle,position):
		position = self.cropBox.view.transform().map(position)
		line = self.line()
		p1 = line.p1()
		p2 = line.p2()
		if handle is self.handle1:
			self.setLine(QtCore.QLineF(position,p2))
		elif handle is self.handle2:
			self.setLine(QtCore.QLineF(p1,position))
		else:
			raise Exception('unknown handle %s'%handle)
	

class CropBox(object):
	def __init__(self,view,scene):
		self.view = view
		self.scene = scene
		self.tl = CropHandle(self)
		self.tr = CropHandle(self)
		self.bl = CropHandle(self)
		self.br = CropHandle(self)
		self.handles = [self.tl,self.tr,self.bl,self.br]
		self.top = CropLine(self,self.tl,self.tr)
		self.left = CropLine(self,self.tl,self.bl)
		self.right = CropLine(self,self.tr,self.br)
		self.bottom = CropLine(self,self.bl,self.br)
		self.lines = [self.top,self.left,self.right,self.bottom]
		scene.addItem(self.tl)
		scene.addItem(self.tr)
		scene.addItem(self.bl)
		scene.addItem(self.br)
		scene.addItem(self.top)
		scene.addItem(self.left)
		scene.addItem(self.right)
		scene.addItem(self.bottom)
		
	def hide(self):
		for i in self.lines + self.handles:
			i.hide()
		
	def show(self):
		for i in self.lines + self.handles:
			i.show()

	def _setRect(self,rect):		
		self.tl.setCenterPos(rect.topLeft())
		self.tr.setCenterPos(rect.topRight())
		self.bl.setCenterPos(rect.bottomLeft())
		self.br.setCenterPos(rect.bottomRight())
		
	def setRect(self,rect):
		self._setRect(rect)
		self.recalc()
		
	def recalc(self):
		if getattr(self,'lastrect',None):
			self.setImageRect(self.lastrect)
		
		for line in self.lines:
			line.handleMoved(line.handle1,line.handle1.getCenterPos())
			line.handleMoved(line.handle2,line.handle2.getCenterPos())
		self.scene.setSceneRect(self.scene.itemsBoundingRect())
		
	def getImageRect(self):
		rect = QtCore.QRectF(self.tl.getCenterPos(),self.br.getCenterPos())
		return rect
	
	def setImageRect(self,rect):
		self._setRect(rect)

	def rectChanged(self):
		rect = self.getImageRect()
		self.lastrect = rect
		coords = tuple([int(round(i)) for i in rect.getCoords()])
		self.view.app.cropboxChanged.emit(self.view,coords) 


#
# Start image viewer stuff
#		

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
			self.addWidget(self._up.ImageView,1)
			self.addWidget(self._up.Toolbar,0)
		
	class ImageView(BaseWidget,QtGui.QGraphicsView):
		
		def init(self):
			self._scene = QtGui.QGraphicsScene()
			self.setScene(self._scene)
			self.setBackgroundRole(QtGui.QPalette.Base)
			self._image = None

			# crop box set up
			self._up.cropBox = CropBox(self,self._scene)
			self._up.cropBox.setRect(QtCore.QRectF(0,0,400.0,400.0))
			self._up.cropBox.hide()

			self.currentCenter = None
			self.setCenter(QtCore.QPointF(0, 0))
			
		def setPixmap(self,pm):
			#if self._image:
			#	self._scene.removeItem(self._image)
			if not self._image:
				self._image = self._scene.addPixmap(pm)
				self._image.setZValue(10)
			self._image.setPixmap(pm)
			
		def setTransform(self,transform):
			QtGui.QGraphicsView.setTransform(self,transform)
			# crop box (allow it to rescale lines) 
			self._up.cropBox.recalc()
			
		def wheelEvent(self, event):
			if self._up.fitToWindowAct.isChecked():
				self._up.fitToWindowAct.setChecked(False)
				self._up.updateActions()
			
			pointBeforeScale = QtCore.QPointF(self.mapToScene(event.pos()))
			screenCenter = self.currentCenter
			
			if event.delta() > 0:
				self._up.zoomIn()
			else:
				self._up.zoomOut()
			
			pointAfterScale = self.mapToScene(event.pos())
			offset = pointBeforeScale - pointAfterScale
			newCenter = screenCenter + offset
			
			self.setCenter(newCenter)

		def setCenter(self, centerPoint):
			visibleArea = self.mapToScene(self.rect()).boundingRect()
			sceneBounds = self.sceneRect()
			
			boundX = visibleArea.width() / 2.0
			boundY = visibleArea.height() / 2.0
			boundWidth = sceneBounds.width() - 2.0 * boundX
			boundHeight = sceneBounds.height() - 2.0 * boundY
			
			bounds = QtCore.QRectF(boundX, boundY, boundWidth, boundHeight)
		
			if bounds.contains(centerPoint):
				self.currentCenter = centerPoint
			else:
				if visibleArea.contains(sceneBounds):
					self.currentCenter = sceneBounds.center()
				else:
					self.currentCenter = centerPoint
		
					if centerPoint.x() > bounds.x() + bounds.width():
						self.currentCenter.setX(bounds.x() + bounds.width())
					elif centerPoint.x() < bounds.x():
						self.currentCenter.setX(bounds.x())
					
					if centerPoint.y() > bounds.y() + bounds.height():
						self.currentCenter.setY(bounds.y() + bounds.height())
					elif centerPoint.y() < bounds.y():
						self.currentCenter.setY(bounds.y())
		
			self.centerOn(self.currentCenter)
		
		
	def load(self,image):
		self._pm.load(image)
		self.loadFromData(self._pm)


	def clear(self):
		self.ImageView.setPixmap(QtGui.QPixmap())

		
	def loadFromData(self,data):
		if isinstance(data,QtGui.QPixmap):
			self._pm = data
		else:
			self._pm.loadFromData(data)
			
		self.ImageView.setPixmap(self._pm)
		
		if self.fitToWindowAct.isChecked():
			self.fitToWindow()
			self.updateActions()
		else:
			self.rescale()
			self.updateActions()
			self.updateSlider()
			

	def zoomIn(self):
		self.scaleImage(1.25)


	def zoomOut(self):
		self.scaleImage(0.8)


	def normalSize(self):
		self.scaleFactor = 1.0
		self.rescale()
		self.updateSlider()


	def fitToWindow(self):
		if not self.ImageView._image:
			return
		if not self.fitToWindowAct.isChecked():
			self.fitToWindowAct.setChecked(True)
		if self._pm.isNull():
			return
		scaledSize = self._pm.size()
		scaledSize.scale(self.ImageView.contentsRect().size(), Qt.KeepAspectRatio)
		scaledSize.setWidth(scaledSize.width()-10)
		scaledSize.setHeight(scaledSize.height()-10)
		self.scaleFactor = (float(scaledSize.width()) / float(self._pm.size().width()))
		self.rescale()
		self.updateSlider()


	def rescale(self):
		transform = QtGui.QTransform()
		transform.scale(self.scaleFactor,self.scaleFactor)
		self.ImageView.setTransform(transform)
		
		
	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.rescale()
		self.updateSlider()

	
	def updateSlider(self):
		self.Toolbar.Slider.setValueFromFactor(self.scaleFactor)


	def resizeEvent(self,e):
		if not self.fitToWindowAct.isChecked():
			return 
		if not self.hasImage():
			return
		self.fitToWindow()


	def hasImage(self):
		return hasattr(self,'_pm') and not self._pm.isNull()


	def handleFitToWindow(self):
		if self.fitToWindowAct.isChecked():
			self.fitToWindow()
		self.updateActions()


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
				
			def onvalueChanged(self,value):
				self._up._up.scaleFactor = self.getValueAsFactor()
				self._up._up.rescale()
				
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


