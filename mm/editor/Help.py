__version__ = "$Id$"

# Help window

# Interface:
# (1) optionally call sethelpdir(dirname) with a directory name argument;
# (2) if the user presses a Help button, call showhelpwindow();
# (3) or call givehelp(topic) to show help on a particular subject.
# When the help window is already open, it is popped up.


import os
import string
import sys
sys.path.append('/ufs/guido/src/www') # XXX
#import helplib


helpdir = None # Directory where the help files live

def sethelpdir(dirname):
	global helpdir
	helpdir = dirname


#helpwindow = None # Help window instance, once opened

def givehelp(window, topic):
	#global helpwindow, helpdir
	#if helpwindow is None:
	#	if helpdir is None:
	#		import cmif
	#		helpdir = cmif.findfile('help')
	#	#helpwindow = 'CMIF_help'
	#	print 'Initializing help server... be patient...'
	#helplib.init(helpwindow)
	#helplib.show('file:' + helpdir + '/' + topic + '.html')
	pass

"""
	import win32api, win32con, string
	global helpdir
	if helpdir is None:
			import cmif
			helpdir = cmif.findfile('help')
	strs = string.splitfields(helpdir, '\\')
	if not 'Cmifed.hlp' in strs:
		helpdir = helpdir + "\\Cmifed.hlp"
	win32api.WinHelp(window.GetSafeHwnd(),helpdir,win32con.HELP_KEY,topic)
"""


def showhelpwindow(window):
	#givehelp('Help')
	#CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
	#dir = CMIFDIR+"\\Help\\Cmifed.hlp"
	import win32api, win32con, string
	global helpdir
	if helpdir is None:
			import cmif
			helpdir = cmif.findfile('help')
	strs = string.splitfields(helpdir, '\\')
	if not 'Cmifed.hlp' in strs:
		helpdir = helpdir + "\\Cmifed.hlp"
	win32api.WinHelp(window.GetSafeHwnd(),helpdir,win32con.HELP_CONTENTS,0)
