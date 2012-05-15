from .common import *

class _GridLayout(base._AbstractGroup):

	QtClass = QtGui.QWidget
	
	Properties = Properties(
		
		base._AbstractGroup.Properties,
		Properties.core,
		Properties.widget,

		# Layout properties		
		QtProperty(name='sizeConstraint',
			options=[
				QtGui.QLayout.SetDefaultConstraint,QtGui.QLayout.SetFixedSize,QtGui.QLayout.SetMinimumSize,
				QtGui.QLayout.SetMaximumSize,QtGui.QLayout.SetMinAndMaxSize,QtGui.QLayout.SetNoConstraint
			],
			target='Layout'
		),
						
		# Grid layout properties 
		QtProperty(name='horizontalSpacing',type=int,target='Layout'),
		QtProperty(name='verticalSpacing',type=int,target='Layout'),
		QtProperty(name='contentsMargins',type=QtCore.QMargins,default=(0,0,0,0),target='Layout'),
		Property(name='columnStretch',default=[]),
		Property(name='rowStretch',default=[]),
	)

	def layoutChildren(self):
		self._qt.Layout = QtGui.QGridLayout()
		self._qt.setLayout(self._qt.Layout)
		
		for field in self._children.values():
			row = field.row
			if row is NOTSET:
				row = self._qt.Layout.rowCount()
			col = field.col
			if col is NOTSET:
				col = self._qt.Layout.colCount()
			rowSpan = field.rowSpan
			if rowSpan is NOTSET:
				rowSpan = 1
			colSpan = field.colSpan
			if colSpan is NOTSET:
				colSpan = 1
			cellAlignment = field.cellAlignment
			if cellAlignment is NOTSET:
				cellAlignment = 0
				
			self._qt.Layout.addWidget(
				field._qt,
				row,
				col,
				rowSpan,
				colSpan,
				cellAlignment,
			)

		for index,v in enumerate(self.columnStretch):
			self._qt.Layout.setColumnStretch(index,v)
			
		for index,v in enumerate(self.rowStretch):
			self._qt.Layout.setRowStretch(index,v)
		
	
class GridLayout(Factory):
	klass = _GridLayout



