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
		
		Property(name='icon',type=QtGui.QIcon)
	)

	def markError(self,error):
		tabIndex = self._qt.parent().parent().indexOf(self._qt)
		self._qt.parent().parent().setTabIcon(tabIndex,QtGui.QIcon(':/error-16.png'))

	
	def clearError(self):
		tabIndex = self._qt.parent().parent().indexOf(self._qt)
		self._qt.parent().parent().setTabIcon(tabIndex,QtGui.QIcon())

class Tab(Factory):
	klass = _Tab



