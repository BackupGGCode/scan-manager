from .common import *		


class Crop(PipelineStage):
	
	def __init__(self,*args,**kargs):
		super(Crop,self).__init__(*args,**kargs)
		self.coords = (0,0,0,0)

	
	def getName(self):
		return 'Crop'

	
	def getId(self):
		return 'crop'

	
	def process(self,pixmap):
		c = self.coords
		if c == (0,0,0,0):
			return pixmap
		qi = pixmap.toImage()
		size = qi.size()
		qi = qi.copy(c[0],c[1],max(size.width()-c[2],c[0]+1),max(size.height()-c[3],c[1]+1))
		return QtGui.QPixmap.fromImage(qi)

	
	@classmethod
	def getGUI(cls):
		return CropGUI



class CropGUI(BaseWidget,QtGui.QGroupBox):
	
	@property
	def selectedStage(self):
		### TODO: fetch the pipeline object associated with the currently selected image (for this camera) then fetch the right stage
		pass
	
	def init(self):
		self._up.Layout.addRow(self)

	class Layout(BaseLayout,QtGui.QFormLayout):
		def init(self):
			self._up.setLayout(self)


	class CropCheckbox(BaseWidget,QtGui.QCheckBox): 
		def init(self):
			self._up.Layout.addRow(self)
			self.setText(self.tr('Crop images'))
			self.setChecked(self.app.settings.crop.get('enabled',False))
			
		def onstateChanged(self):
			if self.isChecked():
				self._up.CropSpinners.update()
				self.app.settings.crop.enabled = True
			else:
				self.app.settings.crop.enabled = False
		
		
	class CropSpinners(BaseWidget,QtGui.QWidget):
		def init(self):
			self._up.Layout.addRow(self)
			c = self._up.selectedStage.coords
			self.Left.setValue(c[0])
			self.Top.setValue(c[1])
			self.Right.setValue(c[2])
			self.Bottom.setValue(c[3])
			
		def update(self):
			self._up.selectedStage.coords = (self.Left.value(),self.Top.value(),self.Right.value(),self.Bottom.value())
		
		class Layout(BaseLayout,QtGui.QGridLayout):
			def init(self):
				self.setContentsMargins(0,0,0,0)
				self._up.setLayout(self)
			
		class Top(BaseWidget,QtGui.QSpinBox):
			def init(self):
				self.setAccelerated(True)
				self.setMinimum(0)
				self.setMaximum(99999)
				self.localInit()
			def onvalueChanged(self):
				self._up.update()
			def localInit(self):
				self._up.Layout.addWidget(self,0,1)
				
		class Left(Top):
			def localInit(self):
				self._up.Layout.addWidget(self,1,0)
				
		class Right(Top):
			def localInit(self):
				self._up.Layout.addWidget(self,1,2)
				
		class Bottom(Top):
			def localInit(self):
				self._up.Layout.addWidget(self,2,1)
