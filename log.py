"""
Set up logging and provide standard logging functions
"""

import sys
import traceback
import logging
import logging.handlers
from logging import CRITICAL,ERROR,WARNING,INFO,DEBUG
import os
import types
from base import smDataPath

__all__ = ['configureLogging','log','logException','debug','info','warning','warn','error','critical','exception','CRITICAL','ERROR','WARNING','INFO','DEBUG']

#
# Setup Python logging based on configuration options
#

def configureLogging(fileLevel=DEBUG,screenLevel=WARNING):
	""" 
	Set up logging based on configuration options 
	
	@return: None
	"""
	global logger
	
	if 'logger' in globals():
		raise Exception('Logging has already been configured')
	
	logger = logging.getLogger('scanmanager')
	
	handler = logging.handlers.RotatingFileHandler(
		filename=os.path.join(smDataPath(),'scanmanager.log'),
		mode='a',
		maxBytes=(1024)*1024,
		backupCount=10,
	)
	handler.setLevel(DEBUG)
	formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	
	console = logging.StreamHandler()
	console.setLevel(DEBUG)
	formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	logger.addHandler(console)

	logger.setLevel(-1)


def logException(text=None,level=ERROR,excInfo=None):
	"""
	Log an exception
	
	@param text: additional text to explain the error
	@param level: log level (see logging.DEBUG, logging.INFO, etc.)
	@param excInfo: optional tuple returned by C{sys.exc_info()} (we just call sys.exc_info it this is None) 
	@return: None
	"""
	if excInfo is None:
		excInfo = sys.exc_info()
	lines = traceback.format_exception(*excInfo)
	tb = ''.join(lines)
	if text is None:
		text = tb
	else:
		text = text + '\n' + tb
	log(level,text)
	return text
	

def log(*args,**kargs):
	logger.log(*args,**kargs)

def debug(*args,**kargs):
	logger.debug(*args,**kargs)

def info(*args,**kargs):
	logger.info(*args,**kargs)

def warning(*args,**kargs):
	logger.warning(*args,**kargs)

def warn(*args,**kargs):
	logger.warn(*args,**kargs)

def error(*args,**kargs):
	logger.error(*args,**kargs)

def critical(*args,**kargs):
	logger.critical(*args,**kargs)

def exception(*args,**kargs):
	logger.exception(*args,**kargs)
	
	

class TracedCallable(object):
	
	def __init__(self,parent,f,callbackStart=None,callbackEnd=None):
		self.parent = parent
		self.f = f
		self.callbackStart = callbackStart
		self.callbackEnd = callbackEnd
	
	def __call__(self,*args,**kargs):
		if self.callbackStart:
			self.callbackStart(self.parent,self.f,args,kargs)
		result = self.f(*args,**kargs)
		if self.callbackEnd:
			self.callbackEnd(self.parent,self.f,args,kargs,result)
		return result
	

class TracingWrapper(object):
	"""
	Wrap an object so that its method invocations are traced 
	"""
	
	def __init__(self,parent,prefix='',callbackStart=None,callbackEnd=None):
		self.__dict__['parent'] = parent
		self.__dict__['callbackStart'] = callbackStart or self.traceStart
		self.__dict__['callbackEnd'] = callbackEnd or self.traceEnd
		self.__dict__['prefix'] = 'trace'
		
	def __getattr__(self,k):
		v = getattr(self.parent,k)
		if type(v) is types.MethodType:
			return TracedCallable(self.parent,v,self.callbackStart,self.callbackEnd)
		else:
			return v
	def __setattr__(self,k,v):
		return setattr(self.parent,k,v)
	def __hasattr(self,k):
		return k in self.__dict__ or hasattr(self.parent,k)
		

	def traceStart(self,parent,function,args,kargs):
		if hasattr(parent,'getId'):
			name = parent.getId()
		elif hasattr(parent,'getName'):
			name = parent.getName()
		else:
			name = parent.__class__.__name__
		sArgs = ['%r'%i for i in args]
		sArgs += ['%s=%r'%(k,v) for k,v in kargs.items()]
		s = '[%s] %s.%s(%s)'%(self.prefix,name,function.__name__,','.join(sArgs))
		debug(s)
		
		
	def traceEnd(self,parent,function,args,kargs,result):
		if hasattr(parent,'getId'):
			name = parent.getId()
		elif hasattr(parent,'getName'):
			name = parent.getName()
		else:
			name = parent.__class__.__name__
		sArgs = ['%r'%i for i in args]
		sArgs += ['%s=%r'%(k,v) for k,v in kargs.items()]
		s = '[%s] %s.%s(%s) -> %r'%(self.prefix,name,function.__name__,','.join(sArgs),result)
		debug(s)

		
