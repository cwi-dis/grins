__version__ = "$Id$"

# Main program for the CMIF player.

import sys
import os

try:
	sys.path.remove('')
except:
	pass

## if os.name == 'posix' and __file__ != '<frozen>':
## 	import fastimp
## 	fastimp.install()

import getopt

def usage(msg):
	sys.stdout = sys.stderr
	print msg
	print 'usage: grins file ...'
	print 'file ...   : one or more SMIL or CMIF files or URLs'
	sys.exit(2)

from MainDialog import MainDialog

from version import version

class Main(MainDialog):
	def __init__(self, opts, files):
		import MMurl, TopLevel, windowinterface
		self._tracing = 0
		self.nocontrol = 0	# For player compatability
		self._closing = 0
		self._mm_callbacks = {}
		self.tops = []
		try:
			import mm, posix, fcntl, FCNTL
		except ImportError:
			pass
		else:
			pipe_r, pipe_w = posix.pipe()
			mm.setsyncfd(pipe_w)
			self._mmfd = pipe_r
			windowinterface.select_setcallback(pipe_r,
						self._mmcallback,
						(posix.read, fcntl.fcntl, FCNTL))
		from usercmd import *
		self.commandlist = [
			OPEN(callback = (self.open_callback, ())),
			PREFERENCES(callback = (self.preferences_callback, ())),
			EXIT(callback = (self.close_callback, ())),
			]
		if __debug__:
			self.commandlist = self.commandlist + [
				TRACE(callback = (self.trace_callback, ())),
				DEBUG(callback = (self.debug_callback, ())),
				CRASH(callback = (self.crash_callback, ())),
				]
		MainDialog.__init__(self, 'GRiNS')
		# first open all files
		for file in files:
			self.openURL_callback(MMurl.guessurl(file))
		# then play them
		for top in self.tops:
			top.player.playsubtree(top.root)

	def openURL_callback(self, url):
		import windowinterface
		windowinterface.setwaiting()
		from MMExc import MSyntaxError
		import TopLevel
		try:
			top = TopLevel.TopLevel(self, url)
		except IOError:
			import windowinterface
			windowinterface.showmessage('error opening document %s' % url)
		except MSyntaxError:
			import windowinterface
			windowinterface.showmessage('parsing document %s failed' % url)
		else:
			self.tops.append(top)
			top.show()
			top.player.show()

	def close_callback(self):
		raise SystemExit, 0

	def crash_callback(self):
		raise 'Crash requested by user'

	def debug_callback(self):
		import pdb
		pdb.set_trace()

	def trace_callback(self):
		import trace
		if self._tracing:
			trace.unset_trace()
			self._tracing = 0
		else:
			self._tracing = 1
			trace.set_trace()

	def preferences_callback(self):
		import Preferences
		Preferences.showpreferences(1, self.prefschanged)

	def prefschanged(self):
		for top in self.tops:
			top.prefschanged()

	def closetop(self, top):
		if self._closing:
			return
		self._closing = 1
		self.tops.remove(top)
		top.hide()
		if len(self.tops) == 0:
			# no TopLevels left: exit
			sys.exit(0)
		self._closing = 0

	def run(self):
		import windowinterface
		windowinterface.mainloop()

	def setmmcallback(self, dev, callback):
		if callback:
			self._mm_callbacks[dev] = callback
		elif self._mm_callbacks.has_key(dev):
			del self._mm_callbacks[dev]

	def _mmcallback(self, read, fcntl, FCNTL):
		# set in non-blocking mode
		dummy = fcntl(self._mmfd, FCNTL.F_SETFL, FCNTL.O_NDELAY)
		# read a byte
		devval = read(self._mmfd, 1)
		# set in blocking mode
		dummy = fcntl(self._mmfd, FCNTL.F_SETFL, 0)
		# return if nothing read
		if not devval:
			return
		devval = ord(devval)
		dev, val = devval >> 2, devval & 3
		if self._mm_callbacks.has_key(dev):
			func = self._mm_callbacks[dev]
			func(val)
		else:
			print 'Warning: unknown device in mmcallback'

