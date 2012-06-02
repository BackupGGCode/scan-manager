import cPickle

from .core import *
from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import Qt



class HTMLDelegate(QtGui.QStyledItemDelegate):
	def __init__(self,parent=None):
		super(HTMLDelegate,self).__init__(parent)
		self.m_textDoc = QtGui.QTextDocument(self)
		
	def paint(self,painter,option,index):
		opt = QtGui.QStyleOptionViewItemV4(option)
		self.initStyleOption( opt, index );
	
		widget = opt.widget
		style = widget.style() if widget else QtGui.QApplication.style()
	
		textRect = style.subElementRect( QtGui.QStyle.SE_ItemViewItemText, opt, widget )
	
		# draw the item without text
		opt.text = ''
		style.drawControl( QtGui.QStyle.CE_ItemViewItem, opt, painter, widget )
	
		# draw the text (rich text)
		cg = QtGui.QPalette.Normal if opt.state & QtGui.QStyle.State_Enabled else QtGui.QPalette.Disabled
		if cg == QtGui.QPalette.Normal and not (opt.state & QtGui.QStyle.State_Active):
			cg = QtGui.QPalette.Inactive
		
		if opt.state & QtGui.QStyle.State_Selected:
			color = opt.palette.brush( cg, QtGui.QPalette.HighlightedText ).color()
		else:
			color = opt.palette.brush( cg, QtGui.QPalette.Text ).color()
			
		if opt.state & QtGui.QStyle.State_Editing:
			color = opt.palette.brush( cg, QtGui.QPalette.Text ).color()
			painter.drawRect( textRect.adjusted( 0, 0, -1, -1 ) )
	
		html = '<span style="color:%s;">%s</span>'%(color.name(),index.data())
		self.m_textDoc.setHtml( html )

		painter.save()
		try:
			painter.translate( textRect.topLeft() )
		
			tmpRect = QtCore.QRect(textRect)
			tmpRect.moveTo( 0, 0 )
			self.m_textDoc.setTextWidth( tmpRect.width() )
			self.m_textDoc.drawContents( painter, tmpRect )
			
		finally:
			painter.restore()


	def sizeHint( self, option, index ):
		ret = QtGui.QStyledItemDelegate.sizeHint( self, option, index )
		self.m_textDoc.setHtml( index.data() )
		ret = ret.expandedTo( self.m_textDoc.size().toSize() )
		# limit height to max. 2 lines
		# TODO add graphical hint when truncating! make configurable height?
		if ( ret.height() > option.fontMetrics.height() * 2 ):
			ret.setHeight( option.fontMetrics.height() * 2 )
		return ret;



class Column(object):

	__slots__ = ['name','label','editable','selectable','checkable','enabled','tristate','hidden','resizeMode','isRichText']
	
	def __init__(self,**kargs):
		self.editable = False
		self.selectable = True
		self.checkable = False
		self.enabled = True
		self.tristate = False
		self.hidden = False
		self.resizeMode = QtGui.QHeaderView.Interactive
		self.isRichText = False
		for k,v in kargs.items():
			setattr(self,k,v)
	


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
			
		flags |= QtCore.Qt.ItemIsDragEnabled 
		flags |= QtCore.Qt.ItemIsDropEnabled 

		return Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index) | flags)
	
	#
	# Drag and drop behaviour (for reordering, primarily)
	#
	
	def supportedDropActions(self): 
		return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction	
	
	def mimeTypes(self):
		return ['application/x-pickle']

	def mimeData(self, indexes):
		data = QtCore.QMimeData()
		data.setData('application/x-pickle', cPickle.dumps([(i.row(),i.column()) for i in indexes]))
		return data

	def dropMimeData(self, data, action, row, column, parent):
		data = cPickle.loads(str(data.data('application/x-pickle')))
		sourceRow = data[0][0]
		targetRow = parent.row()
		if action == QtCore.Qt.DropAction.MoveAction:
			d = self[sourceRow]
			del(self[sourceRow])
			self.insert(targetRow,d)
		elif action == QtCore.Qt.DropAction.CopyAction:
			d = self[sourceRow]
			self.insert(targetRow,d)
		return True
	
	#
	# Local methods
	#
	
	def fromList(self,l):
		self.removeRows(0,self.rowCount())
		for i in l:
			self.append(i)

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
		
		
