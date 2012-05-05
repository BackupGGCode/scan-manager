"""
Thumbnail 'contact strip' widget
"""

from base import * 
from .common import *

from pysideline import *

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

import uuid
import os
import re


class ThumbnailItem(BaseRootInstantiable,QtGui.QFrame):
	""" Hold a single thumbnail image """
	
	def __init__(self,parent,uid=None):
		super(ThumbnailItem,self).__init__(parent)
		self.dragStartPosition = None
		if uid is None:
			uid = uuid.uuid1().hex
		self.uid = uid
		self.setAcceptDrops(True)
		self.setContextMenuPolicy(Qt.ActionsContextMenu)
		
		self.aDelete = QtGui.QAction("Delete page", self)
		self.aDelete.triggered.connect(self.doDelete)
		self.addAction(self.aDelete)
		if parent.solo:
			self.Images.Image2.hide()

	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self._up.setLayout(self)
			self.setContentsMargins(2,2,2,2)
			
	class Images(BaseWidget,QtGui.QWidget):
		
		def init(self):
			self._up.Layout.addWidget(self)
		
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				self._up.setLayout(self)
				self.setContentsMargins(2,2,2,2)
	
		class Image1(BaseWidget,QtGui.QLabel):
			def init(self):
				self.setPixmap(self._up._up.parent().hourglass)
				self.setAlignment(Qt.AlignCenter)
				self._up.Layout.addWidget(self)
		
	
		class Image2(BaseWidget,QtGui.QLabel):
			def init(self):
				self.setPixmap(self._up._up.parent().hourglass)
				self.setAlignment(Qt.AlignCenter)
				self._up.Layout.addWidget(self)
				
				
	class Label(BaseWidget,QtGui.QLabel):
		def init(self):
			self._up.Layout.addWidget(self)
			self.setAlignment(Qt.AlignCenter)
			
	
	def relabel(self):
		self.Label.setText(self.parent().app.imageManager.getLabel(self.image))
	

	def doDelete(self):
		self.parent().app.imageManager.delete(self.image)


	def updateImage(self,pm,cameraIndex=1):
		image = getattr(self.Images,'Image%d'%cameraIndex)
		image.setPixmap(pm)

			
	#
	# Drag and drop handling
	#
	
	def dragEnterEvent(self, event):
		if event.mimeData().hasFormat('image/x-page'):
			event.accept()
		else:
			event.ignore()


	def dropEvent(self, event):
		if event.mimeData().hasFormat('image/x-page'):
			imageId = event.mimeData().text()
			event.setDropAction(QtCore.Qt.MoveAction)
			
			sourceItem = self.parent().byId[str(imageId)]
			targetIndex = self.parent().Layout.indexOf(self)
			
			self.parent().app.imageManager.move(sourceItem.image,targetIndex)
			
			event.accept()
		else:
			event.ignore()

						
	def mousePressEvent(self,event):
		if event.button() == Qt.LeftButton:
			self.dragStartPosition = event.pos()

			
	def mouseReleaseEvent(self,event):
		if event.button() == Qt.LeftButton:
			self.parent().select(self)

		
	def mouseMoveEvent(self,event):
		if not (event.buttons() & Qt.LeftButton):
			return
		if ((event.pos() - self.dragStartPosition).manhattanLength() < QtGui.QApplication.startDragDistance()):
			return
		drag = QtGui.QDrag(self)
		mimeData = QtCore.QMimeData()
		mimeData.setData('image/x-page',self.uid)
		mimeData.setText(self.uid)
		drag.setMimeData(mimeData)
		#drag.setPixmap(iconPixmap)
		dropAction = drag.exec_()



class ThumbnailView(BaseWidget,QtGui.QWidget):
	
	def init(self):
		self.thumbnailWidth = 100
		self.thumbnailHeight = 100
		self.byId = {}
		self.hourglass = QtGui.QPixmap()
		self.hourglass.load(':/hourglass-48.png')
		self.solo = False
		self.selected = None
		self.setStyleSheet('ThumbnailItem  { border: 1px solid rgba(0,0,0,0); }')


	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.TopToBottom,)
		def init(self):
			self.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
			self.setContentsMargins(0,2,0,2)
			self._up.setLayout(self)

			
	def new(self,uid=None):
		item = ThumbnailItem(parent=self,uid=uid)
		self.byId[item.uid] = item
		self.Layout.addWidget(item)
		return item


	def move(self,item,toIndex):
		self.Layout.removeWidget(item)
		self.Layout.insertWidget(toIndex,item)

	
	def remove(self,item):
		self.Layout.removeWidget(item)
		item.setParent(None) ### TODO: get rid of these and just keep destroy
		item.hide()
		item.destroy()
		if self.selected is item:
			self.selected = None
			self.app.imageManager.select(None)


	def select(self,item):
		if self.selected:
			self.selected.setStyleSheet('')
		self.selected = item
		item.setStyleSheet('ThumbnailItem  { border: 1px solid blue; }')
		self.app.imageManager.select(item.image)


