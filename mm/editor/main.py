__version__ = "$Id$"

# Main program for the CMIF editor.

import sys

try:
	sys.path.remove('')
except:
	pass

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

class Main:
	def __init__(self, opts, files):
		import TopLevel, windowinterface
		self.tops = []
		self._mm_callbacks = {}
		try:
			import mm, posix
		except ImportError:
			pass
		else:
			pipe_r, pipe_w = posix.pipe()
			mm.setsyncfd(pipe_w)
			self._mmfd = pipe_r
			windowinterface.select_setcallback(pipe_r,
						self._mmcallback, ())
		new_file = 0
		if not files:
			files = ['NEW-DOCUMENT.cmif']
			new_file = 1
		for fn in files:
			top = TopLevel.TopLevel(self, fn, new_file)
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
##				elif opt == '-S':
##					top.styleview.show()
				elif opt == '-L':
					top.links.show()
			top.checkviews()
			self.tops.append(top)

		for top in self.tops:
			top.setready()

	def do_exit(self, *args):
		for top in self.tops:
			top.close()

	def run(self):
		import windowinterface
		windowinterface.mainloop()

	def setmmcallback(self, dev, callback):
		if callback:
			self._mm_callbacks[dev] = callback
		elif self._mm_callbacks.has_key(dev):
			del self._mm_callbacks[dev]

	def _mmcallback(self):
		import posix, fcntl, FCNTL
		# set in non-blocking mode
		dummy = fcntl.fcntl(self._mmfd, FCNTL.F_SETFL, FCNTL.O_NDELAY)
		# read a byte
		devval = posix.read(self._mmfd, 1)
		# set in blocking mode
		dummy = fcntl.fcntl(self._mmfd, FCNTL.F_SETFL, 0)
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
			ok = top.save_to_file(top.filename)

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
		import signal, pdb
	except ImportError:
		pass
	else:
		signal.signal(signal.SIGINT, handler)

	if ('-q', '') in opts:
		sys.stdout = open('/dev/null', 'w')

	if sys.argv[0] and sys.argv[0][0] == '-':
		sys.argv[0] = 'cmifed'

	for fn in files:
		try:
			# Make sure the files exist first...
			f = open(fn, 'r')
			f.close()
		except IOError, msg:
			sys.stderr.write(fn + ': cannot open ' + `msg` + '\n')
			sys.exit(2)

	# patch the module search path
	# so we are less dependent on where we are called
	sys.path.append(findfile('lib'))
	sys.path.append(findfile('video'))

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
			print '\t--------------------------------------------'
			print '\t| Entering debugger -- call Sjoerd or Jack |'
			print '\t--------------------------------------------'
			print
			print '\t' + str(sys.exc_type) + ':', `sys.exc_value`
			print
##			import os
##			sts = os.system('/ufs/guido/bin/playaudio /ufs/guido/lib/woowoo &')
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
