"""Dialog for the Attribute Editor.

This module contains three classes:
AttrEditorDialog is used as a baseclass for AttrEdit, and represents the whole
dialog. It has a number of attributepages as children, one of which is displayed
at any one time.
It handles the ok/apply/cancel buttons and the listwidget to select which page
to display.

TabPage is an attribute page. It contains the GUI-controls for a number of
attributes, which it has references to. It handles display of attrvalues and
updating of those values by the user.

AttrEditorDialogField is the baseclass for AttrEditorField, and is the glue
between that class and the TabPage to which it belongs. It also keeps the
current value of an attribute, as set through the GUI, which may be different
from the real current value which is kept by AttrEditorField.

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
ID_DIALOG_EXTRAS=635

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

ALL_GROUPS=[ITEM_1_GROUP, ITEM_2_GROUP, ITEM_3_GROUP, ITEM_4_GROUP]

# ITEM_BALLOONHELP=15

ITEMLIST_ALL=ITEMrange(ITEM_OK, ITEM_4_MENU)

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
		self._dialog.AppendDialogItemList(ID_DIALOG_EXTRAS, 0)
## This doesn't work for (a) tabbing to a field and (b) popup menus
		self._ok_enabled = 0
##		self._setsensitive([ITEM_APPLY, ITEM_OK], 0)

		#
		# Create the pages with the attributes, and the datastructures linking
		# attributes and pages together
		#
		initpagenum = 0
		self._attr_to_pageindex = {}
		self._pages = []
		for a in attriblist:
			pageclass = tabpage_singleattr(a)
			page = pageclass(self, [a])
			if a is initattr:
				initpagenum = len(self._pages)
			self._attr_to_pageindex[a] = len(self._pages)
			self._pages.append(page)
		self._hideitemcontrols(ALL_GROUPS)
		self._cur_page = None
		#
		# Create the page browser data and select the initial page
		#
		pagenames = []
		for a in self._pages:
			label = a.createwidget()
			pagenames.append(label)
		self._pagebrowser = self._window.ListWidget(ITEM_SELECT, pagenames)
		self._selectpage(initpagenum)

		self.show()
##		# Should work above...
##		self._hideitemcontrols(allgroups)
##		self._selectpage(initpagenum)

	def close(self):
		for p in self._pages:
			p.close()
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
		
	def _enable_ok(self):
		if self._ok_enabled:
			return
		self._ok_enabled = 1
		self._setsensitive([ITEM_APPLY, ITEM_OK], 1)

	def do_itemhit(self, item, event):
		if item == ITEM_SELECT:
			item = self._pagebrowser.getselect()
			self._selectpage(item)
			# We steal back the keyboard focus
			self._pagebrowser.setkeyboardfocus()
		elif item == ITEM_CANCEL:
			self.cancel_callback()
		elif item == ITEM_OK:
			self.ok_callback()
		elif item == ITEM_APPLY:
			self.apply_callback()
		elif self._cur_page and self._cur_page.do_itemhit(item, event):
			pass
##		elif item == ITEM_RESTORE:
##			self.restore_callback()
##		elif item == ITEM_RESET:
##			if self._cur_page:
##				self._cur_page.reset_callback()
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
		for i in range(1,1000):
			try:
				print '%d:%d',i, self._dialog.GetDialogItemAsControl(i).IsControlVisible()
			except:
				break
		print


	def _is_shown(self, attrfield):
		"""Return true if this attr is currently being displayed"""
		if not self._cur_page:
			return 0
		num = self._attr_to_pageindex[attrfield]
		return (self._pages[num] is self._cur_page)
		
	def _savepagevalues(self):
		"""Save values from the current page (if any)"""
		if self._cur_page:
			self._cur_page.save()

	def _updatepagevalues(self):
		"""Update values in the current page (if any)"""
		if self._cur_page:
			self._cur_page.update()

	def showmessage(self, *args, **kw):
		apply(windowinterface.showmessage, args, kw)

class TabPage:
	"""The internal representation of a tab-page. Used for subclassing only."""
	
	def __init__(self, dialog, fieldlist):
		self.fieldlist = fieldlist
		self.attreditor = dialog
		self.init_controls()

	def init_controls(self):
		"""Initialize optional controls, overriden by subclasses that need it"""
		pass
		
	def close(self):
		del self.fieldlist
		del self.attreditor
		
	def createwidget(self):
		for f in self.fieldlist:
			name = f._widgetcreated()
		return name 
		
	def show(self):
		"""Called by the dialog when the page is shown. Show all
		controls and update their values"""
		self.update()
		self.attreditor._showitemcontrols([self.GROUP])
			
	def hide(self):
		"""Called by the dialog when the page is hidden. Save values
		and hide controls"""
		self.save()
		self.attreditor._hideitemcontrols([self.GROUP])
	
	def save(self):
		"""Save all values from the dialogpage to the attrfields"""
		raise 'No save() for page' # Cannot happen
		
	def update(self):
		"""Update all values in the dialogpage from the attrfields"""
		raise 'No update() for page' # Cannot happen
			
	def getcurattr(self):
		"""Return our first attr, so it can be reshown after an apply"""
		return self.fieldlist[0]
		
	def do_itemhit(self, item, event):
		return 0	# To be overridden
		
class SingleTabPage(TabPage):

	def show(self):
		# For single-attribute pages we do the help and default work
		attrname, default, help = self.fieldlist[0].gethelpdata()
		self.attreditor._setlabel(ITEM_TABGROUP, attrname)
		self.attreditor._setlabel(ITEM_HELP, help)
		if default:
			self.attreditor._setlabel(ITEM_DEFAULT, default)
			self.attreditor._showitemcontrols([ITEM_DEFAULTGROUP])
		else:
			self.attreditor._hideitemcontrols([ITEM_DEFAULTGROUP])
		TabPage.show(self)

class StringTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported=None
	GROUP=ITEM_1_GROUP

	def do_itemhit(self, item, event):
		if item == ITEM_1_STRING:
			self.attreditor._enable_ok()
			return 1
		return 0

	def save(self):
		value = self.attreditor._getlabel(ITEM_1_STRING)
		self.fieldlist[0]._savevaluefrompage(value)
		
	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(ITEM_1_STRING, value)

class FileTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported='file'
	GROUP=ITEM_2_GROUP

	def do_itemhit(self, item, event):
		if item == ITEM_2_STRING:
			self.attreditor._enable_ok()
			return 1
		elif item == ITEM_2_BROWSE:
			self.fieldlist[0].browser_callback()
			return 1
		return 0

	def save(self):
		value =  self.attreditor._getlabel(ITEM_2_STRING)
		self.fieldlist[0]._savevaluefrompage(value)

	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(ITEM_2_STRING, value)

class ColorTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported='color'
	GROUP=ITEM_3_GROUP

	def do_itemhit(self, item, event):
		if item == ITEM_3_STRING:
			self.attreditor._enable_ok()
			return 1
		elif item == ITEM_3_PICK:
			self._select_color()
			return 1
		return 0

	def save(self):
		value =  self.attreditor._getlabel(ITEM_3_STRING)
		self.fieldlist[0]._savevaluefrompage(value)

	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(ITEM_3_STRING, value)

	def _select_color(self):
		import ColorPicker
		value = self.attreditor._getlabel(ITEM_3_STRING)
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
			self.attreditor._setlabel(ITEM_3_STRING, value)
			self.attreditor._selectinputfield(ITEM_3_STRING)
		
class OptionTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported='option'
	GROUP=ITEM_4_GROUP

	def init_controls(self):
		self._option = windowinterface.SelectWidget(self.attreditor._dialog, ITEM_4_MENU,
				[], None)
		pass

	def close(self):
		self._option.delete()
		TabPage.close(self)
		
	def do_itemhit(self, item, event):
		if item == ITEM_4_MENU:
			self._option_click()
			return 1
		return 0

	def save(self):
		value = self._option.getselectvalue()
		self.fieldlist[0]._savevaluefrompage(value)

	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		list = self.fieldlist[0].getoptions()
		self._option.setitems(list, value)

	def _option_click(self):
		pass
		
SINGLE_ATTR_CLASSES = [ FileTabPage, ColorTabPage, OptionTabPage, StringTabPage ]

def tabpage_singleattr(attrfield):
	for cl in SINGLE_ATTR_CLASSES:
		if cl.type_supported == attrfield.type:
			return cl
		if cl.type_supported is None:
			return cl
	raise 'Unsupported attrclass' # Cannot happen

class AttrEditorDialogField:
	
	def _widgetcreated(self):
		label = self.getlabel()
		self.__value = self.getcurrent()
		return '%s' % label

	def _savevaluefrompage(self, value):
		self.__value = value
		
	def _getvalueforpage(self):
		return self.__value
				
##	def _show(self): # XXXX Should go to tabpage
##		value = self.__value
##		attrname, default, help = self.gethelpdata()
##		if self.type == 'file':
##			toshow=ITEMLIST_FILE
##			tohide=ITEMLISTNOT_FILE
##		elif self.type == 'color':
##			toshow=ITEMLIST_COLOR
##			tohide=ITEMLISTNOT_COLOR
##		elif self.type == 'option':
##			list = self.getoptions()
##			toshow=ITEMLIST_OPTION
##			tohide=ITEMLISTNOT_OPTION
##		else:
##			toshow=ITEMLIST_STRING
##			tohide=ITEMLISTNOT_STRING
##		if default is None:
##			tohide = tohide + [ITEM_DEFAULTGROUP]
##		else:
##			toshow = toshow + [ITEM_DEFAULTGROUP]
##		self.attreditor._hideitemlist(tohide)
##		# It appears input fields have to be shown before
##		# values are inserted??!?
####		if ITEM_STRING in toshow:
####			self.attreditor._showitemlist([ITEM_STRING])
##		self.attreditor._showitemlist(toshow)
##		xxxx self._dosetvalue(initialize=1)
##		if not default is None:
##			self.attreditor._setlabel(ITEM_DEFAULT, default)
##		self.attreditor._setlabel(ITEM_HELP, help)
####		self.attreditor._showitemlist(toshow)

	def close(self):
		"""Close the instance and free all resources."""
		del self.__value

	def getvalue(self):
		"""Return the current value of the attribute.

		The return value is a string giving the current value.
		"""
		if self.type is None:
			return self.getcurrent()
		if self.attreditor._is_shown(self):
			self.attreditor._savepagevalues()
		return self.__value

	def setvalue(self, value):
		"""Set the current value of the attribute.

		Arguments (no defaults):
		value -- string giving the new value
		"""
		self.__value = value
		if self.attreditor._is_shown(self):
			self.attreditor._updatepagevalues()
		if value != self.getcurrent():
			self.attreditor._enable_ok()
			
	def recalcoptions(self):
		"""Recalculate the list of options and set the value."""
		if self.attreditor._is_shown(self) and self.type == 'option':
			self.attreditor._updatepagevalues()

	def askchannelname(self, default):
		windowinterface.InputDialog('Name for new channel',
					    default,
					    self.newchan_callback,
					    cancelCallback = (self.newchan_callback, ()))
