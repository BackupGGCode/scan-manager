import platform

class Info(object):
    @classmethod
    def getName(cls):
        return 'Dummy (simply scans a directory for new files)'
    
    @classmethod
    def isAvailable(cls):
        return True
    