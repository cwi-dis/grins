# Integration -- main program for testing

import gl
gl.foreground()
import sys
from MMExc import *
import TopLevel

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
except ExitException, status:
	if status <> 0: print 'Exit status', status
	sys.exit(status)
except KeyboardInterrupt:
	print 'Interrupt.'
	sys.exit(1)
