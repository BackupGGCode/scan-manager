from .common import *

from .dialogs import ProgressDialog

import backend
import backend.interface
import backend.chdk.wrapper

from pysideline.forms import *
from pysideline.treemodel import TreeModel,TreeItem

import cPickle

import base
import log
import copy


def optCameraControls(f):
	return [('Select a control',None)]+[('%s->%s'%(p.getSection(),p.getName()),p.getIdent()) for p in f.parent.form.camera.getProperties()]

CameraSettings = Form(name='cameraSettings',contents=[
	Label(name='l1',wordWrap=True,text=lambda f:'<center><h2>%s</h2></center>'%f.camera.getName()),
	CheckBox(name='startViewfinder',label='Start viewfinder on startup'),
	Label(name='l2',wordWrap=True,text='''
	<hr/>
	<h4>Camera properties to show on screen</h4>
	<p align="justified">
		This setting determines which of the camera controls are visible and allows you to organise them under
		your own tabs. If this table is empty then all available controls are shown organised under standard
		tabs.
	</p>
	'''),
	TableView(name='cameraControls',tableActions=TableAction.All,formPosition=FormPosition.Bottom,
		editForm=Form(name='cameraControlsForm',contentsMargins=QtCore.QMargins(0,11,0,11),contents=[
			ComboBox(name='ident',label='Control:',options=optCameraControls),
			LineEdit(name='section',label='Tab:',type=str),
		]),
		columns=[
			Column(name='ident',label='Control',resizeMode=QtGui.QHeaderView.Stretch),
			Column(name='section',label='Tab',resizeMode=QtGui.QHeaderView.Stretch),
		],
	),
	Label(name='l3',wordWrap=True,text='''
	<hr/>
	<h4>Camera properties to save/restore</h4>
	<p align="justified">
		This setting determines which properties are saved and loaded and in what order.
		Note that <b>the order is important</b> for some backends: for example, if you set the camera's exposure
		before setting the shooting mode to manual, the exposure setting will be ignored by most cameras.
	</p>
	'''),
	TableView(name='savedProperties',tableActions=TableAction.All,formPosition=FormPosition.Bottom,
		editForm=Form(name='cameraControlsForm',contentsMargins=QtCore.QMargins(0,11,0,11),contents=[
			ComboBox(name='control',label='Control:',options=optCameraControls),
		]),
		columns=[
			Column(name='control',label='Control',resizeMode=QtGui.QHeaderView.Stretch),
		],
	),
])


def Script(name,label,fixedHelp='',luaHelp='',hideFixed=False,**kargs):
	opts = [
		('LUA (execute a LUA script)','lua'),
		('Fixed value','fixed'),
	]	
	if hideFixed:
		del(opts[-1])
	
	return Tab(name=name,label=label,contents=[
		ComboBox(name='%sScriptType'%name,label='Script type:',options=opts),
		Label(name='%sLuaHelp'%name,wordWrap=True,text='<p>%s</p>'%luaHelp,
				hidden=lambda f:getattr(f,'%sScriptType'%name).getValue() != 'lua',depends='%sScriptType'%name),
		TextEdit(name='%sScript'%name,label='Script:',type=str,font=QtGui.QFont('Courier New'),wordWrapMode=QtGui.QTextOption.NoWrap,tabStopWidth=40,
				hidden=lambda f:getattr(f,'%sScriptType'%name).getValue() != 'lua',depends='%sScriptType'%name),
		TextEdit(name='%sFixedValue'%name,label='Fixed value:',type=str,font=QtGui.QFont('Courier New'),wordWrapMode=QtGui.QTextOption.NoWrap,tabStopWidth=40,
				hidden=lambda f:getattr(f,'%sScriptType'%name).getValue() != 'fixed',depends='%sScriptType'%name),
	],**kargs)

CT = backend.interface.ControlType

