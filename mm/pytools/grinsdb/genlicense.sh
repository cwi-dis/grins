#!/bin/sh
PYTHON=/ufs/jack/bin/sgi/python
SCRIPTDIR=/ufs/jack/src/mm/pytools/grinsdb/src
DATABASE=/ufs/mm/clients
$PYTHON $SCRIPTDIR/grlicense.py -E -d +31 -o $DATABASE/.evallicense
