from gui.main import App
import sys
import traceback

from gui.dialogs import CrashDialog

import backend
from log import *

import resources


def excepthook(excType, excValue, tracebackobj):
	"""
	Global catchall for unhandled exceptions
	"""
	global app
	excInfo = (excType, excValue, tracebackobj)
	text = logException(excInfo=excInfo)
	try:
		dialog = CrashDialog(parent=app.activeWindow(),html='<pre>%s</pre>'%text)
		dialog.open()
	except:
		pass


if __name__ == '__main__':

	try:
		configureLogging()
		app = App(sys.argv)
		sys.excepthook = excepthook
		app.exec_()
	finally:
		for api in backend.apis:
			try: api.saveSettings()
			except: pass
			try: api.close()
			except: pass
		try: app.db.close()
		except: pass
		print 'now exit'
