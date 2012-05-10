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

class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, addresses=None, parent=None):
        super(TableModel, self).__init__(parent)

        if addresses is None:
            self.addresses = []
        else:
            self.addresses = addresses

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self.addresses)

    def columnCount(self, index=QtCore.QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.addresses):
            return None

        if role == Qt.DisplayRole:
            name = self.addresses[index.row()]["name"]
            address = self.addresses[index.row()]["address"]

            if index.column() == 0:
                return name
            elif index.column() == 1:
                return address

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Address"
        
        return None

    def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)

        for row in range(rows):
            self.addresses.insert(position + row, {"name":"", "address":""})

        self.endInsertRows()
        return True

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows - 1)

        del self.addresses[position:position+rows]

        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False

        if index.isValid() and 0 <= index.row() < len(self.addresses):
            address = self.addresses[index.row()]
            if index.column() == 0:
                address["name"] = value
            elif index.column() == 1:
                address["address"] = value
            else:
                return False

            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index) |
                            Qt.ItemIsEditable)


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
					
			class FormWidget(BaseWidget,QtGui.QWidget):
				class Layout(BaseLayout,QtGui.QVBoxLayout):
					def init(self):
						self._up.setLayout(self)
						
				def init(self):
					self._up.Layout.addWidget(self)
					
					self.app.myForm = MyForm(None)
					self.form = self.app.myForm.create(self)
					self.Layout.addWidget(self.form)
					
			class MyTable(BaseWidget,QtGui.QTableView):
				def init(self):
					self.model = TableModel()
					self.setModel(self.model)
					self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
					self.horizontalHeader().setStretchLastSection(True)
					self.verticalHeader().hide()
					#self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
					self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
					self.model.insertRows(position=0,rows=2)
					self.model.setData(self.model.index(0,0),'a')
					self.model.setData(self.model.index(0,1),'b')
					self._up.Layout.addWidget(self)
					
			class OKButton(BaseWidget,QtGui.QPushButton):
				def init(self):
					self._up.Layout.addWidget(self)
					self.setText('OK')
				def onclicked(self):
					print self.app.myForm.getValue()._pp()
				
app = App(sys.argv)
app.exec_()


