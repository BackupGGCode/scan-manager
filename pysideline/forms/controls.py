import base
from .base import *

#
# Common properties
#

Properties.core = Properties(
    # Core properies
    Property(name='name',type=str,required=True),
    Property(name='label',type=str),
    Property(name='depends',type=list,subType=str),
)
    
Properties.widget = Properties(
    # General widget properties
    QtProperty(name='styleSheet',type=str),
    QtProperty(name='enabled',type=bool),
    QtProperty(name='font',type=object),
    QtProperty(name='visible',type=object),
    QtProperty(name='graphicsEffect',type=object),
    QtProperty(name='inputMethodHints',type=object,
        options=[Qt.ImhDialableCharactersOnly,Qt.ImhDigitsOnly,Qt.ImhEmailCharactersOnly,Qt.ImhExclusiveInputMask,
                 Qt.ImhFormattedNumbersOnly,Qt.ImhHiddenText,Qt.ImhLowercaseOnly,Qt.ImhNoAutoUppercase,Qt.ImhNoPredictiveText,
                 Qt.ImhPreferLowercase,Qt.ImhPreferNumbers,Qt.ImhPreferUppercase,Qt.ImhUppercaseOnly,Qt.ImhUrlCharactersOnly]),
    QtProperty(name='whatsThis',type=str),
    QtProperty(name='toolTip',type=str),

    # General widget properties (size)
    QtProperty(name='fixedWidth',type=object),
    QtProperty(name='fixedHeight',type=object),
    QtProperty(name='minimumWidth',type=object),
    QtProperty(name='minimumHeight',type=object),
)


Properties.valueField = Properties(
    # General value-field properties
    Property(name='type'),
    Property(name='default'),
    Property(name='validate'),
    Property(name='required',type=bool),
)        


Properties.formLayout = Properties(
    # Form layout properties
    QtProperty(name='fieldGrowthPolicy',target='Layout',options=[
        QtGui.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow,
        QtGui.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        QtGui.QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint,
    ]),
    QtProperty(name='formAlignment',target='Layout',type=int,
        flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
    ),
    QtProperty(name='horizontalSpacing',target='Layout',type=int),
    QtProperty(name='labelAlignment',target='Layout',type=int,
        flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
    ),
    QtProperty(name='rowWrapPolicy',target='Layout',options=[
        QtGui.QFormLayout.RowWrapPolicy.DontWrapRows,
        QtGui.QFormLayout.RowWrapPolicy.WrapAllRows,
        QtGui.QFormLayout.RowWrapPolicy.WrapLongRows,
    ]),
    QtProperty(name='spacing',type=int,target='Layout'),
    QtProperty(name='verticalSpacing',type=int,target='Layout'),
    QtProperty(name='contentsMargins',type=tuple,target='Layout',setter='setContentsMargins'),
)



#
# Concrete fields
#

        
class _Form(base._AbstractGroup):
    Name = 'Form'

    QtClass = QtGui.QWidget

    Properties = Properties(
        Properties.formLayout,
        Properties.widget,
                
        Property(name='name',type=str,required=True),
        Property(name='contents',required=True),
    )
    

    def __init__(self,parent,**kargs):
        super(_Form,self).__init__(parent,**kargs)
        self.groupData = True
        
    
    def registerObject(self,field):
        self.fields[field.name] = field
        
        
    @property
    def form(self):
        return self

class Form(Factory):
    klass = _Form



class _LineEdit(BaseWidgetField):
    Name = 'LineEdit'
    QtClass = QtGui.QLineEdit
    
    Properties = Properties(
        
        Properties.core,
        Properties.widget,
        Properties.valueField,

        # Line-edit specific properties
        QtProperty(name='inputMask',type=str),
        QtProperty(name='maxLength',type=int),
        QtProperty(name='readOnly',type=bool,getter='isReadOnly'),
        QtProperty(name='placeholderText',type=str),
        QtProperty(name='alignment',type=int,
            flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
        ),
        QtProperty(name='echoMode',type=int,
            options=[QtGui.QLineEdit.Normal,QtGui.QLineEdit.NoEcho,QtGui.QLineEdit.Password,QtGui.QLineEdit.PasswordEchoOnEdit]
        ),
        QtProperty(name='completer',type=object),
        QtProperty(name='margins',type=tuple,subType=(int,int,int,int)),

        # Special properties for pysidline.forms
        Property(name='validator',type=callable),
    
        EventProperty(name='textEdited'),
        EventProperty(name='textChanged'),
    )
    
    def init(self):
        self.initValidator()
    
    def getValue(self):
        error,value = self.qtToValue(self._qt.text())
        self.setError(error)
        return value
        
    def setValue(self,v):
        if type(v) is int:
            v = unicode(v)
        self._qt.setText(v)

class LineEdit(Factory):
    klass = _LineEdit
    

    
