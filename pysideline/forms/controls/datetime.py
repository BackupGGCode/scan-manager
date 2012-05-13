from .common import *

class _DateTimeEdit(BaseWidgetField):

    QtClass = QtGui.QDateTimeEdit
    
    Properties = Properties(
                        
        Properties.core,
        Properties.widget,
        Properties.valueField,

        Properties.dateTimeEdit,
        
        EventProperty(name='dateChanged'),
        EventProperty(name='dateTimeChanged',isDefault=True),
        EventProperty(name='timeChanged'),
    )
    
    def getRawValue(self):
        return self._qt.dateTime()
    
    def setRawValue(self,v):
        return self._qt.setDateTime(v)
    
    def valueToRaw(self,v):
        out = QtCore.QDateTime()
        out.setDate(v.date())
        out.setTime(v.time())
        return out

    def rawToValue(self,v):
        return v.toPython()
    
class DateTimeEdit(Factory):
    klass = _DateTimeEdit



class _DateEdit(BaseWidgetField):

    QtClass = QtGui.QDateEdit
    
    Properties = Properties(
                        
        Properties.core,
        Properties.widget,
        Properties.valueField,

        Properties.dateTimeEdit,
        
        EventProperty(name='dateChanged',isDefault=True),
    )
    
    def getRawValue(self):
        return self.date()
    
    def setRawValue(self,v):
        return self._qt.setDate(v)
    
    def valueToRaw(self,v):
        out = QtCore.QDateTime()
        out.setDate(v.date())
        return out.date()

    def rawToValue(self,v):
        return v.toPython()
    
class DateEdit(Factory):
    klass = _DateEdit



class _TimeEdit(BaseWidgetField):

    QtClass = QtGui.QDateEdit
    
    Properties = Properties(
                        
        Properties.core,
        Properties.widget,
        Properties.valueField,

        Properties.dateTimeEdit,
        
        EventProperty(name='timeChanged',isDefault=True),
    )
    
    def getRawValue(self):
        return self._qt.time()
    
    def setRawValue(self,v):
        return self._qt.setTime(v)
    
    def valueToRaw(self,v):
        out = QtCore.QDateTime()
        out.setDate(v.date())
        return out.time()

    def rawToValue(self,v):
        return v.toPython()
    
class TimeEdit(Factory):
    klass = _TimeEdit



