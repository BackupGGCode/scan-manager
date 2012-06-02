import threading
import Queue
from PySide import QtGui
from PySide import QtCore
import log
import itertools
import Queue



class ProcessingJob(object):

	priority = 10
	order = 0
	
	def execute(self):
		return
	
	def oncompletion(self):
		return

	def __cmp__(self,other):
		return cmp((self.priority,self.order),(other.priority,other.order))
	
	

class PostCaptureJob(ProcessingJob):
	
	priority = 5
	
	def __init__(self,app,image,cameraIndex,pm=None):
		self.app = app
		self.image = image
		self.cameraIndex = cameraIndex
		self.pm = pm
		
	def execute(self):
		
		camera = self.app.cameras[self.cameraIndex-1]
		
		if not self.pm:
			self.pm = QtGui.QPixmap()
			self.pm.load(self.image[self.cameraIndex].raw.getFilePath())

		self.pmUndistorted = self.pm

		if not (camera.settings.get('undistort',None) and camera.settings.undistort.isActive()) and not (camera.settings.crop.get('enabled',False)):
			# neither correction nor cropping configured so do not save a processed version
			return
		
		# calibration correction
		if camera.settings.get('undistort',None) and camera.settings.undistort.isActive():
			self.pm = camera.settings.undistort.correct(self.pm)
			self.pmUndistorted = self.pm

		# cropping
		if camera.settings.crop.get('enabled',False) and camera.settings.crop.coords:
			c = camera.settings.crop.coords
			
			qi = self.pm.toImage()
			size = qi.size()

			rect = QtCore.QRect(
				min(size.height(),c[0]),
				min(size.width(),c[1]),
				max(0,size.width()-(c[0]+c[2])),
				max(0,size.height()-(c[1]+c[3]))
			)

			qi = qi.copy(rect)
			self.pm = QtGui.QPixmap.fromImage(qi)
		
		self.pm.save(self.image[self.cameraIndex].processed.getFilePath())

	def oncompletion(self):
		self.app.previews[self.cameraIndex].loadFromData('undistorted',self.pmUndistorted)
		self.app.previews[self.cameraIndex].loadFromData('processed',self.pm)



class ImageLoadJob(ProcessingJob):
	
	priority = 4
	
	def __init__(self,app,image):
		self.app = app
		self.image = image
		self.pms = {1:dict(raw=None,processed=None),2:dict(raw=None,processed=None)}
		
	def execute(self):
		for cameraIndex in self.app.cameraIndices:
			for state in ['raw','processed']:
				image = getattr(self.image[cameraIndex],state)
				if image.exists():
					pm = QtGui.QPixmap()
					rc = pm.load(image.getFilePath())
					if rc:
						self.pms[cameraIndex][state] = pm
		
	def oncompletion(self):
		for cameraIndex in self.app.cameraIndices:
			self.app.previews[cameraIndex].loadFromData('raw',self.pms[cameraIndex]['raw'])
			if self.pms[cameraIndex]['processed']:
				self.app.previews[cameraIndex].loadFromData('undistorted',QtGui.QPixmap())
				self.app.previews[cameraIndex].loadFromData('processed',self.pms[cameraIndex]['processed'])
			else:
				self.app.previews[cameraIndex].loadFromData('undistorted',QtGui.QPixmap())
				self.app.previews[cameraIndex].loadFromData('processed',self.pms[cameraIndex]['raw'])
				



class SimpleJob(ProcessingJob):
	
	def __init__(self,execute,oncompletion=lambda a:None):
		self._execute = execute
		self._oncompletion = oncompletion
	
	def execute(self):
		return self._execute(self)
	
	def oncompletion(self):
		return self._oncompletion(self)



class ProcessingThread(threading.Thread):
	
	def __init__(self,app):
		threading.Thread.__init__(self)
		self.app = app
	
	def run(self):
		try:
			while 1:
				if self.app.closingDown() or getattr(self.app,'allDone',None):
					return
				try:
					item = self.app.processingQueue.get(True,0.1)
				except Queue.Empty:
					continue
				
				item.execute()
				self.app.MainWindow.processingCompleted.emit(item)
		except:
			log.logException('processing thread error',log.ERROR)
			raise
		finally:
			log.debug('processing thread exiting')



class ProcessingQueue(Queue.PriorityQueue):
	
	def __init__(self,maxsize=None):
		Queue.PriorityQueue.__init__(self,maxsize=maxsize)
		self.counter = itertools.count()
	
	def put(self,*args,**kargs):
		args[0].order = self.counter.next()
		Queue.PriorityQueue.put(self,*args,**kargs)
		
