__version__ = "$Id$"

import string

import urllib, MMurl

import win32dxm

def GetFrameRate(url, maintype, subtype):
	fr = 30
	if string.find(string.lower(subtype), 'real') >= 0 or string.find(subtype, 'shockwave') >= 0:
		if maintype == 'audio':
			fr = 8000
		else:
			fr = 20
	elif maintype in ('image', 'text'):
		fr = 10
	elif maintype == 'video':
		fr = win32dxm.GetFrameRate(url)
	elif maintype == 'audio':
		try:
			import audio
			filename = MMurl.urlretrieve(url)[0]
			a = audio.reader(filename)
			fr = a.getframerate()
		except (audio.Error, IOError, EOFError), msg:
			print 'error in sound file', url, ':', msg
			fr = 8000
	return fr
