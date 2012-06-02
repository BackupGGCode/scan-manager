from .common import *

from ... import tablemodel

import copy
import cPickle

__all__ = ['TableView','TableAction','FormPosition','Column']


class TableAction:
	Insert = 0x1
	Delete = 0x2
	Order = 0x4
	Edit = Insert|Delete
	All = Insert|Delete|Order
	NoActions = 0x0
		
		
		
class FormPosition:
	Top = 1
	Bottom = 2
	Left = 3
	Right = 4
		
		
		
class ColumnDelegate(QtGui.QItemDelegate):
	def __init__(self,column,*args,**kargs):
		self.column = column
		super(ColumnDelegate,self).__init__(*args,**kargs)
	def createEditor(self,parent,option,index):
		return self.column.editor.create(parent)
	def setEditorData(self,editor,index):
		v = index.model().data(index)
		return editor._field.setValue(v)
	def setModelData(self,editor,model,index):
		model.setData(index,editor._field.getValue())
		
		

class Column(Configurable):
	
	Properties = Properties(
		# Core properties
		Property(name='name',required=True,type=str),
		Property(name='label'),
		
		# Properties determining item flags for items in this column
		Property(name='editable',default=False),
		Property(name='selectable',default=True),
		Property(name='checkable',default=False),
		Property(name='enabled',default=True),
		Property(name='tristate',default=False),
		
		# Specialised proeprties
		DescriptorProperty(name='editor'),

		# Properties to be set on the vertical header for this column
		Property(name='resizeMode',
			options=[QtGui.QHeaderView.Interactive,QtGui.QHeaderView.Fixed,QtGui.QHeaderView.Stretch,QtGui.QHeaderView.ResizeToContents]
		),
		Property(name='hidden',type=bool),
		
	)
	
	def __init__(self,*args,**kargs):
		super(Column,self).__init__(*args,**kargs)
		if self.editor and not self.editable:
			self.editable = True

	
	def createDelegate(self,parent):
		if self.editor:
			return ColumnDelegate(self,parent)



class FormsTableModel(tablemodel.TableModel):
	# turns out we didn't need to override anything -- get rid of this? 
	pass



