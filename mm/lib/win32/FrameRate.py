__version__ = "$Id$"

import string

import urllib, MMurl

import win32dxm

def GetFrameRate(url, maintype, subtype):
	fr = 30
	if string.find(string.lower(subtype), 'real') >= 0 or string.find(subtype, 'shockwave') >= 0:
		return 30
	elif maintype == 'image':
		return 10
	elif maintype == 'video':
		fr = win32dxm.GetFrameRate(url)
	return fr

