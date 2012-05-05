"""
A class for managing a list of image pairs stored on disk which also handles keeping track of processed and raw versions on each image 
"""

from base import * 
from .common import *

from pysideline import *

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

import uuid
import os
import re

from . import processing


class ThumbnailJob(processing.ProcessingJob):

	priority = 100
	
	def __init__(self,app,image,cameraIndex,size,withPreview=False):
		self.app = app
		self.image = image
		self.cameraIndex = cameraIndex
		self.size = size
		self.withPreview = withPreview
		
	def execute(self):
		pm = QtGui.QPixmap(self.image[self.cameraIndex].raw.getFilePath())
		s = pm.size()
		s.scale(self.size[0], self.size[1],Qt.KeepAspectRatio)
		self.pm = pm.scaled(s,transformMode=Qt.SmoothTransformation)
		#self.pm.save(self.image[self.cameraIndex].getThumbnailPath(self.size))

	def oncompletion(self):
		self.image.thumbnail.updateImage(self.pm,cameraIndex=self.cameraIndex)
		if self.withPreview:
			preview = self.app.previews[self.cameraIndex]
			preview.raw.loadFromData(self.pm)



class CapturedImageFile(object):
	"""
	A basic image file object supporting the simple manipulations required for files in the image list
	 
	@ivar path: the path to the directory in which the image is stored
	@ivar filename: the currently configured filename for the image (excluding path)
	"""
	
	def __init__(self,path,filename):
		self.path = path 
		self.filename = filename
		self.ext = os.path.splitext(filename)[-1]


	def write(self,data):
		f = open(self.getFilePath(),'wb')
		f.write(data)
		f.close()

	
	def delete(self):
		if self.exists():
			os.remove(self.getFilePath())

	
	def rename(self,filename):
		filename = os.path.splitext(filename)[0] + self.ext
		exists = self.exists()
		oldFilePath = self.getFilePath()
		self.filename = filename
		newFilePath = self.getFilePath()
		if newFilePath == oldFilePath:
			return
		if exists:
			os.rename(oldFilePath,newFilePath)

	
	def exists(self):
		return os.path.exists(self.getFilePath())
	
		
	def getFilePath(self):
		return os.path.join(self.path,self.filename)
	



class CapturedImage(object):
	"""
	An image that can (optionally) have raw and processed versions stored on disk
	
	@ivar raw: a L{CapturedImageFile} object for the raw image
	@ivar processed: a L{CapturedImageFile} object for the raw image (the object if present even if no such file is ever created)
	"""
	
	def __init__(self,path,filename):
		self.raw = CapturedImageFile(path,filename)
		self.processed = CapturedImageFile(self.calcProcessedPath(path),filename)
		self.thumbnail = CapturedImageFile(self.calcThumbnailPath(path),filename)
		self.auxiliary = []


	@property
	def files(self):
		return [self.raw,self.processed,self.thumbnail] + self.auxiliary


	def delete(self):
		for f in self.files:
			f.delete()
		
		
	def rename(self,filename):
		for f in self.files:
			f.rename(filename)

		
	def addAuxFromFile(self,old):
		ext = os.path.splitext(old)[-1]
		rawBase = os.path.splitext(self.raw.getFilePath())[0]
		new = rawBase + ext
		path,filename = os.path.split(new)
		if os.path.exists(new):
			raise Exception('Cannot add new auxiliary file %s from %s because the new filename already exists'%(new,old))
		os.rename(old,new)
		self.auxiliary.append(CapturedImageFile(path,filename))
		
		
	def calcProcessedPath(self,path):
		return os.path.join(path,'processed')
	
	
	def calcThumbnailPath(self,path):
		return os.path.join(path,'thumbnails')
	
		

class CapturedImageBase(object):
	""" 
	Common base for both kinds of image pair (the one that's actually a pair and the one that only looks like a pair!)
	"""


class CapturedImagePair(CapturedImageBase):
	"""
	An PAIR of images (left and right) that can (optionally) also have raw and processed versions stored on disk
	
	@ivar left: a L{CapturedImageFile} object for the left image
	@ivar right: a L{CapturedImageFile} object for the right image (the object if present even if no such file is ever created)
	"""
	
	def __init__(self,path,filename):
		self.uid = uuid.uuid1().hex
		base,ext = os.path.splitext(filename)
		self.left = CapturedImage(path,'%sL%s'%(base,ext))
		self.right = CapturedImage(path,'%sR%s'%(base,ext))


	def __getitem__(self,k):
		if k == 1:
			return self.left
		elif k == 2:
			return self.right
		else:
			raise KeyError(k)


	def delete(self):
		self.left.delete()
		self.right.delete()

	
	def rename(self,filename):
		base,ext = os.path.splitext(filename)
		self.left.rename('%sL%s'%(base,ext))
		self.right.rename('%sR%s'%(base,ext))


class CapturedImageSingle(CapturedImageBase):
	"""
	An SINGLE image to use in place of pairs where pairs are not wanted
	
	@ivar image: a L{CapturedImageFile} object for the underlying images
	"""
	
	def __init__(self,path,filename):
		self.uid = uuid.uuid1().hex
		self.image = CapturedImage(path,filename)


	def __getitem__(self,k):
		if k == 1:
			return self.image
		else:
			raise KeyError(k)


	def delete(self):
		self.image.delete()

	
	def rename(self,filename):
		self.image.rename(filename)
	
	
	
