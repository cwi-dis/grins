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
import mw_resources

# Common items:
ITEM_OK=1
ITEM_CANCEL=2
ITEM_APPLY=3
ITEM_SELECT=4
ITEM_LAST_COMMON=4

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
		windowinterface.MACDialog.__init__(self, title, mw_resources.ID_DIALOG_ATTREDIT,
				default=ITEM_OK, cancel=ITEM_CANCEL)
## This doesn't work for (a) tabbing to a field and (b) popup menus
		self._ok_enabled = 0
##		self._setsensitive([ITEM_APPLY, ITEM_OK], 0)

		#
		# Create the pages with the attributes, and the datastructures linking
		# attributes and pages together.
		# Each page starts with a grouping item encompassing all the others.
		#
		attriblist = attriblist[:]
		initpagenum = 0
		self._attr_to_pageindex = {}
		self._pages = []
		item0 = ITEM_LAST_COMMON
		all_groups = []
		#
		# First pass: loop over multi-attribute pages (and single-attribute special
		# case pages, which are implemented similarly) and filter out all attributes
		# that fit on such a page
		#
		attribnames = map(lambda a: a.getname(), attriblist)
##		print 'DBG NAMES:', attribnames
		for cl in MULTI_ATTR_CLASSES:
			if tabpage_multi_match(cl, attribnames):
				# Instantiate the class and filter out the attributes taken care of
				attrsdone = tabpage_multi_getfields(cl, attriblist)
				page = cl(self, attrsdone)
				all_groups.append(item0+1)
				item0 = page.init_controls(item0)
				for a in attrsdone:
					self._attr_to_pageindex[a] = len(self._pages)
					attribnames.remove(a.getname())
				self._pages.append(page)
		#
		# Second pass: everything left in attriblist should be handled by one of the
		# generic single-attribute pages.
		#
		for a in attriblist:
			pageclass = tabpage_single_find(a)
			page = pageclass(self, [a])
			all_groups.append(item0+1)
			item0 = page.init_controls(item0)
			self._attr_to_pageindex[a] = len(self._pages)
			self._pages.append(page)
		self._hideitemcontrols(all_groups)
		self._cur_page = None
		#
		# Create the page browser data and select the initial page
		#
		pagenames = []
		for a in self._pages:
			label = a.createwidget()
			pagenames.append(label)
		self._pagebrowser = self._window.ListWidget(ITEM_SELECT, pagenames)
		try:
			initpagenum = self._attr_to_pageindex[initattr]
		except KeyError:
			initpagenum = 0
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

	def init_controls(self, item0):
		"""Initialize controls. Base item number is passed, and we return the
		base item number for the next tabpage"""
		self.item0 = item0
		if __debug__:
			if self.attreditor._dialog.CountDITL() != self.item0:
				raise 'CountDITL != item0', (self._dialog.CountDITL(), self.item0)
		self.attreditor._dialog.AppendDialogItemList(self.ID_DITL, 0)
		# Sanity check
		if __debug__:
			if self.attreditor._dialog.CountDITL() != self.item0+self.N_ITEMS:
				raise 'CountDITL != N_ITEMS', (self._dialog.CountDITL(), self.item0+self.N_ITEMS)
		return self.item0 + self.N_ITEMS
		
	def close(self):
		del self.fieldlist
		del self.attreditor
		
	def createwidget(self):
		return self.fieldlist[0]._widgetcreated()
		
	def show(self):
		"""Called by the dialog when the page is shown. Show all
		controls and update their values"""
		self.update()
		self.attreditor._showitemcontrols([self.item0+self.ITEM_GROUP])
			
	def hide(self):
		"""Called by the dialog when the page is hidden. Save values
		and hide controls"""
		self.save()
		self.attreditor._hideitemcontrols([self.item0+self.ITEM_GROUP])
	
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
		
class MultiTabPage(TabPage):
	def createwidget(self):
		for f in self.fieldlist:
			f._widgetcreated()
		return self.TAB_LABEL
		
class SingleTabPage(TabPage):
	"""A tab-page with a single item plus its description"""

	def show(self):
		# For single-attribute pages we do the help and default work
		attrname, default, help = self.fieldlist[0].gethelpdata()
		label = self.fieldlist[0].getlabel()
		self.attreditor._settitle(self.item0+self.ITEM_GROUP, label)
		self.attreditor._setlabel(self.item0+self.ITEM_HELP, help)
		TabPage.show(self)
		
