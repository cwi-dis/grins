__version__ = "$Id$"

Error = 'audio.dev.Error'

import sys

if sys.platform[:4] == 'irix':
	from audio.devsgi import AudioDevSGI
	writer = AudioDevSGI
	del AudioDevSGI
elif sys.platform[:5] == 'sunos':
	from audio.devsun import AudioDevSUN
	writer = AudioDevSUN
	del AudioDevSUN
elif sys.platform[:5] == 'linux':
	from audio.devlinux import AudioDevLINUX
	writer = AudioDevLINUX
	del AudioDevLINUX
elif sys.platform in ('mac', 'darwin'):
	from audio.devmac import AudioDevMAC
	writer = AudioDevMAC
	del AudioDevMAC
elif sys.platform == 'win32':
	from audio.devwin import AudioDevWin
	writer = AudioDevWin
	del AudioDevWin
else:
	raise ImportError('No module named audio.dev')

del sys
