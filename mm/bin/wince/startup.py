
# Global Application Objects
if __name__ == '__main__':
	toplevel = None
	resdll = None
else:
	import __main__
	__main__.toplevel = None
	__main__.resdll = None
	
##################### Main Script
import os
import sys
orgpath = repr(sys.path)

GRINSDIR = r'\Program Files\GRiNS'

specificPath = "grins"

GRINSPATH = [
	os.path.join(GRINSDIR, 'lib\\wince'), # override folder
#	os.path.join(GRINSDIR, 'bin\\wince'), # bin (set by exe)

	os.path.join(GRINSDIR, '%s\\smil20\\win32' % specificPath),
	os.path.join(GRINSDIR, '%s\\smil20' % specificPath),
	os.path.join(GRINSDIR, '%s\\wince' % specificPath),
	os.path.join(GRINSDIR, '%s\\win32' % specificPath),
	os.path.join(GRINSDIR, '%s' % specificPath),

#	os.path.join(GRINSDIR, 'common\\win32'),

	os.path.join(GRINSDIR, 'common'),
	os.path.join(GRINSDIR, 'lib'),
	os.path.join(GRINSDIR, 'pylib'),
]

sys.path[0:0] = GRINSPATH


import grinsNL_CE	

