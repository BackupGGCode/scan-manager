import sys
import os
WIN32 = (sys.platform == 'win32')
CYGWIN = (sys.platform == 'cygwin')


if WIN32:
    from remote import client
    api = client.GPhotoClient()
    opened = True
    basePath = os.path.join(r'd:\projects\scanmanager','backend','libgphoto2')
    dllDir = os.path.join(basePath,'win32')
    api.open(basePath=basePath,dllDir=dllDir)
elif CYGWIN:
    sys.path.append('.')
    import api
    api = api.API()
    api.open('win32')
else:
    import api
    api = api.API()
    api.open()

import time
print 'main'
import time
from constants import *

cameras = api.getCameras()
for camera in cameras:
    
    camera.init()
    
    #captured = camera.captureImage()
    #print captured
    #print 'data: %r'%captured.getData()[:10]
    
    #preview = camera.capturePreview()
    #print 'data p: %r'%preview.getData()[:10]
    
    tStart = time.time()

    if 0:
        config = camera.getConfiguration()
        def setZoom(config,value):
            set = False
            for section in config['children']:
                for widget in section['children']:
                    if widget['name'] == 'zoom':
                        widget['value'] = value
                        widget['changed'] = True
                        set = True
            if not set:
                raise Exception('couldn\'t find zoom')
        
        print 'zooming'
        for v in [1.0]: #,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0]:
            print '  %s get config'%v
            setZoom(config,v)
            print '  %s set config'%v
            camera.setConfiguration(config)
            print '  %s set config done'%v
        config = camera.getConfiguration()
    
    elif 0:
        config = camera.getConfig()
        def setZoom(config,value):
            set = False
            for section in config.getChildren():
                for widget in section.getChildren():
                    if widget.name in ['d02a','d01e','d01d','d01f','d01c','aperture','shutterspeed','iso']:
                        print '%s %s = %r'%(widget.name,widget.label,widget.value)
                    if widget.getName() == 'zoom':
                        widget.setValue(value)
                        set = True
            if not set:
                raise Exception('couldn\'t find zoom')
        print 'zooming'
        for v in [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0]:
            setZoom(config,v)
            camera.setConfig(config)
            config = camera.getConfig()
            print '='*80
            
    camera.exit()
    print 'FINISHED '

