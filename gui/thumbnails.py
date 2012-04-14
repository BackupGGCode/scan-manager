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


class ThumbnailItem(BaseRootInstantiable,QtGui.QWidget):
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


	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.LeftToRight,)
		def init(self):
			self._up.setLayout(self)
	
	class Image1(BaseWidget,QtGui.QLabel):
		def init(self):
			self._up.Layout.addWidget(self)

	class Image2(BaseWidget,QtGui.QLabel):
		def init(self):
			self._up.Layout.addWidget(self)
		

	def doDelete(self):
		self.parent().app.imageManager.delete(self.image)


	def updateImage(self,pm,cameraIndex=1):
		getattr(self,'Image%d'%cameraIndex).setPixmap(pm.scaled(self.parent().thumbnailWidth,self.parent().thumbnailHeight,Qt.KeepAspectRatio))

			
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
			self.parent().app.imageManager.select(self.image)

		
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


	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.TopToBottom,)
		def init(self):
			self.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
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



class CapturedImagePair(object):
	"""
	@ivar path: the path to the directory in which the image is stored
	@ivar filenames: dict of 1 -> left image filename (including path) and 2 -> right image filename
	@ivar thumbnail: the related L{ThumbnailItem} object
	"""
	
	def __init__(self,manager,filename1=None,filename2=None):
		self.uid = uuid.uuid1().hex
		self.manager = manager
		self.filenames = {1:filename1,2:filename2}
		self._hasImage = {1:(None,None),2:(None,None)}
		
		
	def write(self,data,cameraIndex=None):
		if self.manager.solo:
			assert cameraIndex in (1,None)
			cameraIndex = 1
		
		if type(data) in (list,tuple):
			self.write(data[0],1)
			self.write(data[0],2)
			return
		
		assert cameraIndex in (1,2)
		
		if not self.filenames[cameraIndex]:
			self.filenames[cameraIndex] = self.calcFilename(cameraIndex)
		f = open(self.filenames[cameraIndex],'wb')
		f.write(data)
		f.close()

	
	def delete(self,cameraIndex=None):
		if self.manager.solo:
			assert cameraIndex in (1,None)
			cameraIndex = 1
			
		if not cameraIndex:
			self.delete(1)
			self.delete(2)
			return
			
		assert cameraIndex in (1,2)
		
		if self.filenames[cameraIndex]:
			os.remove(self.filenames[cameraIndex])
			self._hasImage[cameraIndex] = (self.filenames[cameraIndex],False)

	
	def rename(self,newName=None,cameraIndex=None):
		if self.manager.solo:
			assert cameraIndex in (1,None)
			cameraIndex = 1
			
		if cameraIndex is None:
			if newName is None:
				for ndx in 1,2:
					if self.hasImage(ndx):
						self.rename(cameraIndex=ndx)
				return
			else:
				fn = '.'.join(newName.split('.')[:-1])
				ext = newName.split('.')[-1]
				self.rename(newName='%sL.%s'%(fn,ext),cameraIndex=1)
				self.rename(newName='%sR.%s'%(fn,ext),cameraIndex=2)
				return
			
		assert cameraIndex in (1,2)
		
		if newName is not None:
			if os.pathsep not in newName:
				newName = os.path.join(self.manager.path,newName)
		else:
			newName = self.calcFilename(cameraIndex=cameraIndex)
		if self.filenames[cameraIndex] and self.filenames[cameraIndex] == newName:
			return
		os.rename(self.filenames[cameraIndex],newName)
		self.filenames[cameraIndex] = newName

	
	def calcFilename(self,cameraIndex):
		assert cameraIndex in (1,2)
		if self.manager.solo:
			side = ''
		else:
			side = {1:'L',2:'R'}[cameraIndex]
		return os.path.join(self.manager.path,'page%04d%s.jpg'%(self.manager.images.index(self)+1,side))


	def hasImage(self,cameraIndex):
		assert cameraIndex in (1,2)
		if not self.filenames[cameraIndex]:
			self.filenames[cameraIndex] = self.calcFilename(cameraIndex)
		fn = self.filenames[cameraIndex]
		### TODO: enable this for speed
		#if self._hasImage[cameraIndex][0] == fn and self._hasImage[cameraIndex][1] is not None:
		#	return self._hasImage[cameraIndex][1]
		has = os.path.exists(fn)
		self._hasImage[cameraIndex] = (fn,has)
		return has
		


