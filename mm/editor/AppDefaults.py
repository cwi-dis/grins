__version__ = "$Id$";

import settings;
import windowinterface;
import features;

hierarchy_minimum_sizes = settings.get('hierarchy_minimum_sizes')
root_expanded = settings.get('root_expanded')
structure_name_size = settings.get('structure_name_size')
show_links = settings.get('show_links')

# Fonts used 
f_title = windowinterface.findfont('Helvetica', 10)
f_channel = windowinterface.findfont('Helvetica', 8)
f_timescale = f_channel

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
FREEZECOLOR = settings.get('structure_freezecolor')
REPEATCOLOR = settings.get('structure_repeatcolor')
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

# Focus color assignments (from light to dark gray)

FOCUSLEFT = settings.get('structure_focusleft')
FOCUSTOP = settings.get('structure_focustop')
FOCUSRIGHT = settings.get('structure_focusright')
FOCUSBOTTOM = settings.get('structure_focusbottom')

DROPCOLOR = settings.get('structure_dropcolor')

class sizes_time:
	SIZEUNIT = windowinterface.UNIT_PXL # units for the following
	MINSIZE = 48 
	MAXSIZE = 128
	TITLESIZE = int(f_title.fontheightPXL()*1.2)
	if TITLESIZE < windowinterface.ICONSIZE_PXL:
		TITLESIZE = windowinterface.ICONSIZE_PXL
	CHNAMESIZE = int(f_channel.fontheightPXL()*1.2) #0
	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
	HOREXTRASIZE = f_title.strsizePXL('XX')[0]
	ARRSIZE = windowinterface.ICONSIZE_PXL	# width of collapse/expand arrow
	ERRSIZE = windowinterface.ICONSIZE_PXL	# width of error/bandwidth indicator
	GAPSIZE = 0 #2						# size of gap between nodes
	HEDGSIZE = 0 #3						# size of edges
	VEDGSIZE = 3 #3						# size of edges
	FLATBOX = 1
	TIMEBARHEIGHT = f_timescale.strsizePXL('X')[1]*3
	DROPAREA = MINSIZE + HOREXTRASIZE

class sizes_notime:
	SIZEUNIT = windowinterface.UNIT_PXL # units for the following
	MINSIZE = 48 
	MAXSIZE = 128
	TITLESIZE = int(f_title.fontheightPXL()*1.2)
	if TITLESIZE < windowinterface.ICONSIZE_PXL:
		TITLESIZE = windowinterface.ICONSIZE_PXL
	CHNAMESIZE = 0
	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
	HOREXTRASIZE = f_title.strsizePXL('XX')[0]
	ARRSIZE = windowinterface.ICONSIZE_PXL	# width of collapse/expand arrow
	ERRSIZE = windowinterface.ICONSIZE_PXL	# width of error/bandwidth indicator

	GAPSIZE = 4 #2						# size of gap between nodes
	HEDGSIZE = 4 #3						# size of edges
	VEDGSIZE = 4 #3						# size of edges
	HANDLESIZE = 16;
	DROPAREASIZE = 32;		# size of the decoration at the end of a "roll of film"
	FLATBOX = 0
	TIMEBARHEIGHT = 0
	DROPAREA = MINSIZE + HOREXTRASIZE

##class othersizes:
##	SIZEUNIT = windowinterface.UNIT_MM # units for the following
##	MINSIZE = settings.get('thumbnail_size') # minimum size for a node
##	MAXSIZE = 2 * MINSIZE
##	TITLESIZE = f_title.fontheight()*1.2
##	CHNAMESIZE = 0
##	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
##	HOREXTRASIZE = f_title.strsize('XX')[0]
##	ARRSIZE = f_title.strsize('xx')[0]	# width of collapse/expand arrow
##	GAPSIZE = 1.0						# size of gap between nodes
##	HEDGSIZE = 1.0						# size of edges
##	VEDGSIZE = 1.0						# size of edges
##	FLATBOX = 0


##class oldsizes:
##	SIZEUNIT = windowinterface.UNIT_MM # units for the following
##	MINSIZE = settings.get('thumbnail_size') # minimum size for a node
##	MAXSIZE = 2 * MINSIZE
##	TITLESIZE = f_title.fontheight()*1.2
##	CHNAMESIZE = f_channel.fontheight()*1.2
##	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
##	HOREXTRASIZE = f_title.strsize('XX')[0]
##	ARRSIZE = f_title.strsize('xx')[0]	# width of collapse/expand arrow
##	GAPSIZE = 1.0						# size of gap between nodes
##	HEDGSIZE = 1.0						# size of edges
##	VEDGSIZE = 1.0						# size of edges
##	FLATBOX = 0

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





