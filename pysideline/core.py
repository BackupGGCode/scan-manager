"""
PySideLine is a simple wrapper to allow semi-declarative programming of PySide (Qt4) GUIs in python

The basic idea is that instead of laying out widgets in a tree structure procedurally, it should be possible to lay them out as a set of nested classes.

Similarly signals, instead of needing to be connected procedurally using .connect calls, should be connected automatically to methods on the widget based on method names.
"""

from PySide import QtCore
from PySide import QtGui
import itertools
import sys

__all__ = ['NOTSET','signalsCache','BaseInstantiable','BaseWidget','BaseLayout','BaseDialog','BaseRootInstantiable','Application']


class __NOTSET(object):
	def __nonzero__(self):
		return False
	def __eq__(self,other):
		if isinstance(other,self.__class__):
			return True
		else:
			return False
NOTSET = __NOTSET()

signalsCache = {} #: a local cache of class->(dict of signal id->QtCore.Signal)
classDefinitionOrderCounter = itertools.count() #: a (thread-safe) counter used to number classes so we can sort them in order of class definition later


class CounterMetaclass(type(QtCore.QObject)): 
	""" 
	Metaclass that allows us to track the order in which sub-classes are defined in the source files
	
	This lets us auto-instantiate them in the right order (vital for automatic layouts)
	"""
	def __new__(cls, name, bases, dct):
		global classDefinitionOrderCounter
		### 3.0
		#dct['_psl_serial'] = classDefinitionOrderCounter.__next__()
		dct['_psl_serial'] = classDefinitionOrderCounter.next()
		return super(CounterMetaclass, cls).__new__(cls, name, bases, dct)



### 3.0		
#class BaseInstantiable(metaclass=CounterMetaclass):



class Acquisition(object):
	
	def __init__(self,base):
		self.base = base
	
	def __getattr__(self,k):
		o = self.base
		while 1:
			if hasattr(o,k):
				return getattr(o,k)
			if hasattr(o,'_up') and o._up is not None:
				o = o._up
			else:
				raise AttributeError(k)
				#ei = sys.exc_info()
				#if ei[2]:
				#	raise ei[0],None,ei[2].tb_next



class BaseInstantiable(object):
	"""
	Base class for all objects that should be auto-instantiated
	
	Also, if not overridden acts as a top-level namespace for all objects registered under it with M{registerObject} (see below)
	"""
	
	__metaclass__ = CounterMetaclass

	def __init__(self,*args,**kargs):
		
		self.aq = Acquisition(self)
		
		if 'noAutoInstantiate' in kargs:
			noAutoInstantiate = kargs['noAutoInstantiate']
			del(kargs['noAutoInstantiate'])
		else:
			noAutoInstantiate = False
			
		super(BaseInstantiable,self).__init__(*args,**kargs)

		if not noAutoInstantiate:
			parent = (args and args[0]) or kargs.get('parent',None)
			self._up = parent
			toInit = self._autoInstantiate()
			for o in toInit:
				o.init()
			self.init()
		
		
	def _autoInstantiate(self,recurse=True):
		"""
		Swap  attributes of this class that are classes that subclass BaseInstantiable into instances of themselves
		
		If these classes are also subclasses of BaseWidget then self is set as their parent
		"""
		if hasattr(self,'_findSignals') and not hasattr(self,'_signals'):
			self._findSignals()

		toInstantiate = []
		for k in dir(self):
		
			# ignore anything starting with '_' -- can't be a subobject or a signal handler method
			if k.startswith('_') or k == 'app':
				continue
				
			# check if this attribute is a class that needs instantiation
			v = getattr(self,k)
			if isinstance(v,type) and issubclass(v,BaseInstantiable):
				toInstantiate.append((k,v))
				
			# connect signals to methods named on<signalName> automatically
			if k.startswith('on') and k[2:] in self._signals:
				signal = getattr(self,k[2:])
				signal.connect(v)
		
		# instantiate and initialise sub-objects in the order in which they were defined
		toInstantiate.sort(key=lambda a:a[1]._psl_serial)
		done = []
		for k,v in toInstantiate:
			if hasattr(v,'args'):
				o = v(*v.args,noAutoInstantiate=True)
			else:
				o = v(noAutoInstantiate=True)
			self._registerSubObject(k,o)
			if isinstance(self,QtGui.QWidget) and isinstance(o,QtGui.QWidget):
				o.setParent(self)
			o._up = self
			done.append(o)
			if recurse:
				done = done[:-1] + o._autoInstantiate() + done[-1:]
			setattr(self,k,o)
			
		return done

		
	def _registerSubObject(self,k,v):
		"""
		This version of _registerSubObject just passes the call up to the parent
		"""
		if self._up:
			self._up._registerSubObject(k,v)

			
	def _findSignals(self):
		"""
		Dynamically find any signals exposed by the class and keep a list of them in _signals
		
		Used for quickly auto-connecting signals to named C{on...} event handlers. Signals found are cached in C{singalsCache}
		"""
		self._signals = {}
		for parent in self.__class__.__bases__:
			if parent not in signalsCache:
				signals = {}
				for k in dir(parent):
					v = getattr(parent,k)
					if isinstance(v,QtCore.Signal):
						signals[k] = v
				signalsCache[parent] = signals

			self._signals.update(signalsCache[parent])
		

	@property
	def app(self):
		if isinstance(self,QtGui.QApplication):
			return self
		else:
			return self._up.app
		
		
	def init(self):
		""" Placeholder for user-defined initialisation functions """
		pass
		

		
class BaseWidget(BaseInstantiable):
	"""
	Mixin class for all PySide widgets to be used with PySideLine
	"""	
	
	pass
		
		
			
	
class BaseLayout(BaseInstantiable):
	"""
	Mixin class for all PySide layouts to be used with PySideLine
	"""	
	def init(self,*args,**kargs):
		self._up.setLayout(self)
		
	
	
class BaseDialog(BaseWidget):

	def __init__(self,*args,**kargs):
		super(BaseDialog,self).__init__(*args,**kargs)
		

class BaseRootInstantiable(BaseInstantiable):

	def __init__(self,*args,**kargs):
		self._subObjects = {}
		super(BaseRootInstantiable,self).__init__(*args,**kargs)
		
		
	def _registerSubObject(self,k,v):
		""" 
		Register a child object of this object so that it appears in the app-level namespace (used as a shortcut for accessing deeply nested widgets)
		"""
		self._subObjects[k] = v
		parent = self.parent()
		if parent is not None:
			parent._registerSubObject(k,v)

			
	def __getattr__(self,k):
		""" This maps all objects defined under the application to the applications namespace 
		
		It's designed to do away with long chains of attribute access like C{app.mywindow.mytabs.mytab.mygroup.mycontrol}
		"""
		if k in self._subObjects:
			return self._subObjects[k]
		else:
			raise AttributeError(k)



class Application(BaseRootInstantiable,QtGui.QApplication):
	"""
	A main application
	
	The Application class does a bit of contorsion to ensure that the init methods of all the classes get executed 
	within the main GUI thread and after the QApplication has been initialised. This makes it easier to do startup tasks that
	e.g. need to popup dialogue boxes etc. on failuer.  
	"""
	
	def __init__(self,*args,**kargs):
		self._subObjects = {}
		self._up = None
		QtGui.QApplication.__init__(self,*args,**kargs)
		QtCore.QTimer.singleShot(0,self._on_startup)
		
	def _on_startup(self):
		toInit = self._autoInstantiate()
		for o in toInit:
			o.init()
		self.init()

