c:\utils\sysinternals\pskill.exe python.exe
cd chdkimage
del chdkimage.pyd
d:\python27\python setup.py build
copy build\lib.win32-2.7\chdkimage.pyd .
cd ..
d:\python27\python test.py