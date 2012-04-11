#
# Based on: piggyphoto.py which is Copyright (C) 2010 Alex Dumitrache
#

#cdef extern from "gphoto2/gphoto2-port-version.h":
# ctypedef enum GPVersionVerbosity:
GP_VERSION_SHORT = 0
GP_VERSION_VERBOSE = 1

#cdef extern from "gphoto2/gphoto2-abilities-list.h":
# ctypedef enum CameraDriverStatus:
GP_DRIVER_STATUS_PRODUCTION = 0
GP_DRIVER_STATUS_TESTING = 1
GP_DRIVER_STATUS_EXPERIMENTAL = 2
GP_DRIVER_STATUS_DEPRECATED = 3

# ctypedef enum CameraOperation:
GP_OPERATION_NONE = 0
GP_OPERATION_CAPTURE_IMAGE = 1
GP_OPERATION_CAPTURE_VIDEO = 2
GP_OPERATION_CAPTURE_AUDIO = 3
GP_OPERATION_CAPTURE_PREVIEW = 4
GP_OPERATION_CONFIG = 5

# ctypedef enum CameraFileOperation:
GP_FILE_OPERATION_NONE = 0
GP_FILE_OPERATION_DELETE = 1
GP_FILE_OPERATION_PREVIEW = 2
GP_FILE_OPERATION_RAW = 3
GP_FILE_OPERATION_AUDIO = 4
GP_FILE_OPERATION_EXIF = 5

# ctypedef enum CameraFolderOperation:
GP_FOLDER_OPERATION_NONE = 0
GP_FOLDER_OPERATION_DELETE_ALL = 1
GP_FOLDER_OPERATION_PUT_FILE = 2
GP_FOLDER_OPERATION_MAKE_DIR = 3
GP_FOLDER_OPERATION_REMOVE_DIR = 4

#cdef extern from "gphoto2/gphoto2-port-info-list.h":
# ctypedef enum GPPortType:
GP_PORT_NONE = 0
GP_PORT_SERIAL = 1
GP_PORT_USB = 2

# ctypedef enum CameraEventType
GP_EVENT_UNKNOWN = 0
GP_EVENT_TIMEOUT = 1	
GP_EVENT_FILE_ADDED = 2	
GP_EVENT_FOLDER_ADDED = 3

# gphoto constants
# Defined in 'gphoto2-port-result.h'
GP_OK = 0
# CameraCaptureType enum in 'gphoto2-camera.h'
GP_CAPTURE_IMAGE = 0
# CameraFileType enum in 'gphoto2-file.h'
GP_FILE_TYPE_NORMAL = 1

GP_WIDGET_WINDOW = 0 # Window widget This is the toplevel configuration widget. It should likely contain multiple GP_WIDGET_SECTION entries.
GP_WIDGET_SECTION = 1 # Section widget (think Tab).
GP_WIDGET_TEXT = 2 # Text widget.
GP_WIDGET_RANGE = 3 # Slider widget.
GP_WIDGET_TOGGLE = 4 # Toggle widget (think check box).
GP_WIDGET_RADIO = 5 # Radio button widget.
GP_WIDGET_MENU = 6 # Menu widget (same as RADIO).
GP_WIDGET_BUTTON = 7 # Button press widget.
GP_WIDGET_DATE = 8 # Date entering widget.
widget_types = ['Window', 'Section', 'Text', 'Range', 'Toggle', 'Radio', 'Menu', 'Button', 'Date']

