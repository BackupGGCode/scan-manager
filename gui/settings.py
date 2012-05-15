from .common import *

from .dialogs import ProgressDialog
import backend

from pysideline.forms import *

import base
import log
import copy



class FormData(BaseSettings):
	pass



class SettingsData(BaseSettings):
	pass



def apiFromName(apiName):
	api = [i for i in backend.apis if i.getName() == apiName]
	if not api: 
		return None
	return api[0]


def cameraFromName(api,cameraName):
	if api is None:
		return None
	try:
		camera = [i for i in api.getCameras() if i.getName() == cameraName]
	except:
		return None
	if not camera: 
		return None
	return camera[0]


def apiOptions(form):
	out = [('not selected',None)]
	if backend.apis:
		out += [(api.getName(),api.getName()) for api in backend.apis]
	return out


def cameraOptions(apiField):
	if apiField.getValue():
		return [('not selected',None)]+[(camera.getName(),camera.getName()) for camera in apiFromName(apiField.getValue()).getCameras()]
	else:
		return [('chose an API first',None)]


def CameraBox(title,suffix,**kargs):
	return GroupBox(name='cameraBox%s'%suffix,groupData=False,title=title,contents=[
		ComboBox(name='api%s'%suffix,label='Choose API:',options=apiOptions,required=True),
		ComboBox(name='camera%s'%suffix,label='Choose Camera:',options=lambda f:cameraOptions(getattr(f,'api%s'%suffix)),depends=['options=api%s'%suffix],required=True),
	],**kargs)


SettingsForm = TabbedForm(name='main',documentMode=True,contents=[
	Tab(name='tab1',label='Cameras',contents=[
		ComboBox(name='mode',label='Operating mode:',options=[
			('V: a camera for each side of the book',Mode.V),
			('Flat: a single camera capturing two pages at a time)',Mode.Flat),
			#('Alternate: a single camera capturing pages that need to be interpolated',Mode.Alternate),
		]),
		CameraBox('Left','L',hidden=lambda f:f.mode.getValue() != Mode.V,depends='hidden=mode'),
		CameraBox('Right','R',hidden=lambda f:f.mode.getValue() != Mode.V,depends='hidden=mode'),
		CameraBox('Centre','C',hidden=lambda f:f.mode.getValue() == Mode.V,depends='hidden=mode'),
		File(name='outputDirectory',label='Output directory:',mode=FileMode.ExistingDirectory,required=True),
		GridLayout(name='thumbnailSize',label='Thumbnail size:',groupData=True,contents=[
			LineEdit(name='width',row=0,col=0,type=int,required=True),
			LineEdit(name='height',row=0,col=1,type=int,required=True),
		]),
	]),
	#Tab(name='tab2',label='Camera Controls',contents=[
	#	TableView(name='cameraControls',tableActions=TableAction.All,formPosition=FormPosition.Bottom,
	#		editForm=Form(name='cameraControlsForm',contentsMargins=QtCore.QMargins(0,11,0,11),contents=[
	#			ComboBox(name='control',label='Control:',options=[]),
	#			LineEdit(name='tab',label='Tab:',type=str),
	#		]),
	#		columns=[
	#			Column(name='control',label='Control',resizeMode=QtGui.QHeaderView.Stretch),
	#			Column(name='tab',label='Tab',resizeMode=QtGui.QHeaderView.Stretch),
	#		],
	#	),
	#]),
	#Tab(name='tab3',label='Save and Restore',contents=[
	#]),
])


class SetupWindow(BaseWidget,QtGui.QWidget):
	
	def initialiseOptions(self):
		self.form.apiL.recalculate()
		self.form.apiR.recalculate()
		self.form.apiC.recalculate()
		self.loadSettings()

		
	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self.setContentsMargins(0,0,0,0)
			self._up.setLayout(self)
			
	def init(self):
		self.hide()
		self.setWindowTitle(self.tr('ScanManager %s - settings')%smGetVersion())

		self.form = SettingsForm(None)
		self.Form = self.form.create(self)
		self.Layout.addWidget(self.Form)
		self.Layout.addWidget(self.Buttons)
		#self.Form.setTabEnabled(1,False)
		#self.Form.setTabEnabled(2,False)
	
						
	class Buttons(BaseWidget,QtGui.QFrame):

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
				error,data = self._up._up.form.getValueAndError()
				if error:
					out = ''
					for k,v in data._errors.items():
						field = getattr(self._up._up.form,k)
						if v is True:
							out += '%s is invalid\n'%(field.label)
						else:
							out += '%s %s\n'%(field.label or field.name,v)
					QtGui.QMessageBox.critical(self,'Errors',out)
					return
				
				#self._up._up.Form.setTabEnabled(1,True)
				#self._up._up.Form.setCurrentIndex(1)
				
				print data._pp()
				
				progress = ProgressDialog(parent=self.app.SetupWindow,text='Connecting to cameras (may take some time for WIA)')
				progress.open()
				
				self.app.setup = SettingsData()
				self.app.setup.mode = data.mode
				if data.mode == Mode.V:
					self.app.setup.cameraL = cameraFromName(apiFromName(data.apiL),data.cameraL)
					self.app.setup.cameraR = cameraFromName(apiFromName(data.apiR),data.cameraR)
				else:
					self.app.setup.cameraC = cameraFromName(apiFromName(data.apiC),data.cameraC)
				self.app.setup.thumbnailSize = data.thumbnailSize
				self.app.setup.outputDirectory = data.outputDirectory
				self.app.SetupWindow.saveSettings(data)
				
				i = 3
				progress.setValue(i)
				for camera in self.app.cameras:
					i += 3
					progress.setValue(i)
					camera.open()
					camera.captureComplete.connect(self.app.MainWindow.captureCompleteCallback)
					camera.viewfinderFrame.connect(self.app.MainWindow.viewfinderFrameCallback)
					
				progress.close()
				
				self.app.SetupWindow.close()
				self.app.MainWindow.startShooting()
				self.app.MainWindow.show()

	#
	# Window-level methods
	#			
					
	def saveSettings(self,data):
		"""
		Save current settings in the the app's shelve db
		"""
		self.app.settings.setup = data
		
	
	def loadSettings(self):
		"""
		Load previous settings from the the app's shelve db
		"""
		if 'setup' not in self.app.settings:
			return
		self.form.setValue(self.app.settings.setup)

