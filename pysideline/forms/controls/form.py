from .common import *

class _Form(base._AbstractGroup):

	QtClass = QtGui.QWidget

	Properties = Properties(
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.formLayout,
		Properties.widget,
	)

	def __init__(self,parent,**kargs):
		super(_Form,self).__init__(parent,**kargs)
		self.groupData = True

		
	@property
	def form(self):
		return self


	def showErrorPopup(self,data):
		if not data._errors:
			return False
		out = ''
		for k,v in data._errors.items():
			field = getattr(self,k)
			if v is True:
				out += '%s is invalid\n'%(field.label)
			else:
				out += '%s %s\n'%(field.label or field.name,v)
		QtGui.QMessageBox.critical(self,'Errors',out)
		return True

class Form(Factory):
	klass = _Form



class _TabbedForm(_Form):

	QtClass = QtGui.QTabWidget

	Properties = Properties(
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.widget,
		
		QtProperty(name='documentMode',type=bool),
		QtProperty(name='moveable',type=bool),
		QtProperty(name='tabsClosable',type=bool),
		QtProperty(name='usesScrollButtons',type=bool),
		QtProperty(name='elideMode',options=[
			Qt.ElideLeft,Qt.ElideMiddle,Qt.ElideNone,Qt.ElideRight
		]),
		QtProperty(name='iconSize',type=QtCore.QSize),
		QtProperty(name='tabPosition',options=[
			QtGui.QTabWidget.North,QtGui.QTabWidget.South,QtGui.QTabWidget.East,QtGui.QTabWidget.West
		]),
		QtProperty(name='tabShape',options=[
			QtGui.QTabWidget.Rounded,QtGui.QTabWidget.Triangular
		]),
	)
	
	def init(self):
		self._qt.setIconSize(QtCore.QSize(10,10))

	def layoutChildren(self):
		for field in self._children.values():
			icon = getattr(field,'labelIcon',None)
			if icon:
				self._qt.addTab(field._qt,icon,field.label)
			else:
				self._qt.addTab(field._qt,field.label)

class TabbedForm(Factory):
	klass = _TabbedForm



class _Tab(base._AbstractGroup):
	
	QtClass = QtGui.QWidget 
	
	Properties = Properties(
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.formLayout,
		Properties.widget,
		
		Property(name='icon',type=QtGui.QIcon),
		QtProperty(name='enabled',type=bool,target='_field',setter='setEnabled',getter='getEnabled'),
	)

	def markError(self,error):
		tabIndex = self._qt.parent().parent().indexOf(self._qt)
		self._qt.parent().parent().setTabIcon(tabIndex,QtGui.QIcon(':/error-16.png'))

	
	def clearError(self):
		tabIndex = self._qt.parent().parent().indexOf(self._qt)
		self._qt.parent().parent().setTabIcon(tabIndex,QtGui.QIcon())
		
	
	def getEnabled(self):
		tabw = self._qt.parent().parent()
		index = tabw.indexOf(self._qt)
		return tabw.isTabEnabled(index)


	def setEnabled(self,v):
		tabw = self._qt.parent().parent()
		index = tabw.indexOf(self._qt)
		tabw.setTabEnabled(index,v)

class Tab(Factory):
	klass = _Tab



class ScrollTabWidget(BaseWidget,QtGui.QWidget):
	
	def init(self):
		self.Layout = self.Scroll.Main.Layout
	
	class LocalLayout(BaseLayout,QtGui.QVBoxLayout):
		def init(self):
			self._up.setLayout(self)
			self.setSpacing(0)
			self.setContentsMargins(0,0,0,0)
			
	class Scroll(BaseWidget,QtGui.QScrollArea):
		def init(self):
			self._up.LocalLayout.addWidget(self,1)
			self.setWidgetResizable(True)
			self.setContentsMargins(0,0,0,0)
			
		class Main(BaseWidget,QtGui.QFrame):
			
			class Layout(BaseLayout,QtGui.QFormLayout):
				def init(self):
					self._up.setLayout(self)
		
			def init(self):
				self._up.setWidget(self)
				

class _ScrollTab(_Tab):
	
	QtClass = ScrollTabWidget

	def layoutChildren(self):
		_Tab.layoutChildren(self)
		self._qt.Scroll.Main.adjustSize()

class ScrollTab(Factory):
	klass = _ScrollTab
