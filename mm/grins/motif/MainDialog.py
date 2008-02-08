__version__ = "$Id$"

"""Dialog for the Main window.

This is a very simple dialog, it consists of four choices and three
callback functions.

The choices are labeled `New', `Open...', `Preferences...', `Help',
and `Exit'.  If the Open choice is selected, a dialog window asks for
a URL and also has a `Browse...' button to browse the file system.  If
a URL is selected, the callback self.open_callback is called with the
selected location (always passed in the form of a URL).

"""

class MainDialog:
    def __init__(self, title):
        """Create the Main dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) and pop it up (i.e. display it on the
        screen).

        Arguments (no defaults):
        title -- string to be displayed as window title
        """

        self.__recent = []
        self.__lasturl = ''

    def open_callback(self):
        import windowinterface
        w = windowinterface.Window('Open location', resizable = 1,
                                   grab = 1, horizontalSpacing = 5,
                                   verticalSpacing = 5)
        l = w.Label('Enter the Internet location (URL) or browse to the local file you would like to open', top = None, left = None,
                    right = None)
        f = w.SubWindow(left = None, top = l, right = None,
                        horizontalSpacing = 5, verticalSpacing = 5)
        b = f.Button('Browse...', (self.__openfile_callback, ()),
                     top = None, right = None, bottom = None)
        t = f.ListEdit('Open:', self.__lasturl, (self.__tcallback, ()),
                       self.__recent,
                       left = None, right = b, top = None, bottom = None)
        s = w.Separator(top = f, left = None, right = None)
        r = w.ButtonRow([('Open', (self.__tcallback, ())),
                         ('Cancel', (self.__ccallback, ()))],
                        vertical = 0, tight = 1, top = f, left = None,
                        right = None, bottom = None)
        self.__text = t
        self.__owindow = w
        w.show()

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
        import features
        from compatibility import Boston
        if features.compatibility == Boston:
            filetypes = ['/SMIL presentation', 'application/smil', 'application/x-grins-project']
        else:
            filetypes = ['/SMIL presentation', 'application/x-grins-project', 'application/smil']
##         import features
##         if not features.lightweight:
##             filetypes.append('application/x-grins-cmif')
        windowinterface.FileDialog('Open file', dir, filetypes, file,
                                   self.__filecvt, None, 1,
                                   parent = self.__owindow)

    def __filecvt(self, filename):
        import MMurl
##         import os
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

    def set_recent_list(self, list):
        recent = []
        for base, url in list:
            recent.append(url[0])
        self.__recent = recent
