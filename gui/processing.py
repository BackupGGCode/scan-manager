import threading
import Queue
from PySide import QtGui
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
		if not self.pm:
			self.pm = QtGui.QPixmap()
			self.pm.load(self.image[self.cameraIndex].raw.getFilePath())
			
		# calibration correction
		if self.app.settings.calibrators[self.cameraIndex] and self.app.settings.calibrators[self.cameraIndex].isActive():
			self.pm = self.app.settings.calibrators[self.cameraIndex].correct(self.pm)

		# cropping
		if self.app.settings.crop.get('enabled',False):
			qi = self.pm.toImage()
			c = self.app.settings.crop.coords[self.cameraIndex]
			size = qi.size()
			qi = qi.copy(c[0],c[1],max(size.width()-c[2],c[0]+1),max(size.height()-c[3],c[1]+1))
			self.pm = QtGui.QPixmap.fromImage(qi)
		
		self.pm.save(self.image[self.cameraIndex].processed.getFilePath())

	def oncompletion(self):
		self.app.previews[self.cameraIndex].processed.loadFromData(self.pm)


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
		