class SingleDefaultTabPage(SingleTabPage):
	"""A tabpage with a single item, a description and a default"""

	def show(self):
		# For single-attribute pages we do the help and default work
		attrname, default, help = self.fieldlist[0].gethelpdata()
		if default:
			self.attreditor._setlabel(self.item0+self.ITEM_DEFAULT, default)
		else:
			self.attreditor._hideitemcontrols([self.item0+self.ITEM_DEFAULTGROUP])
		SingleTabPage.show(self)

class StringTabPage(SingleDefaultTabPage):
	attrs_on_page=None
	type_supported=None
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_STRING
	ITEM_GROUP=1
	ITEM_HELPGROUP=2
	ITEM_HELP=3
	ITEM_DEFAULTGROUP=4
	ITEM_DEFAULT=5
	ITEM_STRING=6
	N_ITEMS=6

	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_STRING:
			self.attreditor._enable_ok()
			return 1
		return 0

	def save(self):
		value = self.attreditor._getlabel(self.item0+self.ITEM_STRING)
		self.fieldlist[0]._savevaluefrompage(value)
		
	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_STRING, value)
		
class TextTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported='text'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_TEXT
	ITEM_GROUP=1
	ITEM_HELPGROUP=2
	ITEM_HELP=3
	ITEM_STRING=4
	N_ITEMS=4

	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_STRING:
			self.attreditor._enable_ok()
			return 1
		return 0

	def save(self):
		value = self.attreditor._getlabel(self.item0+self.ITEM_STRING)
		self.fieldlist[0]._savevaluefrompage(value)
		
	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_STRING, value)

class FileTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported='file'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_FILE
	ITEM_GROUP=1
	ITEM_HELPGROUP=2
	ITEM_HELP=3
	ITEM_STRING=4
	ITEM_BROWSE=5
	N_ITEMS=5

	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_STRING:
			self.attreditor._enable_ok()
			return 1
		elif item == self.item0+self.ITEM_BROWSE:
			self.fieldlist[0].browser_callback()
			return 1
		return 0

	def save(self):
		value =  self.attreditor._getlabel(self.item0+self.ITEM_STRING)
		self.fieldlist[0]._savevaluefrompage(value)

	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_STRING, value)
		
class XXFileTabPage(FileTabPage):
	# Special case used in multiattr searching, so the URL comes
	# near the top of the list of attributes
	attrs_on_page = ['file']

class ColorTabPage(SingleDefaultTabPage):
	attrs_on_page=None
	type_supported='color'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_COLOR
	ITEM_GROUP=1
	ITEM_HELPGROUP=2
	ITEM_HELP=3
	ITEM_DEFAULTGROUP=4
	ITEM_DEFAULT=5
	ITEM_STRING=6
	ITEM_PICK=7
	N_ITEMS=7

	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_STRING:
			self.attreditor._enable_ok()
			return 1
		elif item == self.item0+self.ITEM_PICK:
			self._select_color()
			return 1
		return 0

	def save(self):
		value =  self.attreditor._getlabel(self.item0+self.ITEM_STRING)
		self.fieldlist[0]._savevaluefrompage(value)

	def update(self):
		"""Update controls to self.__value"""
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_STRING, value)

	def _select_color(self):
		import ColorPicker
		value = self.attreditor._getlabel(self.item0+self.ITEM_STRING)
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
			self.attreditor._setlabel(self.item0+self.ITEM_STRING, value)
			self.attreditor._selectinputfield(self.item0+self.ITEM_STRING)
		
class OptionTabPage(SingleTabPage):
	attrs_on_page=None
	type_supported='option'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_OPTION
	ITEM_GROUP=1
	ITEM_HELPGROUP=2
	ITEM_HELP=3
	ITEM_MENU=4
	N_ITEMS=4

	def init_controls(self, item0):
		rv = SingleTabPage.init_controls(self, item0)
		self._option = windowinterface.SelectWidget(self.attreditor._dialog, self.item0+self.ITEM_MENU,
				[], None)
		return rv

	def close(self):
		self._option.delete()
		TabPage.close(self)
		
	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_MENU:
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

class ChannelTabPage(OptionTabPage):
	attrs_on_page=['channel']
##	type_supported='channel' # XXXX does not work
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_CHANNEL
	ITEM_GROUP=1
	ITEM_HELPGROUP=2
	ITEM_HELP=3
	ITEM_MENU=4
	ITEM_CHATTRS=5
	N_ITEMS=5

	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_CHATTRS:
			self.fieldlist[0].channelprops()
			return 1
		return OptionTabPage.do_itemhit(self, item, event)


