#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import traceback
from PtpUsbTransport import PtpUsbTransport
from PtpSession import PtpException
import PtpCHDK
import PtpValues
import time

ptpTransport = PtpUsbTransport(PtpUsbTransport.findptps()[0])
ptpSession = PtpCHDK.PtpCHDKSession(ptpTransport)

vendorId = PtpValues.Vendors.STANDARD

ptpSession.OpenSession()
deviceInfo = ptpSession.GetDeviceInfo()
vendorId = deviceInfo.VendorExtensionID

import ctypes

import cProfile
import pstats


import Image

def doLV():
	for i in range(10):
		t = time.time()
		frame = ptpSession.GetLiveData()
		tRetrieved = time.time()
		viewport = Image.fromstring("RGB",(frame.header.bitmap.logical_width,frame.header.bitmap.logical_height),frame.viewportRGB,'raw','RGB')
		bitmap = Image.fromstring("RGBA",(frame.header.bitmap.logical_width,frame.header.bitmap.logical_height),frame.bitmapRGBA,'raw','RGBA')
		viewport.save(r'd:\temp\test-vp.jpg')
		bitmap.save(r'd:\temp\test-bm.jpg')
		print 'live data retrieved in %.2fs'%(tRetrieved-t)

	
try:
	version = ptpSession.GetVersion()
	print 'version',version

	scriptId,rc = ptpSession.ExecuteScript('switch_mode_usb(1)')
	print 'execute switch mode',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d %s'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))
	
	cProfile.run('doLV()', 'mydata')
	p = pstats.Stats('mydata')
	p.strip_dirs().sort_stats('cumulative').print_stats()
	
	rc = ptpSession.Upload('A/CHDK/SCRIPTS/testme.lua','''print( "hello world" )''')
	print 'upload',rc
	rc = ptpSession.Download('A/CHDK/SCRIPTS/testme.lua')
	print 'download',rc
	scriptId,rc = ptpSession.ExecuteScript('loadfile("A/CHDK/SCRIPTS/testme.lua")()')
	print 'execute loadfile',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d %s'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))
	
	scriptId,rc = ptpSession.ExecuteScript('return "returning a string from a Lua script"')
	print 'execute',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d (=%s)'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))

	while 1:
		rc = ptpSession.ReadScriptMessage(scriptId=0)
		if rc:
			print 'flushing message',rc
		else:
			break
		
	scriptId,rc = ptpSession.ExecuteScript('write_usb_msg({apples=-1},10)')
	rc = ptpSession.ReadScriptMessage(scriptId=scriptId)
	print 'read message',rc

	scriptId,rc = ptpSession.ExecuteScript('write_usb_msg(read_usb_msg(100))')
	print 'execute',scriptId,rc
	rc = ptpSession.WriteScriptMessage(scriptId=scriptId,message='hello world')
	print 'write message',rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d (=%s)'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))
	rc = ptpSession.ReadScriptMessage(scriptId=scriptId)
	print 'read message',rc
except PtpException, e:
	print "PTP Exception: %s" % PtpValues.ResponseNameById(e.responsecode, vendorId)
	raise
