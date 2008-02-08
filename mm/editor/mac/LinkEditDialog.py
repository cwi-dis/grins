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

from Carbon import Dlg
from Carbon import Qd

import windowinterface
import WMEVENTS

def ITEMrange(fr, to): return range(fr, to+1)
# Dialog info
from mw_resources import ID_DIALOG_LINKBROWSE, ID_DIALOG_LINKEDIT

# Browser window dialog
ITEM_LEFT_ATITLE=1
ITEM_LEFT_NODE=2
ITEM_LEFT_NODESELECT=3
ITEM_LEFT_ALIST=4
ITEM_LEFT_PUSH=5
ITEM_LEFT_AEDIT=6
ITEMLIST_LEFT=ITEMrange(ITEM_LEFT_ALIST, ITEM_LEFT_AEDIT)
ITEMLIST_LEFT_BUTTONS=ITEMrange(ITEM_LEFT_PUSH, ITEM_LEFT_AEDIT)

ITEM_RIGHT_ATITLE=7
ITEM_RIGHT_NODE=8
ITEM_RIGHT_NODESELECT=9
ITEM_RIGHT_ALIST=10
ITEM_RIGHT_ADDEXT=18
ITEM_RIGHT_PUSH=11
ITEM_RIGHT_AEDIT=12
ITEMLIST_RIGHT=ITEMrange(ITEM_RIGHT_ALIST, ITEM_RIGHT_AEDIT)+[ITEM_RIGHT_ADDEXT]
ITEMLIST_RIGHT_BUTTONS=ITEMrange(ITEM_RIGHT_PUSH, ITEM_RIGHT_AEDIT)

ITEM_LINKS_TITLE=13
ITEM_LINKS_LLIST=14
ITEM_LINKS_ADD=15
ITEM_LINKS_EDIT=16
ITEM_LINKS_DELETE=17
ITEMLIST_LINKS=ITEMrange(ITEM_LINKS_TITLE, ITEM_LINKS_DELETE)

ITEM_BROWSER_BALLOONHELP=19
ITEMLIST_BROWSER_ALL=ITEMrange(ITEM_LEFT_ATITLE, ITEM_BROWSER_BALLOONHELP)


# Editor window dialog
ITEM_DIR_TITLE=1
ITEM_DIR_RIGHT=2
ITEM_DIR_LEFT=3
ITEM_DIR_BOTH=4
ITEM_TYPE_TITLE=5
ITEM_TYPE_JUMP=6
ITEM_TYPE_CALL=7
ITEM_TYPE_FORK=8
ITEM_CANCEL=9
ITEM_OK=10

ITEM_EDITOR_BALLOONHELP=1

ITEMLIST_DIR=ITEMrange(ITEM_DIR_TITLE, ITEM_DIR_BOTH)
ITEMLIST_TYPE=ITEMrange(ITEM_TYPE_TITLE, ITEM_TYPE_FORK)

ITEMLIST_EDITOR_ALL=ITEMrange(ITEM_DIR_TITLE, ITEM_EDITOR_BALLOONHELP)

__version__ = "$Id$"

class LinkBrowserDialog(windowinterface.MACDialog):
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
        windowinterface.MACDialog.__init__(self, title, ID_DIALOG_LINKBROWSE,
                        ITEMLIST_BROWSER_ALL, cancel=self._close_window)
        self._window.register(WMEVENTS.WindowExit, self._close_window, ())

        self._left_client_data = cbarg1
        self._right_client_data = cbarg2

        # Create the scrolled lists
        self._leftlist = self._window.ListWidget(ITEM_LEFT_ALIST)
        self._rightlist = self._window.ListWidget(ITEM_RIGHT_ALIST)
        self._linklist = self._window.ListWidget(ITEM_LINKS_LLIST)
