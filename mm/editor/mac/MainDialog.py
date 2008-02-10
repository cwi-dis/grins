__version__ = "$Id$"

"""Dialog for the Main window.

This is a very simple dialog, it consists of four choices and three
callback functions.

Thex choices are labeled `New', `Open Location...', `Open File...', and
`Exit'.  If either of the Open choices is selected, a dialog window
asks for a URL or a file name respectively, and if one is selected,
the callback self.open_callback is called with the selected location
(always passed in the form of a URL).

If the New choice is selected, the callback self.new_callback is
called without arguments.  If the Exit choice is selected, the
callback self.close_callback is called without arguments.  Also, if
the dialog window is closed in some other way, the callback
self.close_callback is also called.

"""
import usercmd
import os
import macfs
import MMurl
import windowinterface

class MainDialog:
    def __init__(self, title, hasarguments=1):
        """Create the Main dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) and pop it up (i.e. display it on the
        screen).

        Arguments (no defaults):
        title -- string to be displayed as window title
        """

        if __debug__:
            self.commandlist.append(
                    usercmd.CONSOLE(callback=(self.console_callback, ())))
            self.commandlist.append(
                    usercmd.DUMPWINDOWS(callback = (self.dumpwindows_callback, ())))
        self.__window = w = windowinterface.windowgroup(title, self.commandlist, globalgroup=1)
        windowinterface.installaehandler('aevt', 'oapp', self._ae_openapp)
        windowinterface.installaehandler('aevt', 'quit', self._ae_quit)
        windowinterface.installaehandler('aevt', 'odoc', self._ae_opendoc)

    def getparentwindow(self):
        # Used by machine-independent code to pass as parent
        # parameter to dialogs. Not implemented on mac.
        return None

    def open_callback(self):
        import windowinterface
        if not self.canopennewtop():
            return
        windowinterface.InputURLDialog('Open location', self.last_location,
                                    self.openURL_callback)

    def dumpwindows_callback(self):
        windowinterface.dumpwindows()

    def openfile_callback(self):
        """Callback for OPENFILE menu command"""
        import windowinterface
        if not self.canopennewtop():
            return
        filetypes = ['/SMIL presentation', 'application/x-grins-project', 'application/smil']
        windowinterface.FileDialog('', '', filetypes, '',
                                   self.__openfile_done, None, 1)

    def __openfile_done(self, filename):
        """End of OPENFILE menu command. Open the file (as url)"""
        url = self.__path2url(filename)
        if url:
            self.openURL_callback(url)

    def __path2url(self, filename):
        import os, MMurl
        if os.path.isabs(filename):
            cwd = os.getcwd()
            if os.path.isdir(filename):
                dir, file = filename, os.curdir
            else:
                dir, file = os.path.split(filename)
            # XXXX maybe should check that dir gets shorter!
            while len(dir) > len(cwd):
                dir, f = os.path.split(dir)
                file = os.path.join(f, file)
            if dir == cwd:
                filename = file
        return MMurl.pathname2url(filename)

    def setbutton(self, button, value):
        pass                    # for now...

    def set_recent_list(self, list):
        self.__window.set_dynamiclist(usercmd.OPEN_RECENT, list)

    # Callback functions.  These functions should be supplied by
    # the user of this class (i.e., the class that inherits from
    # this class).

    def console_callback(self):
        import quietconsole
        quietconsole.revert()

    def _ae_openapp(self, *args, **kwargs):
        import settings
        if settings.get('initial_dialog'):
            OpenAppDialog(self.new_callback, self.openfile_callback, self.never_again)

    def _ae_opendoc(self, aliases, **kwargs):
        if not type(aliases) in (type(()), type([])):
            aliases=[aliases]
        for alias in aliases:
            try:
                fss, changed = alias.Resolve()
            except macfs.error, arg:
                windowinterface.message("Cannot resolve: %s"%str(arg))
                return
            pathname = fss.as_pathname()
            url = MMurl.pathname2url(pathname)
            if not self.canopennewtop():
                return
            self.openURL_callback(url)

    def _ae_quit(self, *args, **kwargs):
        #
        # Obfuscated code ahead. We call do_close to check that the user wants to close
        # but in stead of actually doing the exit here, which would result in the
        # AE reply not being sent, we schedule the exit for a short while later.
        #
        exitcallback = (windowinterface.settimer, (0.1, (self._quitnow, ())))
        self.close_callback(exitcallback)

    def _quitnow(self):
        raise SystemExit, 0

# The dialog shown when you open the application

def ITEMrange(fr, to): return range(fr, to+1)

ID_DIALOG_OPENAPP=632

ITEM_OK=1
ITEM_PICTURE=2
ITEM_NEW=3
ITEM_OPEN=4
ITEM_NOTHING=5
ITEM_NEVER_AGAIN=6
ITEMLIST_OPENAPP_ALL=ITEMrange(ITEM_OK, ITEM_NEVER_AGAIN)

class OpenAppDialog(windowinterface.MACDialog):
    def __init__(self, cb_new, cb_open, cb_never_again):
        windowinterface.MACDialog.__init__(self, "Oratrix GRiNS", ID_DIALOG_OPENAPP,
                        ITEMLIST_OPENAPP_ALL, default=ITEM_OK)
        self.cb_new = cb_new
        self.cb_open = cb_open
        self.cb_never_again = cb_never_again
        self.cb = None
        self.setradio(ITEM_NEW)
        self.never_again = 0
        self.show()

    def close(self):
        windowinterface.MACDialog.close(self)

    def setradio(self, which):
        self._setbutton(ITEM_NEW, (which==ITEM_NEW))
        self._setbutton(ITEM_OPEN, (which==ITEM_OPEN))
        self._setbutton(ITEM_NOTHING, (which==ITEM_NOTHING))
        if which == ITEM_NEW:
            self.cb = self.cb_new
        elif which == ITEM_OPEN:
            self.cb = self.cb_open
        else:
            self.cb = None

    def do_itemhit(self, n, event):
        if n == ITEM_OK:
            self.close()
            if self.never_again:
                if self.cb_never_again:
                    self.cb_never_again()
            if self.cb:
                self.cb()
        elif n in (ITEM_NEW, ITEM_OPEN, ITEM_NOTHING):
            self.setradio(n)
        elif n == ITEM_NEVER_AGAIN:
            self.never_again = not self.never_again
            self._setbutton(ITEM_NEVER_AGAIN, self.never_again)
        else:
            print 'Unknown LicenseDialog item', n
        return 1
