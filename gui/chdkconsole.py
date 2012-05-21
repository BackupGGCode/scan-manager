from .common import *
from . import cameracontrols
from . import imageviewer
from . import processing 
import log
import time

import backend.chdk.wrapper as chdkModule
from backend.chdk import chdkconstants

class CHDKConsole(BaseWidget,QtGui.QWidget):
	
	def __init__(self,camera=None,*args,**kargs):
		self.camera = camera
		super(CHDKConsole,self).__init__(*args,**kargs)

	class Layout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self.setContentsMargins(0,0,0,0)
			self._up.setLayout(self)

	class LogLabel(BaseWidget,QtGui.QLabel):
		def init(self):
			self.setText('<h3 align="center">%s</h3><h4 align="center">Event log</h4>'%(self.aq.camera.getName()))
			self.setWordWrap(True)
			self._up.Layout.addWidget(self)

	class Log(BaseWidget,QtGui.QTextEdit):
		def init(self):
			self.setMinimumHeight(100)
			self.setReadOnly(True)
			self.setFont(QtGui.QFont('Courier New'))
			self.setWordWrapMode(QtGui.QTextOption.NoWrap)
			self.setTabStopWidth(40)
			self.append('[INITIALISED]')
			self._up.Layout.addWidget(self,1)
			
		def messageHandler(self,msg):
			if msg.type == chdkconstants.ScriptMessageType.RET:
				return
			typeName = chdkconstants.ScriptMessageType[msg.type]
			self.append('<span style="color: blue;"><b>[MESSAGE]</b> type=%s value=%r</span><br/>'%(typeName,msg.value))

		def logError(self,v):
			self.append('<span style="color: red;"><b>[ERROR]</b> %r</span><br/>'%v)
			
		def logLine(self,v):
			self.append('%s<br/>'%v)
			

	class ScriptLabel(BaseWidget,QtGui.QLabel):
		def init(self):
			self.setText('<h4 align="center">Command or script to execute</h4>')
			self.setWordWrap(True)
			self._up.Layout.addWidget(self)

	class Script(BaseWidget,QtGui.QTextEdit):
		def init(self):
			self.setMinimumHeight(50)
			self.setFont(QtGui.QFont('Courier New'))
			self.setWordWrapMode(QtGui.QTextOption.NoWrap)
			self.setTabStopWidth(40)
			self._up.Layout.addWidget(self)

			self.executeShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+E"),self) 
			self.executeShortcut.activated.connect(self._up.ExecuteButton.onclicked)

	class ExecuteButton(BaseWidget,QtGui.QPushButton):
		def init(self):
			self._up.Layout.addWidget(self)
			self.setText(self.tr('Execute (Ctrl+E)'))
			
		def onclicked(self,*args):
			script = self._up.Script.toPlainText()
			script.replace('\r','')
			script = str(script)
			self._up.Log.logLine('[EXECUTE] Executing script')
			tStart = time.time()
			try:
				rc,messages = self.aq.camera.execute(script,expectMessages=True,messageCallback=self._up.Log.messageHandler)
			except chdkModule.CHDKError:
				t,v,tb = sys.exc_info()
				self._up.Log.logError(v)
			else:
				self._up.Log.logLine('<span style="color: green;"><b>[END]</b> Script completed in %.2fs with return value %r</span>'%(time.time()-tStart,rc))
			