##         self._rightlist.setcellsize(1024, 0) XXXX does not work...

        # Create the menus
        self._leftmenu = windowinterface.FullPopupMenu(menu1)
        self._rightmenu = windowinterface.FullPopupMenu(menu2)
        self.addexternalsetsensitive(0)

    def _close_window(self, *dummies):
        self.delete_callback()

    def do_itemhit(self, item, event):
        if item == ITEM_LEFT_NODESELECT:
            self._showmenu(event, ITEM_LEFT_NODESELECT, self._leftmenu)
        elif item == ITEM_LEFT_ALIST:
##             self._listclick(event, self._leftlist, self.anchor_browser_callback,
##                     (self._left_client_data,))
            self.anchor_browser_callback(self._left_client_data)
        elif item == ITEM_LEFT_PUSH:
            self.show_callback(self._left_client_data)
        elif item == ITEM_LEFT_AEDIT:
            self.anchoredit_callback(self._left_client_data)

        elif item == ITEM_RIGHT_NODESELECT:
            self._showmenu(event, ITEM_RIGHT_NODESELECT, self._rightmenu)
        elif item == ITEM_RIGHT_ALIST:
##             self._listclick(event, self._rightlist, self.anchor_browser_callback,
##                     (self._right_client_data,))
            double = self._rightlist.lastclickwasdouble()
            print 'Double:', `double`
            if double:
                data = self._rightlist.getselectvalue()
                if data:
                    windowinterface.showmessage(data)
            self.anchor_browser_callback(self._right_client_data)
        elif item == ITEM_RIGHT_PUSH:
            self.show_callback(self._right_client_data)
        elif item == ITEM_RIGHT_AEDIT:
            self.anchoredit_callback(self._right_client_data)
        elif item == ITEM_RIGHT_ADDEXT:
            self.add_external_callback()

        elif item == ITEM_LINKS_LLIST:
