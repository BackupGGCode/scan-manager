from .base import *
import base
import copy

class ColumnDelegate(QtGui.QItemDelegate):
	def __init__(self,column,*args,**kargs):
		self.column = column
		super(ColumnDelegate,self).__init__(*args,**kargs)
	def createEditor(self,parent,option,index):
		print 'createEditor'
		return self.column.editor.create(parent)
	def setEditorData(self,editor,index):
		v = index.model().data(index)
		return editor._field.setValue(v)
	def setModelData(self,editor,model,index):
		print 'setModelData'
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
	)
	
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
		return self._data[index.row()][column.name]

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
			self._data.insert(position + row, d)

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
			flags = Qt.ItemIsEditable
		if column.selectable:
			flags = Qt.ItemIsSelectable
		if column.checkable:
			flags = Qt.ItemIsUserCheckable
		if column.enabled:
			flags = Qt.ItemIsEnabled
		if column.tristate:
			flags = Qt.ItemIsTristate

		return Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index) | flags)
	
	def __setitem__(self,row,v):
		self._data[row] = v
		tl = self.index(row,0)
		br = self.index(row,len(self._columns)-1)
		self.dataChanged.emit(tl,br)
	
	def __getitem__(self,row):
		return self._data[row]
	
	def append(self,data):
		rowData = DataRow(self,**data)
		self._data.append(rowData)
		
	def fromList(self,l):
		rowsBefore = len(self._data)
		self._data = []
		for item in l:
			row = DataRow(self,**item)
			self._data.append(row)
		tl = self.index(0,0)
		br = self.index(max(rowsBefore-1,len(self._data)-1),len(self._columns)-1)
		self.dataChanged.emit(tl,br)

	def toList(self):
		out = [i._toDict() for i in self._data]
	
	
class _TableView(BaseWidgetField):
	Name = 'TableView'
	QtClass = QtGui.QTableView 
	
	Properties = Properties(
		
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.widget,
		Properties.formLayout,
		
		Property(name='columns',required=True,type=list,subType=Column),

	)
	
	def init(self):
		self.model = TableModel(self.columns)
		self._qt.setModel(self.model)
		self._qt.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._qt.horizontalHeader().setStretchLastSection(True)
		self._qt.verticalHeader().hide()
		#self._qt.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self._qt.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.model.insertRows(position=0,rows=2)
		self.model.setData(self.model.index(0,0),'a')
		self.model.setData(self.model.index(0,1),0.01)
		#self._qt.setStyleSheet('QTableView::item { background-color: red; padding: 0px; border: 0px; height: 16px;}')
		#self._qt.setStyleSheet('QTableView::item::text { color: blue; padding: 0px; border: 0px; }')
		#self._qt.verticalHeader().setDefaultSectionSize( 16 )

		for index,column in enumerate(self.columns):
			delegate = column.createDelegate(self._qt)
			if not delegate:
				continue
			self._qt.setItemDelegateForColumn(index,delegate)
		
	def getValue(self):
		return self.model._data
	
	def setValue(self,v):
		rowsBefore = len(self.model._data)
		self.model._data.fromList(v)
	
class TableView(Factory):
	klass = _TableView

