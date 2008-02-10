__version__ = "$Id$"

# Dialog for the Preferences window.

# @win32doc|PreferencesDialog
# The actual dialog is implemented by _PreferencesDialog class
# in lib/win32/_PreferencesDialog.py

# This PreferencesDialog class defined in this module
# is the interface between the Preferences platform independent
# class and its implementation.

__version__ = "$Id$"


PreferencesDialogError="PreferencesDialog.Error"

stringitems = {
        'system_language': '2-character name for a language',
        }
intitems = {
        'system_bitrate': 'bitrate of connection with outside world',
        }
boolitems = {
        'system_captions': 'whether captions are to be shown',
        'system_overdub_or_caption': 'audible or visible "captions"',
        'cmif': 'enable GRiNS-specific extensions',
        'html_control': 'choose between IE4 and WebsterPro HTML controls',
        }

class PreferencesDialog:

    def __init__(self, title):
        # Create the Preferences dialog.
        #
        # Create the dialog window, but does not display it yet
        #
        # Arguments (no defaults):
        # title -- string to be displayed as window title
        callbacks={
                'OK':(self.ok_callback, ()),
                'Cancel':(self.cancel_callback, ()),
                'Reset':(self.reset_callback, ()),}
        import _PreferencesDialog
        self.__window = _PreferencesDialog.PreferencesDialog(callbacks)
        self.__window.create()

    def close(self):
        if self.__window is not None:
            self.__window.close()
            self.__window = None
            del self.__window

    def show(self):
        self.__window.show()

    def hide(self):
        self.__window.hide()

    def pop(self):
        self.__window.show()

    #
    # interface methods
    #
    def setstringitem(self, item, value):
        return self.__window.setstringitem(item, value)

    def getstringitem(self, item):
        return self.__window.getstringitem(item)

    def getstringnames(self):
        return self.__window.getstringnames()

    def setintitem(self, item, value):
        self.__window.setintitem(item, value)

    def getintitem(self, item):
        return self.__window.getintitem(item)

    def getintnames(self):
        return self.__window.getintnames()

    def setfloatitem(self, item, value):
        self.__window.setfloatitem(item, value)

    def getfloatitem(self, item):
        return self.__window.getfloatitem(item)

    def getfloatnames(self):
        return self.__window.getfloatnames()

    def setboolitem(self, item, value):
        self.__window.setboolitem(item, value)

    def getboolitem(self, item):
        return self.__window.getboolitem(item)

    def getboolnames(self):
        return self.__window.getboolnames()

    # Callback functions.  These functions should be supplied by
    # the user of this class (i.e., the class that inherits from
    # this class).
    def cancel_callback(self):
        # Called when `Cancel' button is pressed.
        pass

    def reset_callback(self):
        # Called when `Restore' button is pressed.
        pass

    def ok_callback(self):
        # Called when `OK' button is pressed.
        pass
