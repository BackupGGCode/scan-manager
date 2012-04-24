import platform
from glob import glob
import base

if platform.system().lower() == 'windows':
	from distutils.core import setup
	import py2exe
	
	setup(
		name = "scanmanager",
		version = base.smGetVersion(),
		description = "Tethered shooting GUI for book scanners",
		data_files = [
			# Canon PS-ReC dlls
			('backend/canonpsrec',['backend/canonpsrec/PRLIB.dll','backend/canonpsrec/PRSDK.dll']),
			# Nikon DLLs and plugins
			('backend/nikonsdk',['backend/nikonsdk/NkdPTP.dll','backend/nikonsdk/NkdPTPDi.dll','backend/nikonsdk/D80_Mod.md3']),
            # libgphoto2 backend dlls etc.
            ('backend/libgphoto2',glob('backend/libgphoto2/*.py')),
            ('backend/libgphoto2/remote',glob('backend/libgphoto2/remote/*.py')),
            ('backend/libgphoto2/remote/bin',glob('backend/libgphoto2/remote/bin/*')),
            ('backend/libgphoto2/win32',glob('backend/libgphoto2/win32/*.dll')),
            ('backend/libgphoto2/win32',glob('backend/libgphoto2/win32/*.exe')),
            ('backend/libgphoto2/win32',glob('backend/libgphoto2/win32/*.bat')),
            ('backend/libgphoto2/win32',glob('backend/libgphoto2/win32/*.txt')),
            ('backend/libgphoto2/win32/camlibs',glob('backend/libgphoto2/win32/camlibs/*.dll')),
            ('backend/libgphoto2/win32/iolibs',glob('backend/libgphoto2/win32/iolibs/*.dll')),
			# Image format plugins for PyQt4
			('imageformats',glob('d:\Python27\Lib\site-packages\PySide\plugins\imageformats\*')),
			#glob('d:\Python27\Lib\site-packages\PySide\qt.conf'),
            ("Microsoft.VC90.CRT", glob(r'win32\Microsoft.VC90.CRT\*.*')),
		],
		options = dict(
			py2exe = dict(
				typelibs = [('{94A0E92D-43C0-494E-AC29-FD45948A5221}', 0, 1, 0)],
				includes = ['PySide.QtNetwork','dumbdbm','dbhash','numpy','numpy.core','numpy.core.multiarray'],
                excludes = ['Tkconstants','Tkinter','tcl','tk'],
                dll_excludes = [ 'mswsock.dll', 'powrprof.dll' ],
			),
		),
		#console = ('scanmanager.py',),
		windows = [
	       dict(
				script = 'scanmanager.py',
                icon_resources = [(1,'scanmanager.ico')],
			)
		],	
	)