class CaptionChannelTabPage(ChannelTabPage):
	attrs_on_page=['captionchannel']
		
class MultiStringTabPage(MultiTabPage):
	
	def do_itemhit(self, item, event):
		if item-self.item0 in self._items_on_page:
			return 1
		return 0
		
	def update(self):
		for field in self.fieldlist:
			attr = field.getname()
			item = self._attr_to_item[attr]
			value = field._getvalueforpage()
			self.attreditor._setlabel(self.item0+item, value)

	def save(self):
		for field in self.fieldlist:
			attr = field.getname()
			item = self._attr_to_item[attr]
			value = self.attreditor._getlabel(self.item0+item)
			field._savevaluefrompage(value)

class InfoTabPage(MultiStringTabPage):
	TAB_LABEL='Info'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_INFO
	ITEM_GROUP=1
	ITEM_TITLE=3
	ITEM_ABSTRACT=5
	ITEM_ALT=7
	ITEM_LONGDESC=9
	ITEM_AUTHOR=11
	ITEM_COPYRIGHT=13
	N_ITEMS=13
	_attr_to_item = {
		'title': ITEM_TITLE,
		'abstract': ITEM_ABSTRACT,
		'alt': ITEM_ALT,
		'longdesc': ITEM_LONGDESC,
		'author': ITEM_AUTHOR,
		'copyright': ITEM_COPYRIGHT,
	}
	attrs_on_page = _attr_to_item.keys()
	_items_on_page = _attr_to_item.values()

class TimingTabPage(MultiStringTabPage):
	TAB_LABEL='Timing'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_TIMING
	ITEM_GROUP=1
	ITEM_DURATION=3
	ITEM_LOOP=5
	ITEM_BEGIN=7
	N_ITEMS=7
	_attr_to_item = {
		'duration': ITEM_DURATION,
		'loop': ITEM_LOOP,
		'begin': ITEM_BEGIN,
	}
	attrs_on_page = _attr_to_item.keys()
	_items_on_page = _attr_to_item.values()

class ClipTabPage(MultiStringTabPage):
	TAB_LABEL='Clip'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_CLIP
	ITEM_GROUP=1
	ITEM_BEGIN=3
	ITEM_END=5
	N_ITEMS=5
	_attr_to_item = {
		'clipbegin': ITEM_BEGIN,
		'clipend': ITEM_END,
	}
	attrs_on_page = _attr_to_item.keys()
	_items_on_page = _attr_to_item.values()

class TargetAudienceTabPage(MultiTabPage):
	TAB_LABEL='Target audience'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_TARGET_AUDIENCE
	ITEM_GROUP=1
	ITEM_28K8=2
	ITEM_56K=3
	ITEM_ISDN=4
	ITEM_2ISDN=5
	ITEM_CABLE=6
	ITEM_LAN=7
	N_ITEMS=7
	# Note: the keys here are the values in AttrEdit.RMTargetsAttrEditorField
	_value_to_item = {
		'28k8 modem': ITEM_28K8,
		'56k modem': ITEM_56K,
		'Single ISDN': ITEM_ISDN,
		'Double ISDN': ITEM_2ISDN,
		'Cable modem': ITEM_CABLE,
		'LAN': ITEM_LAN,
	}
	attrs_on_page = ['project_targets']
	_items_on_page = _value_to_item.values()

	def do_itemhit(self, item, event):
		if item-self.item0 in self._items_on_page:
			self.attreditor._togglebutton(item)
			return 1
		return 0
		
	def update(self):
		self.update_target()
		
	def update_target(self):
		field = self.fieldlist[0]
		attr = field._getvalueforpage()
		targets = string.split(attr, ',')
		print 'update dbg targets', targets
		for t, item in self._value_to_item.items():
			print 'dbg', item, t, t in targets
			self.attreditor._setbutton(self.item0+item, (t in targets))

	def save(self):
		self.save_target()
		
	def save_target(self):
		field = self.fieldlist[0]
		targets = []
		for t, item in self._value_to_item.items():
			if self.attreditor._getbutton(self.item0+item):
				targets.append(t)
		print 'save dbg targets', targets
		field._savevaluefrompage(string.join(targets, ','))

