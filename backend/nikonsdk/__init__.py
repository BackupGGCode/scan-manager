import platform

class Info(object):
    @classmethod
    def getName(cls):
        return 'Nikon ED-SDK (recent DSLRs) - Windows only'
    
    @classmethod
    def isAvailable(cls):
        return platform.system().lower() == 'windows'
    