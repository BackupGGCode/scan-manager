#ScanManager
ScanManager is designed to enhance the productivity of camera-based book scanning. It lets you interactively capture and download images directly from digital cameras connected via USB.

## Gettings started ##
This project is at an early stage but there is working softare including an installer for Windows users. If you want to check it out download the latest installer from the Downloads section.

Each camera is different and it may not work or work right for your particular model. The code is designed to make it relatively easy to hack about with the way the camera is controlled so a better way to get started with this might be to check out the latest source code and run the application from source.

The binary installer should run on Windows without any special dependencies. If you want to use this with the libgphoto2 backend you'll need [libusb-win32](http://sourceforge.net/projects/libusb-win32/files/) filter drivers set up for each of your cameras.

The requrements for running from source are:

### Windows ###
  * [Python 2.7](http://www.python.org)
  * [PythonWin (requried for the Windows Image Acquisition backend)](http://sourceforge.net/projects/pywin32/)
  * [PySide](http://www.pyside.org/downloads/) (Qt4 library for Python)
  * For auto calibration you'll also want NumPy and OpenCV 2.3 for Python.

### Linux ###
  * [Python 2.7](http://www.python.org)
  * [PySide](http://www.pyside.org/downloads/) (Qt4 library for Python)
  * A recent version of libgphoto2
  * NumPy and OpenCV 2.3 for Python for auto calibration.

## Camera Support ##

A key feature of this app is its pluggable camera SDK support. At the moment it supports four basic Camera SDKs:
downloading of manually captured images on others
  * libgphoto2 (Linux and Windows; may work with the Mac port)
    * libgphoto2 supports an exteremly wide range of cameras but not all features are supported on all cameras -- please test and report success of failure
  * Canon's PS-ReC SDK for older PowerShot Cameras (Windows only) (this is the best tested)
    * Full support including viewfinder view if the camera supports it
    * PowerShot A620, PowerShot S80, PowerShot S3 IS, PowerShot G7, PowerShot A640, PowerShot S5 IS, PowerShot G9, PowerShot SX100 IS, PowerShot G10, PowerShot SX110 IS
  * Nikon's ED-SDK for Nikon DSLRs (Windows only)
    * Supports remote capture and camera control; live view is work in progress.
    * D3, D3S, D3X, D40, D60, D80, D90, D200, D300, D300S, D700, D5000, D5100, D7000
  * Windows Image Acquisition (WIA) (Windows only)
    * Windows only and supports basic image download as well as simple remote capture on some cameras
