"""Dialog for the AnchorEditor.

The AnchorEditorDialog is a window that displays two lists from which
the user can choose an item.  In both cases, the current selection
must be indicated.  In the case of the the types list, there is always
a selected item which is not editable.  Also, after creation, this
list doesn't change (although which item is selected might).  It may
be that some entries from the types list are not currently selectable.
It may also be that the type list and the accompanying label is not
shown.  The other list is the list of anchors.  This list is much more
dynamic.  The user can select one item in the list, and under certain
condition, edit the value.  Also, entries can be added or deleted
dynamically.  In Motif, the types list is presented as an OptionMenu,
and the anchor list as a SelectionBox (which consists of a scrollable
list and an text input area).  A callback is called when the user
selects an item from one of the lists, and when the user edits the
name of the currently selected anchor.

Apart from these two lists, there are 8 buttons, some of which may be
made insensitive (or hidden) under program control.  The buttons are
`Cancel', `Restore', `Apply', `OK', `New', `Edit...', `Delete', and
`Export...'.  These buttons form two groups.  New, Edit, Delete, and
Export work on the anchors, whereas Cancel, Restore, Apply, and OK
work on the whole dialog.  This means that the two sets should be
visually separate.  There are callbacks for all these buttons.

"""

__version__ = "$Id$"

import Dlg
import Qd
import windowinterface
import WMEVENTS

def ITEMrange(fr, to): return range(fr, to+1)

# Dialog info
from mw_resources import ID_DIALOG_ANCHOR
ITEM_BROWSER=1

ITEM_NEW=2
ITEM_EDIT=3
ITEM_DELETE=4
ITEM_EXPORT=5

ITEM_ID_TITLE=6
ITEM_ID=7
ITEM_ID_CHANGE=8

ITEM_TYPE_TITLE=9
ITEM_WHOLE=10
ITEM_DEST_ONLY=11
ITEM_NORMAL=12
ITEM_PAUSING=13
ITEM_AUTO=14
ITEM_COMPOSITE=15
ITEM_ARGUMENT=16
ITEMLIST_TYPE=ITEMrange(ITEM_TYPE_TITLE, ITEM_ARGUMENT)
ITEMFIRST_TYPE=ITEM_WHOLE
ITEMNUM_TYPE=(ITEM_ARGUMENT-ITEM_WHOLE)+1

ITEM_COMPDATA_LABEL=17
ITEM_COMPDATA=18
ITEMLIST_COMPDATA=ITEMrange(ITEM_COMPDATA_LABEL, ITEM_COMPDATA)

ITEM_CANCEL=19
ITEM_RESTORE=20
ITEM_APPLY=21
ITEM_OK=22

ITEM_BALLOONHELP=23
ITEMLIST_ALL=ITEMrange(ITEM_BROWSER, ITEM_BALLOONHELP)

