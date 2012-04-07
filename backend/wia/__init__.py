import platform

class Info(object):
    @classmethod
    def getName(cls):
        return 'Windows Image Acquisition (WIA) - Windows only'
    
    @classmethod
    def isAvailable(cls):
        return platform.system().lower() == 'windows'
    