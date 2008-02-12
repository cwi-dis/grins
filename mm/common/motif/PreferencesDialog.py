"""Dialog for the Preferences window.

"""

__version__ = "$Id$"


class PreferencesDialogError(Exception):
    pass

import windowinterface

stringitems = {
        'system_language': '2-character name for a language',
        }
intitems = {
        'system_bitrate': 'bitrate of connection with outside world',
        }
boolitems = {
        'system_captions': 'whether captions are to be shown',
        'system_overdub_or_caption': 'audible or visible "captions"',
        'cmif': 'enable CMIF-specific extensions',
        }

class PreferencesDialog:

    def __init__(self, title):
        """Create the Preferences dialog.

        Create the dialog window, but does not display it yet

        Arguments (no defaults):
        title -- string to be displayed as window title
        """
        self.__window = w = windowinterface.Window(title, resizable=1,
                        deleteCallback = (self.cancel_callback, ()))
        b = w.ButtonRow([('OK', (self.ok_callback, ())),
                         ('Restore', (self.reset_callback, ())),
                         ('Cancel', (self.cancel_callback, ()))],
                        bottom = None, left = None, right = None,
                        vertical = 0)
        self.__w = w.Separator(bottom = b, left = None, right = None)
        self.__items = {}

    def close(self):
        if self.__window is not None:
            self.__window.close()
            self.__window = None
            del self.__w

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
        t = self.__items.get(item)
        if t is not None:
            t.settext(value or '')
            return
        self.__w = w = self.__window.SubWindow(bottom = self.__w,
                                               left = None,
                                               right = None)
        l = w.Label(item, tooltip = stringitems[item],
                    left = None, right = 0.50,
                    bottom = None, top = None)
        t = w.TextInput(None, value or '', None, None, left = l, top = None, bottom = None, right = None)
        self.__items[item] = t

    def getstringitem(self, item):
        return self.__items[item].gettext()

    def getstringnames(self):
        return stringitems.keys()

    def setintitem(self, item, value):
        if value is None:
            value = ''
        else:
            value = `value`
        t = self.__items.get(item)
        if t is not None:
            t.settext(value)
            return
        self.__w = w = self.__window.SubWindow(bottom = self.__w,
                                               left = None,
                                               right = None)
        l = w.Label(item, tooltip = intitems[item],
                    left = None, right = 0.50,
                    bottom = None, top = None)
        t = w.TextInput(None, value, None, None, left = l, top = None, bottom = None, right = None)
        self.__items[item] = t

    def getintitem(self, item):
        import string
        value = self.__items[item].gettext()
        if value == '':
            return None
        try:
            return string.atoi(value)
        except ValueError:
            raise PreferencesDialogError, '%s value should be integer'%item

    def getintnames(self):
        return ['system_bitrate']

    def setboolitem(self, item, value):
        o = self.__items.get(item)
        if o is not None:
            o.setpos(not not value)
            return
        from Preferences import SPECIAL_NAMES
        list = SPECIAL_NAMES.get(item, ['off', 'on'])
        self.__w = w = self.__window.SubWindow(bottom = self.__w,
                                               left = None,
                                               right = None)
        l = w.Label(item, tooltip = boolitems[item],
                    left = None, right = 0.50,
                    bottom = None, top = None)
        o = w.OptionMenu(None, list, not not value, None,
                         left = l, right = None, bottom = None,
                         top = None)
        self.__items[item] = o

    def getboolitem(self, item):
        return self.__items[item].getpos()

    def getboolnames(self):
        return ['system_captions', 'system_overdub_or_caption',
                'cmif']

    # Callback functions.  These functions should be supplied by
    # the user of this class (i.e., the class that inherits from
    # this class).
    def cancel_callback(self):
        """Called when `Cancel' button is pressed."""
        pass

    def reset_callback(self):
        """Called when `Restore' button is pressed."""
        pass

    def ok_callback(self):
        """Called when `OK' button is pressed."""
        pass
