"""Dialog for the Transition View.

The Transition View is a window that displays a list of transitions and
gives the ability to edit these.

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


class TransitionViewDialog(windowinterface.MACDialog):
	def __init__(self):
		"""Create the TransitionView dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) but don't pop it up.
		"""

		windowinterface.MACDialog.__init__(self, "Transition view",
				ID_DIALOG_UGROUP_BROWSER, ITEMLIST_B_ALL)

		self.__list = self._window.ListWidget(ITEM_B_BROWSER)
##		self.selection_setlist(list, initial)

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

## 	def show(self):
## 		"""Show the dialog."""
## 		self.__window.show()
## 
## 	def is_showing(self):
## 		if self.__window is None:
## 			return 0
## 		return self.__window.is_showing()
## 
## 	def hide(self):
## 		"""Hide the dialog."""
## 		if self.__window is not None:
## 			self.__window.hide()

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
			print 'Unknown TransitionViewDialog item', item, 'event', event
		return 1
