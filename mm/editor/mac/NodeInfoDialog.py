"""Dialog for the NodeInfo dialog.

There are three different types of NodeInfo dialogs.  Only one of
these can be displayed at any one time, but it must be possible to
switch between the three.  This is always done under program control.
Apart from the variable part, there is also a constant part.  This
constant part is described first, the three different variable parts
are described after that.

The constant part of the dialog consists of the following items:
- An editable text field with a `Name:' label.  There is no callback
  associated with this text field, but it must be possible to read the
  text.
- A list of items of which one is always selected, and which does not
  change over time.  There is a label `Type:' associated with this
  list.  When the user changes the current selection, a callback must
  be called.  Also, it must be possible to set the current selection
  under program control.
- A list if items of which one is always selected, but which can be
  changed under program control.  When the user changes the current
  selection, a callback must be called.  Also, it must be possible to
  set the current selection under program control.
- Buttons, each with their own callback: `Cancel', `Restore', `Apply',
  `OK', `Node properties...', and `Anchors...'.

The three variable parts are known as external, immediate, and
interior.  A description of each follows.

The external part consists of an interface to show and select a file
name (actually: a URL) and a button `Edit contents...'.  [ In Motif,
there is an editable text field and a `Browser...' button. ]  When the
file name is changed, a callback is called.  There is also a callback
for the browser button (although that could conceivably be changed so
that the browser is called from within NodeInfoDialog instead of from
the parent class).

The immediate part consists of an editable text area.  There are no
callbacks associated with this text area, but it must be possible to
read the text.

The internal part consists of a list of items.  It must be possible to
select one item and get the selection programmatically.  There must be
an interface to 'open' the selection (double clicking, `Open...'
button, whatever) at which time a callback is called.

"""

__version__ = "$Id$"

import Dlg
import Qd
import string
import windowinterface
import WMEVENTS

def ITEMrange(fr, to): return range(fr, to+1)
# Dialog info
from mw_resources import ID_DIALOG_NODEINFO

ITEM_NAME_LABEL=1
ITEM_NAME=2
ITEM_TYPE=3
ITEM_CHANNEL=4

ITEM_CANCEL=5
ITEM_RESTORE=6
ITEM_ATTREDIT=7
ITEM_ANCHOREDIT=8
ITEM_APPLY=9
ITEM_OK=10

ITEM_URL_LABEL=11
ITEM_URL=12
ITEM_URL_BROWSE=13
ITEM_URL_EDIT=14
ITEMLIST_EXT=ITEMrange(ITEM_URL_LABEL, ITEM_URL_EDIT)

ITEM_IMM_LABEL=15
ITEM_IMM=16
ITEMLIST_IMM=ITEMrange(ITEM_IMM_LABEL, ITEM_IMM)

ITEM_BALLOONHELP=17
ITEMLIST_ALL=ITEMrange(1, ITEM_BALLOONHELP)

