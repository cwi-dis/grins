__version__ = "$Id$"

#
# Commands, player version
#

class _CommandBase:
	callback = None
	help = None
	dynamiccascade = 0
	def __init__(self, **kwargs):
		for attr, val in kwargs.items():
			setattr(self, attr, val)

class _DynamicCascade(_CommandBase):
	dynamiccascade = 1

#
# Global commands
#
class CLOSE_WINDOW(_CommandBase):
	help = 'Close this window'
class HELP(_CommandBase):
	help = 'Display help'
class PREFERENCES(_CommandBase):
	help = 'Display preferences window'
#
# Commands for a global edit menu (mac only?)
#
class UNDO(_CommandBase):
	pass
class CUT(_CommandBase):
	pass
class COPY(_CommandBase):
	pass
class PASTE(_CommandBase):
	pass
class DELETE(_CommandBase):
	pass

#
# MainDialog commands
#
class OPEN(_CommandBase):
	help = 'Open existing document by URL'
class OPENFILE(_CommandBase):
	help = 'Open existing local file'
class OPEN_RECENT(_DynamicCascade):
	help = 'Open a recently used document'
class RELOAD(_CommandBase):
	help = 'Reloads the current document'
class TRACE(_CommandBase):
	help = 'DEBUG: toggle trace flag'
class DEBUG(_CommandBase):
	help = 'DEBUG: enter Python debugger'
class SOURCEVIEW(_CommandBase):
	help = 'Show source'
class EXIT(_CommandBase):
	help = 'Exit GRiNS'
class CLOSE(_CommandBase):
	help = 'Close current document'
class CONSOLE(_CommandBase):
	help = "DEBUG: Show debug/log output window"
class CHECKVERSION(_CommandBase):
	help = 'Check for newer versions of the software'
class CHOOSESKIN(_CommandBase):
	help = 'Choose a skin descriptor file'
class CHOOSECOMPONENTS(_CommandBase):
	help = 'Choose a systemComponents configuration file'

#
# Player view commands
#
class PLAY(_CommandBase):
	help = 'Play document'
class PAUSE(_CommandBase):
	help = 'Pause playing document'
class STOP(_CommandBase):
	help = 'Stop playing document'
class MAGIC_PLAY(_CommandBase):
	help = 'Continue when paused, pause when playing, play when stopped'
class USERGROUPS(_DynamicCascade):
	help = 'Custom tests'
class CHANNELS(_DynamicCascade):
	help = 'Toggle channels on/off'
class CRASH(_CommandBase):
	help = 'DEBUG: Force a crash'
class SCHEDDUMP(_CommandBase):
	help = 'DEBUG: Dump scheduler data'

class CONSOLE(_CommandBase):
	help = "DEBUG: Show debug/log output window"

