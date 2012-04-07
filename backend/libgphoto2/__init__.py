import platform

class Info(object):
    @classmethod
    def getName(cls):
        return 'GPhoto API (libgphoto2) - Linux only'
    
    @classmethod
    def isAvailable(cls):
        return platform.system().lower() == 'linux'
    