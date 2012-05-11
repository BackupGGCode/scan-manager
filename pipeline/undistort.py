from .common import *

class Undistort(PipelineStage):
	
	def __init__(self,calibrator):
		self.calibrator = calibrator
	
	def getName(self):
		return 'Undistort'
	
	def getId(self):
		return 'undistort'
	
	def process(self,pixmap):
		return self.calibrator.correctDistortion(pixmap)
		
	@classmethod
	def getGUI(cls):
		return None