class CapturedImageManager(object):
	

	PAT_FILE_DOUBLE = re.compile(r'(page[0-9]+)([lr])\.(jpg|jpeg)',re.I)
	PAT_FILE_SINGLE = re.compile(r'(page[0-9]+)()\.(jpg|jpeg)',re.I)
	
	sideToCameraIndex = {'l':1,'L':1,'R':2,'r':2,'':1,None:1}

	
	def __init__(self,path,view,solo=False):
		self.path = path
		self.images = []
		self.view = view
		self.solo = solo
		self.selected = None
		
		if self.solo:
			self.cameraIndices = [1]
		else:
			self.cameraIndices = [1,2]
		
		pPath = os.path.join(self.path,'processed')
		if not os.path.exists(pPath):
			os.mkdir(pPath)

		tPath = os.path.join(self.path,'thumbnails')
		if not os.path.exists(tPath):
			os.mkdir(tPath)
		
	
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
			side = m.group(2)
			baseName = '%s.%s'%(m.group(1),m.group(3))
			self.addFromExistingLocalFile(filename=name,baseFilename=baseName,cameraIndex=self.sideToCameraIndex[side])
			done += 1
			progressCallback(total,done)
		self.renameChanged()
			

	def new(self,filename):
		if self.solo:
			image = CapturedImageSingle(path=self.path,filename=filename)
		else:
			image = CapturedImagePair(path=self.path,filename=filename)
		self.images.append(image)
		image.thumbnail = self.view.new(uid=image.uid)
		image.thumbnail.image = image
		image.thumbnail.relabel()
		return image


	def addFromData(self,data=None,pm=None,cameraIndex=1,withPreview=False):

		if pm is None:	
			pm = QtGui.QPixmap()
			pm.loadFromData(data)
		
		ndx = 0
		for ndx,image in enumerate(self.images):
			if not image[cameraIndex].raw.exists():
				break
		else:
			filename = self.calcBaseFilename(len(self.images))
			image = self.new(filename)
		
		pm.save(image[cameraIndex].raw.getFilePath())
		image.thumbnail.updateImage(pm,cameraIndex=cameraIndex)
		
		if withPreview:
			preview = self.view.app.previews[cameraIndex]
			preview.raw.loadFromData(pm)
		
		return image


	def addFromExistingLocalFile(self,filename,baseFilename,cameraIndex=1,withPreview=False):
		
		filepath = os.path.join(self.path,filename)
		
		for image in self.images:
			if not image[cameraIndex].raw.exists():
				break
			if image[cameraIndex].raw.filename == filename:
				break
		else:
			image = self.new(baseFilename)
			
		self.view.app.processingQueue.put(
			ThumbnailJob(
				app = self.view.app,
				image = image,
				cameraIndex = cameraIndex,
				size = (self.view.thumbnailWidth,self.view.thumbnailHeight),
				withPreview = withPreview
			)
		)

		return image


	
	def normalise(self,v):
		if isinstance(v,CapturedImageBase):
			image = v
			index = self.images.index(v)
		else:
			index = v
			image = self.images[v]
		return index,image
	
	
	def move(self,fromLocation,toLocation):
		fromIndex,fromImage = self.normalise(fromLocation)
		toIndex,toImage = self.normalise(toLocation)
		del(self.images[fromIndex])
		self.images.insert(toIndex,fromImage)
		self.view.move(fromImage.thumbnail,toIndex)
		self.renameChanged()

	
	def renameChanged(self):
		changed = []
		for ndx,image in enumerate(self.images):
			for cameraIndex in self.cameraIndices:
				if image[cameraIndex].raw.filename and image[cameraIndex].raw.filename != self.calcFilename(ndx,cameraIndex=cameraIndex):
					changed.append(image)
					break
		for ndx,image in enumerate(changed):
			image.rename('temp%04d.jpg'%(ndx+1))
		for ndx,image in enumerate(changed):
			image.thumbnail.relabel()
			for cameraIndex in self.cameraIndices:
				image[cameraIndex].rename(self.calcFilename(self.images.index(image),cameraIndex=cameraIndex))
		
		
	def delete(self,fromLocation):
		index,image = self.normalise(fromLocation)
		del(self.images[index])
		image.delete()
		self.view.remove(image.thumbnail)
		for ndx,i in enumerate(self.images[index:]):
			i.rename(self.calcBaseFilename(ndx+index))


	def select(self,image):
		self.selected = image
		self.view.app.processingQueue.put(processing.ImageLoadJob(self.view.app,image))

		
	def calcFilename(self,ndx,cameraIndex=1):
		if self.solo:
			assert cameraIndex == 1
			return 'page%04d.jpg'%(ndx+1)
		else:
			assert cameraIndex in (1,2)
			if cameraIndex == 1:
				return 'page%04dL.jpg'%(ndx+1)
			else:
				return 'page%04dR.jpg'%(ndx+1)


	def calcBaseFilename(self,ndx):
		return 'page%04d.jpg'%(ndx+1)
	

	def getLabel(self,location):
		index,image = self.normalise(location)
		return 'page %d'%(index + 1)
		