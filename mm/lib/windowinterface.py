import sys

has_gl = 0
try:
	import gl, fm
	has_gl = 1
except ImportError:
	sys.last_traceback = None
	sys.exc_traceback = None
	try:
		import Xlib, Xt, Xm
	except ImportError:
		raise ImportError, 'No module named windowinterface'
	from X_windowinterface import *
if has_gl:
	from GL_windowinterface import *
del has_gl
