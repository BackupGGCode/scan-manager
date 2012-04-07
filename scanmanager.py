from gui.main import App
import sys
import traceback

from gui.dialogs import CrashDialog

import backend

def excepthook(excType, excValue, tracebackobj):
	"""
	Global catchall for unhandled exceptions
	"""
	global app
	excInfo = (excType, excValue, tracebackobj)
	lines = traceback.format_exception(*excInfo)
	tb = ''.join(lines)
	sys.stderr.write(tb)
	try:
		dialog = CrashDialog(parent=app.activeWindow(),text=tb)
		dialog.open()
	except:
		pass


if __name__ == '__main__':
	
	app = App(sys.argv)
	sys.excepthook = excepthook
	app.exec_()
	for api in backend.apis:
		try: api.saveSettings()
		except: pass
		try: api.close()
		except: pass
	try: app.db.close()
	except: pass
	sys.exit()
