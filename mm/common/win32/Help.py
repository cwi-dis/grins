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

helpdir = None				# directory where the help files live
helpfile = None				# the help file itself

def sethelpdir(dirname):
	global helpdir, helpfile
	helpdir = dirname
	helpfile = None

def fixhelpdir():
	global helpdir, helpfile
	if helpdir is None:
		import cmif
		helpdir = os.path.join(cmif.findfile('Help'), 'win32')
	if helpfile is None:
		helpfile = os.path.join(helpdir, 'Cmifed.hlp')

def givehelp(topic):
	import win32api, win32con, win32ui
	fixhelpdir()
	win32api.WinHelp(win32ui.GetActiveWindow().GetSafeHwnd(), helpfile,
			 win32con.HELP_KEY, topic)


def showhelpwindow():
	import win32api, win32con, win32ui
	fixhelpdir()
	win32api.WinHelp(win32ui.GetActiveWindow().GetSafeHwnd(), helpfile,
			 win32con.HELP_CONTENTS, 0)
