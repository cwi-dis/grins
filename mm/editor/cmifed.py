__version__ = "$Id$"

# Main program for the CMIF editor.

import sys
import os

try:
	sys.path.remove('')
except:
	pass

if os.name != 'mac' and __file__ != '<frozen>':
	import fastimp
	fastimp.install()


import getopt

def usage(msg):
	sys.stdout = sys.stderr
	print msg
	print 'usage: cmifed [-qpsnTHPSL] [-h helpdir] file ...'
	print '-q         : quiet (don\'t print anything to stdout)'
	print '-p         : start playing right away'
	print '-j name    : start playing at given global anchor'
	print '-s         : report statistics (guru only)'
	print '-n         : no pre-arming (guru only)'
	print '-C         : open Channel view right away'
	print '-H         : open Hierarchy view right away'
	print '-P         : open Player window right away'
##	print '-S         : open Style sheet window right away'
	print '-L         : open Hyperlinks window right away'
	print '-h helpdir : specify help directory'
	print 'file ...   : one or more CMIF files'
	sys.exit(2)

from MainDialog import MainDialog

class Main(MainDialog):
	def __init__(self, opts, files):
		self._tracing = 0
		from MMExc import MSyntaxError
		self.tops = []
		self._mm_callbacks = {}
		try:
			import mm, posix, fcntl, FCNTL
		except ImportError:
			pass
		else:
			import windowinterface
			pipe_r, pipe_w = posix.pipe()
			mm.setsyncfd(pipe_w)
			self._mmfd = pipe_r
			windowinterface.select_setcallback(pipe_r,
						self._mmcallback,
						(posix.read, fcntl.fcntl, FCNTL))
		MainDialog.__init__(self, 'CMIFed')
		for file in files:
			self.open_callback(file)

	def new_callback(self):
		import TopLevel
		top = TopLevel.TopLevel(self, 'NEW-DOCUMENT.cmif', 1)
		self.new_top(top)

	def open_callback(self, url):
		import TopLevel
		try:
			top = TopLevel.TopLevel(self, url, 0)
		except IOError:
			import windowinterface
			windowinterface.showmessage('error opening URL %s' % url)
		else:
			self.new_top(top)
		
	def close_callback(self):
		self.do_exit()

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

	def new_top(self, top):
		top.setwaiting()
		top.show()
		top.checkviews()
		self.tops.append(top)
		top.setready()

	def do_exit(self, *args):
		for top in self.tops[:]:
			top.close()
		if not self.tops:
			raise SystemExit, 0

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

	def save(self):
		# this is a debug method.  it can be used after a
		# crash to save the documents being edited.
		for top in self.tops:
			nf = top.new_file
			top.new_file = 0
			ok = top.save_callback()
			top.new_file = nf

def handler(sig, frame):
	import pdb
	pdb.set_trace()

def main():
	import os
	os.environ['CMIF_USE_X'] = '1'
	try:
		opts, files = getopt.getopt(sys.argv[1:], 'qpj:snh:CHPSL')
	except getopt.error, msg:
		usage(msg)
	try:
		import splash
	except ImportError:
		splash = None
	else:
		splash.splash(version = 'cmifed V0.9')
	try:
		import signal, pdb
	except ImportError:
		pass
	else:
		signal.signal(signal.SIGINT, handler)

	if ('-q', '') in opts:
		sys.stdout = open('/dev/null', 'w')

	if sys.argv[0] and sys.argv[0][0] == '-':
		sys.argv[0] = 'cmifed'

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

	import mimetypes
	mimetypes.types_map['.smi'] = mimetypes.types_map['.smil'] = \
				      'application/smil'
	mimetypes.types_map['.cmif'] = 'application/x-cmif'

	import Channel
	import GLLock
	#
	stats = 0
	#
	for opt, arg in opts:
		if opt == '-s':
			stats = 1
		if opt == '-n':
			Channel.disable_prearm()
		if opt == '-h':
			import Help
			Help.sethelpdir(arg)
	#
	GLLock.init()
	import windowinterface
	windowinterface.usewindowlock(GLLock.gl_lock)

	m = Main(opts, files)

	if splash is not None:
		splash.unsplash()


	try:
		try:
			m.run()
##		except KeyboardInterrupt:
##			print 'Interrupt.'
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
			import traceback, pdb
			print
			print '\t--------------------------------------------'
			print '\t| Entering debugger -- call Sjoerd or Jack |'
			print '\t--------------------------------------------'
			print
			traceback.print_exception(exc_type, exc_value, None)
			print
			pdb.post_mortem(exc_traceback)
	finally:
		import windowinterface
		windowinterface.close()
		if stats:
			import MMNode
			MMNode._prstats()


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
			cmifpath = [DEFAULTDIR]
	for dir in cmifpath:
		fullname = os.path.join(dir, name)
		if os.path.exists(fullname):
			return fullname
	return name


# Call the main program

main()
