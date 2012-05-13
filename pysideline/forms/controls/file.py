from .common import *
import os

class DirectoryField(BaseWidget,QtGui.QWidget):
	"""
	Input field + 'Browse...' button pair for selecting existing files/directories
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
			field = self._up._field
			mode = field.mode
			kargs = dict(parent=self,caption=field.caption or None,dir=field.directory or None,options=field.browserOptions or 0)
			if mode == FileMode.ExistingDirectory:
				out = QtGui.QFileDialog.getExistingDirectory(**kargs)
			elif mode == FileMode.OpenFileName:
				out,filter = QtGui.QFileDialog.getOpenFileName(**kargs)
			elif mode == FileMode.OpenFileNames:
				out,filter = QtGui.QFileDialog.getOpenFileNames(**kargs)
			elif mode == FileMode.SaveFileName:
				out,filter = QtGui.QFileDialog.getSaveFileName(**kargs)
			if out:
				self._up.Field.setText(out)



class FileMode(object):
	ExistingDirectory = 1
	OpenFileName = 2
	OpenFileNames = 3
	SaveFileName = 4

class _File(BaseWidgetField):

	QtClass = DirectoryField
	
	Properties = Properties(
		Properties.core,
		Properties.widget,
		Properties.valueField,

		Property(name='caption',type=unicode),
		Property(name='directory',type=unicode),
		Property(name='filter',type=unicode),
		Property(name='selectedFilter',type=unicode),
		Property(name='browserOptions',type=int,flags=[
			QtGui.QFileDialog.ShowDirsOnly,QtGui.QFileDialog.DontResolveSymlinks,QtGui.QFileDialog.DontConfirmOverwrite,QtGui.QFileDialog.DontUseNativeDialog,
			QtGui.QFileDialog.ReadOnly,QtGui.QFileDialog.HideNameFilterDetails,QtGui.QFileDialog.DontUseSheet
		]),
		Property(name='mode',options=[FileMode.ExistingDirectory,FileMode.OpenFileName,FileMode.OpenFileNames,FileMode.SaveFileName],default=FileMode.OpenFileName),
	)
	
	def getRawValue(self):
		return self._qt.Field.text()

	def setRawValue(self,v):
		return self._qt.Field.setText(v)
	
	def defaultValidator(self,v):
		if not v:
			return None
		elif self.mode == FileMode.ExistingDirectory:
			if not os.path.isdir(v):
				return 'Must refer to an existing directory'
		elif self.mode == FileMode.OpenFileName:
			if not os.path.isfile(v):
				return 'Must refer to an existing file'
		elif self.mode == FileMode.SaveFileName:
			if not os.path.exists(os.path.split(v)[0]):
				return 'Must be a valid filename in an existing directory'
		return None
	
class File(Factory):
	klass = _File

		