class GeneralTabPage(MultiTabPage):
	TAB_LABEL='General'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_GENERAL
	ITEM_GROUP=1
	ITEM_NODENAME=3
	ITEM_CHANNEL=5
	ITEM_CHANNELPROPS=6
	ITEM_NODETYPE=8
	N_ITEMS=8
	_attr_to_item = {
		'name': ITEM_NODENAME,
		'channel': ITEM_CHANNEL,
		'.type': ITEM_NODETYPE,
	}
	attrs_on_page = _attr_to_item.keys()
	
	def init_controls(self, item0):
		rv = MultiTabPage.init_controls(self, item0)
		self._channelpopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_CHANNEL, [], None)
		self._typepopup = windowinterface.SelectWidget(self.attreditor._dialog,
				self.item0+self.ITEM_NODETYPE, [], None)
		return rv

	def close(self):
		self._channelpopup.delete()
		self._typepopup.delete()
		TabPage.close(self)
		
	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_NODENAME:
			return 1
		elif item == self.item0+self.ITEM_CHANNEL:
			# popup
			return 1
		elif item == self.item0+self.ITEM_CHANNELPROPS:
			self.fieldlist[1].channelprops()
			return 1
		elif item == self.item0+self.ITEM_NODETYPE:
			# popup
			return 1
		return 0
		
	def update(self):
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_NODENAME, value)
		value = self.fieldlist[1]._getvalueforpage()
		list = self.fieldlist[1].getoptions()
		self._channelpopup.setitems(list, value)
		value = self.fieldlist[2]._getvalueforpage()
		list = self.fieldlist[2].getoptions()
		self._typepopup.setitems(list, value)

	def save(self):
		value = self.attreditor._getlabel(self.item0+self.ITEM_NODENAME)
		self.fieldlist[0]._savevaluefrompage(value)
		value = self._channelpopup.getselectvalue()
		self.fieldlist[1]._savevaluefrompage(value)
		value = self._typepopup.getselectvalue()
		self.fieldlist[2]._savevaluefrompage(value)