CHDKSettings = TabbedForm(name='chdkSettings',documentMode=True,contents=[
	Tab(name='t2',label='Basic Settings',contents=[
		ComboBox(name='downloadMode',label='Image download mode:',options=[
			('Download in the background','background'),
			('Download later (do not download images)  (RECOMMENDED)','later'),
		]),
		Label(name='t2_l1',wordWrap=True,text='''
			<hr/>
			<p>This script is used in the background to look for new files. It should include the string <i>##LASTTIME##</i> which will
			be replaced with the integer value of the last time the script was run and found some files to download. 
			It must return a LUA table of the form 
			<pre>{0='A/DCIM/file1',1='A/DCIM/file2',started=START_TIME}</pre> 
			where START_TIME is the	time the search for new files was started.</p>
		'''),
		TextEdit(name='listNewFilesScript',type=str,
				font=QtGui.QFont('Courier New'),wordWrapMode=QtGui.QTextOption.NoWrap,tabStopWidth=40,
		),
	]),
	ScrollTab(name='t1',label='Camera Controls',contents=[
		Label(name='t1_l1',wordWrap=True,text='''
			<p>You must create one control with the name "capture" which returns a value of 
			<i>downloaded:...</i> where ... is the path on the camera of the newly captured file.</p>
		'''),
		TableView(name='chdkControls',tableActions=TableAction.All,formPosition=FormPosition.Bottom,
			editForm=TabbedForm(name='chdkControlsForm',documentMode=True,contents=[
				Tab(name='t1_1',label='Basic settings',contents=[
					LineEdit(name='name',label='Name (short name):',type=str),
					LineEdit(name='label',label='Label (full name):',type=str),
					LineEdit(name='tab',label='Tab:',type=str),
					ComboBox(name='controlType',label='Control type:',options=[
						('Button',CT.Button),
						('Checkbox',CT.Checkbox),
						('Combo box',CT.Combo),
						('Line edit',CT.LineEdit),
						('Slider',CT.Slider),
						('Static (non-editable)',CT.Static),
						('Enable/disable buttons',CT.TwinButton),
					]),
				]),
				Script(name='readOnly',label='Read only',
					luaHelp='The LUA script or message should return a bool to indicate whether this control should be set to read only.',
					depends='controlType',enabled=lambda f:f.controlType.getValue() not in [CT.Static],
					hideFixed=True,
				),
				Script(name='options',label='Options',
					depends='controlType',enabled=lambda f:f.controlType.getValue() in [CT.Combo],
					luaHelp='The LUA script should return an array table of strings',
					fixedHelp='Enter all possible options for this combo, one option per line.',
				),
				Script(name='range',label='Range',
					depends='controlType',enabled=lambda f:f.controlType.getValue() in [CT.Slider],
					luaHelp='The LUA script should return a table of the form {min=,max=,step=}',
					fixedHelp='Enter three integer values separated by commas: <min>,<max>,<step>.',
				),
				Script(name='getValue',label='Get value',
					depends='controlType',enabled=lambda f:f.controlType.getValue() not in [CT.Button],
					luaHelp='The LUA script should return the current value for the field.',
					hideFixed=True,
				),
				Script(name='setValue',label='Set value',
					depends='controlType',enabled=lambda f:f.controlType.getValue() not in [CT.Button,CT.Static],
					luaHelp='The LUA script should contain the string ##VALUE##. This will be replaced by the (unquoted) value to be set.',
					hideFixed=True,
				),
				Script(name='execute',label='Execute',
					depends='controlType',enabled=lambda f:f.controlType.getValue() in [CT.Button],
					luaHelp='The LUA script should immediately execute the action for this button.',
					hideFixed=True,
				),
			]),
			columns=[
				Column(name='name',label='Name',resizeMode=QtGui.QHeaderView.Stretch),
				Column(name='tab',label='Tab',resizeMode=QtGui.QHeaderView.Stretch),
			],
		),
	]),
])


