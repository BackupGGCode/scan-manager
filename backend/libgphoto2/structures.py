#
# Based on: piggyphoto.py which is Copyright (C) 2010 Alex Dumitrache
#

import ctypes

class CameraFilePath(ctypes.Structure):
	_fields_ = [('name', (ctypes.c_char * 128)),
				('folder', (ctypes.c_char * 1024))]


class CameraText(ctypes.Structure):
	_fields_ = [('text', (ctypes.c_char * (32 * 1024)))]


class CameraAbilities(ctypes.Structure):
	_fields_ = [('model', (ctypes.c_char * 128)),
				('status', ctypes.c_int),
				('port', ctypes.c_int),
				('speed', (ctypes.c_int * 64)),
				('operations', ctypes.c_int),
				('file_operations', ctypes.c_int),
				('folder_operations', ctypes.c_int),
				('usb_vendor', ctypes.c_int),
				('usb_product', ctypes.c_int),
				('usb_class', ctypes.c_int),
				('usb_subclass', ctypes.c_int),
				('usb_protocol', ctypes.c_int),
				('library', (ctypes.c_char * 1024)),
				('id', (ctypes.c_char * 1024)),
				('device_type', ctypes.c_int),
				('reserved2', ctypes.c_int),
				('reserved3', ctypes.c_int),
				('reserved4', ctypes.c_int),
				('reserved5', ctypes.c_int),
				('reserved6', ctypes.c_int),
				('reserved7', ctypes.c_int),
				('reserved8', ctypes.c_int)]


class CameraWidget(ctypes.Structure):
	_fields_ = [('type', ctypes.c_int),
				('label', (ctypes.c_char * 256)),
				('info', (ctypes.c_char * 1024)),
				('name', (ctypes.c_char * 256)),
				('parent', (ctypes.c_void_p)),
				('value_string', ctypes.c_char_p),
				('value_int', ctypes.c_int),
				('value_float', ctypes.c_float),
				('choice', (ctypes.c_void_p)),
				('choice_count', ctypes.c_int),
				('min', ctypes.c_float),
				('max', ctypes.c_float),
				('increment', ctypes.c_float),
				('children', (ctypes.c_void_p)),
				('children_count', (ctypes.c_int)),
				('changed', (ctypes.c_int)),
				('readonly', (ctypes.c_int)),
				('ref_count', (ctypes.c_int)),
				('id', (ctypes.c_int)),
				('callback', (ctypes.c_void_p))]


class PortInfo(ctypes.Structure):
	_fields_ = [
			('type', ctypes.c_int), # enum is 32 bits on 32 and 64 bit Linux
			('name', (ctypes.c_char * 64)),
			('path', (ctypes.c_char * 64)),
			('library_filename', (ctypes.c_char * 1024))
			]


class PortInfoNew(ctypes.c_void_p):
	""" Latest SVN code uses a pointer for PortInfo rather than the old structure """ 

