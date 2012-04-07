"""
Set up logging and provide standard logging functions
"""

import sys
import traceback
import logging
import logging.handlers
from logging import CRITICAL,ERROR,WARNING,INFO,DEBUG

__all__ = ['configureLogging','log','logException','debug','info','warning','warn','error','critical','exception','CRITICAL','ERROR','WARNING','INFO','DEBUG']

import config

#
# Setup Python logging based on configuration options
#

def configureLogging():
	""" 
	Set up logging based on configuration options 
	
	@return: None
	"""
	global logger
	
	logger = logging.getLogger('scanmanager')
	
	handler = logging.handlers.RotatingFileHandler(
		filename=config.cfg.logging.logFile,
		mode='a',
		maxBytes=(1024)*1024,
		backupCount=10,
	)
	handler.setLevel(config.cfg.logging.fileLogLevel)
	formatter = logging.Formatter('%(asctime)s %(levelname)-8s [scanmanager] %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.NOTSET)
	
	if config.cfg.logging.logToScreen:
		console = logging.StreamHandler()
		console.setLevel(config.cfg.logging.screenLogLevel)
		formatter = logging.Formatter('%(asctime)s %(levelname)-8s [scanmanager] %(message)s')
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
	

