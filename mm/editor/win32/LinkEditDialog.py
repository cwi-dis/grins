"""Dialog for the LinkEditor.

The LinkEditDialog is a window that displays three lists from which
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

""" @win32doc|LinkEditDialog
This class represents the interface between the LinkEdit platform independent
class and its implementation class LinkForm in lib/win32/LinkForm.py which 
implements the actual dialog.

"""
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
		self._adornments={'form_id':'leview_',
			'callbacks':{
				'LeftPushFocus':(self.show_callback, (cbarg1,)),
				'LeftAnchorEd':(self.anchoredit_callback, (cbarg1,)),
				'LeftList':(self.anchor_browser_callback, (cbarg1,)),
				'AddLink':(self.link_new_callback, ()),
				'EditLink':(self.link_edit_callback, ()),
				'DeleteLink':(self.link_delete_callback, ()),
				'LinkList':(self.link_browser_callback, ()),
				'RightPushFocus':(self.show_callback, (cbarg2,)),
				'RightAnchorEd':(self.anchoredit_callback, (cbarg2,)),
				'RightList':(self.anchor_browser_callback, (cbarg2,)),
			}
		}
		# hold args so that we can create wnd later
		self._init_args=(title, menu1, cbarg1, menu2, cbarg2,self._adornments)
		self.__window=None
								
	def is_showing(self):
		if not self.__window: return 0
		return self.__window.is_showing()

	def show(self):
		self.assertcreated()
		self.__window.show()

	# needed because core-code supposes that wnd has been created
	# as an os object but it isn't before self.show
	def assertcreated(self):
		toplevel_window=self.toplevel.window
		if not self.__window:
			w=toplevel_window.newviewobj(self._adornments['form_id'])
			apply(w.do_init,self._init_args)
			self.__window=w	
		if not self.__window.is_oswindow():
			toplevel_window.showview(self.__window,'leview_')
			self.__window.show()

	def hide(self):
		if not self.__window: return
		if self.is_showing():
			self.__window.close()
		self.__window=None

	def close(self):
		if not self.__window: return
		if self.is_showing():
			self.__window.close()
		self.__window=None

	def settitle(self,title):
		pass

	# Interface to the left list and associated buttons.
	def lefthide(self):
		"""Hide the left list with associated buttons."""
		self.__window.lefthide()
		
	def leftshow(self):
		"""Show the left list with associated buttons."""
		self.assertcreated()
		self.__window.leftshow()

	def leftsetlabel(self, label):
		"""Set the label for the left list.

		Arguments (no defaults):
		label -- string -- the label to be displayed
		"""
		self.assertcreated()
		self.__window.leftsetlabel(label)

	def leftdellistitems(self, poslist):
		"""Delete items from left list.

		Arguments (no defaults):
		poslist -- list of integers -- the indices of the
			items to be deleted
		"""
		self.__window.leftdellistitems(poslist)

	def leftdelalllistitems(self):
		"""Delete all items from the left list."""
		self.__window.leftdelalllistitems()

	def leftaddlistitems(self, items, pos):
		"""Add items to the left list.

		Arguments (no defaults):
		items -- list of strings -- the items to be added
		pos -- integer -- the index of the item before which
			the items are to be added (-1: add at end)
		"""
		self.__window.leftaddlistitems(items, pos)

	def leftreplacelistitem(self, pos, newitem):
		"""Replace an item in the left list.

		Arguments (no defaults):
		pos -- the index of the item to be replaced
		newitem -- string -- the new item
		"""
		self.__window.leftreplacelistitem(pos, newitem)
		
	def leftselectitem(self, pos):
		"""Select an item in the left list.

		Arguments (no defaults):
		pos -- integer -- the index of the item to be selected
		"""
		self.__window.leftselectitem(pos)

	def leftgetselected(self):
		"""Return the index of the currently selected item or None."""
		return self.__window.leftgetselected()

	def leftgetlist(self):
		"""Return the left list as a list of strings."""
		return self.__window.leftgetlist()

	def leftmakevisible(self, pos):
		"""Maybe scroll list to make an item visible.

		Arguments (no defaults):
		pos -- index of item to be made visible.
		"""
		self.__window.leftmakevisible(pos)
		
	def leftbuttonssetsensitive(self, sensitive):
		"""Make the left buttons (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__window.leftbuttonssetsensitive(sensitive)

	# Interface to the right list and associated buttons.
	def righthide(self):
		"""Hide the right list with associated buttons."""
		self.__window.righthide()

	def rightshow(self):
		"""Show the right list with associated buttons."""
		self.__window.rightshow()

	def rightsetlabel(self, label):
		"""Set the label for the right list.

		Arguments (no defaults):
		label -- string -- the label to be displayed
		"""
		self.__window.rightsetlabel(label)

	def rightdellistitems(self, poslist):
		"""Delete items from right list.

		Arguments (no defaults):
		poslist -- list of integers -- the indices of the
			items to be deleted
		"""
		self.__window.rightdellistitems(poslist)

	def rightdelalllistitems(self):
		"""Delete all items from the right list."""
		self.__window.rightdelalllistitems()

	def rightaddlistitems(self, items, pos):
		"""Add items to the right list.

		Arguments (no defaults):
		items -- list of strings -- the items to be added
		pos -- integer -- the index of the item before which
			the items are to be added (-1: add at end)
		"""
		self.__window.rightaddlistitems(items, pos)

	def rightreplacelistitem(self, pos, newitem):
		"""Replace an item in the right list.

		Arguments (no defaults):
		pos -- the index of the item to be replaced
		newitem -- string -- the new item
		"""
		self.__window.rightreplacelistitem(pos, newitem)
		
	def rightselectitem(self, pos):
		"""Select an item in the right list.

		Arguments (no defaults):
		pos -- integer -- the index of the item to be selected
		"""
		self.__window.rightselectitem(pos)

	def rightgetselected(self):
		"""Return the index of the currently selected item or None."""
		return self.__window.rightgetselected()

	def rightgetlist(self):
		"""Return the right list as a list of strings."""
		return self.__window.rightgetlist()

	def rightmakevisible(self, pos):
		"""Maybe scroll list to make an item visible.

		Arguments (no defaults):
		pos -- index of item to be made visible.
		"""
		self.__window.rightmakevisible(pos)

	def rightbuttonssetsensitive(self, sensitive):
		"""Make the right buttons (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__window.rightbuttonssetsensitive(sensitive)

	# Interface to the middle list and associated buttons.
	def middlehide(self):
		"""Hide the middle list with associated buttons."""
		self.assertcreated()
		self.__window.middlehide()
		
	def middleshow(self):
		"""Show the middle list with associated buttons."""
		self.__window.middleshow()

	def middledelalllistitems(self):
		"""Delete all items from the middle list."""
		self.__window.middledelalllistitems()

	def middleaddlistitems(self, items, pos):
		"""Add items to the middle list.

		Arguments (no defaults):
		items -- list of strings -- the items to be added
		pos -- integer -- the index of the item before which
			the items are to be added (-1: add at end)
		"""
		self.__window.middleaddlistitems(items, pos)

	def middleselectitem(self, pos):
		"""Select an item in the middle list.

		Arguments (no defaults):
		pos -- integer -- the index of the item to be selected
		"""
		self.__window.middleselectitem(pos)

	def middlegetselected(self):
		"""Return the index of the currently selected item or None."""
		return self.__window.middlegetselected()

	def middlemakevisible(self, pos):
		"""Maybe scroll list to make an item visible.

		Arguments (no defaults):
		pos -- index of item to be made visible.
		"""
		self.__window.middlemakevisible(pos)

	def addsetsensitive(self, sensitive):
		"""Make the Add button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__window.addsetsensitive(sensitive)

	def editsetsensitive(self, sensitive):
		"""Make the Edit button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__window.editsetsensitive(sensitive)

	def deletesetsensitive(self, sensitive):
		"""Make the Delete button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__window.deletesetsensitive(sensitive)

	# Interface to the edit group.
	def editgrouphide(self):
		"""Hide the edit group."""
		self.__window.editgrouphide()

	def editgroupshow(self):
		"""Show the edit group."""
		self.__window.editgroupshow()

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
	def __init__(self, title, dirstr, typestr, dir, type):
		cbd = {
				'OK':(self.ok_callback, ()),
				'Cancel':(self.cancel_callback, ()),
				'LinkDir':(self.linkdir_callback, ()),
				'LinkType':(self.linktype_callback, ()),
		}
		self.__window = windowinterface.LinkPropDlg(cbd, dir, type)

	def show(self):
		self.__window.show()

	def close(self):
		pass

	def oksetsensitive(self, sensitive):
		"""Make the Add button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		pass

	def cancelsetsensitive(self, sensitive):
		"""Make the Add button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		pass

	def linkdirsetsensitive(self, pos, sensitive):
		"""Make an entry in the link dir menu (in)sensitive.

		Arguments (no defaults):
		pos -- the index of the entry to be made (in)sensitve
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		pass

	def linkdirsetchoice(self, choice):
		"""Set the current choice of the link dir list.

		Arguments (no defaults):
		choice -- index of the new choice
		"""
		self.__window.linkdirsetchoice(choice)

	def linkdirgetchoice(self):
		"""Return the current choice in the link dir list."""
		return self.__window.linkdirgetchoice()

	def linktypesetsensitive(self, pos, sensitive):
		"""Make an entry in the link type menu (in)sensitive.

		Arguments (no defaults):
		pos -- the index of the entry to be made (in)sensitve
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self.__window.linktypesetsensitive(pos, sensitive)

	def linktypesetchoice(self, choice):
		"""Set the current choice of the link type list.

		Arguments (no defaults):
		choice -- index of the new choice
		"""
		self.__window.linktypesetchoice(choice)

	def linktypegetchoice(self):
		"""Return the current choice in the link type list."""
		return self.__window.linktypegetchoice()

