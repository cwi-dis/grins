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


def hashelp():
	return 1

helpdir = None				# Directory where the help files live

def sethelpdir(dirname):
	global helpdir
	helpdir = dirname


def fixhelpdir():
	global helpdir
	if helpdir is None:
		import cmif
		helpdir = cmif.findfile('help')
	strs = string.splitfields(helpdir, '\\')
	if not 'Cmifed.hlp' in strs:
		helpdir = helpdir + "\\Cmifed.hlp"

def givehelp(topic):
	import win32api, win32con, win32ui
	fixhelpdir()
	win32api.WinHelp(win32ui.GetActiveWindow().GetSafeHwnd(), helpdir,
			 win32con.HELP_KEY, topic)


def showhelpwindow():
	import win32api, win32con, win32ui
	fixhelpdir()
	win32api.WinHelp(win32ui.GetActiveWindow().GetSafeHwnd(), helpdir,
			 win32con.HELP_CONTENTS, 0)