class NodeInfoDialog(windowinterface.MACDialog):
	def __init__(self, title, channelnames, initchannel, types, inittype,
		     name, filename, children, immtext):
		"""Create the NodeInfo dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		channelnames -- list of strings, one of which is
			always selected
		initchannel -- 0 <= initchannel < len(channelnames) --
			the initial selection of the channelnames
		types -- list of strings, one of which is always
			selected
		inittype -- 0 <= inittype < len(types) -- the initial
			selection of the types
		name -- string, the initial value for the name field
		filename -- string, the initial value for the file
			name field, to be displayed as the file name
			in the exterior part
		children -- list of strings -- the list of strings to
			be displayed in the interior part
		immtext -- list of strings or a single string with
			embedded linefeeds -- the text to be displayed
			in the immediate part
		"""
		windowinterface.MACDialog.__init__(self, title, ID_DIALOG_NODEINFO,
				ITEMLIST_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)
				
		self.__type_select=windowinterface.SelectWidget(self._dialog, ITEM_TYPE,
				types, inittype, self.type_callback)
		self.__channel_select=windowinterface.SelectWidget(self._dialog, ITEM_CHANNEL,
				channelnames, initchannel, self.channel_callback)

		self.setname(name)
		self.setfilename(filename)
		self.settext(immtext)
		
		if immtext:
			self.imm_group_show()
		elif filename:
			self.ext_group_show()
		else:
			self.int_group_show()
				
		self.show()

	def close(self):
		self.__channel_select.delete()
		self.__type_select.delete()
		windowinterface.MACDialog.close(self)

	def do_itemhit(self, item, event):
		if item == ITEM_NAME:
			pass
		elif item == ITEM_TYPE:
			self.__type_select.click()
		elif item == ITEM_CHANNEL:
			self.__channel_select.click()
		elif item == ITEM_ATTREDIT:
			self.attributes_callback()
		elif item == ITEM_ANCHOREDIT:
			self.anchors_callback()
		elif item == ITEM_URL:
			self.file_callback()
		elif item == ITEM_URL_BROWSE:
			self.browser_callback()
		elif item == ITEM_URL_EDIT:
			self.conteditor_callback()
		elif item == ITEM_IMM:
			pass
		elif item == ITEM_CANCEL:
			self.cancel_callback()
		elif item == ITEM_OK:
			self.ok_callback()
		elif item == ITEM_RESTORE:
			self.restore_callback()
		elif item == ITEM_APPLY:
			self.apply_callback()
		else:
			print 'Unknown NodeInfoDialog item', item, 'event', event
		return 1

	# Interface to the list of channel names.  This part consists
	# of a label and a list of strings of which one is always the
	# current selection.  Only one element of the list needs to be
	# visible (the current selection) but it must be possible to
	# choose from the list.
	def setchannelnames(self, channelnames, initchannel):
		"""Set the list of strings and the initial selection.

		Arguments (no defaults):
		channelnames -- list of strings
		initchannel -- 0 <= initchannel < len(channelnames) --
			the initial selection
		"""
		self.__channel_select.setitems(channelnames, initchannel)

	def getchannelname(self):
		"""Get the string which is the current selection."""
		return self.__channel_select.getselect()

	def askchannelname(self, default):
		windowinterface.InputDialog('Name for new channel',
					    default,
					    self.newchan_callback,
					    cancelCallback = (self.newchan_callback, ()))

	# Interface to the list of node types.  This part consists of
	# a label and a list of strings of which one is always the
	# current selection.  Only one element of the list needs to be
	# visible (the current selection) but it must be possible to
	# choose from the list.
	def settypes(self, types, inittype):
		"""Set the list of strings and the initial selection.

		Arguments (no defaults):
		types -- list of strings
		inittype -- 0 <= inittype < len(types) -- the initial
			selection
		"""
		self.__type_select.setitems(types, inittype)

	def gettype(self):
		"""Get the string which is the current selection."""
		return self.__type_select.getselect()

	def settype(self, inittype):
		"""Set the current selection.

		Arguments (no defaults):
		inittype -- 0 <= inittype < len(types) -- the new
			current selection
		"""
		self.__type_select.select(inittype)

	# Interface to the name field.  This part consists of an
	# editable text field.
	def setname(self, name):
		"""Set the value of the name field.

		Arguments (no defaults):
		name -- string
		"""
		self._setlabel(ITEM_NAME, name)
		self._selectinputfield(ITEM_NAME)

	def getname(self):
		"""Return the current value of the name field."""
		return self._getlabel(ITEM_NAME)

	# The following methods choose between the three variable
	# parts.  One of the parts is active (the others need not be
	# shown), and when one of the parts is made the active part,
	# the others are automatically made inactive (possibly
	# hidden).
	# In Motif, this is done by using the same screen area for the
	# three parts.
	def imm_group_show(self):
		"""Make the immediate part visible."""
		self._hideitemlist(ITEMLIST_EXT)
		#self._hideitemlist(ITEMLIST_INT)
		self._showitemlist(ITEMLIST_IMM)

	def int_group_show(self):
		"""Make the interior part visible."""
		self._hideitemlist(ITEMLIST_EXT)
		self._hideitemlist(ITEMLIST_IMM)
		#self._showitemlist(ITEMLIST_INT)

	def ext_group_show(self):
		"""Make the external part visible."""
		self._hideitemlist(ITEMLIST_IMM)
		#self._hideitemlist(ITEMLIST_INT)
		self._showitemlist(ITEMLIST_EXT)

	# Interface to the external part.  This part consists of a
	# text field with a URL (with or without the protocol, and if
	# without protocol, absolute or relative) and a `Browser...'
	# button which triggers a callback function.
	def setfilename(self, filename):
		"""Set the value of the filename (URL).

		Arguments (no defaults):
		filename -- string giving the URL
		"""
		self._setlabel(ITEM_URL, filename)
		self._selectinputfield(ITEM_URL)

	def getfilename(self):
		"""Return the value of the filename text field."""
		return self._getlabel(ITEM_URL)

	# Interface to the interior part.  This part consists of a
	# list of strings and an interface to select one item in the
	# list.
	def setchildren(self, children, initchild):
		"""Set the list of children.

		Arguments (no defaults):
		children -- list of strings
		initchild -- 0 <= initchild < len(children) or None --
			the initial selection (no selection igf None)
		"""
##		self.__children_browser.delalllistitems()
##		self.__children_browser.addlistitems(children, -1)
##		if children:
##			self.__children_browser.selectitem(initchild)
		pass

	def getchild(self):
		"""Return the index of the current selection or None."""
##		return self.__children_browser.getselected()
		return None

	# Interface to the immediate part.  This part consists of an
	# editable text area.  There are no callbacks.
	def settext(self, immtext):
		"""Set the current text.

		Arguments (no defaults):
		immtext -- list of strings or a single string with
			embedded linefeeds
		"""
		if type(immtext) == type([]):
			immtext = string.join(immtext, '\r')
		self._setlabel(ITEM_IMM, immtext)
		self._selectinputfield(ITEM_IMM)

	def gettext(self):
		"""Return the current text as one string."""
		lines = self.gettextlines()
		return string.join(lines, '\n')

	def gettextlines(self):
		"""Return the current text as a list of strings."""
		text = self._getlabel(ITEM_IMM)
		return string.split(text, '\n')

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def cancel_callback(self):
		pass

	def restore_callback(self):
		pass

	def apply_callback(self):
		pass

	def ok_callback(self):
		pass

	def channel_callback(self):
		pass

	def type_callback(self):
		pass

	def attributes_callback(self):
		pass

	def anchors_callback(self):
		pass

	def file_callback(self):
		pass

	def conteditor_callback(self):
		pass

	def browser_callback(self):
		pass

	def openchild_callback(self):
		pass
