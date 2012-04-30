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

	
try:
	version = ptpSession.GetVersion()
	print 'version',version

	scriptId,rc = ptpSession.ExecuteScript('switch_mode_usb(1)')
	print 'execute loadfile',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d %s'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))
	
	t = time.time()
	frame = ptpSession.GetLiveData()
	frame.liveview.save(r'd:\temp\test-bm.png')
	frame.bitmap.save(r'd:\temp\test-vp.jpg')
	print 'live data',frame

	rc = ptpSession.Upload('A/CHDK/SCRIPTS/testme.lua','''print( "hello world" )''')
	print 'upload',rc
	rc = ptpSession.Download('A/CHDK/SCRIPTS/testme.lua')
	print 'download',rc
	scriptId,rc = ptpSession.ExecuteScript('loadfile("A/CHDK/SCRIPTS/testme.lua")')
	print 'execute loadfile',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d %s'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))
	
	scriptId,rc = ptpSession.ExecuteScript('print("hello world 2")')
	print 'execute',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status %d %s'%(rc,PtpCHDK.ScriptStatusFlag.pp(rc))
		
	rc = ptpSession.ReadScriptMessage(scriptId=scriptId)
	print 'read message',rc

except PtpException, e:
	print "PTP Exception: %s" % PtpValues.ResponseNameById(e.responsecode, vendorId)
	raise
