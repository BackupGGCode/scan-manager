#
# Based on: piggyphoto.py which is Copyright (C) 2010 Alex Dumitrache
#
from ctypes import *

CameraWidgetCallback = CFUNCTYPE(c_void_p, c_void_p, c_void_p)


class CameraFilePath(Structure):
	_fields_ = [('name', (c_char * 128)),
				('folder', (c_char * 1024))]


class CameraText(Structure):
	_fields_ = [('text', (c_char * (32 * 1024)))]


class CameraAbilities(Structure):
	_fields_ = [('model', (c_char * 128)),
				('status', c_int),
				('port', c_int),
				('speed', (c_int * 64)),
				('operations', c_int),
				('file_operations', c_int),
				('folder_operations', c_int),
				('usb_vendor', c_int),
				('usb_product', c_int),
				('usb_class', c_int),
				('usb_subclass', c_int),
				('usb_protocol', c_int),
				('library', (c_char * 1024)),
				('id', (c_char * 1024)),
				('device_type', c_int),
				('reserved2', c_int),
				('reserved3', c_int),
				('reserved4', c_int),
				('reserved5', c_int),
				('reserved6', c_int),
				('reserved7', c_int),
				('reserved8', c_int)]


class CameraWidget(Structure):
	_fields_ = [('type', c_int),
				('label', (c_char * 256)),
				('info', (c_char * 1024)),
				('name', (c_char * 256)),
				('parent', (c_void_p)),
				('value_string', c_char_p),
				('value_int', c_int),
				('value_float', c_float),
				('choice', (c_void_p)),
				('choice_count', c_int),
				('min', c_float),
				('max', c_float),
				('increment', c_float),
				('children', (c_void_p)),
				('children_count', (c_int)),
				('changed', (c_int)),
				('readonly', (c_int)),
				('ref_count', (c_int)),
				('id', (c_int)),
				('callback', (c_void_p))]


class PortInfo(Structure):
	_fields_ = [
			('type', c_int), # enum is 32 bits on 32 and 64 bit Linux
			('name', (c_char * 64)),
			('path', (c_char * 64)),
			('library_filename', (c_char * 1024))
			]


class PortInfoNew(c_void_p):
	""" Latest SVN code uses a pointer for PortInfo rather than the old structure """ 

