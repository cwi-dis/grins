__version__ = "$Id"

CMIF = 1
SMIL = 2
DBG = 4
ALL = (CMIF|SMIL|DBG)

def curflags():
	import settings
	flags = SMIL		# always enabled
	if settings.get('cmif'):
		flags = flags | CMIF
	if settings.get('debug'):
		flags = flags | DBG
	return flags
