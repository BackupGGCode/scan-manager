Name "ScanManager"
OutFile "scanmanager-setup-windows-x86.exe"
InstallDir "$PROGRAMFILES\ScanManager"
InstallDirRegKey HKLM "Software\ScanManager" "Install_Dir"
RequestExecutionLevel admin

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "ScanManager (required)"

	SectionIn RO

	; Set output path to the installation directory.
	SetOutPath $INSTDIR

	File "API-MS-Win-Core-LocalRegistry-L1-1-0.dll"
	File "API-MS-Win-Core-ProcessThreads-L1-1-0.dll"
	File "API-MS-Win-Security-Base-L1-1-0.dll"
	File "bz2.pyd"
	File "library.zip"
	File "MPR.dll"
	File "POWRPROF.dll"
	File "pyexpat.pyd"
	File "pyside-python2.7.dll"
	File "PySide.QtCore.pyd"
	File "PySide.QtGui.pyd"
	File "PySide.QtNetwork.pyd"
	File "python27.dll"
	File "pythoncom27.dll"
	File "pywintypes27.dll"
	File "QtCore4.dll"
	File "QtGui4.dll"
	File "QtNetwork4.dll"
	File "scanmanager.exe"
	File "select.pyd"
	File "shiboken-python2.7.dll"
	File "unicodedata.pyd"
	File "w9xpopen.exe"
	File "win32api.pyd"
	File "win32pipe.pyd"
	File "win32trace.pyd"
	File "win32ui.pyd"
	File "win32wnet.pyd"
	File "_bsddb.pyd"
	File "_ctypes.pyd"
	File "_hashlib.pyd"
	File "_socket.pyd"
	File "_ssl.pyd"
	File "_win32sysloader.pyd"
	CreateDirectory "$INSTDIR\backend"
	CreateDirectory "$INSTDIR\backend\canonpsrec"
	File "/oname=backend\canonpsrec\PRLIB.dll" "backend\canonpsrec\PRLIB.dll" 
	File "/oname=backend\canonpsrec\PRSDK.dll" "backend\canonpsrec\PRSDK.dll" 
	CreateDirectory "$INSTDIR\backend\nikonsdk"
	File "/oname=backend\nikonsdk\NkdPTP.dll" "backend\nikonsdk\NkdPTP.dll" 
	File "/oname=backend\nikonsdk\NkdPTPDi.dll"	"backend\nikonsdk\NkdPTPDi.dll" 
	File "/oname=backend\nikonsdk\D80_Mod.md3" "backend\nikonsdk\D80_Mod.md3" 
	CreateDirectory "$INSTDIR\imageformats"
	File "/oname=imageformats\qgif4.dll" "imageformats\qgif4.dll" 
	File "/oname=imageformats\qico4.dll" "imageformats\qico4.dll" 
	File "/oname=imageformats\qjpeg4.dll" "imageformats\qjpeg4.dll" 
	File "/oname=imageformats\qmng4.dll" "imageformats\qmng4.dll" 
	File "/oname=imageformats\qsvg4.dll" "imageformats\qsvg4.dll" 
	File "/oname=imageformats\qtiff4.dll" "imageformats\qtiff4.dll" 
	
	CreateDirectory "$SMPROGRAMS\ScanManager"
	CreateShortCut "$SMPROGRAMS\ScanManager\ScanManager.lnk" "$INSTDIR\scanmanager.exe" "" "$INSTDIR\scanmanager.exe" 0
	CreateShortCut "$SMPROGRAMS\ScanManager\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

	; Create an uninstaller
	WriteUninstaller "uninstall.exe"

	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ScanManager" "DisplayName" "ScanManager Camera Control"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ScanManager" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""	
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ScanManager" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	
SectionEnd


Section "Uninstall"
  
	Delete "$SMPROGRAMS\ScanManager\ScanManager.lnk"
	Delete "$SMPROGRAMS\ScanManager\Uninstall.lnk"
	RMDir "$SMPROGRAMS\ScanManager"

	; Remove installed files
	Delete "$INSTDIR\API-MS-Win-Core-LocalRegistry-L1-1-0.dll"
	Delete "$INSTDIR\API-MS-Win-Core-ProcessThreads-L1-1-0.dll"
	Delete "$INSTDIR\API-MS-Win-Security-Base-L1-1-0.dll"
	Delete "$INSTDIR\bz2.pyd"
	Delete "$INSTDIR\library.zip"
	Delete "$INSTDIR\MPR.dll"
	Delete "$INSTDIR\POWRPROF.dll"
	Delete "$INSTDIR\pyexpat.pyd"
	Delete "$INSTDIR\pyside-python2.7.dll"
	Delete "$INSTDIR\PySide.QtCore.pyd"
	Delete "$INSTDIR\PySide.QtGui.pyd"
	Delete "$INSTDIR\PySide.QtNetwork.pyd"
	Delete "$INSTDIR\python27.dll"
	Delete "$INSTDIR\pythoncom27.dll"
	Delete "$INSTDIR\pywintypes27.dll"
	Delete "$INSTDIR\QtCore4.dll"
	Delete "$INSTDIR\QtGui4.dll"
	Delete "$INSTDIR\QtNetwork4.dll"
	Delete "$INSTDIR\scanmanager.exe"
	Delete "$INSTDIR\scanmanager.settings"
	Delete "$INSTDIR\select.pyd"
	Delete "$INSTDIR\shiboken-python2.7.dll"
	Delete "$INSTDIR\unicodedata.pyd"
	Delete "$INSTDIR\w9xpopen.exe"
	Delete "$INSTDIR\win32api.pyd"
	Delete "$INSTDIR\win32pipe.pyd"
	Delete "$INSTDIR\win32trace.pyd"
	Delete "$INSTDIR\win32ui.pyd"
	Delete "$INSTDIR\win32wnet.pyd"
	Delete "$INSTDIR\_bsddb.pyd"
	Delete "$INSTDIR\_ctypes.pyd"
	Delete "$INSTDIR\_hashlib.pyd"
	Delete "$INSTDIR\_socket.pyd"
	Delete "$INSTDIR\_ssl.pyd"
	Delete "$INSTDIR\_win32sysloader.pyd"
	Delete "$INSTDIR\backend\canonpsrec\PRLIB.dll"
	Delete "$INSTDIR\backend\canonpsrec\PRSDK.dll"
	Delete "$INSTDIR\backend\nikonsdk\NkdPTP.dll"
	Delete "$INSTDIR\backend\nikonsdk\NkdPTPDi.dll"
	Delete "$INSTDIR\backend\nikonsdk\D80_Mod.md3"
	Delete "$INSTDIR\imageformats\qgif4.dll"
	Delete "$INSTDIR\imageformats\qico4.dll"
	Delete "$INSTDIR\imageformats\qjpeg4.dll"
	Delete "$INSTDIR\imageformats\qmng4.dll"
	Delete "$INSTDIR\imageformats\qsvg4.dll"
	Delete "$INSTDIR\imageformats\qtiff4.dll"
	
	; Remove settings
	Delete "$INSTDIR\scanmanger.settings.*"
	
	; Remove uninstaller
	Delete $INSTDIR\uninstall.exe

	; Remove directories used
	RMDir "$INSTDIR\backend\canonpsrec"
	RMDir "$INSTDIR\backend\nikonsdk"
	RMDir "$INSTDIR\backend"
	RMDir "$INSTDIR\imageformats"
	RMDir "$INSTDIR"

	; Remove registry keys
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ScanManager"
	DeleteRegKey HKLM "Software\ScanManager"
	
SectionEnd
