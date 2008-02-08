"""Dialog for the Usergroup View.

The Usergroup View is a window that displays a list of user groups and
gives the ability to edit these user groups.

"""

__version__ = "$Id$"

import windowinterface
from usercmd import *

class UsergroupViewDialog:
    def __init__(self):
        """Create the UsergroupView dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) but don't pop it up.
        """
        w = windowinterface.Window('UsergroupDialog', resizable = 1,
                                   deleteCallback = (self.hide, ()))
        self.__window = w
        self.__buttons = w.ButtonRow(
                [('New...', (self.new_callback, ())),
                 ('Edit...', (self.edit_callback, ())),
                 ('Delete', (self.delete_callback, ())),
                 ],
                vertical = 1, top = None, right = None)
        self.__list = w.List(None, [], (self.__list_callback, ()),
                             top = None, bottom = None, left = None,
                             right = self.__buttons, width = 200)

    def __list_callback(self):
        pos = self.__list.getselected()
        self.__buttons.setsensitive(1, pos is not None)
        self.__buttons.setsensitive(2, pos is not None)

    def getgroup(self):
        """Return name of currently selected user group."""
        return self.__list.getselection()

    def setgroups(self, ugroups, pos):
        """Set the list of user groups.

        Arguments (no defaults):
        ugroups -- list of strings giving the names of the user groups
        pos -- None or index in ugroups list--the initially
                selected element in the list
        """
        self.__list.delalllistitems()
        self.__list.addlistitems(ugroups, 0)
        self.__list.selectitem(pos)
        self.__list_callback()

    def show(self):
        """Show the dialog."""
        self.__window.show()

    def is_showing(self):
        if self.__window is None:
            return 0
        return self.__window.is_showing()

    def hide(self):
        """Hide the dialog."""
        if self.__window is not None:
            self.__window.hide()

    def destroy(self):
        """Destroy the dialog."""
        if self.__window is None:
            return
        self.__window.close()
        self.__window = None

class UsergroupEditDialog:
    __overrideindex = {'hidden':0,'visible':1}
    def __init__(self, ugroup, title, ustate, override, uid):
        """Create the UsergroupEdit dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) and pop it up.
        """
        w = windowinterface.Window('Edit custom test', resizable = 1)
        self.__window = w
        self.__ugroup = w.TextInput('Custom test name', ugroup, None,
                                    None, top = None, left = None,
                                    right = None)
        self.__title = w.TextInput('Custom test title', title, None,
                                   None, top = self.__ugroup,
                                   left = None, right = None)
        self.__state = w.OptionMenu('Default state',
                                    ['false', 'true'],
                                    ustate == 'RENDERED', None,
                                    top = self.__title, left = None,
                                    right = None)
        self.__override = w.OptionMenu('User override',
                                       ['hidden', 'visible'],
                                       self.__overrideindex[override], None,
                                       top = self.__state,
                                       left = None, right = None)
        self.__uid = w.TextInput('Custom test UID', uid, None, None,
                                 top = self.__override,
                                 left = None, right = None)
        sep = w.Separator(top = self.__uid, left = None,
                          right = None)
        self.__buttons = w.ButtonRow(
                [('Cancel', (self.cancel_callback, ())),
                 ('Restore', (self.restore_callback, ())),
                 ('Apply', (self.apply_callback, ())),
                 ('OK', (self.ok_callback, ()))], vertical = 0,
                top = sep, left = None, right = None, bottom = None)
        w.show()

    def showmessage(self, text):
        windowinterface.showmessage(text, parent = self.__window)

    def show(self):
        """Show the dialog (pop it up again)."""
        self.__window.show()

    def close(self):
        """Close the dialog."""
        self.__window.close()
        self.__window = None

    def setstate(self, ugroup, title, ustate, override, uid):
        """Set the values in the dialog.

        Arguments (no defaults):
        ugroup -- string name of the user group
        title -- string title of the user group
        ustate -- string 'RENDERED' or 'NOT RENDERED'
        override -- string 'visible' or 'hidden'
        """
        self.__ugroup.settext(ugroup)
        self.__title.settext(title)
        self.__state.setpos(ustate == 'RENDERED')
        self.__override.setpos(self.__overrideindex[override])
        self.__uid.settext(uid)

    def getstate(self):
        """Return the current values in the dialog."""
        opos = self.__override.getpos()
        for k, v in self.__overrideindex.items():
            if v == opos:
                override = k
                break
        else:
            override = 'hidden'
        return self.__ugroup.gettext(), \
               self.__title.gettext(), \
               self.__state.getvalue(), \
               override, \
               self.__uid.gettext()
