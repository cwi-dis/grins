"""Dialog for the Attribute Editor.

The Attribute editor dialog consists of four buttons that are always
present (`Cancel', `Restore', `Apply', and `OK'), and a row of
attribute editor fields.  The number and type of these fields are
determined at run time, but there are only a limited number of
different types.  The fields are represented by instances of
sub-classes of the AttrEditorDialogField.  A list of these instances
is passed to the constructor of the AttrEditorDialog class.

Each of the attribute editor fields has a label with the name of the
attribute, an interface to edit the value (the interface depends on
the type of the value), and a `Reset' button.  There are two callbacks
associated with an attribute editor field, one to get help, and one
that is called when the `Reset' button is pressed.  There are also
some methods to get and set the current value of the attribute.

The base class of the AttrEditorDialogField class must provide some
methods also.

"""

__version__ = "$Id$"

import Dlg
import Qd
import string
import windowinterface
import WMEVENTS

def ITEMrange(fr, to): return range(fr, to+1)
# Dialog info
from mw_resources import ID_DIALOG_NODEATTR

# Common items:
ITEM_OK=1
ITEM_CANCEL=2
ITEM_APPLY=3
ITEM_SELECT=4

# Main group on righthandside
ITEM_TABGROUP=5
ITEM_HELPGROUP=6
ITEM_HELP=7
ITEM_DEFAULTGROUP=8
ITEM_DEFAULT=9

# Per-type items
ITEM_1_GROUP=10			# String
ITEM_1_STRING=11

ITEM_2_GROUP=12			# Filename
ITEM_2_STRING=13
ITEM_2_BROWSE=14

ITEM_3_GROUP=15			# Color
ITEM_3_STRING=16
ITEM_3_PICK=17

ITEM_4_GROUP=18			# Option
ITEM_4_MENU=19


ITEM_BALLOONHELP=15


# Variant items
ITEM_COLOR_SELECT=14

ITEMLIST_STRING=[ITEM_1_GROUP]
ITEMLISTNOT_STRING=[ITEM_2_GROUP, ITEM_3_GROUP, ITEM_4_GROUP]
ITEMLIST_FILE=[ITEM_2_GROUP]
ITEMLISTNOT_FILE=[ITEM_1_GROUP, ITEM_3_GROUP, ITEM_4_GROUP]
ITEMLIST_COLOR=[ITEM_3_GROUP]
ITEMLISTNOT_COLOR=[ITEM_1_GROUP, ITEM_2_GROUP, ITEM_4_GROUP]
ITEMLIST_OPTION=[ITEM_4_GROUP]
ITEMLISTNOT_OPTION=[ITEM_1_GROUP, ITEM_2_GROUP, ITEM_3_GROUP]

ITEMLIST_ALL=ITEMrange(ITEM_SELECT, ITEM_BALLOONHELP)

class AttrEditorDialog(windowinterface.MACDialog):
	def __init__(self, title, attriblist, toplevel=None, initattr=None):
		"""Create the AttrEditor dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as the window title
		attriblist -- list of instances of subclasses of
			AttrEditorDialogField
		"""
		windowinterface.MACDialog.__init__(self, title, ID_DIALOG_NODEATTR,
				ITEMLIST_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)

		# XXXX This should go elsewhere
		self._option = windowinterface.SelectWidget(self._dialog, ITEM_4_MENU,
				[], None)
		#
		# Create the pages with the attributes, and the datastructures linking
		# attributes and pages together
		#
		initpagenum = 0
		self._attr_to_pageindex = {}
		self._pages = []
		for a in attriblist:
			page = TabPage([a])
			if a is initattr:
				initpagenum = len(self._pages)
			self._attr_to_pageindex[a] = len(self._pages)
			self._pages.append(page)
		self._cur_page = None
		#
		# Create the page browser data and select the initial page
		#
		pagenames = []
		for a in self._pages:
			label = a.createwidget(self)
			pagenames.append(label)
		self._pagebrowser = self._window.ListWidget(ITEM_SELECT, pagenames)
		self._selectpage(initpagenum)

		self.show()

	def close(self):
		for p in self._pages:
			p.close()
		self._option.delete()
		del self._pagebrowser
		del self._pages
		windowinterface.MACDialog.close(self)

	def getcurattr(self):
		if not self._cur_page:
			return None
		return self._cur_page.getcurattr()

	def setcurattr(self, attr):
		try:
			num = self._attr_to_pageindex[attr]
		except KeyError:
			pass
		self._selectpage(num)

	def do_itemhit(self, item, event):
		if item == ITEM_SELECT:
			item = self._pagebrowser.getselect()
			self._selectpage(item)
			# We steal back the keyboard focus
			self._pagebrowser.setkeyboardfocus()
##		elif item == ITEM_RESET:
##			if self._cur_page:
##				self._cur_page.reset_callback()
		elif item in (ITEM_1_STRING, ITEM_2_STRING, ITEM_3_STRING):
			pass
		elif item == ITEM_2_BROWSE:
			if self._cur_page:
				self._cur_page.browser_callback()
		elif item == ITEM_4_MENU:
			if self._cur_page:
				self._cur_page._option_click()
		elif item == ITEM_3_PICK:
			if self._cur_page:
				self._cur_page._select_color()
		elif item == ITEM_CANCEL:
			self.cancel_callback()
		elif item == ITEM_OK:
			self.ok_callback()
