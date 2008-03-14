"""Dialog for the Paramgroup View.

The Paramgroup View is a window that displays a list of user groups and
gives the ability to edit these user groups.

"""

__version__ = "$Id$"

import windowinterface
from usercmd import *

class ParamgroupViewDialog:
    def __init__(self):
        """Create the ParamgroupView dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) but don't pop it up.
        """
        w = windowinterface.Window('ParamgroupDialog', resizable = 1,
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
