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

import windowinterface

class AnchorEditorDialog:
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

		self.__window = w = windowinterface.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))

		buttons = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			bottom = None, left = None, right = None, vertical = 0)
		self.__composite = w.Label('Composite:', useGadget = 0,
					   bottom = buttons, left = None,
					   right = None)
		self.__type_choice = w.OptionMenu('Type:', typelabels, 0,
						  (self.type_callback, ()),
						  bottom = self.__composite,
						  left = None, right = None)
		self.__buttons = w.ButtonRow(
			[('New', (self.add_callback, ())),
			 ('Edit...', (self.edit_callback, ())),
			 ('Delete', (self.delete_callback, ())),
			 ('Export...', (self.export_callback, ()))],
			top = None, right = None)
		self.__anchor_browser = w.Selection(
			None, 'Id:', list, initial, (self.anchor_callback, ()),
			top = None, left = None, right = self.__buttons,
			bottom = self.__type_choice,
			enterCallback = (self.id_callback, ()))
		w.show()

	def close(self):
		"""Close the dialog and free resources."""
		self.__window.close()
		# delete some attributes so that GC can collect them
		del self.__window
		del self.__composite
		del self.__type_choice
		del self.__buttons
		del self.__anchor_browser

	def pop(self):
		"""Pop the dialog window to the foreground."""
		self.__window.pop()

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self.__window.settitle(title)

	# Interface to the composite part of the window.  This part
	# consists of just a single label (piece of text) which can be
	# hidden or shown.  The text in the label can be changed at
	# run time and is initially just `Composite:'.
	def composite_hide(self):
		"""Hide the composite part of the dialog."""
		self.__composite.hide()

	def composite_show(self):
		"""Show the composite part of the dialog."""
		self.__composite.show()

	def composite_setlabel(self, label):
		"""Set the composite label.

		Arguments (no defaults):
		label -- string to display
		"""
		self.__composite.setlabel(label)

	# Interface to the type_choice part of the dialog.  This is a
	# part of the dialog that indicates to the user which of a
	# list of strings is currently selected, and it gives the user
	# the possibility to choose another item.  In Motif this is
	# implemented as a so-called OptionMenu.  It should be
	# possible to hide or deactivate this part of the window.
	def type_choice_hide(self):
		"""Hide the type choice part of the dialog."""
		self.__type_choice.hide()

	def type_choice_show(self):
		"""Show the type choice part of the dialog."""
		self.__type_choice.show()

	def type_choice_setchoice(self, choice):
		"""Set the current choice.

		Arguments (no defaults):
		choice -- index in the list of choices that is to be
			the current choice
		"""
		self.__type_choice.setpos(choice)

	def type_choice_getchoice(self):
		"""Return the current choice (the index into the list)."""
		return self.__type_choice.getpos()

	def type_choice_setsensitive(self, pos, sensitive):
		"""Make a choice sensitive or insensitive.

		Arguments (no defaults):
		pos -- index of the choice to be made (in)sensitive
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__type_choice.setsensitive(pos, sensitive)

	# Interface to the selection area.  The selection area
	# consists of a list of strings with the possibility to select
	# one of these strings, and to edit the value of the selected
	# string.  In some cases, the string should not be editable
	# (see below).  If a string is selected a callback should be
	# called; if the string is edited, another callback should be
	# called.
	def selection_seteditable(self, editable):
		"""Make the selected string editable or not."""
		self.__anchor_browser.seteditable(editable)

	def selection_setlist(self, list, initial):
		"""Set the list of strings.

		Arguments (no defaults):
		list -- list of strings
		initial -- 0 <= initial < len(list) or None -- this is
			the index of the element in list which should
			be the selected item (no element is selected
			if None)
		"""
		self.__anchor_browser.delalllistitems()
		self.__anchor_browser.addlistitems(list, -1)
		self.__anchor_browser.selectitem(initial)

	def selection_setselection(self, pos):
		"""Set the selection to the item indicated.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) or None -- the index of
			the item to be selected
		"""
		self.__anchor_browser.selectitem(pos)

	def selection_getselection(self):
		"""Return the index of the currently selected item.

		The return value is the index of the currently
		selected item, or None if no item is selected.
		"""
		return self.__anchor_browser.getselected()

	def selection_append(self, item):
		"""Append an item to the end of the list.

		Which item is selected after the element is added is
		undefined.  The list which was given to
		selection_setlist or __init__ (whichever was last) is
		modified.
		"""
		self.__anchor_browser.addlistitem(item, -1)

	def selection_gettext(self):
		"""Return the string value of the currently selected item.

		When no item is selected, the behavior is undefined.
		[ This method is called in the id_callback to get the
		new value of the currently selected item. ]
		"""
		return self.__anchor_browser.getselection()

	def selection_replaceitem(self, pos, item):
		"""Replace the indicated item with a new value.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be changed
		item -- string to replace the item with
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self.__anchor_browser.replacelistitem(pos, item)

	def selection_deleteitem(self, pos):
		"""Delete the indicated item from the list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be deleted
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self.__anchor_browser.dellistitem(pos)

	# Interface to the various button.
	def edit_setsensitive(self, sensitive):
		"""Make the `Edit' button (in)sensitive."""
		self.__buttons.setsensitive(1, sensitive)

	def delete_setsensitive(self, sensitive):
		"""Make the `Delete' button (in)sensitive."""
		self.__buttons.setsensitive(2, sensitive)

	def export_setsensitive(self, sensitive):
		"""Make the `Export...' button (in)sensitive."""
		self.__buttons.setsensitive(3, sensitive)

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
