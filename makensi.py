TEMPLATE = r'''
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

%(create)s
    
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
%(delete)s
    
    ; Remove settings
    Delete "$INSTDIR\scanmanger.settings.*"
    
    ; Remove uninstaller
    Delete $INSTDIR\uninstall.exe

    ; Remove directories used
%(deleteDirs)s
    RMDir "$INSTDIR"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ScanManager"
    DeleteRegKey HKLM "Software\ScanManager"
    
SectionEnd
'''

import os
import sys
import base

basePath = os.path.join(*os.path.split(base.__file__)[:-1])

class File(object):
    def __init__(self,**kargs):
        self.__dict__.update(kargs)

class Dir(File):
    pass

create = ''
delete = ''
deleteDirs = ''
def l(path,recurse=True):
    global create,delete,deleteDirs
    files = os.listdir(path)
    files.sort(key=lambda a:(os.path.isdir(a),a))
    for fn in files:
        full = os.path.join(path,fn)
        part = os.path.relpath(full,'dist')
        isdir = os.path.isdir(full)
        f = File(path=full,isdir=isdir)
        if isdir:
            create += '    CreateDirectory "%s"\n'%os.path.join('$INSTDIR',part)
            deleteDirs += '    RMDir "%s"\n'%os.path.join('$INSTDIR',part)
        elif base:
            create += '    File "/oname=%s" "%s"\n'%(part,full)
        else:
            create += '    File "%s"\n'%(part)
            
        if f.isdir and recurse:
            l(f.path)

l('dist')
f = open('scanmanager.nsi','wt')
f.write(TEMPLATE%globals())
f.close()