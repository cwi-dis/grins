# Main program for the CMIF editor.

def main():
	import sys
	import getopt
	#
	usage = '[-pqsnTHPSL] [-h helpdir] [file.cmif]'
	#
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'qpsnh:THPSL')
	except getopt.error, msg:
		sys.stderr.write(msg + '\n')
		sys.stderr.write('usage: cmifed ' + usage + '\n')
		sys.exit(2)
	#
	if ('-q', '') in opts:
		sys.stdout = open('/dev/null', 'w')
	#
	if args:
		if len(args) > 1:
			sys.stderr.write('Warning: only one filename used\n')
		filename = args[0]
	else:
		filename = 'demo.cmif'
	#
	try:
		# Make sure the file exists first...
		f = open(filename, 'r')
		f.close()
	except IOError:
		sys.stderr.write(filename + ': cannot open\n')
		sys.exit(2)
	#
	# patch the module search path
	# so we are less dependent on where we are called
	#
	sys.path.append(findfile('mm4'))
	sys.path.append(findfile('lib'))
	sys.path.append(findfile('video'))
	#
	import TopLevel
	import SoundChannel
	import ImageChannel
	import Channel
	#
	playnow = 0
	stats = 0
	#
	for opt, arg in opts:
		if opt == '-p':
			playnow = 1
		elif opt == '-s':
			stats = 1
		elif opt == '-n':
			Channel.disable_prearm()
		elif opt == '-h':
			TopLevel.sethelpdir(arg)
	#
	top = TopLevel.TopLevel().init(filename)
	#
	top.show()
	#
	for opt, arg in opts:
		if opt == '-T':
			top.channelview.show()
		elif opt == '-H':
			top.blockview.show()
		elif opt in ('-P', '-p'):
			top.player.show()
		elif opt == '-S':
			top.styleview.show()
		elif opt == '-L':
			top.links.show()
	#
	top.checkviews()
	#
	try:
		try:
			if playnow:
				top.player.playsubtree(top.root)
			if sys.__dict__.has_key('mdebug'):
				import os
				if os.environ.has_key('MDEBUG'):
					flag = eval(os.environ['MDEBUG'])
					print 'mallopt( M_DEBUG,', flag, ')'
					sys.mdebug(flag)
			top.run()
			# Actually, this point isn't reached
			top.destroy()
		except KeyboardInterrupt:
			print 'Interrupt.'
		except SystemExit, sts:
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
