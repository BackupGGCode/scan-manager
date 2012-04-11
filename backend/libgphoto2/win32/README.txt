This is built using libusb-win32 so you'll need to install a special driver for each USB camera 
you want to use with it (and remove the driver if you want to use it with other software). 

Download the latest binary version of libusb-win32 from here http://sourceforge.net/projects/libusb-win32/, 
unzip it somewhere, and run ./bin/inf-wizard.exe, select your camera and when you're finished click 
the "Install" button. 

You can roll back the drivers for you camera if you no longer want to use it with gphoto2 by using the 
libusb-win32 tools or using the Device Manager on Windows (see Control Panel -> System).

You also need to tell gphoto2 where its camera and port libraries are. From a Windows command prompt 
in the directory that contains gphoto2.exe do:

set CAMLIBS=camlibs
set IOLIBS=iolibs
gphoto2.exe

You can set these in Control Panel -> System -> Environment Variables if you want them set persistently.