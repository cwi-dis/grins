# Main program for the CMIF editor.

def main():
	import sys
	import getopt
	#
	usage = '[-psnTHPSL] [-h helpdir] [file.cmif]'
	#
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'psnh:THPSL')
	except getopt.error, msg:
		sys.stderr.write(msg + '\n')
		sys.stderr.write('usage: cmifed ' + usage + '\n')
		sys.exit(2)
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
			top.run()
			top.destroy()
		except KeyboardInterrupt:
			print 'Interrupt.'
	finally:
		SoundChannel.restore()
		ImageChannel.cleanup()
		#
		if stats:
			import MMNode
			MMNode._prstats()

def findfile(name):
	import os
	if os.environ.has_key('CMIF'):
		CMIF = os.environ['CMIF']
	else:
		CMIF = '/ufs/guido/mm/demo' # Traditional default
	return os.path.join(CMIF, name)

main()
