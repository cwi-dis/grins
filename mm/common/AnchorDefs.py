# Definition of the lay-out and types of anchor triples.
# This is separated out of AnchorEdit because it is used by many other
# modules (everything to do with following hyperlinks).

# Indices of the fields of an anchor triple:
A_ID   = 0
A_TYPE = 1
A_ARGS = 2
# XXX These cannot really be changed, much code relies on these values

# Types:
ATYPE_WHOLE  = 0	# The whole node is the anchor
ATYPE_AUTO   = 1	# Auto-firing anchor (fires when the node is done)
ATYPE_NORMAL = 2	# Normal (e.g. e box drawn in the window)
ATYPE_PAUSE  = 3	# Pausing (same plus player pauses until choice made)
# XXX ATYPE_PAUSE should be replaced by a separate 'pause' flag on the node
