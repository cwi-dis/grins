# Run player using Pythonwl.exe and light weightframework

# Global Application Objects
toplevel = None
resdll = None

##################### Main Script
import os
import sys
	
CMIFDIR = r'd:\ufs\mm\cmif'

specificPath = "grins"

CMIFPATH = [
	os.path.join(CMIFDIR, 'win32\\Boost\\Bridge\\wintk'), # override lib\win32

	os.path.join(CMIFDIR, 'bin\\win32'),
	os.path.join(CMIFDIR, '%s\\smil20\\win32' % specificPath),
	os.path.join(CMIFDIR, '%s\\smil20' % specificPath),
	os.path.join(CMIFDIR, '%s\\win32' % specificPath),
	os.path.join(CMIFDIR, 'common\\win32'),
	os.path.join(CMIFDIR, '%s' % specificPath),
	os.path.join(CMIFDIR, 'common'),
	os.path.join(CMIFDIR, 'lib'),
	os.path.join(CMIFDIR, 'pylib'),
	os.path.join(CMIFDIR, 'win32\\src\\Build'),
	os.path.join(os.path.split(CMIFDIR)[0], 'python\\Lib')
]

sys.path[0:0] = CMIFPATH

import winkernel
dllPath = os.path.split(winkernel.__file__)[0]
dllPath = os.path.join(dllPath, 'GRiNSRes.dll')
resdll = winkernel.LoadLibrary(dllPath)

import grinsp

