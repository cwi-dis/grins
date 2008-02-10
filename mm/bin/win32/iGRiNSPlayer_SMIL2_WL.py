# Run player using Pythonwl.exe and light weightframework

# Global Application Objects
toplevel = None
resdll = None

##################### Main Script
import os
import sys

def GuessCMIFRoot():
    try:
        # hopefully we can import this
        import win32api
    except ImportError:
        pass
    else:
        selfDir = win32api.GetFullPathName(os.path.join(os.path.split(sys.argv[0])[0], "." ))
        l = selfDir.split('\\')
        dir = ''
        for s in l:
            dir = dir + s
            for sub in ('editor','grins','common','lib'):
                if not os.path.exists(os.path.join(dir, sub)):
                    break
            else:
                return dir
            dir = dir + '\\'
    return r'D:\ufs\mm\cmif'        # default, in case we can't find the directory dynamically

CMIFDIR = GuessCMIFRoot()

specificPath = "grins"

CMIFPATH = [
        os.path.join(CMIFDIR, r'win32\Boost\Bridge\wintk'), # override lib\win32

        os.path.join(CMIFDIR, r'bin\win32'),
        os.path.join(CMIFDIR, r'%s\smil20\win32' % specificPath),
        os.path.join(CMIFDIR, r'%s\smil20' % specificPath),
        os.path.join(CMIFDIR, r'%s\win32' % specificPath),
        os.path.join(CMIFDIR, r'common\win32'),
        os.path.join(CMIFDIR, r'%s' % specificPath),
        os.path.join(CMIFDIR, r'common'),
        os.path.join(CMIFDIR, r'lib'),
        os.path.join(CMIFDIR, r'pylib'),
        os.path.join(CMIFDIR, r'win32\src\Build'),
        os.path.join(os.path.split(CMIFDIR)[0], r'python\Lib')
]

sys.path[0:0] = CMIFPATH

from version import dllname
import winkernel
dllPath = os.path.split(winkernel.__file__)[0]
dllPath = os.path.join(dllPath, dllname)
resdll = winkernel.LoadLibrary(dllPath)

import grinsp
