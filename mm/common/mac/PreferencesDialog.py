"""Dialog for the Preferences window.

"""

__version__ = "$Id$"

from Carbon import Dlg
from Carbon import Qd
import windowinterface
import WMEVENTS
import string
import MacOS

PreferencesDialogError="PreferencesDialog.Error"

def ITEMrange(fr, to): return range(fr, to+1)

# Dialog parameters
from mw_resources import ID_DIALOG_PREFERENCES
ITEM_OVERDUB=3
ITEM_CAPTIONS=4
ITEM_CMIF=5
ITEM_BITRATE=6
ITEM_LANGUAGE=7

ITEM_CANCEL=8
ITEM_RESET=9
ITEM_OK=10
ITEM_HELP=11

# These should be toggled upon activation
ITEMLIST_BOOLEAN=[ITEM_CAPTIONS, ITEM_OVERDUB, ITEM_CMIF]
# Events here can be ignored, the values are obtained when the user presses OK
ITEMLIST_IGNORE=[ITEM_BITRATE, ITEM_LANGUAGE]

# These map names to dialog item numbers
NUMERIC_ITEM_DICT={
        "system_bitrate" : ITEM_BITRATE,
}

STRING_ITEM_DICT={
        "system_language" : ITEM_LANGUAGE,
}

BOOLEAN_ITEM_DICT={
        "system_captions" : ITEM_CAPTIONS,
        "system_overdub_or_caption": ITEM_OVERDUB,
        "cmif" : ITEM_CMIF,
}

ITEMLIST_ALL=ITEMrange(1, ITEM_HELP)

class PreferencesDialog(windowinterface.MACDialog):

    def __init__(self, title):
        """Create the Preferences dialog.

        Create the dialog window, but does not display it yet

        Arguments (no defaults):
        title -- string to be displayed as window title
        """
        windowinterface.MACDialog.__init__(self, title, ID_DIALOG_PREFERENCES,
                        ITEMLIST_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)

    def _toggleboolvalue(self, item):
        ctl = self._dialog.GetDialogItemAsControl(item)
        value = ctl.GetControlValue()
        ctl.SetControlValue(not value)

    def do_itemhit(self, item, event):
        if item in ITEMLIST_BOOLEAN:
            self._toggleboolvalue(item)
        elif item in ITEMLIST_IGNORE:
            pass
        elif item == ITEM_CANCEL:
            self.cancel_callback()
        elif item == ITEM_OK:
            self.ok_callback()
        elif item == ITEM_RESET:
            self.reset_callback()
        else:
            print 'Unknown PreferencesDialog item', item, 'event', event
        return 1

    #
    # interface methods
    #
    def setstringitem(self, item, value):
        if not STRING_ITEM_DICT.has_key(item):
            raise 'Unknown preference item', item
        self._setlabel(STRING_ITEM_DICT[item], value)

    def getstringitem(self, item):
        if not STRING_ITEM_DICT.has_key(item):
            raise 'Unknown preference item', item
        return self._getlabel(STRING_ITEM_DICT[item])

    def getstringnames(self):
        return STRING_ITEM_DICT.keys()

    def setintitem(self, item, value):
        if not NUMERIC_ITEM_DICT.has_key(item):
            raise 'Unknown preference item', item
        if value is None:
            self._setlabel(NUMERIC_ITEM_DICT[item], "")
        else:
            self._setlabel(NUMERIC_ITEM_DICT[item], `value`)

    def getintitem(self, item):
        if not NUMERIC_ITEM_DICT.has_key(item):
            raise 'Unknown preference item', item
        value = self._getlabel(NUMERIC_ITEM_DICT[item])
        if value == '':
            return None
        try:
            value = string.atoi(value)
        except ValueError:
            raise PreferencesDialogError, '%s value should be integer'%item
        return value

    def getintnames(self):
        return NUMERIC_ITEM_DICT.keys()

    def setboolitem(self, item, value):
        if not BOOLEAN_ITEM_DICT.has_key(item):
            raise 'Unknown preference item', item
        ctl = self._dialog.GetDialogItemAsControl(BOOLEAN_ITEM_DICT[item])
        if value:
            ctl.SetControlValue(1)
        else:
            ctl.SetControlValue(0)

    def getboolitem(self, item):
        if not BOOLEAN_ITEM_DICT.has_key(item):
            raise 'Unknown preference item', item
        ctl = self._dialog.GetDialogItemAsControl(BOOLEAN_ITEM_DICT[item])
        return ctl.GetControlValue()

    def getboolnames(self):
        return BOOLEAN_ITEM_DICT.keys()

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
