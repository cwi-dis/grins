import os

if os.environ.has_key('CMIF_USE_DUMMY'):
	from dummy_window import *
elif os.environ.has_key('CMIF_USE_X'):
	from X_window import *
elif os.name == 'mac':
	from mac_window import *
else:
	try:
		import gl, fm
	except ImportError:
		import sys
		sys.last_traceback = None
		sys.exc_traceback = None
		try:
			import Xlib, Xt, Xm
		except ImportError:
			raise ImportError, 'No module named windowinterface'
		from X_window import *
	else:
		from GL_window import *
