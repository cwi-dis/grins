# Main program for the CMIF editor.

import sys
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
	print '-S         : open Style sheet window right away'
	print '-L         : open Hyperlinks window right away'
	print '-h helpdir : specify help directory'
	print 'file ...   : one or more CMIF files'
	sys.exit(2)

class Main:
	def __init__(self, opts, files):
		import TopLevel
		self.tops = []
		self._mm_callbacks = {}
		import mm, posix
		pipe_r, pipe_w = posix.pipe()
		mm.setsyncfd(pipe_w)
		self._mmfd = pipe_r
		for fn in files:
			top = TopLevel.TopLevel().init(self, fn)
			top.setwaiting()
			top.show()
			for opt, arg in opts:
				if opt == '-C':
					top.channelview.show()
				elif opt == '-H':
					top.hierarchyview.show()
				elif opt in ('-P', '-p', '-j'):
					top.player.show()
					if opt == '-p':
						top.player.playsubtree(
							  top.root)
					if opt == '-j':
						top.player.playfromanchor(
							  top.root, arg)
				elif opt == '-S':
					top.styleview.show()
				elif opt == '-L':
					top.links.show()
			top.checkviews()
			self.tops.append(top)

		for top in self.tops:
			top.setready()

	def run(self):
		import select, gl, fl, posix, GLLock
		glfd = gl.qgetfd()
		while 1:
			locked = None
			if GLLock.gl_lock:
				GLLock.gl_lock.acquire()
				locked = 1
			result = fl.check_forms()
			if locked:
				GLLock.gl_lock.release()
			wtd = [glfd, self._mmfd]
			for top in self.tops:
				wtd = wtd + top.select_fdlist
			ifdlist, ofdlist, efdlist = select.select(
				  wtd, [], [], 0.1)
			if self._mmfd in ifdlist:
				self._mmcallback()
			for top in self.tops:
				for fd in top.select_fdlist:
					if fd in ifdlist:
						top.select_ready(fd)

	def setmmcallback(self, dev, callback):
		if callback:
			self._mm_callbacks[dev] = callback
		elif self._mm_callbacks.has_key(dev):
			del self._mm_callbacks[dev]

	def _mmcallback(self):
		import posix
		devval = ord(posix.read(self._mmfd, 1))
		dev, val = devval >> 2, devval & 3
		if self._mm_callbacks.has_key(dev):
			func = self._mm_callbacks[dev]
			func(val)
		else:
			print 'Warning: unknown device in mmcallback'

def main():
	#
	try:
		opts, files = getopt.getopt(sys.argv[1:], 'qpj:snh:CHPSL')
	except getopt.error, msg:
		usage(msg)
	if not files:
		usage('No files specified')
	#
	if ('-q', '') in opts:
		sys.stdout = open('/dev/null', 'w')
	#
	for fn in files:
		try:
			# Make sure the files exist first...
			f = open(fn, 'r')
			f.close()
		except IOError, msg:
			sys.stderr.write(fn + ': cannot open ' + `msg` + '\n')
			sys.exit(2)
	#
	# patch the module search path
	# so we are less dependent on where we are called
	#
	sys.path.append(findfile('mm4'))
	sys.path.append(findfile('lib'))
	sys.path.append(findfile('video'))
	#
	import fl
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

	try:
		try:
			m.run()
##		except KeyboardInterrupt:
##			print 'Interrupt.'
		except SystemExit, sts:
			if sts:
				print 'Exit', sts
			sys.last_traceback = None
			sys.exc_traceback = None
			sys.exit(sts)
		except:
			sys.stdout = sys.stderr
			print
			print '\t-------------------------------------------'
			print '\t| Entering debugger -- call Guido or Jack |'
			print '\t-------------------------------------------'
			print
			print '\t' + sys.exc_type + ':', `sys.exc_value`
			print
			import pdb
			pdb.post_mortem(sys.exc_traceback)
	finally:
##		SoundChannel.restore()
##		ImageChannel.cleanup()
		#
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
	if cmifpath == None:
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