class SystemPropertiesTabPage(MultiTabPage):
	TAB_LABEL='System properties'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_SYSTEM_PROPERTIES
	ITEM_GROUP=1
	ITEM_BITRATE=3
	ITEM_CAPTION_GROUP=5
	ITEM_CAPTION_NOTSET=6
	ITEM_CAPTION_OFF=7
	ITEM_CAPTION_ON=8
	ILIST_CAPTION=(ITEM_CAPTION_NOTSET, ITEM_CAPTION_OFF, ITEM_CAPTION_ON)
	ITEM_LANGUAGE=10
	ITEM_OVERDUB_CAPTION_GROUP=12
	ITEM_OVERDUB_CAPTION_NOTSET=13
	ITEM_OVERDUB_CAPTION_OVERDUB=14
	ITEM_OVERDUB_CAPTION_CAPTION=15
	ILIST_OVERDUB_CAPTION=(ITEM_OVERDUB_CAPTION_NOTSET, 
			ITEM_OVERDUB_CAPTION_OVERDUB, ITEM_OVERDUB_CAPTION_CAPTION)
	ITEM_REQUIRED=17
	ITEM_SCREENDEPTH=19
	ITEM_SCREENSIZE=21
	N_ITEMS=21

	attrs_on_page = [
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		'system_required',
		'system_screen_depth',
		'system_screen_size',
	]
	
	def init_controls(self, item0):
		rv = MultiTabPage.init_controls(self, item0)
		self._bitratepopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_BITRATE, [], None)
		self._languagepopup = windowinterface.SelectWidget(self.attreditor._dialog,
				self.item0+self.ITEM_LANGUAGE, [], None)
		return rv

	def close(self):
		self._bitratepopup.delete()
		self._languagepopup.delete()
		TabPage.close(self)
		
	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_BITRATE:
			return 1
		elif item-self.item0 in self.ILIST_CAPTION:
			self.do_radio(item-self.item0, self.ILIST_CAPTION)
			return 1
		elif item == self.item0+self.ITEM_LANGUAGE:
			return 1
		elif item-self.item0 in self.ILIST_OVERDUB_CAPTION:
			self.do_radio(item-self.item0, self.ILIST_OVERDUB_CAPTION)
			return 1
		elif item == self.item0+self.ITEM_REQUIRED:
			return 1
		elif item == self.item0+self.ITEM_SCREENDEPTH:
			return 1
		elif item == self.item0+self.ITEM_SCREENSIZE:
			return 1
		return 0

	def do_radio(self, item, allitems):
		for i in allitems:
			self.attreditor._setbutton(self.item0+i, (i==item))
			
	def initradio(self, allitems, list, value):
		for i in range(len(allitems)):
			on = (value == list[i])
			self.attreditor._setbutton(self.item0+allitems[i], on)
			
	def getradio(self, allitems, list):
		for i in range(len(allitems)):
			if self.attreditor._getbutton(self.item0+allitems[i]):
				return list[i]
		return None
					
	def update(self):
		value = self.fieldlist[0]._getvalueforpage()
		list = self.fieldlist[0].getoptions()
		self._bitratepopup.setitems(list, value)
		
		value = self.fieldlist[1]._getvalueforpage()
		list = self.fieldlist[1].getoptions()
		self.initradio(self.ILIST_CAPTION, list, value)
		
		value = self.fieldlist[2]._getvalueforpage()
		list = self.fieldlist[2].getoptions()
		self._languagepopup.setitems(list, value)
		
		value = self.fieldlist[3]._getvalueforpage()
		list = self.fieldlist[3].getoptions()
		self.initradio(self.ILIST_OVERDUB_CAPTION, list, value)

		value = self.fieldlist[4]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_REQUIRED, value)

		value = self.fieldlist[5]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_SCREENDEPTH, value)

		value = self.fieldlist[6]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_SCREENSIZE, value)

	def save(self):
		value = self._bitratepopup.getselectvalue()
		self.fieldlist[0]._savevaluefrompage(value)
	
		list = self.fieldlist[1].getoptions()
		value = self.getradio(self.ILIST_CAPTION, list)
		self.fieldlist[1]._savevaluefrompage(value)
		
		value = self._languagepopup.getselectvalue()
		self.fieldlist[2]._savevaluefrompage(value)
	
		list = self.fieldlist[3].getoptions()
		value = self.getradio(self.ILIST_OVERDUB_CAPTION, list)
		self.fieldlist[3]._savevaluefrompage(value)
		
		value = self.attreditor._getlabel(self.item0+self.ITEM_REQUIRED)
		self.fieldlist[4]._savevaluefrompage(value)
		
		value = self.attreditor._getlabel(self.item0+self.ITEM_SCREENDEPTH)
		self.fieldlist[5]._savevaluefrompage(value)
		
		value = self.attreditor._getlabel(self.item0+self.ITEM_SCREENSIZE)
		self.fieldlist[6]._savevaluefrompage(value)

#
# List of classes handling pages with multiple attributes. The order is
# important: we loop over these classes in order, and if all attributes
# required by the class are in the current list of attributes we instantiate
# the page and remove the attributes from the list. So, the first fully
# matching class will get the attribute.
# The order is also the order in which the tabpages will be presented to the
# user
#
MULTI_ATTR_CLASSES = [ 
	GeneralTabPage,
	TimingTabPage,
	XXFileTabPage,
	InfoTabPage,
	ChannelTabPage,
	CaptionChannelTabPage,
	SystemPropertiesTabPage,
	TargetAudienceTabPage,
	ClipTabPage,
]
#
# List of classes handling a generic page for a single attribute.
# The order is important: for all attributes that didn't fit on a multi-attr
# page we look at these in order. The first one to have a matching 'type'
# will be used. The last class, the generic string page, has type_supported
# None and will math everything.
#
SINGLE_ATTR_CLASSES = [
	FileTabPage,
	ColorTabPage,
	OptionTabPage,
	TextTabPage,
	StringTabPage,
]

def tabpage_single_find(attrfield):
	"""Find the best single-attribute page class that can handle this attribute field"""
	for cl in SINGLE_ATTR_CLASSES:
		if cl.type_supported == attrfield.type:
			return cl
		if cl.type_supported is None:
			return cl
	raise 'Unsupported attrclass' # Cannot happen
	
def tabpage_multi_match(cl, attrnames):
	"""Check whether all attributes on pageclass cl are in attrnames"""
	wtd_fields = cl.attrs_on_page
	for field in wtd_fields:
		if not field in attrnames:
			return 0
	return 1
	
def tabpage_multi_getfields(cl, attrfields):
	"""Return (and remove) attrfields needed for pageclass cl"""
	rv = []
	for a in attrfields:
		if a.getname() in cl.attrs_on_page:
			rv.append(a)
	for a in rv:
		attrfields.remove(a)
	return rv

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
