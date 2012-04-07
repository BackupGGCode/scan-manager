from base import Enum

import platform
import sys
import traceback
import importlib

if False:
	# This is here to persuade distribution tools that we're dependant on these packages
	from .canonpsrec import wrapper
	from .wia import wrapper
	from .libgphoto2 import wrapper
	from .directory import wrapper
	
backends = ['canonpsrec','wia','libgphoto2','directory']


APIState = Enum() #: ENUM holding the current state of a backend API
APIState.Opened = 1
APIState.Imported = 2
APIState.NotSupported = 3
APIState.ImportError = 4
APIState.OpenError = 5


class BackendState(object):
	"""
	Class for storing the state of particular backend APIs as they're being loaded and tested
	
	@ivar info: the Info static class from the API's __init__.py
	@ivar api: the L{backend.interface.API} singleton for this API 
	@ivar state: the current state of this API, a member of L{APIState} 
	@ivar module: the wrapper module for this API
	@ivar error: a multi-line error string giving a traceback if there was a problem loading/opening this API 
	"""
	def __init__(self,info,api=None,state=None,module=None,error=None):
		self.info = info
		self.api = api
		self.state = state
		self.module = module
		self.error = error

		

class BackendManager(object):
	""" 
	Class for managing camera backends cleanly including recording any errors that develop attempting to load or start them
	"""
	
	def __init__(self):
		self.states = []

		
	def loadAll(self):
		""" 
		Import all API modules 
		"""
		
		for backend in backends:
			info = importlib.import_module('.%s'%backend,__name__).Info
			name = info.getName()
			available = info.isAvailable()
			if not available:
				self.states.append(BackendState(info=info,state=APIState.NotSupported))
				continue
			try:
				module = importlib.import_module('.%s.wrapper'%backend,__name__)
			except:
				self.states.append(BackendState(info=info,state=APIState.ImportError))
			else:
				self.states.append(BackendState(info=info,state=APIState.Imported,module=module))

			
	def openAll(self,db):
		""" 
		Open imported API modules 
		"""
		for state in self.states:
			if state.state != APIState.Imported:
				continue
			try:
				api = state.module.API(db=db)
				api.open()
			except:
				state.error = self.formatException()
				state.state = APIState.OpenError
			else:
				state.api = api
				state.state = APIState.Opened


	def formatException(self):
		excInfo = sys.exc_info()
		lines = traceback.format_exception(*excInfo)
		tb = ''.join(lines)
		return tb
	
	
	def formatAPIErrors(self):
		out = ''
		for state in self.states:
			if state.state in (APIState.ImportError,APIState.OpenError):
				out += '='*80 + '\n'
				out += '%s\n'%state.info.getName()
				out += '-'*80 + '\n'
				out += state.error
				out += '='*80 + '\n'
		return out
	
	
	def __iter__(self):
		for i in self.states:
			if i.state != APIState.Opened:
				continue
			yield i.api
			
			
apis = BackendManager()
