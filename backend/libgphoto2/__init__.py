import platform

class Info(object):
    @classmethod
    def getName(cls):
        return 'GPhoto2 API (libgphoto2)'
    
    @classmethod
    def isAvailable(cls):
        return True
    