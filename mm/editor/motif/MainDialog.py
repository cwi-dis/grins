"""Dialog for the Main window.

This is a very simple dialog, it consists of four choices and three
callback functions.

The choices are labeled `New', `Open...', `Preferences...', `Help',
and `Exit'.  If the Open choice is selected, a dialog window asks for
a URL and also has a `Browse...' button to browse the file system.  If
a URL is selected, the callback self.open_callback is called with the
selected location (always passed in the form of a URL).

If the New choice is selected, the callback self.new_callback is
called without arguments.  If the Exit choice is selected, the
callback self.close_callback is called without arguments.  Also, if
the dialog window is closed in some other way, the callback
self.close_callback is also called.

"""

__version__ = "$Id$"

from usercmd import *
from flags import *

class MainDialog:
    adornments = {
            'toolbar' : [
                    (FLAG_ALL, 'New', NEW_DOCUMENT),
                    (FLAG_ALL, 'Open...', OPEN),
                    (FLAG_ALL, 'Preferences...', PREFERENCES),
                    (FLAG_ALL|FLAG_DBG, 'Trace', TRACE, 't'),
                    (FLAG_ALL|FLAG_DBG, 'Debug', DEBUG),
                    (FLAG_ALL|FLAG_DBG, 'Crash', CRASH),
                    (FLAG_ALL, 'Help...', HELP),
                    (FLAG_ALL, 'Exit', EXIT),
                    ],
            'close': [ EXIT, ],
            }

    def __init__(self, title, hasarguments=1):
        """Create the Main dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) and pop it up (i.e. display it on the
        screen).

        Arguments (no defaults):
        title -- string to be displayed as window title
        """

        import windowinterface, WMEVENTS

        self.adornments['flags'] = curflags()
        self.__window = w = windowinterface.newcmwindow(None, None, 0, 0,
                        title, adornments = self.adornments,
                        commandlist = self.commandlist)
        self.__recent = []
        self.__lasturl = ''

    def getparentwindow(self):
        # Used by machine-independent code to pass as parent
        # parameter to dialogs. Not implemented on unix.
        return None

    def open_callback(self):
        import windowinterface
        if not self.canopennewtop():
            return
        w = windowinterface.Window('Open location', resizable = 1,
                                   grab = 1, parent = self.__window, horizontalSpacing = 5, verticalSpacing = 5)
        l = w.Label('Enter the Internet location (URL) or browse to the local file you would like to open', top = None, left = None, right = None)
        f = w.SubWindow(left = None, top = l, right = None, horizontalSpacing = 5, verticalSpacing = 5)
        b = f.Button('Browse...', (self.__openfile_callback, ()),
                     top = None, right = None, bottom = None)
##         t = f.TextInput('Open:', '', None, (self.__tcallback, ()),
##                 modifyCB = self.__modifyCB, left = None,
##                 right = b, top = None, bottom = None)
        t = f.ListEdit('Open:', self.__lasturl, (self.__tcallback, ()), self.__recent,
                       left = None, right = b, top = None,
                       bottom = None)
        s = w.Separator(top = f, left = None, right = None)
        r = w.ButtonRow([('Open', (self.__tcallback, ())),
                         ('Cancel', (self.__ccallback, ()))],
                        vertical = 0, tight = 1, top = f, left = None,
                        right = None, bottom = None)
        self.__text = t
        self.__owindow = w
        w.show()

    def __modifyCB(self, text):
        # HACK: this hack is because the SGI file browser adds
        # a space to the end of the filename when you drag and
        # drop it.
        if text and len(text) > 1 and text[-1] == ' ':
            return text[:-1]

    def __ccallback(self):
        self.__owindow.close()
        self.__owindow = None
        self.__text = None

    def __tcallback(self):
        text = self.__text.gettext()
        self.__ccallback()
        if text:
            self.__lasturl = text
            self.openURL_callback(text)

    def __openfile_callback(self):
        import windowinterface
        windowinterface.setwaiting()
        # provide a default directory and file name for the
        # browser based on the current selection (if any)
        dir = '.'
        file = ''
        url = self.__text.gettext() or self.__lasturl
        if url:
            import MMurl
            type, rest = MMurl.splittype(url)
            if not type or type == 'file':
                import os
                dir, file = os.path.split(MMurl.url2pathname(MMurl.splithost(rest)[1]))
        filetypes = ['/SMIL presentation', 'application/x-grins-project', 'application/smil']
        windowinterface.FileDialog('Open file', dir, filetypes, file,
                                   self.__filecvt, None, 1,
                                   parent = self.__owindow)

    def __filecvt(self, filename):
        import os, MMurl
##         if os.path.isabs(filename):
##             cwd = os.getcwd()
##             if os.path.isdir(filename):
##                 dir, file = filename, os.curdir
##             else:
##                 dir, file = os.path.split(filename)
##             # XXXX maybe should check that dir gets shorter!
##             while len(dir) > len(cwd):
##                 dir, f = os.path.split(dir)
##                 file = os.path.join(f, file)
##             if dir == cwd:
##                 filename = file
        self.__lasturl = MMurl.pathname2url(filename)
        self.__text.settext(self.__lasturl)

    def openfile_callback(self):
        """On Unix we only have to "open url" dialog"""
        self.open_callback()

    def setbutton(self, button, value):
        pass                    # for now...

    def set_recent_list(self, list):
        recent = []
        for base, url in list:
            recent.append(url[0])
        self.__recent = recent
