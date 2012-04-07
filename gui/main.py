from .common import *
from . import shooting
from . import settings
import backend

import shelve
import sys

class App(Application):
	
	def __init__(self,*args,**kargs):
		super(App,self).__init__(*args,**kargs)

	def init(self):
		self.db = shelve.open('scanmanager.settings')
		self.images = []

		backend.apis.loadAll()		
		backend.apis.openAll(db=self.db)
		errorText = backend.apis.formatAPIErrors()
		if errorText:
			sys.stderr.write(errorText)
		
		self.SetupWindow.initialiseOptions()
		self.SetupWindow.show()
		self.SetupWindow.loadSettings()


	class SetupWindow(settings.SetupWindow):
		pass


	class MainWindow(shooting.MainWindow):
		pass

	
	class Timer(BaseWidget,QtCore.QTimer):
		
		def init(self):
			self.setInterval(100)
			self.start()
			
		def ontimeout(self):
			if not self.app.MainWindow.isVisible():
				return
			for camera in self.app.cameras:
				camera.ontimer()


	def cameraPropertiesChanged(self,camera):
		ndx = self.cameras.index(camera) + 1
		cc = getattr(self,'Camera%dControls'%ndx)
		cc.refreshFromCamera()
		

	@property
	def cameras(self):
		if not hasattr(self,'settings'):
			return ()
		if self.settings.mode == Mode.V:
			return (self.settings.cameraL,self.settings.cameraR)
		else:
			return (self.settings.cameraC,)


'''
class App(Application):

	def init(self):
		self.db = shelve.open('scanmanager.settings')
		self.images = []
		self.open.connect(self.doOnOpen)
		self.open.emit()
	
	open = QtCore.Signal()

	def doOnOpen(self):
		""" This messing around is needed to ensure all initialisation of SDKs etc. happens in the main GUI thread """
		backend.apis.loadAll()		
		backend.apis.openAll(db=self.db)
		errorText = backend.apis.formatAPIErrors()
		if errorText:
			sys.stderr.write(errorText)
		
		self.SetupWindow = settings.SetupWindow()
		self.SetupWindow._up = self
		toInit = self.SetupWindow._autoInstantiate()
		for o in toInit:
			o.init()
		self.SetupWindow.init()
		self.MainWindow = shooting.MainWindow()
		self.MainWindow._up = self
		toInit = self.MainWindow._autoInstantiate()
		for o in toInit:
			o.init()
		self.MainWindow.init()
		
		
		self.SetupWindow.initialiseOptions()
		self.SetupWindow.show()
		self.SetupWindow.loadSettings()		
		print('doo done')


		
	def cameraPropertiesChanged(self,camera):
		ndx = self.cameras.index(camera) + 1
		cc = getattr(self,'Camera%dControls'%ndx)
		cc.refreshFromCamera()
		

	@property
	def cameras(self):
		if not hasattr(self,'settings'):
			return ()
		if self.settings.mode == Mode.V:
			return (self.settings.cameraL,self.settings.cameraR)
		else:
			return (self.settings.cameraC,)
		

	#class Timer(BaseWidget,QtCore.QTimer):
	#	
	#	def init(self):
	#		self.setInterval(100)
	#		self.start()
	#		
	#	def ontimeout(self):
	#		if not self.app.MainWindow.isVisible():
	#			return
	#		for camera in self.app.cameras:
	#			camera.ontimer()
'''