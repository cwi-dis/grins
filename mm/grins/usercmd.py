#
# Commands, editor version
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

#
# MainDialog commands
#
class OPEN(_CommandBase):
	help = 'Open existing document'
class TRACE(_CommandBase):
	help = 'DEBUG: toggle trace flag'
class DEBUG(_CommandBase):
	help = 'DEBUG: enter Python debugger'
class SOURCE(_CommandBase):
	help = 'Show source'
class EXIT(_CommandBase):
	help = 'Exit GRiNS'
class CLOSE(_CommandBase):
	help = 'Close current document'

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
class CHANNELS(_DynamicCascade):
	help = 'Toggle channels on/off'
class CALCTIMING(_CommandBase):
	help = 'Recalculate document timing'
class CRASH(_CommandBase):
	help = 'DEBUG: Force a crash'
class SCHEDDUMP(_CommandBase):
	help = 'DEBUG: Dump scheduler data'
