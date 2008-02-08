"""Dialog for the LinkEditor.

The LinkEditDialog is a window that dsiplays three lists from which
the user can select an item.  It is best if the lists are shown side
by side, in which case the left and right lists display lists of
anchors, and the middle list a list of links between the anchors.  The
middle and right list may be hidden (but for completeness there is
also an interface to show or hide the left list).  For the left and
right lists, there are menus, and all three lists are headed by a
label.  The label of the left and right lists can be changed under
program control.  With the lists are also associated some buttons that
may or may not be sensitive.  When a list is not displayed, the
buttons and label should not be displayed either (or at least not be
sensitive).  The menus should always be available.

The button labels for the left and right lists are `Push focus' and
`Anchor editor...'; the button labels for the middle list are
`Add...', `Edit...', and `Delete'.

There is also an edit group consisting of a list of which one item is
always selected (can be implemented as a Motif Option menu) and two
buttons `OK' and `Cancel'.  The edit group may be hidden.

The list menus are specified through the constructor method as lists
of tuples.  The tuples consist of a string (the label of the menu
entry) and another tuple.  This latter tuple consists of the callback
funtion and the argument tuple.

All buttons have callbacks associated with them.  The callbacks for
the buttons belonging to the left and right lists are the same.  In
order to be able to distinguish them, arguments must be passed to the
constructor which are passed on to the callback for these buttons.
All other callbacks are called without arguments.

"""

__version__ = "$Id$"

import windowinterface