def main():
	import os
	os.environ['CMIF_USE_X'] = '1'
	try:
		opts, files = getopt.getopt(sys.argv[1:], 'qj:')
	except getopt.error, msg:
		usage(msg)
	if not files and sys.platform not in ('mac', 'win32'):
		usage('No files specified')

	if sys.argv[0] and sys.argv[0][0] == '-':
		sys.argv[0] = 'grins'

	try:
		import splash
	except ImportError:
		splash = None
	else:
		splash.splash(version = 'GRiNS ' + version)

	import Help
	if hasattr(Help, 'sethelpprogram'):
		Help.sethelpprogram('player')
		
	if ('-q', '') in opts:
		sys.stdout = open('/dev/null', 'w')
	elif __debug__:
		try:
			import signal, pdb
		except ImportError:
			pass
		else:
			signal.signal(signal.SIGINT,
				      lambda s, f, pdb=pdb: pdb.set_trace())

## 	for fn in files:
## 		try:
## 			# Make sure the files exist first...
## 			f = open(fn, 'r')
## 			f.close()
## 		except IOError, msg:
## 			import types
## 			if type(msg) is types.InstanceType:
## 				msg = msg.strerror
## 			else:
## 				msg = msg[1]
## 			sys.stderr.write('%s: cannot open: %s\n' % (fn, msg))
## 			sys.exit(2)

## 	# patch the module search path
## 	# so we are less dependent on where we are called
## 	sys.path.append(findfile('lib'))
## 	sys.path.append(findfile('video'))

	import mimetypes, grins_mimetypes
	mimetypes.types_map.update(grins_mimetypes.mimetypes)

	import Channel
	import GLLock

	GLLock.init()
	import windowinterface
	windowinterface.usewindowlock(GLLock.gl_lock)

	m = Main(opts, files)

	if splash is not None:
		splash.unsplash()

	try:
		try:
			m.run()
		except KeyboardInterrupt:
			print 'Interrupt.'
		except SystemExit, sts:
			if type(sts) is type(m):
				if sts.code:
					print 'Exit %d' % sts.code
			elif sts:
				print 'Exit', sts
			sys.last_traceback = None
			sys.exc_traceback = None
			sys.exit(sts)
		except:
			sys.stdout = sys.stderr
			if hasattr(sys, 'exc_info'):
				exc_type, exc_value, exc_traceback = sys.exc_info()
			else:
				exc_type, exc_value, exc_traceback = sys.exc_type, sys.exc_value, sys.exc_traceback
			if __debug__:
				import traceback, pdb
				print
				print '\t--------------------------------------------'
				print '\t| Entering debugger -- call Sjoerd or Jack |'
				print '\t--------------------------------------------'
				print
				traceback.print_exception(exc_type, exc_value, None)
				print
				pdb.post_mortem(exc_traceback)
			else:
				import traceback
				print
				print 'GRiNS crash, please e-mail this output to grins-support@cwi.nl:'
				traceback.print_exception(exc_type, exc_value, exc_traceback)
	finally:
		if sys.platform != 'win32':
			import windowinterface
			windowinterface.close()


# A copy of cmif.findfile().  It is copied here rather than imported
# because the result is needed to extend the Python search path to
# find the cmif module!

# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
# *********  If you change this, also change ../lib/cmif.py   ***********
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

DEFAULTDIR = '/ufs/guido/mm/demo'	# Traditional default

cmifpath = None

def findfile(name):
	global cmifpath
	import os
	if os.path.isabs(name):
		return name
	if cmifpath is None:
		if os.environ.has_key('CMIFPATH'):
			import string
			var = os.environ['CMIFPATH']
			cmifpath = string.splitfields(var, ':')
		elif os.environ.has_key('CMIF'):
			cmifpath = [os.environ['CMIF']]
		else:
			import sys
			cmifpath = [os.path.split(sys.executable)[0],
				    DEFAULTDIR]
	for dir in cmifpath:
		fullname = os.path.join(dir, name)
		if os.path.exists(fullname):
			return fullname
	return name


# Call the main program

main()