##		elif item == ITEM_RESTORE:
##			self.restore_callback()
		elif item == ITEM_APPLY:
			self.apply_callback()
		else:
			print 'Unknown NodeAttrDialog item', item, 'event', event
		return 1

	def _selectpage(self, item):
		if self._cur_page:
			if item and self._cur_page == self._pages[item]:
				return
			self._cur_page.hide()
		else:
			if item == None:
				return
		self._cur_page = None

		if item != None:
			self._cur_page = self._pages[item] # XXXX?
			self._cur_page.show()
			self._pagebrowser.select(item)


	def _is_shown(self, attrfield):
		"""Return true if this attr is currently being displayed"""
		if not self._cur_page:
			return 0
		num = self._attr_to_pageindex[attrfield]
		return (self._pages[num] is self._cur_page)

	def showmessage(self, *args, **kw):
		apply(windowinterface.showmessage, args, kw)

class TabPage:
	"""The internal representation of a tab-page"""
	def __init__(self, fieldlist):
		self.fieldlist = fieldlist
		
	def close(self):
		del self.fieldlist
		
	def createwidget(self, dialog):
		for f in self.fieldlist:
			name = f._createwidget(dialog)
		return name 
		
	def show(self):
		"""Called by the dialog when the page is shown. Show all
		controls and update their values"""
		for f in self.fieldlist:
			f._show()
			
	def hide(self):
		"""Called by the dialog when the page is hidden. Save values
		and hide controls"""
		for f in self.fieldlist:
			f._save()
			
	def getcurattr(self):
		"""Return our first attr, so it can be reshown after an apply"""
		return self.fieldlist[0]

class AttrEditorDialogField:
	
##	def __init__(self):
##		pass

	def _createwidget(self, parent):
		self.__parent = parent
		label = self.getlabel()
		self.__value = self.getcurrent()
		return '%s' % label

	def _save(self):
		if self.type == 'option':
			self.__value = self.__parent._option.getselectvalue()
		elif self.type == 'color':
			self.__value =  self.__parent._getlabel(ITEM_3_STRING)
		elif self.type == 'file':
			self.__value =  self.__parent._getlabel(ITEM_2_STRING)
		else:
			self.__value =  self.__parent._getlabel(ITEM_1_STRING)

	def _show(self):
		value = self.__value
		attrname, default, help = self.gethelpdata()
		if self.type == 'file':
			toshow=ITEMLIST_FILE
			tohide=ITEMLISTNOT_FILE
		elif self.type == 'color':
			toshow=ITEMLIST_COLOR
			tohide=ITEMLISTNOT_COLOR
		elif self.type == 'option':
			list = self.getoptions()
			toshow=ITEMLIST_OPTION
			tohide=ITEMLISTNOT_OPTION
		else:
			toshow=ITEMLIST_STRING
			tohide=ITEMLISTNOT_STRING
		if default is None:
			tohide = tohide + [ITEM_DEFAULTGROUP]
		else:
			toshow = toshow + [ITEM_DEFAULTGROUP]
		self.__parent._hideitemlist(tohide)
		# It appears input fields have to be shown before
		# values are inserted??!?
##		if ITEM_STRING in toshow:
##			self.__parent._showitemlist([ITEM_STRING])
		self.__parent._showitemlist(toshow)
		self._dosetvalue(initialize=1)
		if not default is None:
			self.__parent._setlabel(ITEM_DEFAULT, default)
		self.__parent._setlabel(ITEM_HELP, help)
##		self.__parent._showitemlist(toshow)

	def close(self):
		"""Close the instance and free all resources."""
		del self.__parent
		del self.__value

	def _option_click(self):
		pass

	def _select_color(self):
		import ColorPicker
		value = self.__parent._getlabel(ITEM_3_STRING)
		import string
		rgb = string.split(string.strip(value))
		if len(rgb) == 3:
			r = g = b = 0
			try:
				r = string.atoi(rgb[0])
				g = string.atoi(rgb[1])
				b = string.atoi(rgb[2])
			except ValueError:
				pass
			if r > 255: r = 255
			if g > 255: g = 255
			if b > 255: b = 255
			if r < 0: r = 0
			if g < 0: g = 0
			if b < 0: b = 0
		else:
			r = g = b = 0
		color, ok = ColorPicker.GetColor("Select color", ( (r|r<<8), (g|g<<8), b|b<<8))
		if ok:
			r, g, b = color
			value = "%d %d %d"%((r>>8), (g>>8), (b>>8))
			self.__parent._setlabel(ITEM_3_STRING, value)
			self.__parent._selectinputfield(ITEM_3_STRING)

	def getvalue(self):
		"""Return the current value of the attribute.

		The return value is a string giving the current value.
		"""
		if self.type is None:
			return self.getcurrent()
		if self.__parent._is_shown(self):
			self._save() # XXXX via parent
		return self.__value

	def setvalue(self, value):
		"""Set the current value of the attribute.

		Arguments (no defaults):
		value -- string giving the new value
		"""
		self.__value = value
		if self.__parent._is_shown(self):
			self._dosetvalue() # XXXX via parent
			
	def _dosetvalue(self, initialize=0):
		"""Update controls to self.__value"""
		value = self.__value
		if self.type == 'option':
			if initialize:
				list = self.getoptions()
				self.__parent._option.setitems(list, value)
			else:
				self.__parent._option.select(value)
		else:
			if self.type == 'color':
				item = ITEM_3_STRING
			elif self.type == 'file':
				item = ITEM_2_STRING
			else:
				item = ITEM_1_STRING
			self.__parent._setlabel(item, value)
			self.__parent._selectinputfield(item)

	def recalcoptions(self):
		"""Recalculate the list of options and set the value."""
		if not self.__parent._is_shown(self):
			return
		if self.type == 'option':
			val = self.getcurrent()
			list = self.getoptions()
			self.__parent._option.setitems(list, val)

	def askchannelname(self, default):
		windowinterface.InputDialog('Name for new channel',
					    default,
					    self.newchan_callback,
					    cancelCallback = (self.newchan_callback, ()))
