import sys, os

if os.environ.has_key('CMIF_USE_X'):
	from X_windowinterface import *
else:
	try:
		import gl, fm
	except ImportError:
		sys.last_traceback = None
		sys.exc_traceback = None
		try:
			import Xlib, Xt, Xm
		except ImportError:
			raise ImportError, 'No module named windowinterface'
		from X_windowinterface import *
	else:
		from GL_windowinterface import *