class AnchorEditorDialog(windowinterface.MACDialog):
	def __init__(self, title, typelabels, list, initial):
		"""Create the AnchorEditor dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		typelabels -- list of strings--in the old dialog,
			these are the options after the Type: label.
			the initial selection is unspecified.
		list -- list of strings--this is the list of anchors
			that should be displayed initially
		initial -- 0 <= initial < len(list) or None--this is
			the index of the element in list which should
			have the focus (no element selected if None)
		"""

		windowinterface.MACDialog.__init__(self, title, ID_DIALOG_ANCHOR,
				ITEMLIST_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)
				
		# Enable correct set of type labels
		self.__numtypes = len(typelabels)

		self.__anchor_browser = self._window.ListWidget(ITEM_BROWSER)
		self.selection_setlist(list, initial)

		self.show()

	def do_itemhit(self, item, event):
		if item == ITEM_BROWSER:
			(what, message, when, where, modifiers) = event
			Qd.SetPort(self._dialog)
			where = Qd.GlobalToLocal(where)
			item, is_double = self.__anchor_browser.click(where, modifiers)
			self._setidfromlist()
			self.anchor_callback()
		elif item == ITEM_ID:
			self._setsensitive([ITEM_ID_CHANGE], 1)
		elif item == ITEM_ID_CHANGE:
			self.id_callback()
		elif item == ITEM_NEW:
			self.add_callback()
		elif item == ITEM_EDIT:
			self.edit_callback()
		elif item == ITEM_DELETE:
			self.delete_callback()
		elif item == ITEM_EXPORT:
			self.export_callback()
		elif item in ITEMLIST_TYPE:
			self.type_choice_setchoice(item-ITEMFIRST_TYPE)
			self.type_callback()
		elif item == ITEM_CANCEL:
			self.cancel_callback()
		elif item == ITEM_OK:
			self.ok_callback()
		elif item == ITEM_RESTORE:
			self.restore_callback()
		elif item == ITEM_APPLY:
			self.apply_callback()
		else:
			print 'Unknown AnchorEditDialog item', item, 'event', event
		return 1
		
	def _setidfromlist(self):
		"""Propagate list selection to id field"""
		num = self.__anchor_browser.getselect()
		if num == None:
			name = ''
		else:
			name = self.__anchor_browser.getitem(num)
		self._setlabel(ITEM_ID, name)
		self._setsensitive([ITEM_ID_CHANGE], 0)

	# Interface to the composite part of the window.  This part
	# consists of just a single label (piece of text) which can be
	# hidden or shown.  The text in the label can be changed at
	# run time and is initially just `Composite:'.
	def composite_hide(self):
		"""Hide the composite part of the dialog."""
		self._hideitemlist(ITEMLIST_COMPDATA)

	def composite_show(self):
		"""Show the composite part of the dialog."""
		self._showitemlist(ITEMLIST_COMPDATA)

	def composite_setlabel(self, label):
		"""Set the composite label.

		Arguments (no defaults):
		label -- string to display
		"""
		self._setlabel(ITEM_COMPDATA, label)

	# Interface to the type_choice part of the dialog.  This is a
	# part of the dialog that indicates to the user which of a
	# list of strings is currently selected, and it gives the user
	# the possibility to choose another item.  In Motif this is
	# implemented as a so-called OptionMenu.  It should be
	# possible to hide or deactivate this part of the window.
	def type_choice_hide(self):
		"""Hide the type choice part of the dialog."""
		self._hideitemlist(ITEMLIST_TYPE)

	def type_choice_show(self):
		"""Show the type choice part of the dialog."""
		self._showitemlist(ITEMLIST_TYPE[:self.__numtypes+1])

	def type_choice_setchoice(self, choice):
		"""Set the current choice.

		Arguments (no defaults):
		choice -- index in the list of choices that is to be
			the current choice
		"""
		if not choice in range(ITEMNUM_TYPE):
			print 'AnchorEditDialog: unexpected choice', choice
		for i in range(ITEMNUM_TYPE):
			tp, h, rect = self._dialog.GetDialogItem(ITEMFIRST_TYPE+i)
			ctl = h.as_Control()
			if i == choice:
				ctl.SetControlValue(1)
			else:
				ctl.SetControlValue(0)

	def type_choice_getchoice(self):
		"""Return the current choice (the index into the list)."""
		for i in range(ITEMNUM_TYPE):
			tp, h, rect = self._dialog.GetDialogItem(ITEMFIRST_TYPE+i)
			ctl = h.as_Control()
			if ctl.GetControlValue():
				return i
		raise 'No type set?'

	def type_choice_setsensitive(self, pos, sensitive):
		"""Make a choice sensitive or insensitive.

		Arguments (no defaults):
		pos -- index of the choice to be made (in)sensitive
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self._setsensitive(ITEMLIST_TYPE[pos+1:pos+2], sensitive)

	# Interface to the selection area.  The selection area
	# consists of a list of strings with the possibility to select
	# one of these strings, and to edit the value of the selected
	# string.  In some cases, the string should not be editable
	# (see below).  If a string is selected a callback should be
	# called; if the string is edited, another callback should be
	# called.
	def selection_seteditable(self, editable):
		"""Make the selected string editable or not."""
		self._settextsensitive([ITEM_ID], editable)
		if not editable:
			self._setsensitive([ITEM_ID_CHANGE], 0)

	def selection_setlist(self, list, initial):
		"""Set the list of strings.

		Arguments (no defaults):
		list -- list of strings
		initial -- 0 <= initial < len(list) or None -- this is
			the index of the element in list which should
			be the selected item (no element is selected
			if None)
		"""
		self.__anchor_browser.set(list)
		self.__anchor_browser.select(initial)
		self._setidfromlist()

	def selection_setselection(self, pos):
		"""Set the selection to the item indicated.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) or None -- the index of
			the item to be selected
		"""
		self.__anchor_browser.select(pos)
		self._setidfromlist()

	def selection_getselection(self):
		"""Return the index of the currently selected item.

		The return value is the index of the currently
		selected item, or None if no item is selected.
		"""
		return self.__anchor_browser.getselect()

	def selection_append(self, item):
		"""Append an item to the end of the list.

		Which item is selected after the element is added is
		undefined.  The list which was given to
		selection_setlist or __init__ (whichever was last) is
		modified.
		"""
		self.__anchor_browser.insert(-1, [item])

	def selection_gettext(self):
		"""Return the string value of the currently selected item.

		When no item is selected, the behavior is undefined.
		[ This method is called in the id_callback to get the
		new value of the currently selected item. ]
		"""
		return self._getlabel(ITEM_ID)

	def selection_replaceitem(self, pos, item):
		"""Replace the indicated item with a new value.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be changed
		item -- string to replace the item with
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self.__anchor_browser.replace(pos, item)
		self._setidfromlist()

	def selection_deleteitem(self, pos):
		"""Delete the indicated item from the list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be deleted
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self.__anchor_browser.delete(pos)
		self._setidfromlist()

	# Interface to the various button.
	def edit_setsensitive(self, sensitive):
		"""Make the `Edit' button (in)sensitive."""
		self._setsensitive([ITEM_EDIT], sensitive)

	def delete_setsensitive(self, sensitive):
		"""Make the `Delete' button (in)sensitive."""
		self._setsensitive([ITEM_DELETE], sensitive)

	def export_setsensitive(self, sensitive):
		"""Make the `Export...' button (in)sensitive."""
		self._setsensitive([ITEM_EXPORT], sensitive)

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def cancel_callback(self):
		"""Called when `Cancel' button is pressed."""
		pass

	def restore_callback(self):
		"""Called when `Restore' button is pressed."""
		pass

	def apply_callback(self):
		"""Called when `Apply' button is pressed."""
		pass

	def ok_callback(self):
		"""Called when `OK' button is pressed."""
		pass

	def add_callback(self):
		"""Called when `Add' button is pressed."""
		pass

	def edit_callback(self):
		"""Called when `Edit...' button is pressed."""
		pass

	def delete_callback(self):
		"""Called when `Delete' button is pressed."""
		pass

	def export_callback(self):
		"""Called when `Export...' button is pressed."""
		pass

	def anchor_callback(self):
		"""Called when a new selection is made in the list."""
		pass

	def id_callback(self):
		"""Called when the name of the current selection is changed."""
		pass

	def type_callback(self):
		"""Called when a new type is selected."""
		pass
