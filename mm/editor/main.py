# Integration -- main program for testing

import gl
gl.foreground()
import sys
from MMExc import *
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
	top.run()

try:
	main()
	status = 0
except ExitException, status:
	if status <> 0: print 'Exit status', status
except KeyboardInterrupt:
	print 'Interrupt.'
	status = 1
finally:
	SoundChannel.restore()

sys.exit(status)
