__version__ = "$Id$"

Error = 'audio.dev.Error'

import sys

if sys.platform in ('irix4', 'irix5', 'irix6'):
	import devsgi
	writer = devsgi.AudioDevSGI
	del devsgi
elif sys.platform in ('sunos4', 'sunos5'):
	import devsun
	writer = devsun.AudioDevSUN
	del devsun
elif sys.platform == 'mac':
	import devmac
	writer = devmac.AudioDevMAC
	del devmac
elif sys.platform == 'win32':
	import devwin
	writer = devwin.AudioDevWin
	del devwin
else:
	raise ImportError, 'No module named audio.dev'

del sys