class TableViewWidget(BaseWidget,QtGui.QWidget):
	
	dataChanged = QtCore.Signal()

	def afterCreate(self):
		if self._field.editForm:
			subField = self._field.editForm(self._field)
			self.Form = subField.create(self)
			self.Form._field = subField
			self.Form.setDisabled(True)
			
			pos = self._field.formPosition
			if pos == FormPosition.Left: 
				self.Layout.setDirection(QtGui.QBoxLayout.LeftToRight)
				self.Layout.addWidget(self.Form)
				self.Layout.addWidget(self.TableContainer,1)
			elif pos == FormPosition.Right: 
				self.Layout.setDirection(QtGui.QBoxLayout.LeftToRight)
				self.Layout.addWidget(self.TableContainer,1)
				self.Layout.addWidget(self.Form)
			elif pos == FormPosition.Top:
				self.Layout.setDirection(QtGui.QBoxLayout.TopToBottom)
				self.Layout.addWidget(self.Form)
				self.Layout.addWidget(self.TableContainer,1)
			elif pos == FormPosition.Bottom:
				self.Layout.setDirection(QtGui.QBoxLayout.TopToBottom)
				self.Layout.addWidget(self.TableContainer,1)
				self.Layout.addWidget(self.Form)
		else:
			self.Form = None
			self.Layout.setDirection(QtGui.QBoxLayout.LeftToRight)
			self.Layout.addWidget(self.TableContainer,1)
			
		toolbar = self.TableContainer.Toolbar
		field = self._field

		toolbar.actionInsert.setVisible(field.tableActions & TableAction.Insert)
		toolbar.actionDelete.setVisible(field.tableActions & TableAction.Delete)
		toolbar.actionTop.setVisible(field.tableActions & TableAction.Order)
		toolbar.actionUp.setVisible(field.tableActions & TableAction.Order)
		toolbar.actionDown.setVisible(field.tableActions & TableAction.Order)
		toolbar.actionBottom.setVisible(field.tableActions & TableAction.Order)
		toolbar.setHidden(field.tableActions == TableAction.NoActions)

	class Layout(BaseLayout,QtGui.QBoxLayout):
		
		args = (QtGui.QBoxLayout.LeftToRight,)
		
		def init(self):
			self.setContentsMargins(0,0,0,0)
			self.setSpacing(0)
			self._up.setLayout(self)
			self._up.Table = self._up.TableContainer.Table
			
	class TableContainer(BaseWidget,QtGui.QWidget):
			
		class Layout(BaseLayout,QtGui.QVBoxLayout):
			def init(self):
				self.setContentsMargins(0,0,0,0)
				self.setSpacing(0)
				self._up.setLayout(self)
		
		class Toolbar(BaseWidget,QtGui.QToolBar):
			def init(self):
				self._up.Layout.addWidget(self)

				self.actionInsert = self.addAction(QtGui.QIcon(':/plus-16.png'),'')
				self.actionDelete = self.addAction(QtGui.QIcon(':/minus-16.png'),'')
				self.actionUp = self.addAction(QtGui.QIcon(':/up-16.png'),'')
				self.actionTop = self.addAction(QtGui.QIcon(':/top-16.png'),'')
				self.actionDown = self.addAction(QtGui.QIcon(':/down-16.png'),'')
				self.actionBottom = self.addAction(QtGui.QIcon(':/bottom-16.png'),'')
				self.setIconSize(QtCore.QSize(16,16))
					
			def onactionTriggered(self,action):
				
				if action not in (self.actionInsert,self.actionDelete,self.actionUp,self.actionTop,self.actionDown,self.actionBottom):
					return
				
				model = self._up._up._field.model
				view = self._up.Table
				index = view.currentIndex()
				
				view.saveForm(view.currentSelection)

				row = index.row()
				
				if action == self.actionInsert:
					view.currentSelection = None
					view.clearForm()
					model.insertRows(row,1)
					view.selectRow(row+1)
					view.currentSelection = model.index(row+1,0)
					
				if not index.isValid():
					return
				
				if action == self.actionDelete:
					del(model[row])
					new = view.currentIndex()
					if new and new.isValid():
						view.currentSelection = new
						view.showRow(new)
					else:
						view.currentSelection = None
						view.clearForm()
						view.disableForm()
				elif action == self.actionUp:
					if row == 0:
						return
					d = model[row-1]
					model[row-1] = model[row]
					model[row] = d
					view.currentSelection = None
					view.selectRow(row-1)
				elif action == self.actionDown:
					if row >= (len(model)-1):
						return
					d = model[row+1]
					model[row+1] = model[row]
					model[row] = d
					view.currentSelection = None
					view.selectRow(row+1)
				elif action == self.actionTop:
					if row == 0:
						return
					d = model[row]
					del(model[row])
					model.insert(0,d)
					view.currentSelection = None
					view.selectRow(0)
				elif action == self.actionBottom:
					if row >= (len(model)-1):
						return
					d = model[row]
					del(model[row])
					model.append(d)
					view.currentSelection = None
					view.selectRow(len(model)-1)
				else:
					return
				
	
		class Table(BaseWidget,QtGui.QTableView):
			def init(self):
				self.currentSelection = None
				self._up.Layout.addWidget(self)
				self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
				
				
			def currentChanged(self,current,previous):
				super(TableViewWidget.TableContainer.Table,self).currentChanged(current,previous)
				if current == self.currentSelection:
					return
				if self.currentSelection:
					self.saveForm(self.currentSelection)
				if current is None or not current.isValid():
					self.clearForm()
					self.disableForm()
					self.currentSelection = None
					return
				self.showRow(current)
				self.currentSelection = current
				
			def focusInEvent(self, *args, **kwargs):
				self.saveForm(self.currentSelection)
				return QtGui.QTableView.focusInEvent(self, *args, **kwargs)
				

			#
			# Local methods
			#
			
			def clearForm(self):
				if not self._up._up.Form: return 
				self._up._up.Form._field.clear()

			def disableForm(self):
				if not self._up._up.Form: return 
				self._up._up.Form.setDisabled(True)

			def showRow(self,index):
				if not self._up._up.Form: return 
				self.clearForm()
				model = self.model()
				form = self._up._up.Form
				value = FormData(**model[index.row()])
				form._field.setValue(value)
				form.setDisabled(False)
				
			def saveForm(self,index):
				if not self._up._up.Form: return 
				if index is None or not index.isValid():
					return
				model = self.model()
				form = self._up._up.Form
				value = form._field.getValue()
				if value == NOTSET:
					return
				model[index.row()] = value._data
	
	

