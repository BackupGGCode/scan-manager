"""
Base objects/settings common to most modules

Modules will usually import this early on via an "import *" to provide basic functionality/settings
"""

import os.path

class NODEFAULT:
	"""
	Used in keyword argument lists so we can detect whether a keyword argument was supplied by doing::
	
		myArg is not NODEFAULT
		
	(The usual C{def f(x=None): ...} can't easily distinguish f(None) and f().)
	    
	"""
	pass


	
class ScanManagerError(Exception):
	pass


	
class Enum(object):
	
	def __iter__(self):
		for k,v in self.__dict__.items():
			yield (k,v)
	
	
	def __getitem__(self,i):
		for k,v in self.__dict__.items():
			if v == i:
				return k
		else:
			raise KeyError(i)


class BaseSettings(object):
	def __init__(self,**kargs):
		self.__dict__.update(kargs)
	def __getitem__(self,k):
		return self.__dict__[k]
	def __setitem__(self,k,v):
		self.__dict__[k] = v
	def __contains__(self,k):
		return k in self.__dict__
			
			
def indent(s,prefix='  ',stripInitialWhitespace=False):
	"""
	Indent a multi-line text string, optionally removing a common whitespace prefix
	
	@param s: the string to indent
	@param prefix: the indentation to add (usually some spaces or a tab character)
	@param stripInitialWhitespace: if C{True} we will try to find a common whitespace prefix for all the lines
		and if we find one, remove it (blank/whitespace-only lines are not considered for this so they
		won't prevent a prefix common to all non-blank/white lines from being removed)
	@return: the indented string  
	"""
	lines = s.split('\n')
	nonblank = [line for line in lines if line.strip()]
	toStrip = 0

	if stripInitialWhitespace:
		for x in range(1,len(s)+1):
			common = nonblank[0][:x]
			if [i for i in common if i not in ' \t']:
				# break out if there are non-whitespace characters in the common prefix
				break
			for line in lines:
				if not line.strip():
					continue # ignore blank lines
				if not line.startswith(common):
					break
			else:
				toStrip = x
				continue
			break
		
		out = []
		for line in lines:
			if line.strip():
				out.append(prefix + line[toStrip:])
			else:
				out.append(prefix + line)
		
		return '\n'.join(out)
	else:
		return '\n'.join([prefix+line for line in lines]) 


def smBasePath():
	"""
	Get the home path of the installed application
	"""
	path = os.path.join(os.path.split(__file__)[:-1])[0]
	while path.endswith('.zip') or path.endswith('.exe'): 
		# this is present if the python package has been converted to an exe with cx_Freeze  
		path = os.path.join(os.path.split(path)[:-1])[0]
	return path