##             self._listclick(event, self._linklist, self.link_browser_callback, ())
            self.link_browser_callback()
        elif item == ITEM_LINKS_ADD:
            self.link_new_callback()
        elif item == ITEM_LINKS_EDIT:
            self.link_edit_callback()
        elif item == ITEM_LINKS_DELETE:
            self.link_delete_callback()
        else:
            print 'Unexpected dialog browser event, item', item, 'event', event
        return 1

    def _showmenu(self, event, baseitem, menu):
        tp, h, (x0, y0, x1, y1) = self._dialog.GetDialogItem(baseitem)
        Qd.SetPort(self._dialog)
        y, x = Qd.LocalToGlobal((x0, y0))
        menu.popup(x, y, event, self._window)


    # Interface to the left list and associated buttons.
    def lefthide(self):
        """Hide the left list with associated buttons."""
        self._hideitemlist(ITEMLIST_LEFT)

    def leftshow(self):
        """Show the left list with associated buttons."""
        self._showitemlist(ITEMLIST_LEFT)

    def leftsetlabel(self, label):
        """Set the label for the left list.

        Arguments (no defaults):
        label -- string -- the label to be displayed
        """
        self._setlabel(ITEM_LEFT_NODE, label)

    def leftdellistitems(self, poslist):
        """Delete items from left list.

        Arguments (no defaults):
        poslist -- list of integers -- the indices of the
                items to be deleted
        """
        poslist = poslist[:]
        poslist.sort()
        poslist.reverse()
        for pos in poslist:
            self._leftlist.delete(pos)

    def leftdelalllistitems(self):
        """Delete all items from the left list."""
        self._leftlist.delete()

    def leftaddlistitems(self, items, pos):
        """Add items to the left list.

        Arguments (no defaults):
        items -- list of strings -- the items to be added
        pos -- integer -- the index of the item before which
                the items are to be added (-1: add at end)
        """
        self._leftlist.insert(pos, items)

    def leftreplacelistitem(self, pos, newitem):
        """Replace an item in the left list.

        Arguments (no defaults):
        pos -- the index of the item to be replaced
        newitem -- string -- the new item
        """
        self._leftlist.replace(pos, newitem)

    def leftselectitem(self, pos):
        """Select an item in the left list.

        Arguments (no defaults):
        pos -- integer -- the index of the item to be selected
        """
        self._leftlist.select(pos)

    def leftgetselected(self):
        """Return the index of the currently selected item or None."""
        return self._leftlist.getselect()

    def leftgetlist(self):
        """Return the left list as a list of strings."""
        return self._leftlist.get()

    def leftmakevisible(self, pos):
        """Maybe scroll list to make an item visible.

        Arguments (no defaults):
        pos -- index of item to be made visible.
        """
        pass

    def leftbuttonssetsensitive(self, sensitive):
        """Make the left buttons (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive(ITEMLIST_LEFT_BUTTONS, sensitive)

    # Interface to the right list and associated buttons.
    def righthide(self):
        """Hide the right list with associated buttons."""
        self._hideitemlist(ITEMLIST_RIGHT)

    def rightshow(self):
        """Show the right list with associated buttons."""
        self._showitemlist(ITEMLIST_RIGHT)

    def rightsetlabel(self, label):
        """Set the label for the right list.

        Arguments (no defaults):
        label -- string -- the label to be displayed
        """
        self._setlabel(ITEM_RIGHT_NODE, label)

    def rightdellistitems(self, poslist):
        """Delete items from right list.

        Arguments (no defaults):
        poslist -- list of integers -- the indices of the
                items to be deleted
        """
        poslist = poslist[:]
        poslist.sort()
        poslist.reverse()
        for pos in poslist:
            self._rightlist.delete(pos)

    def rightdelalllistitems(self):
        """Delete all items from the right list."""
        self._rightlist.delete()

    def rightaddlistitems(self, items, pos):
        """Add items to the right list.

        Arguments (no defaults):
        items -- list of strings -- the items to be added
        pos -- integer -- the index of the item before which
                the items are to be added (-1: add at end)
        """
        self._rightlist.insert(pos, items)

    def rightreplacelistitem(self, pos, newitem):
        """Replace an item in the right list.

        Arguments (no defaults):
        pos -- the index of the item to be replaced
        newitem -- string -- the new item
        """
        self._rightlist.replace(pos, newitem)

    def rightselectitem(self, pos):
        """Select an item in the right list.

        Arguments (no defaults):
        pos -- integer -- the index of the item to be selected
        """
        self._rightlist.select(pos)

    def rightgetselected(self):
        """Return the index of the currently selected item or None."""
        return self._rightlist.getselect()

    def rightgetlist(self):
        """Return the right list as a list of strings."""
        return self._rightlist.get()

    def rightmakevisible(self, pos):
        """Maybe scroll list to make an item visible.

        Arguments (no defaults):
        pos -- index of item to be made visible.
        """
        pass

    def rightbuttonssetsensitive(self, sensitive):
        """Make the right buttons (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive(ITEMLIST_RIGHT_BUTTONS, sensitive)

    def addexternalsetsensitive(self, sensitive):
        self._setsensitive([ITEM_RIGHT_ADDEXT], sensitive)

    # Interface to the middle list and associated buttons.
    def middlehide(self):
        """Hide the middle list with associated buttons."""
        self._hideitemlist(ITEMLIST_LINKS)

    def middleshow(self):
        """Show the middle list with associated buttons."""
        self._showitemlist(ITEMLIST_LINKS)

    def middledelalllistitems(self):
        """Delete all items from the middle list."""
        self._linklist.delete()

    def middleaddlistitems(self, items, pos):
        """Add items to the middle list.

        Arguments (no defaults):
        items -- list of strings -- the items to be added
        pos -- integer -- the index of the item before which
                the items are to be added (-1: add at end)
        """
        self._linklist.insert(pos, items)

    def middleselectitem(self, pos):
        """Select an item in the middle list.

        Arguments (no defaults):
        pos -- integer -- the index of the item to be selected
        """
        self._linklist.select(pos)

    def middlegetselected(self):
        """Return the index of the currently selected item or None."""
        return self._linklist.getselect()

    def middlemakevisible(self, pos):
        """Maybe scroll list to make an item visible.

        Arguments (no defaults):
        pos -- index of item to be made visible.
        """
        pass

    def addsetsensitive(self, sensitive):
        """Make the Add button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive([ITEM_LINKS_ADD], sensitive)

    def editsetsensitive(self, sensitive):
        """Make the Edit button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive([ITEM_LINKS_EDIT], sensitive)

    def deletesetsensitive(self, sensitive):
        """Make the Delete button (in)sensitive.

        Arguments (no defaults):
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive([ITEM_LINKS_DELETE], sensitive)


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

## XXXX

class LinkEditorDialog(windowinterface.MACDialog):
    def __init__(self, title, dirstr, typestr, dir, type, dirsens):
        """Create the LinkEditor dialog.
        """
        windowinterface.MACDialog.__init__(self, title, ID_DIALOG_LINKEDIT,
                        ITEMLIST_EDITOR_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)
        self.linkdirsetchoice(dir)
        self.linktypesetchoice(type)
        for i in range(len(dirsens)):
            if not dirsens[i]:
                self._setsensitive([ITEM_DIR_RIGHT+i], 0)

    def show(self):
        windowinterface.MACDialog.show(self)
        self.rungrabbed()

    def _close_window(self, *dummies):
        self.delete_callback()

    def oksetsensitive(self, sensitive):
        self._setsensitive([ITEM_OK], sensitive)

    def do_itemhit(self, item, event):
        if item in ITEMLIST_DIR:
            self._dirclick(item-ITEM_DIR_RIGHT)
        elif item in ITEMLIST_TYPE:
            self._typeclick(item-ITEM_TYPE_JUMP)

        elif item == ITEM_CANCEL:
            self.cancel_callback()
        elif item == ITEM_OK:
            self.ok_callback()
        else:
            print 'Unexpected link edit dialog event, item', item, 'event', event
        return 1

    def _typeclick(self, item):
        self.linktypesetchoice(item)
        self.linktype_callback()

    def _dirclick(self, item):
        self.linkdirsetchoice(item)
        self.linkdir_callback()

    def linkdirsetsensitive(self, pos, sensitive):
        """Make an entry in the link dir menu (in)sensitive.

        Arguments (no defaults):
        pos -- the index of the entry to be made (in)sensitve
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive(ITEMLIST_DIR[pos+1:pos+2], sensitive)

    def linkdirsetchoice(self, choice):
        """Set the current choice of the link dir list.

        Arguments (no defaults):
        choice -- index of the new choice
        """
        for i in range(3):
            ctl = self._dialog.GetDialogItemAsControl(ITEM_DIR_RIGHT+i)
            if i == choice:
                ctl.SetControlValue(1)
            else:
                ctl.SetControlValue(0)

    def linkdirgetchoice(self):
        """Return the current choice in the link dir list."""
        for i in range(3):
            ctl = self._dialog.GetDialogItemAsControl(ITEM_DIR_RIGHT+i)
            if ctl.GetControlValue():
                return i
        raise 'No direction set?'

    def linktypesetsensitive(self, pos, sensitive):
        """Make an entry in the link type menu (in)sensitive.

        Arguments (no defaults):
        pos -- the index of the entry to be made (in)sensitve
        sensitive -- boolean indicating whether to make
                sensitive or insensitive
        """
        self._setsensitive(ITEMLIST_TYPE[pos+1:pos+2], sensitive)

    def linktypesetchoice(self, choice):
        """Set the current choice of the link type list.

        Arguments (no defaults):
        choice -- index of the new choice
        """
        for i in range(3):
            ctl = self._dialog.GetDialogItemAsControl(ITEM_TYPE_JUMP+i)
            if i == choice:
                ctl.SetControlValue(1)
            else:
                ctl.SetControlValue(0)

    def linktypegetchoice(self):
        """Return the current choice in the link type list."""
        for i in range(3):
            ctl = self._dialog.GetDialogItemAsControl(ITEM_TYPE_JUMP+i)
            if ctl.GetControlValue():
                return i
        raise 'No type set?'

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