class _TextEdit(BaseWidgetField):
    Name = 'TextEdit'
    QtClass = QtGui.QTextEdit
    
    Properties = Properties(
        
        Properties.core,
        Properties.widget,
        Properties.valueField,

        # Text-edit specific properties
        QtProperty(name='acceptRichText',type=bool),
        QtProperty(name='autoFormatting',type=int,flags=[QtGui.QTextEdit.AutoNone,QtGui.QTextEdit.AutoBulletList,QtGui.QTextEdit.AutoAll]),
        QtProperty(name='cursorWidth',type=bool),
        QtProperty(name='documentTitle',type=str),
        QtProperty(name='lineWrapColumnOrWidth',type=int),
        QtProperty(name='lineWrapMode',type=int,options=[QtGui.QTextEdit.NoWrap,QtGui.QTextEdit.WidgetWidth,QtGui.QTextEdit.FixedPixelWidth,QtGui.QTextEdit.FixedColumnWidth]),
        QtProperty(name='overwriteMode',type=bool),
        QtProperty(name='readOnly',type=bool,getter='isReadOnly'),
        QtProperty(name='textInteractionFlags',type=int,flags=[
            Qt.NoTextInteraction,Qt.TextSelectableByMouse,Qt.TextSelectableByKeyboard,Qt.LinksAccessibleByMouse,Qt.LinksAccessibleByKeyboard,Qt.TextEditable,
            Qt.TextEditorInteraction,Qt.TextBrowserInteraction]
        ),
        QtProperty(name='undoRedoEnabled',type=bool,getter='isUndoRedoEnabled'),
        QtProperty(name='wordWrapMode',type=int,options=[QtGui.QTextOption.NoWrap,QtGui.QTextOption.WordWrap,QtGui.QTextOption.ManualWrap,QtGui.QTextOption.WrapAnywhere,
            QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere]
        ),

        # Special properties for pysidline.forms
        Property(name='useHTML',type=bool,default=False),
        
        # Events
        EventProperty(name='textChanged'),
    )
    
    def getValue(self):
        if self.useHTML:
            return self._qt.toHtml()
        else:
            return self._qt.toPlainText()
        
    def setValue(self,v):
        if self.useHTML:
            return self._qt.setHtml(v)
        else:
            return self._qt.setPlainText(v)

class TextEdit(Factory):
    klass = _TextEdit
    


class _ComboOptions(base._QtProperty):
    def toQt(self,q):
        if self.value is NOTSET:
            return
        q.clear()
        for ndx,item in enumerate(self.value):
            if type(item) != tuple:
                q.addItem(item)
            elif len(item) == 1:
                q.addItem(item[0])
            elif len(item) == 2:
                q.addItem(item[1],item[0])
            elif len(item) == 3:
                icon = QtGui.QIcon(item[3])
                q.addItem(icon,item[1],item[0])
            else:
                raise self._properties['options'].configurationError('invalid item at index %d'%ndx)

class ComboOptions(Factory):
    klass = _ComboOptions
    

    
class _ComboBox(BaseWidgetField):
    Name = 'ComboBox'
    QtClass = QtGui.QComboBox
    
    Properties = Properties(
        
        Properties.core,
        Properties.widget,
        Properties.valueField,
        
        ComboOptions(name='options'),
        
        # Combo-box specific properties
        QtProperty(name='editable',type=bool,getter='isEditable'),
        QtProperty(name='duplicatesEnabled',type=bool,getter='isEditable'),
        QtProperty(name='frame',type=bool,getter='hasFrame'),
        QtProperty(name='iconSize',type=QtCore.QSize),
        QtProperty(name='insertPolicy',type=int,options=[
            QtGui.QComboBox.NoInsert,QtGui.QComboBox.InsertAtTop,QtGui.QComboBox.InsertAtCurrent,QtGui.QComboBox.InsertAfterCurrent,QtGui.QComboBox.InsertBeforeCurrent,
            QtGui.QComboBox.InsertAlphabetically]
        ),
        QtProperty(name='maxCount',type=int),
        QtProperty(name='maxVisibleItems',type=int),
        QtProperty(name='minimumContentsLength',type=int),
        QtProperty(name='sizeAdjustPolicy',type=int,options=[
            QtGui.QComboBox.AdjustToContents,QtGui.QComboBox.AdjustToContentsOnFirstShow,QtGui.
            QComboBox.AdjustToMinimumContentsLength,QtGui.QComboBox.AdjustToMinimumContentsLengthWithIcon]
        ),
                        
        # pysideline.forms specific properties
        Property(name='textAsValue',type=bool,default=False),
        Property(name='validator',type=callable),
        
        # Events
        EventProperty(name='currentIndexChanged'),
        EventProperty(name='editTextChanged'),
    )
    
    def init(self):
        self.initValidator()
    
    
    def getValue(self):
        if self.textAsValue:
            return self._qt.currentText()
        else:
            index = self._qt.currentIndex()
            data = self._qt.itemData(index)
            return data
    
        
    def setValue(self,v):
        if self.textAsValue:
            self._qt.lineEdit().setText(v)
        else:
            index = self._qt.findData(v)
            if index == -1:
                raise KeyError(v)
            self._qt.setCurrentIndex(index)

