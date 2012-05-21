from .common import *
from . import shooting
from . import setup
from gui.dialogs import CrashDialog
import backend
import base
import log
import os
import shutil
from . import processing

import shelve
import Queue


class ApplicationSettings(object):
	
	def __contains__(self,k):
		return k in self.__dict__
	
	def __getitem__(self,k):
		return self.__dict__[k]
	
	def __setitem__(self,k,v):
		self.__dict__[k] = v
	
	def get(self,*args):
		return self.__dict__.get(*args)


class ApplicationMainSettings(object):
	
	_children = ['setup']
	
	def __init__(self,db):
		self.__dict__['_db'] = db
		
	def __hasattr__(self,k):
		return k in self.__dict__
	
	def __setattr__(self,k,v):
		if k not in self._children:
			raise AttributeError(k)
		self.__dict__[k] = v
	
	def save(self):
		for k,v in self.__dict__.items():
			if k == '_db':
				continue
			try:
				self._db[k] = v
			except:
				log.error('error saving %s in settings db'%k)
		self._db.sync()
				
	def load(self):
		if self._db.get('version',None) != base.smGetSettingsVersion():
			return False
		for k,v in self._db.items():
			if k not in self._children:
				continue
			setattr(self,k,v)
		for k in self._children:
			if k not in self:
				setattr(self,k,ApplicationSettings())
		return True
	
	def __contains__(self,k):
		return k in self.__dict__
		
		

class App(Application):

	def init(self):
		
		dbFile = os.path.join(smDataPath(),'scanmanager.settings')
		
		if not os.path.exists(dbFile):
			shutil.copyfile(os.path.join(smBasePath(),'scanmanager.settings.default'),dbFile)
		
		# open a db and check we can access its keys
		db = shelve.open(dbFile)
		[i for i in db.keys()]
		db.close()
		
		# db seems OK -- make a backup and then open it for real
		shutil.copyfile(dbFile,os.path.join(smDataPath(),'scanmanager.settings.backup'))
		self.db = shelve.open(dbFile)
		
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
	
		
	class SetupWindow(setup.SetupWindow):
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
		if self.setup.mode == Mode.V:
			return (self.setup.cameraL,self.setup.cameraR)
		else:
			return (self.setup.cameraC,)

	def cameraSetting(self,camera):
		if type(camera) is int:
			camera = self.cameras[camera]
			
		name = 'CameraSetting:%s'%camera.getName()
		
		if name not in self.settings.cameras:
			self.settings.cameras[name] = ApplicationSettings()
			
		return self.settings.cameras[name]
		

	calibrationDataChanged = QtCore.Signal()
	cropboxChanged = QtCore.Signal(object,object)



