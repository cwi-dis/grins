# Main program for the CMIF editor

import sys
sys.path.append('/ufs/guido/mm/demo/mm4')
sys.path.append('/ufs/guido/mm/demo/lib')

import MMExc
import TopLevel
import SoundChannel
import getopt
import image

def main():
	playnow = 0
	stats = 0
	opts, args = getopt.getopt(sys.argv[1:], 'ps')
	for opt, arg in opts:
		if opt = '-p':
			playnow = 1
		elif opt = '-s':
			stats = 1
	if args:
		filename = args[0]
	else:
		filename = 'demo.cmif'
	#
	top = TopLevel.TopLevel().init(filename)
	top.show()
	#
	try:
		if playnow:
			top.player.playsubtree(top.root)
		top.run()
		top.destroy()
	except MMExc.ExitException, status:
		if status <> 0: print 'Exit status', status
	except KeyboardInterrupt:
		print 'Interrupt.'
	finally:
		try:
			SoundChannel.restore()
		finally:
			image.zapcache()
	#
	if stats:
		import MMNode
		MMNode._prstats()


# Special hack to enter an interactive debugger.
# This only works if you use a special Python binary
# (~guido/bin/sgi/python).
#
idebug = 0
try:
	1/0
except:
	if sys.__dict__.has_key('exc_traceback'):
		idebug = 1
		import tb

if not idebug:
	main()
else:
	try:
		main()
	except:
		if idebug:
			msg = sys.exc_type + ': ' + `sys.exc_value`
			print 'Exception:', msg
			tb.printtb(sys.exc_traceback)
			print 'Exception: ', msg
			tb.browser(sys.exc_traceback)
