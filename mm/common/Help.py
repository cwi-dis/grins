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
import version
import features

def hashelp():
    import windowinterface
    return hasattr(windowinterface, 'htmlwindow')

helpbase = None                         # directory where the help files live
helpbase_web = None                     # web location where the help files live
helpwindow = None

def sethelpprogram(program):
    pass

def sethelpdir(dirname):
    global helpbase
    helpbase = MMurl.pathname2url(os.path.join(dirname, 'index.html'))

def fixhelpdir():
    global helpbase
    global helpbase_web
    if helpbase_web is None:
        helpbase_web = 'http://www.oratrix.com/indir/%s/help/index.html'%version.shortversion
    if helpbase is None:
        import cmif
        helpdir = cmif.findfile('Help')
        basefile = os.path.join(helpdir, 'index.html')
        if os.path.exists(basefile):
            helpbase = MMurl.pathname2url(basefile)
        else:
            helpbase = helpbase_web

def givehelp(topic, web=0):
    global helpwindow
    import windowinterface
    if topic == 'buy' and hasattr(features, 'buyurl'):
        helpurl = features.buyurl
    else:
        fixhelpdir()
        helpfile = '%s.html'%topic
        if web:
            base = helpbase_web
        else:
            base = helpbase
        helpurl = MMurl.basejoin(base, helpfile)
    if helpwindow is not None and not helpwindow.is_closed():
        helpwindow.goto_url(helpurl)
    else:
        helpwindow = windowinterface.htmlwindow(helpurl)

def showhelpwindow():
    givehelp('index')