class ConfigurationDialog(BaseDialog,QtGui.QDialog):
	
	def init(self):
		self.setWindowTitle(self.tr('ScanManager %s - configuration')%smGetVersion())
		self.setModal(True)
		self.resize(1000,740)
		
		self.initialDataByForm = {}
		
		for form in self.cameraForms:
			if form.camera.settings.get('config',None):
				form.setValue(form.camera.settings.config)
			self.initialDataByForm[form.name] = form.getValue()
				
		if self.chdkAPI and self.chdkAPI.settings.get('config',None):
			self.chdkForm.setValue(self.chdkAPI.settings.config)
		self.initialDataByForm[self.chdkForm.name] = self.chdkForm.getValue()
		
	@property
	def chdkAPI(self):
		api = [i for i in backend.apis if isinstance(i,backend.chdk.wrapper.API)]
		if api:
			return api[0]
		else:
			return None

	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self.setContentsMargins(0,0,0,0)
			self._up.setLayout(self)
			
	class TreeAndForm(BaseWidget,QtGui.QSplitter):
		def init(self):
			self.addWidget(self.Tree)
			self.addWidget(self.FormWidget)
			self.setSizes([200,600])
			self._up.Layout.addWidget(self,1)
				
		class Tree(BaseWidget,QtGui.QTreeView):
			def init(self):
				
				dialog = self._up._up
				dialog.cameraForms = []
				
				model = TreeModel([])
				
				root = TreeItem([''])
				cameras = TreeItem(['Per-camera configuration'],root)
				root.childItems.append(cameras)
				for camera in self.app.cameras:
					item = TreeItem([camera.getName()],cameras)
					item.form = CameraSettings(None)
					item.form.camera = camera
					item.Form = item.form.create(self._up.FormWidget)
					item.Form.hide()
					dialog.cameraForms.append(item.form)
					cameras.childItems.append(item)
					
				if dialog.chdkAPI:
					item = TreeItem(['CHDK configuration'],root)
					item.form = CHDKSettings(None)
					item.Form = item.form.create(self._up.FormWidget)
					item.Form.hide()
					dialog.chdkForm = item.form
					root.childItems.append(item)
				else:
					dialog.chdkForm = None

				model.rootItem = root
				
				self.setModel(model)
	
			def currentChanged(self,current,previous):
				super(ConfigurationDialog.TreeAndForm.Tree,self).currentChanged(current,previous)
				self._up.FormWidget.currentChanged(current,previous)
				
		class FormWidget(BaseWidget,QtGui.QWidget):
			
			def init(self):
				self.Form = None
				self.form = None
			
			class Layout(BaseLayout,QtGui.QVBoxLayout):
				def init(self):
					self.setContentsMargins(0,0,0,0)
					self._up.setLayout(self)
			
			def currentChanged(self,current,previous):
				
				if self.Form:
					self.Layout.removeWidget(self.Form)
					self.Form.hide()
					self.Form = None
					self.form = None

				item = self._up.Tree.model().getItem(current)

				if item:					
					form = getattr(item,'form',None)
					self.form = form
					if form:
						self.Form = item.Form
						self.Form.show()
				
				if self.Form is None:
					self.Form = QtGui.QLabel()
					self.Form.setWordWrap(True)
					self.Form.setText('<center><p>Select a configuration item from the tree.</p></center>')

				self.Layout.addWidget(self.Form)
				
	class ButtonBar(BaseWidget,QtGui.QWidget):
		
		def init(self):
			self._up.Layout.addWidget(self)
		
		class Layout(BaseLayout,QtGui.QHBoxLayout):
			def init(self):
				#self.setContentsMargins(0,0,0,0)
				self._up.setLayout(self)
				
		class SaveButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self.tr('&Save'))
				
			def onclicked(self):
				
				dialog = self._up._up
				
				errorString,dataByForm = dialog.getDataForAll()

				if errorString:
					QtGui.QMessageBox.critical(self,'Errors',errorString)
					return
				
				dialog.initialDataByForm = dataByForm
				
				for form in dialog.cameraForms:
					form.camera.settings.config = dataByForm[form.name]
					form.camera.api.saveSettings()
			
				if dialog.chdkForm:
					dialog.chdkAPI.settings.config = dataByForm[dialog.chdkForm.name]
					dialog.chdkAPI.saveSettings()
					
								
		class CloseButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self.tr('&Close'))
				
			def onclicked(self):
				dialog = self._up._up
				dialog.close()
				

		class ExportButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self.tr('&Export settings (selected category)'))
				
			def onclicked(self):
				dialog = self._up._up
				form = dialog.TreeAndForm.FormWidget.form
				error,data = dialog.getDataForForm(form)
				if data is None:
					QtGui.QMessageBox.critical(self,'No category selected','Select a setup category from the tree before exporting')
					return
				if error:
					QtGui.QMessageBox.critical(self,'Errors in current data',error)
					return
				
				fileName,filter = QtGui.QFileDialog.getSaveFileName(self,caption='Export to...',filter='SM exports (*.pkl)')
				
				f = open(fileName,'wb')
				cPickle.dump((form.name,data),f)
				f.close()


		class ImportButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self._up.Layout.addWidget(self)
				self.setText(self.tr('&Import settings (selected category)'))
				
			def onclicked(self):
				dialog = self._up._up
				form = dialog.TreeAndForm.FormWidget.form
				if form is None:
					QtGui.QMessageBox.critical(self,'No category selected','Select a setup category from the tree before exporting')
					return
				
				fileName,filter = QtGui.QFileDialog.getOpenFileName(self,caption='Import from...',filter='SM exports (*.pkl)')
				
				f = open(fileName,'rb')
				name,data = cPickle.load(f)
				f.close()
				
				if form.name != name:
					QtGui.QMessageBox.critical(self,'Invalid','Data is not valid for the selected category (data is %s, category is %s)'%(name,form.name))
					return
				
				button = QtGui.QMessageBox.question(
					self,
					'Confirmation',
					'This will overwrite all existing data for this category. Are you sure you want to proceed?',
					buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
				)
				if button != QtGui.QMessageBox.Yes:
					return
				
				form.setValue(data)

				
	def getDataForForm(self,form):
		if form is None:
			return None,None
		if not getattr(form,'_qt',None):
			return None,None
		error,data = form.getValueAndError()
		errorString = ''
		if error:
			for k,v in data._errors.items():
				field = getattr(self._up._up.form,k)
				### TODO: add name of form/camera to error messages
				if v is True:
					errorString += '%s is invalid\n'%(field.label)
				else:
					errorString += '%s %s\n'%(field.label or field.name,v)
		return errorString,data


	def getDataForAll(self):
		dialog = self
		dataByForm = {}
		errorString = ''
		for form in dialog.cameraForms + [dialog.chdkForm]:
			error,data = dialog.getDataForForm(form)
			if error:
				errorString += error
			dataByForm[form.name] = data
		return errorString,dataByForm


	def closeEvent(self,e):
		dialog = self
		error,dataByForm = dialog.getDataForAll()
		if  dataByForm != dialog.initialDataByForm:
			button = QtGui.QMessageBox.question(
				self,
				'Confirmation',
				'Data has not been saved. Are you sure you want to exit?',
				buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
			)
			if button != QtGui.QMessageBox.Yes:
				e.ignore()
				return 
		return super(ConfigurationDialog,self).closeEvent(e)