import threading
import Queue
from PySide import QtGui
import log


class ProcessingJob(object):
	
	def execute(self):
		return
	
	def oncompletion(self):
		return


class PostCaptureJob(ProcessingJob):
	
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
			c = self.app.settings.crop.coords
			qi = qi.copy(c[0],c[1],c[2]-c[0],c[3]-c[1])
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
			