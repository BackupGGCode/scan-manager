#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import traceback
from PtpUsbTransport import PtpUsbTransport
from PtpSession import PtpCHDKSession, PtpException
import PtpValues

ptpTransport = PtpUsbTransport(PtpUsbTransport.findptps()[0])
ptpSession = PtpCHDKSession(ptpTransport)

vendorId = PtpValues.Vendors.STANDARD

ptpSession.OpenSession()
deviceInfo = ptpSession.GetDeviceInfo()
vendorId = deviceInfo.VendorExtensionID

id = 0
try:
	version = ptpSession.GetVersion()
	print 'version',version
	rc = ptpSession.Upload('A/CHDK/SCRIPTS/testme.lua','''
print( "hello world" )
''')
	print 'upload',rc
	rc = ptpSession.Download('A/CHDK/SCRIPTS/testme.lua')
	print 'download',rc
	scriptId,rc = ptpSession.ExecuteScript('loadfile("A/CHDK/SCRIPTS/testme.lua")')
	print 'execute',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status',rc
	scriptId,rc = ptpSession.ExecuteScript('print("hello world 2")')
	print 'execute',scriptId,rc
	rc = ptpSession.GetScriptStatus(scriptId=scriptId)
	print 'get status',rc
	rc = ptpSession.ReadScriptMessage(scriptId=scriptId)
	print 'read message',rc
	
	"""
	objectid = None
	while True:
		evt = ptpSession.CheckForEvent(None)
		if evt == None:
			raise Exception("Capture did not complete")
		if evt.eventcode == PtpValues.StandardEvents.OBJECT_ADDED:
			objectid = evt.params[0]

	if objectid != None:
		file = open("capture_%i.jpg" % id, "w")
		ptpSession.GetObject(objectid, file)
		file.close()
		id+=1
		ptpSession.DeleteObject(objectid)
	"""
	
except PtpException, e:
	print "PTP Exception: %s" % PtpValues.ResponseNameById(e.responsecode, vendorId)
	raise
