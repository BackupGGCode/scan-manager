from pysideline import *
from PySide import QtGui
from PySide.QtCore import Qt


class ProgressDialog(BaseDialog,QtGui.QDialog):
	""" 
	A simple progress-bar dialogue window 
	"""
	
	def __init__(self,parent,text=None,stopCallback=None,minimum=1,maximum=10):
		self.minimum = minimum
		self.maximum = maximum
		self.text = text
		self.stopCallback = stopCallback
		super(ProgressDialog,self).__init__(parent)
	
	def init(self):
		self.ProgressBar.setRange(self.minimum,self.maximum)
		if not self.stopCallback:
			self.StopButton.hide()
		if self.text:
			self.Label.setText(self.text)
		self.setModal(True)
		self.setWindowTitle(self.tr('Progress'))
		#self.setWindowFlags(Qt.CustomizeWindowHint|Qt.WindowTitleHint|Qt.Dialog)

	
	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.TopToBottom,)
		def init(self):
			self._up.setLayout(self)
	
	class Label(BaseWidget,QtGui.QLabel):
		def init(self):
			self.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
			self._up.Layout.addWidget(self)
	
	class ProgressBar(BaseWidget,QtGui.QProgressBar):
		def init(self):
			self._up.Layout.addWidget(self)

	class StopButton(BaseWidget,QtGui.QPushButton):
		def init(self):
			self._up.Layout.addWidget(self)
		def onclicked(self):
			self._up.stopCallback()
	

	def setText(self,text):
		"""
		Set the text for the label over the progress bar
		"""
		self.Label.setText(text)


	def setValue(self,v):
		"""
		Set the progress bar's current value
		
		@param v: int
		"""
		self.ProgressBar.setValue(v)


	def setRange(self,minimum,maximum):
		"""
		Set the progress bar's min/max values
		"""
		self.ProgressBar.setRange(minimum,maximum)





class CrashDialog(BaseDialog,QtGui.QDialog):
	""" 
	A dialogue window for reporting unhandled exceptions to the user 
	"""
	
	def __init__(self,parent,text=None,html=None,canContinue=False,title=None):
		self.text = text
		self.html = html
		self.title = title or self.tr('Error')
		self.canContinue = canContinue
		self.clickedExit = False
		self.clickedContinue = False
		super(CrashDialog,self).__init__(parent)
	
	def init(self):
		self.setModal(True)
		self.setWindowTitle(self.title)
		if self.html:
			self.Text.setHtml(self.html)
		elif self.text:
			self.Text.setPlainText(self.text)
		if not self.canContinue:
			self.ButtonBar.ContinueButton.hide()
		self.resize(600,500)
		#self.setWindowFlags(Qt.CustomizeWindowHint|Qt.WindowTitleHint|Qt.Dialog)

	
	class Layout(BaseLayout,QtGui.QBoxLayout):
		args=(QtGui.QBoxLayout.TopToBottom,)
		def init(self):
			self._up.setLayout(self)
	
	class Text(BaseWidget,QtGui.QTextEdit):
		def init(self):
			self._up.Layout.addWidget(self)
			self.setReadOnly(True)
	
	class ButtonBar(BaseWidget,QtGui.QWidget):
		def init(self):
			self._up.Layout.addWidget(self)
			
		class Layout(BaseLayout,QtGui.QBoxLayout):
			args=(QtGui.QBoxLayout.LeftToRight,)
			def init(self):
				self._up.setLayout(self)
	
		class ExitButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self.setText('Exit')
				self._up.Layout.addWidget(self)
			def onclicked(self):
				self._up._up.clickedExit = True
				self._up._up.close()
		
		class ContinueButton(BaseWidget,QtGui.QPushButton):
			def init(self):
				self.setText('Continue')
				self._up.Layout.addWidget(self)
			def onclicked(self):
				self._up._up.clickedContinue = True
				self._up._up.close()

	def onfinished(self):
		if not self.clickedContinue:
			self.app.quit()
		