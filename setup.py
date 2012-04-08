import platform
from glob import glob
   
if platform.system().lower() == 'windows':
	from distutils.core import setup
	import py2exe
	
	setup(
		name = "scanmanager",
		version = "0.1",
		description = "Tethered shooting GUI for book scanners",
		data_files = [
			# Canon PS-ReC dlls
			('backend/canonpsrec',['backend/canonpsrec/PRLIB.dll','backend/canonpsrec/PRSDK.dll']),
			# Nikon DLLs and plugins
			('backend/nikonsdk',['backend/nikonsdk/NkdPTP.dll','backend/nikonsdk/NkdPTPDi.dll','backend/nikonsdk/D80_Mod.md3']),
			# Image format plugins for PyQt4
			('imageformats',glob('d:\Python27\Lib\site-packages\PySide\plugins\imageformats\*')),
			#glob('d:\Python27\Lib\site-packages\PySide\qt.conf'),
		],
		options = dict(
			py2exe = dict(
						typelibs = [('{94A0E92D-43C0-494E-AC29-FD45948A5221}', 0, 1, 0)],
						includes = ['PySide.QtNetwork','dumbdbm','dbhash'],
			),
		),
		#console = ('scanmanager.py',),
		windows = [
	       dict(
				script = 'scanmanager.py',
			)
		],	
	)
