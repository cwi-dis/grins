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

""" @win32doc|Help.py
Utility module that supplies a standard interface to the
application in order to utilize context sensitive help in html form.
The core system recognizes that the application has a help
system by calling the function hashelp().
It displays context sensitive help by calling
the function givehelp(topic) and the index
by calling the function showhelpwindow()
or givehelp('index')
The old documentation was in hlp form but 
for the current version the documentation 
must be converted to the html format.
"""

import os
import string
import sys
import MMurl
import urlparse

# url parsing
import ntpath, urllib

def hashelp():
	return 1

helpbase = None				# directory where the help files live
helpwindow = None

#
# This could be done better, by putting the version number in here.
#
DEFAULT_BASE_URL="http://www.oratrix.com/GRiNS/help/%s/index.html"%sys.platform

def sethelpdir(dirname):
	global helpbase
	helpbase = MMurl.pathname2url(os.path.join(dirname, 'index.html'))

def fixhelpdir():
	global helpbase
	if helpbase is None:
		import cmif
		helpdir = os.path.join(cmif.findfile('Help'), sys.platform)
		if os.path.exists(helpdir):
			basefile = os.path.join(helpdir, 'index.html')
			helpbase = MMurl.pathname2url(basefile)
		else:
			helpbase = DEFAULT_BASE_URL
		

def givehelp(topic):
	global helpwindow
	import windowinterface
	fixhelpdir()
	helpfile = 'player/%s.html'%topic
	helpurl = MMurl.basejoin(helpbase,helpfile)
##	helpurl=toabs(helpurl)
	helpurl = MMurl.canonURL(helpurl)
	import win32api,win32con

	win32api.ShellExecute(0, "open",helpurl, None, "", win32con.SW_SHOW)
	
#	if not helpwindow is None and not helpwindow.is_closed():
#		helpwindow.goto_url(helpurl)
#	helpwindow = windowinterface.htmlwindow(helpurl)

def showhelpwindow():
	givehelp('index')


######################################
# url parsing to pass browser control
def islocal(url):
	utype, host, path, params, query, fragment = urlparse.urlparse(url)
	return (not utype or utype == 'file') and (not host or host == 'localhost')

def toabs(url):
	utype, host, path, params, query, fragment = urlparse.urlparse(url)
	if (utype and utype != 'file') or (host and host != 'localhost'):
		return url
	filename = MMurl.url2pathname(path)
	if os.path.isfile(filename):
		if not os.path.isabs(filename):
			filename=os.path.join(os.getcwd(),filename)
			filename=ntpath.normpath(filename)	
	return filename
