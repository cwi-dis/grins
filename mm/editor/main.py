# Main program for the CMIF editor

import sys
import MMExc
import TopLevel
import SoundChannel

def main():
	if sys.argv[1:]:
		filename = sys.argv[1]
	else:
		filename = 'demo.cmif'
	#
	top = TopLevel.TopLevel().init(filename)
	top.show()
	#
	try:
		top.run()
		top.destroy()
		status = 0
	except MMExc.ExitException, status:
		if status <> 0: print 'Exit status', status
	except KeyboardInterrupt:
		print 'Interrupt.'
		status = 1
	finally:
		SoundChannel.restore()
	#
	sys.exit(status)

main()
