from .common import *
from . import shooting
from . import settings
from gui.dialogs import CrashDialog
import backend
import base
import log
import os
from . import processing

import shelve
import Queue


class ApplicationSettings(object):
	def __contains__(self,k):
		return k in self.__dict__
	def get(self,*args):
		return self.__dict__.get(*args)


class ApplicationMainSettings(object):
	def __init__(self,db):
		self._db = db
	def __getattr__(self,k):
		self.__dict__[k] = ApplicationSettings()
		return self.__dict__[k]
	def save(self):
		for k in self.__dict__:
			if k == '_db':
				continue
			try:
				self._db[k] = getattr(self,k)
			except:
				log.error('error saving %s in settings db'%k)
	def load(self):
		if self._db.get('version',None) != base.smGetSettingsVersion():
			return False
		for k,v in self._db.items():
			setattr(self,k,v)
		return True
	def __contains__(self,k):
		return k in self.__dict__
		
		

class App(Application):

	def init(self):
		self.db = shelve.open(os.path.join(smDataPath(),'scanmanager.settings'))
		if not self.db.keys():
			self.db['version'] = base.smGetSettingsVersion()
		self.settings = ApplicationMainSettings(db=self.db)
		if not self.settings.load():
				log.error('Settings file out of date')
				e = QtGui.QMessageBox.critical(
					None,
					self.tr('Error'),
					self.tr('''
						<p>Your scanmanager.settings file appears to be out of date (existing settings version %s, app settings version %s).</p>
						<p>Try deleting %s</p>''') % (
							self.db.get('version',None),
							base.smGetSettingsVersion(),
							os.path.join(base.smDataPath(),'scanmanager.settings')
						)
				)
				self.quit()
				return
			
		if 'calibrators' not in self.settings:
			self.settings.calibrators = {1:None,2:None}
		if 'rotate' not in self.settings:
			self.settings.rotate = {1:None,2:None}
		
		self.images = []
		
		backend.apis = backend.BackendManager(trace=base.runtimeOptions.trace)
		apis = backend.apis
		apis.loadAll()		
		apis.openAll(db=self.db)
		errorText = apis.formatAPIErrors()
		if errorText:
			sys.stderr.write(errorText)
		

		self.processingQueue = processing.ProcessingQueue()
		
		self.setWindowIcon(QtGui.QIcon(':/scanmanager-16.png'))
		self.SetupWindow.initialiseOptions()
		self.SetupWindow.show()
		self.SetupWindow.loadSettings()
	
		
	class SetupWindow(settings.SetupWindow):
		pass
	
	
	class MainWindow(shooting.MainWindow):
		pass
		

	def cameraPropertiesChanged(self,camera):
		ndx = self.cameras.index(camera) + 1
		cc = getattr(self,'Camera%dControls'%ndx)
		cc.refreshFromCamera()
		

	@property
	def cameras(self):
		if not hasattr(self,'settings'):
			return ()
		if self.settings.setup.mode == Mode.V:
			return (self.setup.cameraL,self.setup.cameraR)
		else:
			return (self.setup.cameraC,)

	calibrationDataChanged = QtCore.Signal()
	cropboxChanged = QtCore.Signal(object,object)


