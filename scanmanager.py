from gui.main import App
import sys
import os
import traceback

from gui.dialogs import CrashDialog

import log
import optparse
import base
import backend

import resources


COMMAND_LINE_HELP = """Usage: scanmanager [--debug]
	-d, --debug			Run in debug mode (logs detailed information to the console as well as the log file) 
	-t, --trace		 Log detailed calls for debugging backend APIs 
"""

def excepthook(excType, excValue, tracebackobj):
	"""
	Global catchall for unhandled exceptions
	"""
	global app
	excInfo = (excType, excValue, tracebackobj)
	text = log.logException(excInfo=excInfo)
	try:
		dialog = CrashDialog(parent=None,html='<pre>%s</pre>'%text)
		dialog.open()
	except:
		pass
	try:
		app.close()
	except:
		pass
	



if __name__ == '__main__':

	class MyOptParser(optparse.OptionParser):
		def print_help(self):
			print 'ScanManager'
			print COMMAND_LINE_HELP
			
	parser = MyOptParser()
	parser.add_option('-d','--debug',action='store_true',dest='debug')
	parser.add_option('-t','--trace',action='store_true',dest='trace')
	(options, args) = parser.parse_args()
	
	base.runtimeOptions.debug = options.debug
	base.runtimeOptions.trace = options.trace

	if getattr(sys,'frozen',None) == 'windows_exe':
		sys.stdout = open(os.path.join(base.smDataPath(),'scanmanager.stdout.log'),'wt')
		sys.stderr = open(os.path.join(base.smDataPath(),'scanmanager.stdout.log'),'wt')

	try:
		if base.runtimeOptions.debug:
			log.configureLogging(fileLevel=log.DEBUG,screenLevel=log.DEBUG)
		else:
			log.configureLogging(fileLevel=log.DEBUG,screenLevel=log.WARNING)
			
		log.debug('starting up')
		
		app = App(sys.argv)
		sys.excepthook = excepthook
		app.exec_()
		
	finally:
		try:
			app.allDone = True # to kill the processing thread
		except:
			pass
		if backend.apis:
			for api in backend.apis:
				try: api.saveSettings()
				except: pass
				try: api.close()
				except: pass
		try: app.settings.save()
		except: log.logException('failed saving settings', log.ERROR)
		try: app.db.close()
		except: pass
