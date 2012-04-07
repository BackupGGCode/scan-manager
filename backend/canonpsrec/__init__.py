import platform

class Info(object):
    @classmethod
    def getName(cls):
        return 'Canon PS-ReC (older PowerShot models) - Windows only'
    
    @classmethod
    def isAvailable(cls):
        return platform.system().lower() == 'windows'
    