class _TableView(BaseWidgetField):

	QtClass = TableViewWidget
	
	Properties = Properties(
		
		Properties.core,
		Properties.widget,

		# QAbstractItemView
		QtProperty(name='alternatingRowColors',target='Table',type=bool),
		QtProperty(name='autoScroll',target='Table',type=bool),
		QtProperty(name='autoScrollMargin',target='Table',type=int),
		QtProperty(name='editTrigers',target='Table',type=int,flags=[
			QtGui.QAbstractItemView.NoEditTriggers, QtGui.QAbstractItemView.CurrentChanged,
			QtGui.QAbstractItemView.DoubleClicked, QtGui.QAbstractItemView.SelectedClicked,
			QtGui.QAbstractItemView.EditKeyPressed, QtGui.QAbstractItemView.AnyKeyPressed,
			QtGui.QAbstractItemView.AllEditTriggers
		]),
		QtProperty(name='horizontalScrollMode',target='Table',options=[
			QtGui.QAbstractItemView.ScrollPerItem, QtGui.QAbstractItemView.ScrollPerPixel
		]),
		QtProperty(name='iconSize',target='Table',type=QtCore.QSize),
		QtProperty(name='selectionBehavior',target='Table',default=QtGui.QAbstractItemView.SelectRows,options=[
			QtGui.QAbstractItemView.SelectItems,
			QtGui.QAbstractItemView.SelectRows,
			QtGui.QAbstractItemView.SelectColumns
		]),
		QtProperty(name='selectionMode',target='Table',default=QtGui.QAbstractItemView.SingleSelection,options=[
			QtGui.QAbstractItemView.SingleSelection,
			QtGui.QAbstractItemView.ContiguousSelection,
			QtGui.QAbstractItemView.ExtendedSelection,
			QtGui.QAbstractItemView.MultiSelection,
			QtGui.QAbstractItemView.NoSelection
		]),
		QtProperty(name='tabKeyNavigation',target='Table',type=bool,default=False),
		QtProperty(name='textElideMode',target='Table',options=[
			Qt.ElideLeft,Qt.ElideMiddle,Qt.ElideNone,Qt.ElideRight
		]),
		QtProperty(name='verticalScrollMode',target='Table',options=[
			QtGui.QAbstractItemView.ScrollPerItem, QtGui.QAbstractItemView.ScrollPerPixel
		]),
			
		# QTableView
		QtProperty(name='showGrid',target='Table',type=bool),
		QtProperty(name='gridStyle',target='Table',type=Qt.PenStyle),
		QtProperty(name='sortingEnabled',target='Table',type=bool,getter='isSortingEnabled'),
		QtProperty(name='cornderButtonEnabled',target='Table',type=bool,getter='isCornerButtonEnabled'),
		QtProperty(name='wordWrap',target='Table',type=bool),

		# Vertical header
		QtProperty(name='vh_hidden',target='Table.verticalHeader()',type=bool,getter='isHidden',default=True),
		QtProperty(name='vh_defaultSectionSize',target='Table.verticalHeader()',type=int,default=20),
		
		# Horizontal header
		QtProperty(name='hh_hidden',target='Table.horizontalHeader()',type=bool,getter='isHidden'),
		QtProperty(name='hh_highlightSections',target='Table.horizontalHeader()',type=bool,default=False),
		QtProperty(name='hh_clickable',target='Table.horizontalHeader()',type=bool,getter='isClickable'),
		QtProperty(name='hh_moveable',target='Table.horizontalHeader()',type=bool,getter='isMovable'),
		QtProperty(name='hh_sortIndicatorShown',target='Table.horizontalHeader()',type=bool,getter='isSortIndicatorShown'),
		QtProperty(name='hh_defaultAlignment',target='Table.horizontalHeader()',
			flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
		),
		QtProperty(name='hh_defaultSectionSize',target='Table.horizontalHeader()',type=int),
		QtProperty(name='hh_minimumSectionSize',target='Table.horizontalHeader()'),
		QtProperty(name='hh_resizeMode',target='Table.horizontalHeader()',
			options=[QtGui.QHeaderView.Interactive,QtGui.QHeaderView.Fixed,QtGui.QHeaderView.Stretch,QtGui.QHeaderView.ResizeToContents]
		),
		
		# Other properties
		Property(name='columns',required=True,type=list,subType=Column),
		Property(name='tableActions',default=TableAction.NoActions,
			flags=[TableAction.Insert,TableAction.Delete,TableAction.Order]
		),
		Property(name='editForm',required=True),
		Property(name='formPosition',default=FormPosition.Right,
			options=[FormPosition.Top,FormPosition.Bottom,FormPosition.Left,FormPosition.Right]
		),
						
		# Events
		EventProperty(name='dataChanged',isDefault=True)
	)
	
	def init(self):
		self.model = FormsTableModel(self.columns)
		self.model.dataChanged.connect(lambda *args:self._qt.dataChanged.emit())
		table = self._qt.Table
		table.setModel(self.model)

		for index,column in enumerate(self.columns):
			delegate = column.createDelegate(self._qt)
			if delegate:
				table.setItemDelegateForColumn(index,delegate)
			if column.resizeMode != NOTSET:
				table.horizontalHeader().setResizeMode(index,column.resizeMode)
			if column.hidden != NOTSET:
				table.horizontalHeader().setSectionHidden(index,column.hidden)
		
		
	def getValueAndError(self,mark=False):
		if self._qt.Table.currentSelection:
			self._qt.Table.saveForm(self._qt.Table.currentSelection)
		return None,self.model._data
	
	def setValue(self,v):
		rowsBefore = len(self.model._data)
		self.model.fromList(v)
		
	def clear(self):
		self.setValue([])
			
class TableView(Factory):
	klass = _TableView
