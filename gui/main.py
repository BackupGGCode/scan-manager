from .common import *
from . import shooting
from . import settings
from . import calibrate
import backend
import base

import shelve
import sys
from dialogs import CrashDialog

class App(Application):

	
	def init(self):
		self.db = shelve.open(os.path.join(smDataPath(),'scanmanager.settings'))
		self.images = []

		backend.apis = backend.BackendManager(trace=base.runtimeOptions.trace)
		apis = backend.apis
		apis.loadAll()		
		apis.openAll(db=self.db)
		errorText = apis.formatAPIErrors()
		if errorText:
			sys.stderr.write(errorText)
		
		if 'calibrators' in self.db:
			self.calibrators = self.db['calibrators']
		else:
			self.calibrators = [None,None]
		
		self.setWindowIcon(QtGui.QIcon(':/scanmanager-16.png'))
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

	calibrationDataChanged = QtCore.Signal()
	
