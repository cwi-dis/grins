__version__ = "$Id$"

import sys, imgformat, mkimg

if len(sys.argv) != 2:
    print 'Usage:',sys.argv[0] or 'python mksplash.py','img-file'
    sys.exit(1)

mkimg.mkimg(sys.argv[1], imgformat.bmprgbbe_noalign)
