__version__ = "$Id$"

# Help window
# XXXX This is far too stateful. The interface should be changed into
# XXXX an object that is kept in the main object. We keep it like this
# XXXX for now to stay compatible with the Windows version.

# Interface:
# (1) optionally call sethelpdir(dirname) with a directory name argument;
# (2) if the user presses a Help button, call showhelpwindow();
# (3) or call givehelp(topic) to show help on a particular subject.
# When the help window is already open, it is popped up.


import os
import string
import sys
import MMurl

def hashelp():
	import windowinterface
	return hasattr(windowinterface, 'htmlwindow')

helpbase = None				# directory where the help files live
helpwindow = None
helpprogram = "player"

#
# This could be done better, by putting the version number in here.
#
DEFAULT_BASE_URL="http://www.cwi.nl/GRiNS/help/%s/index.html"%sys.platform

def sethelpprogram(program):
	global helpprogram
	helpprogram = program
	
def sethelpdir(dirname):
	global helpbase
	helpbase = MMurl.pathname2url(os.path.join(dirname, 'index.html'))

def fixhelpdir():
	global helpbase
	if helpbase is None:
		import cmif
		helpdir = os.path.join(cmif.findfile('Help'), sys.platform)
		helpdir = os.path.join(helpdir, helpprogram)
		if os.path.exists(helpdir):
			basefile = os.path.join(helpdir, 'index.html')
			helpbase = MMurl.pathname2url(basefile)
		else:
			helpbase = DEFAULT_BASE_URL
		

def givehelp(topic):
	global helpwindow
	import windowinterface
	print 'GIVEHELP', topic
	fixhelpdir()
	helpfile = '%s.html'%topic
	helpurl = MMurl.basejoin(helpbase, helpfile)
	if not helpwindow is None and not helpwindow.is_closed():
		helpwindow.goto_url(helpurl)
	helpwindow = windowinterface.htmlwindow(helpurl)

def showhelpwindow():
	givehelp('index')
