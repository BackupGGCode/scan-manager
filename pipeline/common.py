from pysideline import *
from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import Qt
import log


def abstract(f):
	""" Decorator for abstract methods """
	def raiser(*args,**kargs):
		raise Exception('Abstract function must be overridden by a child class before being called')
	return raiser


class Pipeline(object):
	"""
	A complete image processing pipeline
	
	A pickled instance of this class (which includes details on each processing stage) is saved for each image that needs post-processing
	"""

	def __init__(self,source,target):
		self.stages = [i(self) for i in self.Stages]
		self.stageById = {i.getIdent():i for i in self.stages}
		self.source = source
		self.target = target
		
	def getSourceFilename(self):
		return self.source
		
	def getTargetFilename(self):
		return self.target
	
	def addStage(self,stage):
		self.stages.append(stage)
		
	def getStage(self,ident):
		return self.stageById(ident)
	
	def process(self):
		pixmap = QtGui.QPixmap.load(self.source)
		for stage in self.stages:
			pixmap = stage.process(pixmap)
			self.onStageCompleted(stage,pixmap)
		pixmap.save(self.target)
		
	def onStageCompelted(self,stage,pixmap):
		pass
		
		
		

class PipelineStage(object):
	"""
	An abstract base class for stages in an image processing pipleline
	
	The stage should be a pickleable type
	"""
	
	@abstract
	def getPriority(self):
		""" Return a priority value (higher values place items higher in the pipleline) """ 

	@abstract
	def getName(self):
		""" Return the display name of this stage (used for tabs etc.) """
	
	@abstract
	def getId(self):
		""" Return a short identifier for this stage """
	
	@abstract
	def process(self,pixmap):
		"""
		Process the image using the current settings for this stage and return a QPixmap of the processed image
		
		@return: L{PySide.QtGui.QPixmap}
		"""

	@abstract
	def getControls(self):
		"""
		Return a pysideline control class suitable for instantiating in a pysideline widget to manage this stage's settings  
		
		@return: L{pysideline.BaseWidget} or None
		"""
		
	@abstract
	def fromControls(self,widget):
		"""
		Load settings from an on-screen widget into this object 
		
		@return: None 
		"""
	
	@abstract
	def toControls(self,widget):
		"""
		Load settings from an on-screen widget into this object 
		
		@return: None 
		"""
	
	def isEnabled(self):
		"""
		Return True if this stage is currently enabled by user settings 
		"""
		