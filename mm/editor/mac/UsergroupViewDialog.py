"""Dialog for the Usergroup View.

The Usergroup View is a window that displays a list of user groups and
gives the ability to edit these user groups.

"""

__version__ = "$Id$"

from Carbon import Dlg
from Carbon import Qd
import windowinterface
import WMEVENTS

def ITEMrange(fr, to): return range(fr, to+1)

# Dialog info for User group browser
from mw_resources import ID_DIALOG_UGROUP_BROWSER
ITEM_B_BROWSER=1

ITEM_B_NEW=2
ITEM_B_EDIT=3
ITEM_B_DELETE=4
ITEM_B_BALLOONHELP=5
ITEMLIST_B_ALL=ITEMrange(ITEM_B_BROWSER, ITEM_B_BALLOONHELP)

# Dialog info for user group editor
from mw_resources import ID_DIALOG_UGROUP_EDITOR
ITEM_E_NAME_LABEL=1
ITEM_E_NAME=2
ITEM_E_TITLE_LABEL=3
ITEM_E_TITLE=4

ITEM_E_RENDERED=5
ITEM_E_OVERRIDE=6

ITEM_E_CANCEL=7
ITEM_E_RESTORE=8
ITEM_E_APPLY=9
ITEM_E_OK=10

ITEM_E_BALLOONHELP=11
ITEMLIST_E_ALL=ITEMrange(ITEM_E_NAME_LABEL, ITEM_E_BALLOONHELP)


class UsergroupViewDialog(windowinterface.MACDialog):
    def __init__(self):
        """Create the UsergroupView dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) but don't pop it up.
        """

        windowinterface.MACDialog.__init__(self, "Usergroup view",
                        ID_DIALOG_UGROUP_BROWSER, ITEMLIST_B_ALL)

        self.__list = self._window.ListWidget(ITEM_B_BROWSER)
##         self.selection_setlist(list, initial)

    def __list_callback(self):
        pos = self.__list.getselect()
        self._setsensitive([ITEM_B_EDIT, ITEM_B_DELETE], pos is not None)
        if pos is not None and self.__list.lastclickwasdouble():
            self.edit_callback()

    def getgroup(self):
        """Return name of currently selected user group."""
        return self.__list.getselectvalue()

    def setgroups(self, ugroups, pos):
        """Set the list of user groups.

        Arguments (no defaults):
        ugroups -- list of strings giving the names of the user groups
        pos -- None or index in ugroups list--the initially
                selected element in the list
        """
        self.__list.setitems(ugroups, pos)
        self.__list_callback()

##     def show(self):
##         """Show the dialog."""
##         self.__window.show()
##
##     def is_showing(self):
##         if self.__window is None:
##             return 0
##         return self.__window.is_showing()
##
##     def hide(self):
##         """Hide the dialog."""
##         if self.__window is not None:
##             self.__window.hide()

    def destroy(self):
        """Destroy the dialog."""
        self.close()

    def do_itemhit(self, item, event):
        if item == ITEM_B_BROWSER:
            self.__list_callback()
        elif item == ITEM_B_NEW:
            self.new_callback()
        elif item == ITEM_B_EDIT:
            self.edit_callback()
        elif item == ITEM_B_DELETE:
            self.delete_callback()
            print 'Unknown UsergroupViewDialog item', item, 'event', event
        return 1

class UsergroupEditDialog(windowinterface.MACDialog):
    __rangelist = ['0-1 sec', '0-10 sec', '0-100 sec']

    def __init__(self, ugroup, title, ustate, override, uid):
        """Create the UsergroupEdit dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) and pop it up.
        """
        windowinterface.MACDialog.__init__(self, title, ID_DIALOG_UGROUP_EDITOR,
                        ITEMLIST_E_ALL, default=ITEM_E_OK, cancel=ITEM_E_CANCEL)
        self.setstate(ugroup, title, ustate, override, uid)
##         w = windowinterface.Window('Edit user group', resizable = 1)
##         self.__window = w
##         self.__ugroup = w.TextInput('User group name', ugroup, None,
##                         None, top = None, left = None,
##                         right = None)
##         self.__title = w.TextInput('User group title', title, None,
##                        None, top = self.__ugroup,
##                        left = None, right = None)
##         self.__state = w.OptionMenu('Initial state',
##                         ['NOT RENDERED', 'RENDERED'],
##                         ustate == 'RENDERED', None,
##                         top = self.__title, left = None,
##                         right = None)
##         self.__override = w.OptionMenu('User override',
##                            ['hidden', 'visible'],
##                            override == 'visible', None,
##                            top = self.__state,
##                            left = None, right = None)
##         sep = w.Separator(top = self.__override, left = None,
##                   right = None)
##         self.__buttons = w.ButtonRow(
##             [('Cancel', (self.cancel_callback, ())),
##              ('Restore', (self.restore_callback, ())),
##              ('Apply', (self.apply_callback, ())),
##              ('OK', (self.ok_callback, ()))], vertical = 0,
##             top = sep, left = None, right = None, bottom = None)
        self.show()

    def showmessage(self, text):
        windowinterface.showmessage(text)

    def setstate(self, ugroup, title, ustate, override, uid):
        """Set the values in the dialog.

        Arguments (no defaults):
        ugroup -- string name of the user group
        title -- string title of the user group
        ustate -- string 'RENDERED' or 'NOT RENDERED'
        override -- string 'allowed' or 'not allowed'
        """
        self._setlabel(ITEM_E_NAME, ugroup)
        self._setlabel(ITEM_E_TITLE, title)
        self._setbutton(ITEM_E_RENDERED, (ustate == 'RENDERED'))
        self._setbutton(ITEM_E_OVERRIDE, (override == 'visible'))

    def getstate(self):
        if self._getbutton(ITEM_E_RENDERED):
            ustate = 'RENDERED'
        else:
            ustate = 'NOT RENDERED'
        if self._getbutton(ITEM_E_OVERRIDE):
            override = 'visible'
        else:
            override = 'hidden'
        uid = ''                # XXX to be supplied
        return (
                self._getlabel(ITEM_E_NAME),
                self._getlabel(ITEM_E_TITLE),
                ustate,
                override,
                uid)

    def do_itemhit(self, item, event):
        if item == ITEM_E_NAME:
            pass
        elif item == ITEM_E_TITLE:
            pass
        elif item == ITEM_E_RENDERED:
            self._togglebutton(ITEM_E_RENDERED)
        elif item == ITEM_E_OVERRIDE:
            self._togglebutton(ITEM_E_OVERRIDE)
        elif item == ITEM_E_CANCEL:
            self.cancel_callback()
        elif item == ITEM_E_OK:
            self.ok_callback()
        elif item == ITEM_E_RESTORE:
            self.restore_callback()
        elif item == ITEM_E_APPLY:
            self.apply_callback()
        else:
            print 'Unknown UsergroupViewEditDialog item', item, 'event', event
        return 1
