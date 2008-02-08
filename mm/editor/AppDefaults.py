__version__ = "$Id$"

import settings
import windowinterface

hierarchy_minimum_sizes = settings.get('hierarchy_minimum_sizes')
root_expanded = settings.get('root_expanded')
structure_name_size = settings.get('structure_name_size')
show_links = settings.get('show_links')

vertical_spread = settings.get('vertical_spread')

# Fonts used
f_title = windowinterface.findfont('Helvetica', 10)
f_channel = windowinterface.findfont('Helvetica', 8)
f_timescale = f_channel
FONTTWEAK = 2                           # potentially system-dependant vertical tweak of fonts
                                        # this is used to vertically center text

TICKDIST = settings.get('structure_tickdistance')

# Color assignments (RGB)
BGCOLOR = settings.get('structure_bgcolor')
LEAFCOLOR = settings.get('structure_leafcolor')
RPCOLOR = settings.get('structure_rpcolor')
SLIDECOLOR = settings.get('structure_slidecolor')
ALTCOLOR = settings.get('structure_altcolor')
PARCOLOR = settings.get('structure_parcolor')
SEQCOLOR = settings.get('structure_seqcolor')
EXCLCOLOR = settings.get('structure_exclcolor')
PRIOCOLOR = settings.get('structure_priocolor')
COMMENTCOLOR = settings.get('structure_commentcolor')
TEXTCOLOR = settings.get('structure_textcolor')
CTEXTCOLOR = settings.get('structure_ctextcolor')
EXPCOLOR = settings.get('structure_expcolor')
COLCOLOR = settings.get('structure_colcolor')
FILLCOLOR = settings.get('structure_fillcolor')
FREEZECOLOR = settings.get('structure_freezecolor')
REPEATCOLOR = settings.get('structure_repeatcolor')
TRUNCCOLOR = settings.get('structure_trunccolor')
ECBORDERCOLOR = settings.get('structure_ecbordercolor')
FOREIGNCOLOR = settings.get('structure_foreigncolor')

LEAFCOLOR_NOPLAY = settings.get('structure_darkleaf')
RPCOLOR_NOPLAY = settings.get('structure_darkrp')
SLIDECOLOR_NOPLAY = settings.get('structure_darkslide')
ALTCOLOR_NOPLAY = settings.get('structure_darkalt')
PARCOLOR_NOPLAY = settings.get('structure_darkpar')
SEQCOLOR_NOPLAY = settings.get('structure_darkseq')
EXCLCOLOR_NOPLAY = settings.get('structure_darkexcl')
PRIOCOLOR_NOPLAY = settings.get('structure_darkprio')
FOREIGNCOLOR_NOPLAY = settings.get('structure_darkforeign')

# Bandwidth colors
BANDWIDTH_FREE_COLOR = settings.get('structure_bandwidthfree')
BANDWIDTH_OK_COLOR = settings.get('structure_bandwidthok')
BANDWIDTH_NOTOK_COLOR = settings.get('structure_bandwidthnotok')
BANDWIDTH_MAYBEOK_COLOR = settings.get('structure_bandwidthmaybeok')
BANDWIDTH_OKFOCUS_COLOR = settings.get('structure_bandwidthokfocus')
BANDWIDTH_NOTOKFOCUS_COLOR = settings.get('structure_bandwidthnotokfocus')
BANDWIDTH_MAYBEOKFOCUS_COLOR = settings.get('structure_bandwidthmaybeokfocus')
# Timeline colors for stalls
BWPREROLLCOLOR = settings.get('structure_bwprerollcolor')
BWMAYSTALLCOLOR = settings.get('structure_bwmaystallcolor')
BWSTALLCOLOR = settings.get('structure_bwstallcolor')

# Focus color assignments (from light to dark gray)

FOCUSLEFT = settings.get('structure_focusleft')
FOCUSTOP = settings.get('structure_focustop')
FOCUSRIGHT = settings.get('structure_focusright')
FOCUSBOTTOM = settings.get('structure_focusbottom')

DROPCOLOR = settings.get('structure_dropcolor')

SIZEUNIT = windowinterface.UNIT_PXL # units for the following
MINSIZE = 48
MAXSIZE = 128
TITLESIZE = int(f_title.fontheightPXL())
if TITLESIZE < windowinterface.ICONSIZE_PXL:
    TITLESIZE = windowinterface.ICONSIZE_PXL
CHNAMESIZE = 0
LABSIZE = TITLESIZE+CHNAMESIZE          # height of labels
HOREXTRASIZE = f_title.strsizePXL('XX')[0]
ARRSIZE = windowinterface.ICONSIZE_PXL  # width of collapse/expand arrow
ERRSIZE = windowinterface.ICONSIZE_PXL  # width of error/bandwidth indicator

MIN_PXL_PER_SEC_DEFAULT = 0

GAPSIZE = 4 #2                                          # size of gap between nodes
HEDGSIZE = 4 #3                                         # size of edges
VEDGSIZE = 4 #3                                         # size of edges
DRAGHANDLESIZE = 4
TRUNCSIZE = 4
DROPAREASIZE = 32               # size of the decoration at the end of a "roll of film"
FLATBOX = 0
TIMEBARHEIGHT = 0
DROPAREA = MINSIZE + HOREXTRASIZE
MINTHUMBX = 24
MINTHUMBY = 24

#
# We expand a number of hierarchy levels on first open. The number
# given here is the number of _nodes_ we minimally want to open.
# We (of course) continue to open all nodes on the same level.
#
NODES_WANTED_OPEN = 7

# Box types

ANCESTORBOX = 0
INNERBOX = 1
LEAFBOX = 2