class CapturedImageManager(object):
	
	
	def __init__(self,path,view,solo=False):
		self.path = path
		self.images = []
		self.view = view
		self.solo = solo
		
	
	PAT_FILE_DOUBLE = re.compile(r'page([0-9]+)([lr]).(jpg|jpeg)',re.I)
	PAT_FILE_SINGLE = re.compile(r'page([0-9]+).(jpg|jpeg)',re.I)
	sideToCameraIndex = {'l':1,'L':1,'R':2,'r':2,None:1}

	
	def fillFromDirectory(self,progressCallback=None):
		names = os.listdir(self.path)
		names.sort()
		
		if self.solo:
			pat = self.PAT_FILE_SINGLE
		else:
			pat = self.PAT_FILE_DOUBLE
		
		names = [name for name in names if pat.match(name)]
		total = len(names)
		done = 0
		for name in names:
			m = pat.match(name)
			if self.solo:
				side = 'L'
			else:
				side = m.group(2)
			filename = os.path.join(self.path,name)
			self.addFromFile(filename,cameraIndex=self.sideToCameraIndex[side])
			done += 1
			progressCallback(total,done)
		self.renameChanged()
			

	def new(self):
		image = CapturedImagePair(self)
		self.images.append(image)
		image.thumbnail = self.view.new(uid=image.uid)
		image.thumbnail.image = image
		return image


	def addFromData(self,data,cameraIndex=1,withPreview=False):
	
		if isinstance(data,QtGui.QPixmap):
			pm = data
		else:
			pm = QtGui.QPixmap()
			pm.loadFromData(data)
		
		for image in self.images:
			if not image.hasImage(cameraIndex):
				break
		else:
			image = self.new()
		
		image.write(data=data,cameraIndex=cameraIndex)
		image.thumbnail.updateImage(pm,cameraIndex=cameraIndex)
		
		if withPreview:
			preview = getattr(self.view.app,'Preview%d'%(cameraIndex))
			preview.loadFromData(pm,cameraIndex=cameraIndex)


	def addFromFile(self,filename,cameraIndex=1,withPreview=False):
	
		pm = QtGui.QPixmap()
		pm.load(filename)

		for image in self.images:
			if not image.hasImage(cameraIndex):
				break
			if image.filenames[cameraIndex] == filename:
				break 
		else:
			image = self.new()
			image.filenames[cameraIndex] = filename
		
		image.thumbnail.updateImage(pm,cameraIndex=cameraIndex)
		
		if withPreview:
			preview = getattr(self.view.app,'Preview%d'%(cameraIndex))
			preview.loadFromData(pm)

	
	def move(self,fromLocation,toLocation):
		fromIndex,fromImage = self.normalise(fromLocation)
		toIndex,toImage = self.normalise(toLocation)
		del(self.images[fromIndex])
		self.images.insert(toIndex,fromImage)
		self.view.move(fromImage.thumbnail,toIndex)
		self.renameChanged()

	
	def renameChanged(self):
		changed = []
		for image in self.images:
			for cameraIndex in (1,2):
				if image.filenames[cameraIndex] and image.filenames[cameraIndex] != image.calcFilename(cameraIndex):
					changed.append(image)
					break
		for ndx,image in enumerate(changed):
			image.rename('temp%04d.jpg'%(ndx+1))
		for image in changed:
			image.rename()
		
		
	def delete(self,fromLocation):
		index,image = self.normalise(fromLocation)
		del(self.images[index])
		image.delete()
		self.view.remove(image.thumbnail)
		for i in self.images[index:]:
			i.rename()


	def normalise(self,v):
		if isinstance(v,CapturedImagePair):
			image = v
			index = self.images.index(v)
		else:
			index = v
			image = self.images[v]
		return index,image
	
	
	def select(self,image):
		self.view.app.Preview1.load(image.filenames[1])
		if not self.solo:
			self.view.app.Preview2.load(image.filenames[2])
		