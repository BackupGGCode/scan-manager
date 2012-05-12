from .base import *
import base
import copy


class TableAction:
	Insert = 0x1
	Delete = 0x2
	Order = 0x4
	Edit = Insert|Delete
	All = Insert|Delete|Order
	NoActions = 0x0
		
		
		
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



class DataRow(object):
	""" A row object that notifies its parent table of updates to any column values """
	
	def __init__(self,parent,**kargs):
		self.__dict__['_parent'] = parent
		self.__dict__['_data'] = kargs	
	
	def __getitem__(self,k):
		if k in self.data:
			return self.data[k]
		
	def __setitem__(self,k,v):
		for columnIndex,column in self.parent._columns:
			if column.name == k:
				break
		else:
			raise Exception('unknown column %s'%k)
			
		self._data[k] = v
		index = self.parent.index(self.parent._data.index(self),columnIndex)
		self.parent.dataChanged.emit(index, index)
		
	def __getattr__(self,k):
		return self[k]
	
	def __setattr__(self,k,v):
		self[k] = v
		
	def _toDict(self):
		return copy.copy(self._data)
		

class TableModel(QtCore.QAbstractTableModel):

	def __init__(self,columns=None,parent=None):
		super(TableModel, self).__init__(parent)
		if columns is None:
			columns = []
		self._columns = columns
		self._data = []
		
	def rowCount(self, index=QtCore.QModelIndex()):
		return len(self._data)

	def columnCount(self, index=QtCore.QModelIndex()):
		return len(self._columns)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if not 0 <= index.row() < len(self._data):
			return None

		if role != Qt.DisplayRole:
			return None
		
		column = self._columns[index.column()]
		return self._data[index.row()].get(column.name,NOTSET)

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role != Qt.DisplayRole:
			return None

		if orientation != Qt.Horizontal:
			return None
		
		return self._columns[section].label

	def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
		self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)

		for row in range(rows):
			d = {}
			for column in self._columns:
				d[column.name] = NOTSET
			self._data.insert(1 + position + row, d)

		self.endInsertRows()
		return True

	def removeRow(self, position, index=QtCore.QModelIndex()):
		self.beginRemoveRows(QtCore.QModelIndex(), position, position)
		del self._data[position]
		self.endRemoveRows()
		return True

	def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
		self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows - 1)
		del self._data[position:position+rows]
		self.endRemoveRows()
		return True

	def setData(self, index, value, role=Qt.EditRole):
		if role != Qt.EditRole:
			return False

		if not index.isValid():
			return False
		
		if not (0 <= index.row() < len(self._data)):
			return False
		
		datum = self._data[index.row()]
		
		if index.column() < 0  or index.column() >= len(self._columns):
			return True
		
		column = self._columns[index.column()]
		datum[column.name] = value

		self.dataChanged.emit(index, index)
		return True

	def flags(self, index):
		if not index.isValid():
			return Qt.ItemIsEnabled
		flags = 0
		column = self._columns[index.column()]
		if column.editable:
			flags |= Qt.ItemIsEditable
		if column.selectable:
			flags |= Qt.ItemIsSelectable
		if column.checkable:
			flags |= Qt.ItemIsUserCheckable
		if column.enabled:
			flags |= Qt.ItemIsEnabled
		if column.tristate:
			flags |= Qt.ItemIsTristate

		return Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index) | flags)
	
	def fromList(self,l):
		rowsBefore = len(self._data)
		self._data = l
		tl = self.index(0,0)
		br = self.index(max(rowsBefore-1,len(self._data)-1),len(self._columns)-1)
		self.dataChanged.emit(tl,br)

	def toList(self):
		#out = [i._toDict() for i in self._data]
		return self._data
	
	#
	# Python sequence behaviour
	# 

	def __setitem__(self,row,v):
		self._data[row] = v
		tl = self.index(row,0)
		br = self.index(row,len(self._columns)-1)
		self.dataChanged.emit(tl,br)
	
	def __getitem__(self,row):
		return self._data[row]
	
	def __delitem__(self,row):
		self.beginRemoveRows(QtCore.QModelIndex(), row, row)
		del self._data[row]
		self.endRemoveRows()
		
	def __len__(self):
		return len(self._data)
	
	def append(self,data):
		self.beginInsertRows(QtCore.QModelIndex(), len(self._data), len(self._data))
		self._data.append(data)
		self.endInsertRows()
		
	def insert(self,position,data):
		self.beginInsertRows(QtCore.QModelIndex(), position, position)
		self._data.insert(position,data)
		self.endInsertRows()
		

class TableViewWidget(BaseWidget,QtGui.QWidget):

	def afterCreate(self):
		self.Layout.addWidget(self.TableContainer,1)
		if self._field.editForm:
			subField = self._field.editForm(None)
			self.Form = subField.create(self)
			self.Form._field = subField
			self.Layout.addWidget(self.Form)
			self.Form.setDisabled(True)
		else:
			self.Form = None
			
		toolbar = self.TableContainer.Toolbar
		field = self._field

		toolbar.actionInsert.setVisible(field.tableActions & TableAction.Insert)
		toolbar.actionDelete.setVisible(field.tableActions & TableAction.Delete)
		toolbar.actionTop.setVisible(field.tableActions & TableAction.Order)
		toolbar.actionUp.setVisible(field.tableActions & TableAction.Order)
		toolbar.actionDown.setVisible(field.tableActions & TableAction.Order)
		toolbar.actionBottom.setVisible(field.tableActions & TableAction.Order)
		toolbar.setHidden(field.tableActions == TableAction.NoActions)

	class Layout(BaseLayout,QtGui.QHBoxLayout):
		
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
				model[index.row()] = value.__dict__

	
	
class _TableView(BaseWidgetField):
	Name = 'TableView'
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
		Property(name='editForm',required=True),
		Property(name='tableActions',default=TableAction.NoActions,flags=[
			TableAction.Insert,TableAction.Delete,TableAction.Order
		])
	)
	
	def init(self):
		self.model = TableModel(self.columns)
		table = self._qt.Table
		table.setModel(self.model)

		for index,column in enumerate(self.columns):
			delegate = column.createDelegate(self._qt)
			if not delegate:
				continue
			table.setItemDelegateForColumn(index,delegate)
			if column.resizeMode is not NOTSET:
				table.horizontalHeader().setResizeMode(index,column.resizeMode)
			if column.hidden is not NOTSET:
				table.horizontalHeader().setSectionHidden(index,column.hidden)
		
		
	def getValue(self):
		if self._qt.Table.currentSelection:
			self._qt.Table.saveForm(self._qt.Table.currentSelection)
		return self.model._data
	
	def setValue(self,v):
		rowsBefore = len(self.model._data)
		self.model._data.fromList(v)
		
	def clear(self):
		self.setValue([])
			
class TableView(Factory):
	klass = _TableView
