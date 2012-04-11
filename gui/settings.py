from .common import *

from .dialogs import ProgressDialog
import backend


class FormData(BaseSettings):
	pass



class SettingsData(BaseSettings):
	pass



def cameraToName(camera):
	""" 
	Convert a camera object into a 2-tuple of strings that can be pickled and later used to recover that same camera (if it is still plugged in)
	
	@return: (str,str)
	""" 
	return (camera.api.getName(),camera.getName())


def cameraFromName(name):
	"""
	Convert a 2-tuple of strings returned by L{cameraToName} into a Camera object (if it is currently connected and that API is loaded)
	
	@return: {backend.interface.Camera}
	"""
	apiName,cameraName = name
	api = [i for i in backend.apis if i.getName() == apiName]
	if not api: 
		return None
	api = api[0]

	try:	
		api.open()
	except:
		return None
	
	try:
		camera = [i for i in api.getCameras() if i.getName() == cameraName]
	except:
		return None
	
	if not camera: 
		return None
	
	camera = camera[0]
	return camera



class DirectoryField(BaseWidget,QtGui.QWidget):
	"""
	Input field + 'Browse...' button combo set up for selecting existing directories
	"""
	
	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.LeftToRight,)
		def init(self):
			self._up.setLayout(self)
			self.setContentsMargins(0,0,0,0)
			self.addWidget(self._up.Field)
			self.addWidget(self._up.Button)
		

	
	class Field(BaseWidget,QtGui.QLineEdit):
		pass


	class Button(BaseWidget,QtGui.QPushButton):
		def init(self):
			self.setText(self.tr('Browse...'))
			
		def onclicked(self):
			out = QtGui.QFileDialog.getExistingDirectory(self,self.tr('Select output directory'))
			if out:
				self._up.Field.setText(out)

	
	def smGetValue(self):
		return self.Field.text()


	def smSetValue(self,v):
		return self.Field.setText(v)



class SizeField(BaseWidget,QtGui.QWidget):
	"""
	width x height size field
	"""
	
	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.LeftToRight,)
		def init(self):
			self._up.setLayout(self)
			self.setContentsMargins(0,0,0,0)
			self.addWidget(self._up.Width)
			self.addWidget(self._up.Height)
	
	class Width(BaseWidget,QtGui.QLineEdit):
		def init(self):
			self.setValidator(QtGui.QIntValidator(self))


	class Height(BaseWidget,QtGui.QLineEdit):
		def init(self):
			self.setValidator(QtGui.QIntValidator(self))

	
	def smGetValue(self):
		w = None
		try:
			w = int(self.Width.text())
		except:
			pass
		h = None
		try:
			h = int(self.Height.text())
		except:
			pass
		if w and h:
			return w,h
		else:
			return None


	def smSetValue(self,v):
		self.Width.setText(str(v[0]))
		self.Height.setText(str(v[1]))



class CameraGroup(BaseWidget,QtGui.QGroupBox):
	"""
	A widget for choosing an API then a camera accessed via that API
	"""
	
	def initialiseOptions(self):
		self.API.initialiseOptions()
	
	class Layout(BaseLayout,QtGui.QFormLayout):
		def init(self):
			self._up.setLayout(self)


	class API(BaseWidget,QtGui.QComboBox):
		def init(self):
			self._up.Layout.addRow(self.tr('Choose API:'),self)
			
		def initialiseOptions(self):
			self.addItem(self.tr('Not configured'),None)
			for api in backend.apis:
				self.addItem(api.getName(),api)
			
		def oncurrentIndexChanged(self,index):
			api = self.itemData(index)
			if api is None:
				self._up.Camera.clear()
			else:
				self._up.Camera.loadFromAPI(api)


	class Camera(BaseWidget,QtGui.QComboBox):
		def loadFromAPI(self,api):
			self.clear()
			self.addItem(self.tr('Not configured'),None)
			for camera in api.getCameras():
				self.addItem(camera.getName(),camera)

		def init(self):
			self._up.Layout.addRow(self.tr('Choose camera:'),self)


	def smGetValue(self):
		"""
		Get the current value of this field
		
		@return: a L{backend.interface.Camera} object
		"""
		return self.Camera.itemData(self.Camera.currentIndex())


	def smSetValue(self,camera):
		""" 
		Set the value of this field
		
		@param camera: a L{backend.interface.Camera} object or None to do nothing
		"""
		if camera is None:
			self.Camera.setCurrentIndex(1)
			return
			
		self.API.setCurrentIndex(self.API.findText(camera.api.getName()))
		self.Camera.setCurrentIndex(self.Camera.findText(camera.getName()))
		


