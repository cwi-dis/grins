Error = 'audiodev.Error'

import sys

if sys.platform in ('irix4', 'irix5'):
	import audiodevsgi
	AudioDev = audiodevsgi.AudioDevSGI
	del audiodevsgi
elif sys.platform in ('sunos4', 'sunos5'):
	import audiodevsun
	AudioDev = audiodevsun.AudioDevSUN
	del audiodevsun
elif sys.platform == 'mac':
	import audiodevmac
	AudioDev = audiodevmac.AudioDevMAC
	del audiodevmac
else:
	raise ImportError, 'No module named audiodev'

del sys