class LinkBrowserDialog:
    def __init__(self, title, menu1, cbarg1, menu2, cbarg2):
        """Create the LinkEditor dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) but do not pop it up (i.e. do not display
        it on the screen).

        Arguments (no defaults):
        title -- string to be display as window title
        menu1 -- list of tuples -- the menu for the left list
                (see module doc for description of tuples)
        cbarg1 -- any object -- argument passed on to
                callbacks related to the left list
        menu2 -- list of tuples -- the menu for the right list
                (see module doc for description of tuples)
        cbarg2 -- any object -- argument passed on to
                callbacks related to the right list
        """

        w = windowinterface.Window(title, resizable = 1,
                        deleteCallback = (self.delete_callback, ()))
        self.__window = w

        win1 = w.SubWindow(top = None, left = None, right = 1.0/3.0,
                           bottom = None)
        menu = win1.PulldownMenu([('Set anchorlist', menu1)],
                                 top = None, left = None, right = None)
        self.__left_buttons = win1.ButtonRow(
                [('Sync selection', (self.show_callback, (cbarg1,))),
                 ('Anchor editor...',
                  (self.anchoredit_callback, (cbarg1,))),
                 ],
                vertical = 1, bottom = None, left = None, right = None)
        self.__left_browser = win1.List('None', [],
                (self.anchor_browser_callback, (cbarg1,)),
                top = menu, bottom = self.__left_buttons,
                left = None, right = None)

        win2 = w.SubWindow(top = None, left = win1, right = 2.0/3.0,
                           bottom = None)
        dummymenu = win2.PulldownMenu([('Set anchorlist', [])],
                                 top = None, left = None, right = None)
        self.__middle_buttons = win2.ButtonRow(
                [('Add...', (self.link_new_callback, ())),
                 ('Edit...', (self.link_edit_callback, ())),
                 ('Delete', (self.link_delete_callback, ())),
                 ],
                vertical = 1, bottom = None, left = None, right = None)
        self.__middle_browser = win2.List('links:', [],
                (self.link_browser_callback, ()),
                top = dummymenu, bottom = self.__middle_buttons,
                left = None, right = None)

        win3 = w.SubWindow(top = None, left = win2, right = None,
                           bottom = None)
        menu = win3.PulldownMenu([('Set anchorlist', menu2)],
                                 top = None, left = None, right = None)
        self.__right_buttons = win3.ButtonRow(
                [('Add external...', (self.add_external_callback, ())),
                 ('Sync selection', (self.show_callback, (cbarg2,))),
                 ('Anchor editor...', (self.anchoredit_callback, (cbarg2,))),
                 ],
                vertical = 1, bottom = None, left = None, right = None)
        self.__right_browser = win3.List('None', [],
                (self.anchor_browser_callback, (cbarg2,)),
                top = menu, bottom = self.__right_buttons,
                left = None, right = None)

        w.fix()

        dummymenu.hide()

        # the below assignments are merely for efficiency
        self.settitle = self.__window.settitle
        self.is_showing = self.__window.is_showing
        self.leftsetlabel = self.__left_browser.setlabel
        self.leftdellistitems = self.__left_browser.dellistitems
        self.leftdelalllistitems = self.__left_browser.delalllistitems
        self.leftaddlistitems = self.__left_browser.addlistitems
        self.leftreplacelistitem = self.__left_browser.replacelistitem
        self.leftselectitem = self.__left_browser.selectitem
        self.leftgetselected = self.__left_browser.getselected
        self.leftgetlist = self.__left_browser.getlist
        self.rightsetlabel = self.__right_browser.setlabel
        self.rightdellistitems = self.__right_browser.dellistitems
        self.rightdelalllistitems = self.__right_browser.delalllistitems
        self.rightaddlistitems = self.__right_browser.addlistitems
        self.rightreplacelistitem = self.__right_browser.replacelistitem
        self.rightselectitem = self.__right_browser.selectitem
        self.rightgetselected = self.__right_browser.getselected
        self.rightgetlist = self.__right_browser.getlist
        self.middledelalllistitems = self.__middle_browser.delalllistitems
        self.middleaddlistitems = self.__middle_browser.addlistitems
        self.middleselectitem = self.__middle_browser.selectitem
        self.middlegetselected = self.__middle_browser.getselected
        self.addexternalsetsensitive(0)

    def close(self):
        """Close the dialog and free resources."""
        self.__window.close()
        del self.__window
        del self.__left_buttons
        del self.__left_browser
        del self.__middle_buttons
        del self.__middle_browser
        del self.__right_buttons
        del self.__right_browser

        # the below del's only if efficiency assignments above are done
        del self.settitle
        del self.is_showing
        del self.leftsetlabel
        del self.leftdellistitems
        del self.leftdelalllistitems
        del self.leftaddlistitems
        del self.leftreplacelistitem
        del self.leftselectitem
        del self.leftgetselected
        del self.leftgetlist
        del self.rightsetlabel
        del self.rightdellistitems
        del self.rightdelalllistitems
        del self.rightaddlistitems
        del self.rightreplacelistitem
        del self.rightselectitem
        del self.rightgetselected
        del self.rightgetlist
        del self.middledelalllistitems
        del self.middleaddlistitems
        del self.middleselectitem
        del self.middlegetselected

    def show(self):
        """Show the dialog."""
        self.__window.show()

    def hide(self):
        """Hide the dialog."""
        self.__window.hide()

    def settitle(self, title):
        """Set (change) the title of the window.

        Arguments (no defaults):
        title -- string to be displayed as new window title.
        """
        self.__window.settitle(title)

    def is_showing(self):
        """Return whether dialog is showing."""
        return self.__window.is_showing()

    # Interface to the left list and associated buttons.
    def lefthide(self):
        """Hide the left list with associated buttons."""
        self.__left_browser.hide()
        self.__left_buttons.hide()

    def leftshow(self):
        """Show the left list with associated buttons."""
        self.__left_browser.show()
        self.__left_buttons.show()

    def leftsetlabel(self, label):
        """Set the label for the left list.

        Arguments (no defaults):
        label -- string -- the label to be displayed
        """
        self.__left_browser.setlabel(label)

    def leftdellistitems(self, poslist):
        """Delete items from left list.

        Arguments (no defaults):
        poslist -- list of integers -- the indices of the
                items to be deleted
        """
        self.__left_browser.dellistitems(poslist)

    def leftdelalllistitems(self):
        """Delete all items from the left list."""
        self.__left_browser.delalllistitems()

    def leftaddlistitems(self, items, pos):
        """Add items to the left list.

        Arguments (no defaults):
        items -- list of strings -- the items to be added
        pos -- integer -- the index of the item before which
                the items are to be added (-1: add at end)
        """
        self.__left_browser.addlistitems(items, pos)

    def leftreplacelistitem(self, pos, newitem):
        """Replace an item in the left list.

        Arguments (no defaults):
        pos -- the index of the item to be replaced
        newitem -- string -- the new item
        """
        self.__left_browser.replacelistitem(pos, newitem)

    def leftselectitem(self, pos):
        """Select an item in the left list.

        Arguments (no defaults):
        pos -- integer -- the index of the item to be selected
        """
        self.__left_browser.selectitem(pos)

    def leftgetselected(self):
        """Return the index of the currently selected item or None."""
        return self.__left_browser.getselected()

    def leftgetlist(self):
        """Return the left list as a list of strings."""
        return self.__left_browser.getlist()

    def leftmakevisible(self, pos):
        """Maybe scroll list to make an item visible.

        Arguments (no defaults):
        pos -- index of item to be made visible.
        """
        if not self.__left_browser.is_visible(pos):
            self.__left_browser.scrolllist(pos,
                                           windowinterface.CENTER)

    def leftbuttonssetsensitive(self, sensitive):
        """Make the left buttons (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__left_buttons.setsensitive(0, sensitive)
        self.__left_buttons.setsensitive(1, sensitive)

    # Interface to the right list and associated buttons.
    def righthide(self):
        """Hide the right list with associated buttons."""
        self.__right_browser.hide()
        self.__right_buttons.hide()

    def rightshow(self):
        """Show the right list with associated buttons."""
        self.__right_browser.show()
        self.__right_buttons.show()

    def rightsetlabel(self, label):
        """Set the label for the right list.

        Arguments (no defaults):
        label -- string -- the label to be displayed
        """
        self.__right_browser.setlabel(label)

    def rightdellistitems(self, poslist):
        """Delete items from right list.

        Arguments (no defaults):
        poslist -- list of integers -- the indices of the
                items to be deleted
        """
        self.__right_browser.dellistitems(poslist)

    def rightdelalllistitems(self):
        """Delete all items from the right list."""
        self.__right_browser.delalllistitems()

    def rightaddlistitems(self, items, pos):
        """Add items to the right list.

        Arguments (no defaults):
        items -- list of strings -- the items to be added
        pos -- integer -- the index of the item before which
                the items are to be added (-1: add at end)
        """
        self.__right_browser.addlistitems(items, pos)

    def rightreplacelistitem(selfpos, newitem):
        """Replace an item in the right list.

        Arguments (no defaults):
        pos -- the index of the item to be replaced
        newitem -- string -- the new item
        """
        self.__right_browser.replacelistitem(pos, newitem)

    def rightselectitem(self, pos):
        """Select an item in the right list.

        Arguments (no defaults):
        pos -- integer -- the index of the item to be selected
        """
        self.__right_browser.selectitem(pos)

    def rightgetselected(self):
        """Return the index of the currently selected item or None."""
        return self.__right_browser.getselected()

    def rightgetlist(self):
        """Return the right list as a list of strings."""
        return self.__right_browser.getlist()

    def rightmakevisible(self, pos):
        """Maybe scroll list to make an item visible.

        Arguments (no defaults):
        pos -- index of item to be made visible.
        """
        if not self.__right_browser.is_visible(pos):
            self.__right_browser.scrolllist(pos,
                                            windowinterface.CENTER)

    def rightbuttonssetsensitive(self, sensitive):
        """Make the right buttons (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__right_buttons.setsensitive(1, sensitive)
        self.__right_buttons.setsensitive(2, sensitive)

    def addexternalsetsensitive(self, sensitive):
        """Make the Add external button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__right_buttons.setsensitive(0, sensitive)

    # Interface to the middle list and associated buttons.
    def middlehide(self):
        """Hide the middle list with associated buttons."""
        self.__middle_browser.hide()
        self.__middle_buttons.hide()

    def middleshow(self):
        """Show the middle list with associated buttons."""
        self.__middle_browser.show()
        self.__middle_buttons.show()

    def middledelalllistitems(self):
        """Delete all items from the middle list."""
        self.__middle_browser.delalllistitems()

    def middleaddlistitems(self, items, pos):
        """Add items to the middle list.

        Arguments (no defaults):
        items -- list of strings -- the items to be added
        pos -- integer -- the index of the item before which
                the items are to be added (-1: add at end)
        """
        self.__middle_browser.addlistitems(items, pos)

    def middleselectitem(self, pos):
        """Select an item in the middle list.

        Arguments (no defaults):
        pos -- integer -- the index of the item to be selected
        """
        self.__middle_browser.selectitem(pos)

    def middlegetselected(self):
        """Return the index of the currently selected item or None."""
        return self.__middle_browser.getselected()

    def middlemakevisible(self, pos):
        """Maybe scroll list to make an item visible.

        Arguments (no defaults):
        pos -- index of item to be made visible.
        """
        if not self.__middle_browser.is_visible(pos):
            self.__middle_browser.scrolllist(
                    pos, windowinterface.CENTER)

    def addsetsensitive(self, sensitive):
        """Make the Add button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__middle_buttons.setsensitive(0, sensitive)

    def editsetsensitive(self, sensitive):
        """Make the Add button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__middle_buttons.setsensitive(1, sensitive)

    def deletesetsensitive(self, sensitive):
        """Make the Add button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__middle_buttons.setsensitive(2, sensitive)


    # Callback functions.  These functions should be supplied by
    # the user of this class (i.e., the class that inherits from
    # this class).
    def delete_callback(self):
        """Called when `Delete' button is pressed."""
        pass

    def show_callback(self, client_data):
        """Called when a new entry in the left or right list is selected."""
        pass

    def anchoredit_callback(self, client_data):
        """Called when the left or right `Anchor editor...' button is pressed."""
        pass

    def anchor_browser_callback(self, client_data):
        """Called when the left or right `Push focus' button is pressed."""
        pass

    def link_new_callback(self):
        """Called when the `Add...' button is pressed."""
        pass

    def link_edit_callback(self):
        """Called when the `Edit...' button is pressed."""
        pass

    def link_delete_callback(self):
        """Called when the `Delete' button is pressed."""
        pass

    def link_browser_callback(self):
        """Called when a new selection is made in the middle list."""
        pass

class LinkEditorDialog:
    def __init__(self, title, dirstr, typestr, dir, type, dirsens):
        """Create the LinkEditor dialog.
        """

        w = windowinterface.Window(title, resizable = 1, grab=1,
                        deleteCallback = (self.cancel_callback, ()))
        self.__window = w

        self.__edit_group = e = w.SubWindow(top = None, left = None,
                                            right = None, bottom=None)
        self.__link_dir = e.OptionMenu('Link direction:', dirstr, 0,
                                       (self.linkdir_callback, ()),
                                       right = None, top = None)
        self.__link_type = e.OptionMenu('type:', typestr, 0,
                                        (self.linktype_callback, ()),
                                        right = None,
                                        top = self.__link_dir)
        self.__ok_group = e.ButtonRow(
                [('Cancel', (self.cancel_callback, ())),
                 ('OK', (self.ok_callback, ())),
                 ],
                vertical = 0,
                bottom = None, top = self.__link_type, right = None)


        w.fix()

        # the below assignments are merely for efficiency
        self.settitle = self.__window.settitle
        self.is_showing = self.__window.is_showing
        self.linkdirsetsensitive = self.__link_dir.setsensitive
        self.linkdirsetchoice = self.__link_dir.setpos
        self.linkdirgetchoice = self.__link_dir.getpos
        self.linktypesetsensitive = self.__link_type.setsensitive
        self.linktypesetchoice = self.__link_type.setpos
        self.linktypegetchoice = self.__link_type.getpos

        self.show()

        for i in range(len(dirsens)):
            self.linkdirsetsensitive(i, dirsens[i])

    def close(self):
        """Close the dialog and free resources."""
        self.__window.close()
        del self.__window
        del self.__link_dir
        del self.__link_type
        del self.__ok_group

        # the below del's only if efficiency assignments above are done
        del self.settitle
        del self.is_showing
        del self.linkdirsetsensitive
        del self.linkdirsetchoice
        del self.linkdirgetchoice

    def show(self):
        """Show the dialog."""
        self.__window.show()

    def hide(self):
        """Hide the dialog."""
        self.__window.hide()

    def settitle(self, title):
        """Set (change) the title of the window.

        Arguments (no defaults):
        title -- string to be displayed as new window title.
        """
        self.__window.settitle(title)

    def is_showing(self):
        """Return whether dialog is showing."""
        return self.__window.is_showing()

    def oksetsensitive(self, sensitive):
        """Make the Add button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__ok_group.setsensitive(1, sensitive)

    def cancelsetsensitive(self, sensitive):
        """Make the Add button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__ok_group.setsensitive(0, sensitive)

    def linkdirsetsensitive(self, pos, sensitive):
        """Make an entry in the link dir menu (in)sensitive.

        Arguments (no defaults):
        pos -- the index of the entry to be made (in)sensitve
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__link_dir.setsensitive(pos, sensitive)

    def linkdirsetchoice(self, choice):
        """Set the current choice of the link dir list.

        Arguments (no defaults):
        choice -- index of the new choice
        """
        self.__link_dir.setpos(choice)

    def linkdirgetchoice(self):
        """Return the current choice in the link dir list."""
        return self.__link_dir.getpos()

    def linktypesetsensitive(self, pos, sensitive):
        """Make an entry in the link type menu (in)sensitive.

        Arguments (no defaults):
        pos -- the index of the entry to be made (in)sensitve
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self.__link_type.setsensitive(pos, sensitive)

    def linktypesetchoice(self, choice):
        """Set the current choice of the link type list.

        Arguments (no defaults):
        choice -- index of the new choice
        """
        self.__link_type.setpos(choice)

    def linktypegetchoice(self):
        """Return the current choice in the link type list."""
        return self.__link_type.getpos()
    # Callback functions.  These functions should be supplied by
    # the user of this class (i.e., the class that inherits from
    # this class).

    def linkdir_callback(self):
        """Called when a new link direction entry is selected."""
        pass

    def linktype_callback(self):
        """Called when a new link type entry is selected."""
        pass

    def ok_callback(self):
        """Called when `OK' button is pressed."""
        pass

    def cancel_callback(self):
        """Called when `Cancel' button is pressed."""
        pass
