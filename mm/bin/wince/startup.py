
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

GRINSDIR = r'\Program Files\GRiNS'
#PYTHONDIR = r'\Program Files\Python'

specificPath = "grins"

GRINSPATH = [
	os.path.join(GRINSDIR, r'lib\wince'), # override folder
#	os.path.join(GRINSDIR, r'bin\wince'), # bin (set by exe)

	os.path.join(GRINSDIR, r'%s\smil20\win32' % specificPath),
	os.path.join(GRINSDIR, r'%s\smil20' % specificPath),
	os.path.join(GRINSDIR, r'%s\wince' % specificPath),
	os.path.join(GRINSDIR, r'%s\win32' % specificPath),
	os.path.join(GRINSDIR, r'%s' % specificPath),

	os.path.join(GRINSDIR, r'common\wince'),

	os.path.join(GRINSDIR, r'common'),
	os.path.join(GRINSDIR, r'lib'),
	os.path.join(GRINSDIR, r'pylib'),
]

sys.path[0:0] = GRINSPATH

import grinsNL_CE	

