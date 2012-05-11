from common import Pipeline

from crop import Crop
from perspective import Perspective
from undistort import Undistort


class Pipeline(object):
    """
    A complete image processing pipeline
    
    A pickled instance of this class (which includes details on each processing stage) is saved for each image that needs post-processing
    """
    
    Stages = [Crop,Perspective,Undistort]
    
    def onStageCompleted(self,stage,pixmap):
        ### TODO: show this on the application's GUI
        pass