class ComboBox(Factory):
    klass = _ComboBox



class _SpinBox(BaseWidgetField):
    Name = 'SpinBox'
    QtClass = QtGui.QSpinBox 
    
    Properties = Properties(
        
        Properties.core,
        Properties.widget,
        Properties.valueField,
        
        # Spin-box specific properties
        QtProperty(name='accelerated',type=bool,getter='isAccelerated'),
        QtProperty(name='alignment',type=int,flags=[
            Qt.AlignLeft,Qt.AlignRight,Qt.AlignHCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignTop,Qt.AlignBottom,Qt.AlignVCenter,Qt.AlignCenter,
            Qt.AlignAbsolute,Qt.AlignLeading,Qt.AlignTrailing]
        ),
        QtProperty(name='correctionMode',type=int,options=[QtGui.QAbstractSpinBox.CorrectToPreviousValue,QtGui.QAbstractSpinBox.CorrectToNearestValue]),
        QtProperty(name='keyboardTracking',type=bool),
        QtProperty(name='specialValueText',type=str),
        QtProperty(name='wrapping',type=bool),
        QtProperty(name='minimum',type=int),
        QtProperty(name='maximum',type=int),
        QtProperty(name='singleStep',type=int),
        QtProperty(name='suffix',type=str),
        QtProperty(name='prefix',type=str),
        
        # Events
        EventProperty(name='valueChanged'),
        EventProperty(name='editingFinished'),
    )
    
    def getValue(self):
        return self._qt.value()
    
        
    def setValue(self,v):
        if v is NOTSET or v is None:
            self._qt.clear()
        else:
            self._qt.setValue(v)

class SpinBox(Factory):
    klass = _SpinBox



class _Slider(BaseWidgetField):
    Name = 'Slider'
    QtClass = QtGui.QSlider 
    
    Properties = Properties(
        
        Properties.core,
        Properties.widget,
        Properties.valueField,
        
        # QAbstractSlider specific properties
        QtProperty(name='invertedAppearance',type=bool),
        QtProperty(name='invertedControls',type=bool),
        QtProperty(name='maximum',type=int),
        QtProperty(name='minimum',type=int),
        QtProperty(name='orientation',options=[Qt.Horizontal,Qt.Vertical]),
        QtProperty(name='pageStep',type=int),
        QtProperty(name='singleStep',type=int),
        QtProperty(name='tracking',type=bool,getter='hasTracking'),

        # QSlider specific properties
        QtProperty(name='tickInterval',type=int),
        QtProperty(name='tickPosition',options=[QtGui.QSlider.NoTicks,QtGui.QSlider.TicksBothSides,QtGui.QSlider.TicksAbove,
            QtGui.QSlider.TicksBelow,QtGui.QSlider.TicksLeft,QtGui.QSlider.TicksRight]
        ),
        
        
        # Events
        EventProperty(name='valueChanged'),
        EventProperty(name='rangeChanged'),
        EventProperty(name='sliderMoved'),
        EventProperty(name='sliderPressed'),
        EventProperty(name='sliderReleased'),
    )
    
    def getValue(self):
        return self._qt.value()
    
        
    def setValue(self,v):
        self._qt.setValue(v)

class Slider(Factory):
    klass = _Slider



class _GroupBox(base._AbstractGroup):
    Name = 'GroupBox'
    QtClass = QtGui.QGroupBox 
    
    Properties = Properties(
        
        base._AbstractGroup.Properties,
        Properties.core,
        Properties.widget,
        Properties.formLayout,

        QtProperty(name='title',type=str),
        QtProperty(name='flat',type=bool,getter='isFlat'),
        QtProperty(name='checkable',type=bool,getter='isCheckable'),
        QtProperty(name='checked',type=bool,getter='isChecked'),
        QtProperty(name='alignment',type=int,
            flags=[Qt.AlignAbsolute,Qt.AlignBottom,Qt.AlignCenter,Qt.AlignHCenter,Qt.AlignJustify,Qt.AlignLeading,Qt.AlignLeft,Qt.AlignRight,Qt.AlignTop,Qt.AlignTrailing,Qt.AlignVCenter]
        ),
        
    )

    def getValue(self):
        v = super(_GroupBox,self).getValue()
        if self.checkable:
            v.setValue('checked',self.checked)
        return v
    
class GroupBox(Factory):
    klass = _GroupBox
