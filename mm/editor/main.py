# Main program for the CMIF editor

import sys
sys.path.append('/ufs/guido/mm/demo/mm4')
sys.path.append('/ufs/guido/mm/demo/lib')

import MMExc
import TopLevel
import SoundChannel
import getopt
import Channel

def main():
	playnow = 0
	stats = 0
	noarm = 0
	opts, args = getopt.getopt(sys.argv[1:], 'psn')
	for opt, arg in opts:
		if opt == '-p':
			playnow = 1
		elif opt == '-s':
			stats = 1
		elif opt == '-n':
			noarm = 1
	if args:
		filename = args[0]
	else:
		filename = 'demo.cmif'
	#
	if noarm:
		Channel.disable_prearm()
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
			pass
	#
	if stats:
		import MMNode
		MMNode._prstats()

main()
