__version__ = "$Id$"

#
# Create attrdefs resource file
#
import os
import sys
import string
import macfs
import Res
import py_resource

# For now:
progdir=os.path.split(sys.argv[0])[0]
CMIFDIR=os.path.split(progdir)[0]

ATTRDEFPATH = CMIFDIR + ':lib:Attrdefs.atc'

fp = open(ATTRDEFPATH, 'rb')
data = fp.read()
fp.close()

fss, ok = macfs.StandardPutFile('Attrdef resource output file:')
if not ok: sys.exit(0)

fsid = py_resource.create(fss.as_pathname(), creator='RSED')

py_resource.writemodule('Attrdefs', 512, data, 'CMat')

Res.CloseResFile(fsid)
print 'Wrote', ATTRDEFPATH, 'to', fss.as_pathname()
sys.exit(1)
