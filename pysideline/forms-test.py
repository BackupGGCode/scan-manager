import sys
import os
from pysideline import *
from base import *
from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import Qt

from pysideline.forms import Form,LineEdit,TextEdit,ComboBox,SpinBox,Slider,GroupBox

MyForm = Form(name='main',contents=[
	LineEdit(name='f1',label='Field 1 [f1]:',default='default_value'),
	LineEdit(name='f2',label='Field 2 (int) [f2]:',default=2,type=int),
	ComboBox(name='f3',label='Combo [f3]:',default=2,type=int,options=[(1,'test 1'),(2,'test 2'),(3,'test 3')]),
	ComboBox(name='f4',label='Combo [f4]:',default=2,type=str,depends=['options=f3.currentIndexChanged'],
			 options=lambda f:[('%d'%(f.f3.getValue() or 0),'test %d.%d'%((f.f3.getValue() or 0),i)) for i in [5,6,7,8,9]]
	),
	SpinBox(name='f5',label='Field 5 [f5]:',default=4,minimum=0,maximum=100,singleStep=2,prefix='v=',suffix='%'),
	Slider(name='f6',label='Field 6 [f6]:',default=4,minimum=0,maximum=100,tickInterval=10,singleStep=5,tickPosition=QtGui.QSlider.TicksBelow,orientation=Qt.Horizontal),
	GroupBox(name='g1',title='Group 1',groupData=True,contents=[
		LineEdit(name='f7',label='Field g1.1 [f7]:',default='default_value'),
		LineEdit(name='f8',label='Field g1.2 (int) [f8]:',default=2,type=int),
		GroupBox(name='g2',title='Group 1',groupData=True,checkable=True,checked=False,contents=[
			LineEdit(name='f9',label='Field g1.g2.1 [f9]:',default='default_value'),
			LineEdit(name='f10',label='Field g1.g2.2 (int) [f10]:',default=2,type=int),
		]),
	]),
])


class App(Application):
	
	class MainWindow(BaseWidget,QtGui.QMainWindow):
		def init(self):
			self.setWindowTitle(self.tr('testing'))
	
		def init(self):
			self.setCentralWidget(self.MainWidget)
			self.show()

		class MainWidget(BaseWidget,QtGui.QWidget):
			
			class Layout(BaseLayout,QtGui.QVBoxLayout):
				def init(self):
					self._up.setLayout(self)
					
			class MainWindow(BaseWidget,QtGui.QWidget):
				class Layout(BaseLayout,QtGui.QVBoxLayout):
					def init(self):
						self._up.setLayout(self)
						
				def init(self):
					self._up.Layout.addWidget(self)
					
					self.app.myForm = MyForm(None)
					self.form = self.app.myForm.create(self)
					self.Layout.addWidget(self.form)
					
			class OKButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText('OK')
				def onclicked(self):
					print self.app.myForm.getValue()._pp()
				
app = App(sys.argv)
app.exec_()


