__version__ = "$Id$"

Error = 'audiodev.Error'

import sys

if sys.platform in ('irix4', 'irix5', 'irix6'):
	import audiodevsgi
	writer = audiodevsgi.AudioDevSGI
	del audiodevsgi
elif sys.platform in ('sunos4', 'sunos5'):
	import audiodevsun
	writer = audiodevsun.AudioDevSUN
	del audiodevsun
elif sys.platform == 'mac':
	import audiodevmac
	writer = audiodevmac.AudioDevMAC
	del audiodevmac
else:
	raise ImportError, 'No module named audiodev'

del sys
