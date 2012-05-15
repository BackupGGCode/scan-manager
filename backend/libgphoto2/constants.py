#
# Based on: piggyphoto.py which is Copyright (C) 2010 Alex Dumitrache
#

class GPhotoError(Exception):
    def __init__(self, result, message):
        self.result = result
        self.message = message
    def __str__(self):
        if self.message:
            return '%s (%s)'%(self.message,self.result)
        else:
            return '(%s)'%(self.result)
    def __repr__(self):
        return '<%s %s (%s)>'%(self.__class__.__name__,self.message,self.result)


    
class Enum(object):
    
    def __iter__(self):
        for k,v in self.__dict__.items():
            yield (k,v)
    
    
    def __getitem__(self,i):
        for k,v in self.__dict__.items():
            if v == i:
                return k
        else:
            raise KeyError(i)


GPEvent = Enum()
GPEvent.UNKNOWN = 0
GPEvent.TIMEOUT = 1
GPEvent.FILE_ADDED = 2    
GPEvent.FOLDER_ADDED = 3 
GPEvent.CAPTURE_COMPLETE = 4       


#cdef extern from "gphoto2/gphoto2-port-version.h":
# ctypedef enum GPVersionVerbosity:
GPVersion = Enum()
GPVersion.SHORT = 0
GPVersion.VERBOSE = 1

#cdef extern from "gphoto2/gphoto2-abilities-list.h":
# ctypedef enum CameraDriverStatus:
GPDriverStatus = Enum()
GPDriverStatus.PRODUCTION = 0
GPDriverStatus.TESTING = 1
GPDriverStatus.EXPERIMENTAL = 2
GPDriverStatus.DEPRECATED = 3

# ctypedef enum CameraOperation:
GPOperation = Enum()
GPOperation.NONE = 0
GPOperation.CAPTURE_IMAGE = 1 << 0
GPOperation.CAPTURE_VIDEO = 1 << 1
GPOperation.CAPTURE_AUDIO = 1 << 2
GPOperation.CAPTURE_PREVIEW = 1 << 3
GPOperation.CONFIG = 1 << 4

# ctypedef enum CameraFileOperation:
GPFileOperation = Enum()
GPFileOperation.NONE = 0
GPFileOperation.DELETE = 1 << 1
GPFileOperation.PREVIEW = 1 << 3
GPFileOperation.RAW = 1 << 4
GPFileOperation.AUDIO = 1 << 5
GPFileOperation.EXIF = 1 << 6

# ctypedef enum CameraFolderOperation:
GPFolderOperation = Enum()
GPFolderOperation.NONE = 0
GPFolderOperation.DELETE_ALL = 1 << 0
GPFolderOperation.PUT_FILE = 1 << 1
GPFolderOperation.MAKE_DIR = 1 << 2
GPFolderOperation.REMOVE_DIR = 1 << 3

#cdef extern from "gphoto2/gphoto2-port-info-list.h":
# ctypedef enum GPPortType:
GPPort = Enum()
GPPort.NONE = 0
GPPort.SERIAL = 1
GPPort.USB = 2

# gphoto constants
# Defined in 'gphoto2-port-result.h'
GP_OK = 0
# CameraCaptureType enum in 'gphoto2-camera.h'
GP_CAPTURE_IMAGE = 0
# CameraFileType enum in 'gphoto2-file.h'
GP_FILE_TYPE_NORMAL = 1

GPWidget = Enum()
GPWidget.WINDOW = 0 # Window widget This is the toplevel configuration widget. It should likely contain multiple Widget.SECTION entries.
GPWidget.SECTION = 1 # Section widget (think Tab).
GPWidget.TEXT = 2 # Text widget.
GPWidget.RANGE = 3 # Slider widget.
GPWidget.TOGGLE = 4 # Toggle widget (think check box).
GPWidget.RADIO = 5 # Radio button widget.
GPWidget.MENU = 6 # Menu widget (same as RADIO).
GPWidget.BUTTON = 7 # Button press widget.
GPWidget.DATE = 8 # Date entering widget.

widget_types = ['Window', 'Section', 'Text', 'Range', 'Toggle', 'Radio', 'Menu', 'Button', 'Date']

GPCameraStorageInfoFields = Enum()
GPCameraStorageInfoFields.BASE = 1 << 0 # The base directory. Usually / if just 1 storage is attached.
GPCameraStorageInfoFields.LABEL = 1 << 1 # Label of the filesystem. Could also be a DOS label.
GPCameraStorageInfoFields.DESCRIPTION = 1 << 2 # More verbose description.
GPCameraStorageInfoFields.ACCESS = 1 << 3 # Access permissions.
GPCameraStorageInfoFields.STORAGETYPE = 1 << 4 # Hardware type.
GPCameraStorageInfoFields.FILESYSTEMTYPE = 1 << 5 # Filesystem type.
GPCameraStorageInfoFields.MAXCAPACITY = 1 << 6 # Maximum capacity in kbytes.
GPCameraStorageInfoFields.FREESPACEKBYTES = 1 << 7 # Free space in kbytes.
GPCameraStorageInfoFields.FREESPACEIMAGES = 1 << 8 # Free space in images.

 