class SetupWindow(BaseWidget,QtGui.QWidget):
	
	def initialiseOptions(self):
		for ob in (self.app.CameraL,self.app.CameraR,self.app.CameraC):
			ob.initialiseOptions()
	
	def init(self):
		self.Mode.setCurrentIndex(0)
		self.Mode.oncurrentIndexChanged(0)
		self.setWindowTitle(self.tr('ScanManager - settings'))
		self.show()
	
						
	class Layout(BaseLayout,QtGui.QFormLayout):
		def init(self):
			self._up.setLayout(self)
	
			
	class Mode(BaseWidget,QtGui.QComboBox):
		def init(self):
			self.addItem(self.tr('V: a camera for each side of the book'),Mode.V)
			self.addItem(self.tr('Flat: a single camera capturing two pages at a time)'),Mode.Flat)
			#self.addItem(self.tr('Alternate: a single camera capturing pages that need to be interpolated'),Mode.Alternate)
			self._up.Layout.addRow(self.tr('Operating mode:'),self)

		def oncurrentIndexChanged(self,index):
			mode = self.itemData(index)
			if mode == Mode.Flat or mode == Mode.Alternate:
				self._up.CameraL.hide()
				self._up.CameraR.hide()
				self._up.CameraC.show()
			elif mode == Mode.V:
				self._up.CameraL.show()
				self._up.CameraR.show()
				self._up.CameraC.hide()
			else:
				raise Exception('Invalid mode %r'%mode)

		def smGetValue(self):
			return self.itemData(self.currentIndex())

		def smSetValue(self,v):
			self.setCurrentIndex(self.findData(v))
		
	
		
	class CameraC(CameraGroup):
		def init(self):
			self._up.Layout.addRow(self)
			self.setTitle(self.tr('Select camera'))
			self.hide()
		
			
	class CameraL(CameraGroup):
		def init(self):
			self._up.Layout.addRow(self)
			self.setTitle(self.tr('Select left-hand camera'))
			self.hide()
		
			
	class CameraR(CameraGroup):
		def init(self):
			self._up.Layout.addRow(self)
			self.setTitle(self.tr('Select right-hand camera'))
			self.hide()
	
			
	class OutputDirectory(DirectoryField):
		def init(self):
			self._up.Layout.addRow(self.tr('Output directory:'),self)
		

	class ThumbnailSize(SizeField):
		def init(self):
			self._up.Layout.addRow(self.tr('Thumbnail size:'),self)
			self.smSetValue((130,130))


	class Buttons(BaseWidget,QtGui.QFrame):
		def init(self):
			self._up.Layout.addRow(self)

		class Layout(BaseLayout,QtGui.QBoxLayout):
			args=(QtGui.QBoxLayout.LeftToRight,)
			def init(self):
				self._up.setLayout(self)
			
		class CancelButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self.tr('Cancel'))
				
			def onclicked(self):
				self.app.SetupWindow.close()
				
				
		class ContinueButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self.tr('Continue'))
				self.setDefault(True)
				
			def onclicked(self):
				data = self.app.SetupWindow.fromForm()
				errors = self.app.SetupWindow.validate(data)
				if errors:
					message = '\n'.join(errors)
					e = QtGui.QMessageBox.critical(self.app.SetupWindow,self.tr('Error'),message)
					return
				
				progress = ProgressDialog(parent=self.app.SetupWindow,text='Connecting to cameras (may take some time for WIA)')
				progress.open()
				
				self.app.settings = data
				self.app.SetupWindow.saveSettings(data)
				
				progress.setValue(3)
				
				for camera in self.app.cameras:
					camera.open()
					camera.captureComplete.connect(self.app.MainWindow.captureCompleteCallback)
					camera.viewfinderFrame.connect(self.app.MainWindow.viewfinderFrameCallback)
	
				progress.setValue(9)
				progress.close()
				
				self.app.MainWindow.startShooting()
				self.app.MainWindow.show()
				self.app.SetupWindow.close()
			
		
	#
	# Window-level methods
	#			
					
	def fromForm(self):
		"""
		Read data from the from into a L{SettingsData} object
		
		@return: L{SettingsData} 
		"""
		data = SettingsData()
		data.mode = self.Mode.smGetValue()
		if data.mode == Mode.V:
			data.cameraL = self.CameraL.smGetValue()
			data.cameraR = self.CameraR.smGetValue()
		else:
			data.cameraC = self.CameraC.smGetValue()
		data.outputDirectory = self.OutputDirectory.smGetValue()
		data.thumbnailSize = self.ThumbnailSize.smGetValue()
		return data

	
	def toForm(self,data):
		"""
		Load data from a L{SettingsData} object into the form
		
		@param data: L{SettingsData} 
		"""
		self.Mode.smSetValue(data.mode)
		if data.mode == Mode.V:
			self.CameraL.smSetValue(data.cameraL)
			self.CameraR.smSetValue(data.cameraR)
		else:
			self.CameraC.smSetValue(data.cameraC)
		self.OutputDirectory.smSetValue(data.outputDirectory)
		self.ThumbnailSize.smSetValue(data.thumbnailSize)
		return data


	def saveSettings(self,data):
		"""
		Save current settings in the the app's shelve db
		"""
		out = SettingsData()
		out.mode = data.mode
		if data.mode == Mode.V:
			out.cameraL = cameraToName(data.cameraL)
			out.cameraR = cameraToName(data.cameraR)
		else:
			out.cameraC = cameraToName(data.cameraC)
		out.outputDirectory = data.outputDirectory
		out.thumbnailSize = data.thumbnailSize
		self.app.db['setup'] = out
		
	
	def loadSettings(self):
		"""
		Load previous settings from the the app's shelve db
		"""
		if 'setup' not in self.app.db:
			return
		data = self.app.db['setup']
		if data.mode == Mode.V:
			data.cameraL = cameraFromName(data.cameraL)
			data.cameraR = cameraFromName(data.cameraR)
		else:
			data.cameraC = cameraFromName(data.cameraC)
		self.toForm(data)

	
	def validate(self,data):
		""" 
		Validate the supplied form data (as generated by L{toForm}) and return a list of errors
		
		@return: [str,...] or [] if there were no errors
		"""
		errors = []
		if data.mode == Mode.V:
			if not data.cameraL:
				errors.append(self.tr('No left-hand camera selected'))
			if not data.cameraR:
				errors.append(self.tr('No right-hand camera selected'))
			if data.cameraL and data.cameraR and data.cameraL == data.cameraR:
				errors.append(self.tr('You must select different cameras for left and right (chose the left-right mode if you want to alternate one camera)'))
		else:
			if not data.cameraC:
				errors.append(self.tr('No camera selected'))
		if not data.outputDirectory:
			errors.append(self.tr('No output directory selected'))
		if not data.thumbnailSize:
			errors.append(self.tr('No thumbnail size selected'))
		return errors
