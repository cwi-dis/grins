# Main program for the CMIF editor.

import sys
import getopt

gl_lock = None				# global graphics lock

def usage(msg):
	sys.stdout = sys.stderr
	print msg
	print 'usage: cmifed [-qpsnTHPSL] [-h helpdir] file ...'
	print '-q         : quiet (don\'t print anything to stdout)'
	print '-p         : start playing right away'
	print '-s         : report statistics (guru only)'
	print '-n         : no pre-arming (guru only)'
	print '-T         : open Time chart window right away'
	print '-H         : open Hierarchy window right away'
	print '-P         : open Player window right away'
	print '-S         : open Style sheet window right away'
	print '-L         : open Hyperlinks window right away'
	print '-h helpdir : specify help directory'
	print 'file ...   : one or more CMIF files'
	sys.exit(2)

def main():
	#
	try:
		opts, files = getopt.getopt(sys.argv[1:], 'qpsnh:THPSL')
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
	import TopLevel
	import SoundChannel
	import ImageChannel
	import Channel
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
	import thread
	global gl_lock
	gl_lock = thread.allocate_lock()
	tops = []
	for fn in files:
		top = TopLevel.TopLevel().init(fn)
		top.setwaiting()
		top.show()
		for opt, arg in opts:
			if opt == '-T':
				top.channelview.show()
			elif opt == '-H':
				top.hierarchyview.show()
			elif opt in ('-P', '-p'):
				top.player.show()
				if opt == '-p':
					top.player.playsubtree(top.root)
			elif opt == '-S':
				top.styleview.show()
			elif opt == '-L':
				top.links.show()
		top.checkviews()
		tops.append(top)
	#
	for top in tops:
		top.setready()
	#
	try:
		try:
			import select, gl, fl
			glfd = gl.qgetfd()
			while 1:
				locked = None
				if gl_lock:
					gl_lock.acquire()
					locked = 1
				result = fl.check_forms()
				if locked:
					gl_lock.release()
				ifdlist, ofdlist, efdlist = select.select([glfd], [], [], 0.1)
##			fl.do_forms()
			# This point isn't reached
			raise RuntimeError, 'unexpected do_forms return'
		except KeyboardInterrupt:
			print 'Interrupt.'
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
		SoundChannel.restore()
		ImageChannel.cleanup()
		#
		if stats:
			import MMNode
			MMNode._prstats()


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
			cmifpath = ['/ufs/guido/mm/demo'] # Traditional default
	for dir in cmifpath:
		fullname = os.path.join(dir, name)
		if os.path.exists(fullname):
			return fullname
	return name

main()
