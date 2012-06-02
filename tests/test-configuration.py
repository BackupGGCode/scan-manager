from gui.common import *
from pysideline.tablemodel import *
import resources

columns = [Column(name='c1', label='Column 1'),Column(name='c2', label='Column 2')]

class App(Application):
	
	class Main(BaseWidget, QtGui.QWidget):
		def init(self):
			self.resize(800, 600)
			self.show()
			
		class Layout(BaseLayout, QtGui.QVBoxLayout):
			
			def init(self):
				self.setContentsMargins(0, 0, 0, 0)
				self.setSpacing(0)
				self._up.setLayout(self)
				
		class TableViewWidget(BaseWidget, QtGui.QTableView):
			def init(self):
				self._up.Layout.addWidget(self)
				self.hd = HTMLDelegate()
				self.setItemDelegateForColumn(0, self.hd)
				for index, column in enumerate(columns):
					if column.resizeMode:
						self.horizontalHeader().setResizeMode(index, column.resizeMode)
					if column.hidden:
						self.horizontalHeader().setSectionHidden(index, column.hidden)
						
				self.setModel(TableModel(columns))
				m = self.model()
				m.append(dict(c1='abc <b>bold</b> def',c2='abc <b>bold</b> def'))
			
				
app = App(sys.argv)
app.exec_()

























