__version__ = "$Id$"

# Dialog for the Preferences window.

# @win32doc|PreferencesDialog
# The actual dialog is implemented by _PreferencesDialog class.

# This PreferencesDialog class defined in this module
# is the interface between the Preferences platform independent
# class and its implementation.

__version__ = "$Id$"


class PreferencesDialogError(Exception):
    pass

from components import *
import win32dialog
import string
import languages, bitrates

stringitems = {
        'system_language': '2-character name for a language',
        }
intitems = {
        'system_bitrate': 'bitrate of connection with outside world',
        }
boolitems = {
        'system_captions': 'whether captions are to be shown',
        'system_overdub_or_caption': 'audible or visible "captions"',
        'html_control': 'choose between IE4 and WebsterPro HTML controls',
        }
import features
if features.compatibility == features.Boston:
    boolitems['system_audiodesc'] = 'whether audio descriptions are to be shown'


class _PreferencesDialog(win32dialog.ResDialog,ControlsDict):

    # Class constructor. Calls base class constructors and associates ids to controls
    def __init__(self,cbd=None,parent=None):
        langs = languages.l2a.keys()
        langs.sort()
        self.__languages = langs
        if features.compatibility == features.Boston:
            win32dialog.ResDialog.__init__(self,grinsRC.IDD_PREFERENCES2,parent)
        else:
            win32dialog.ResDialog.__init__(self,grinsRC.IDD_PREFERENCES,parent)
        ControlsDict.__init__(self)

        self['system_bitrate']= ComboBox(self,grinsRC.IDC_COMBO1)
        self['system_language']= ComboBox(self,grinsRC.IDC_COMBO2)
        self['system_overdub_or_caption']=CheckButton(self,grinsRC.IDC_CHECK1)
        self['system_captions']=CheckButton(self,grinsRC.IDC_CHECK2)
        if features.compatibility == features.Boston:
            self['system_audiodesc']=CheckButton(self,grinsRC.IDC_CHECK3)
        self['html_control']=CheckButton(self, grinsRC.IDC_CHECK4)

        self['OK']=Button(self,win32con.IDOK)
        self['Cancel']=Button(self,win32con.IDCANCEL)
        self['Reset']=Button(self,grinsRC.IDC_RESET)
        self._cbd=cbd

    # Called by the OS after the OS window has been created
    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self.HookCommand(self.OnReset,self['Reset']._id)
        br = self['system_bitrate']
        br.resetcontent()
        br.setoptions(bitrates.names)
        lang = self['system_language']
        lang.resetcontent()
        lang.setoptions(self.__languages)

    # Create the actual OS window
    def create(self):
        self.CreateWindow()
    # Called by the core system to close the Dialog
    def close(self):
        self.DestroyWindow()

    # Response to the button OK
    def OnOK(self):
        self.win32special()
        apply(apply,self._cbd['OK'])
    # Response to the button Cancel
    def OnCancel(self):apply(apply,self._cbd['Cancel'])
    # Response to the button Reset
    def OnReset(self,id,code):
        apply(apply,self._cbd['Reset'])


    # Called by the core syatem to show the Dialog
    def show(self):
        self.CenterWindow(self.GetParent())
        self.ShowWindow(win32con.SW_SHOW)

    # Called by the core syatem to hide the Dialog
    def hide(self):
        self.ShowWindow(win32con.SW_HIDE)
    # Called by the core system to bring the Dialog in front
    def pop(self):
        self.show()

    #
    # interface methods
    #
    # set the attribute of the string item to the value
    def setstringitem(self, item, value):
        if not self.has_key(item):
            raise 'Unknown preference item', item
        if item == 'system_language':
            lang = languages.a2l.get(value, 'en')
            self[item].setcursel(self.__languages.index(lang))
        else:
            self[item].settext(value)

    # get the attribute of the string item
    def getstringitem(self, item):
        if not self.has_key(item):
            raise 'Unknown preference item', item
        if item == 'system_language':
            return languages.l2a[self[item].getvalue()]
        return self[item].gettext()

    # set the attribute of the int item to the value
    def setintitem(self, item, value):
        if not self.has_key(item):
            raise 'Unknown preference item', item
        if item == 'system_bitrate':
            ix = 0
            for i in range(len(bitrates.rates)):
                if bitrates.rates[i] <= (value or 0):
                    ix = i
            self[item].setcursel(ix)
        elif value is None:
            self[item].settext('')
        else:
            self[item].settext('%d' % value)

    # get the attribute of the int item
    def getintitem(self, item):
        if not self.has_key(item):
            raise 'Unknown preference item', item
        if item == 'system_bitrate':
            return bitrates.l2a[self[item].getvalue()]
        value = self[item].gettext()
        if value == '':
            return None
        try:
            value = string.atoi(value)
        except ValueError:
            raise PreferencesDialogError, '%s value should be integer'%item
        return value

    # set the attribute of the bool item to the value
    def setboolitem(self, item, value):
        if not self.has_key(item):
            raise 'Unknown preference item', item
        self[item].setcheck(value)

    # get the attribute of the bool item
    def getboolitem(self, item):
        if not self.has_key(item):
            raise 'Unknown preference item', item
        return self[item].getcheck()

    def win32special(self):
        lang=self.getstringitem('system_language')
        import Font
        if lang=='el' or lang=='EL':
            Font.set_win32_charset('GREEK')
        else:
            Font.set_win32_charset('DEFAULT')

class PreferencesDialog:

    def __init__(self, title):
        # Create the Preferences dialog.

        # Create the dialog window, but does not display it yet

        # Arguments (no defaults):
        # title -- string to be displayed as window title
        callbacks={
                'OK':(self.ok_callback, ()),
                'Cancel':(self.cancel_callback, ()),
                'Reset':(self.reset_callback, ()),}
        self.__window = _PreferencesDialog(callbacks)
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
        return stringitems.keys()

    def setintitem(self, item, value):
        self.__window.setintitem(item, value)

    def getintitem(self, item):
        return self.__window.getintitem(item)

    def getintnames(self):
        return intitems.keys()

    def setboolitem(self, item, value):
        self.__window.setboolitem(item, value)

    def getboolitem(self, item):
        return self.__window.getboolitem(item)

    def getboolnames(self):
        return boolitems.keys()

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
