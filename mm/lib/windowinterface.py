import os

if os.environ.has_key('CMIF_USE_DUMMY'):
	from dummy_window import *
elif os.name == 'mac':
	from mac_window import *
elif os.name == 'nt':
	from WIN32_window import *
elif os.environ.has_key('CMIF_USE_GL'):
	from GL_window import *
else:
	try:
		import Xlib, Xt, Xm
	except ImportError:
		import sys
		sys.last_traceback = None
		sys.exc_traceback = None
		try:
			import gl, fm
		except ImportError:
			raise ImportError, 'No module named windowinterface'
		from GL_window import *
	else:
		from X_window import *
