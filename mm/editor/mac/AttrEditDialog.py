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
		self._pagebrowser.setkeyboardfocus()
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
	items_to_hide = []		# Can be overridden by subsubclasses to hide some items
	
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
				raise 'CountDITL != N_ITEMS', (self.attreditor._dialog.CountDITL(), self.item0+self.N_ITEMS)
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
		if self.items_to_hide:
			hide=[]
			for i in self.items_to_hide:
				hide.append(i+self.item0)
			self.attreditor._hideitemcontrols(hide)
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
		
class MultiDictTabPage(MultiTabPage):

	def init_controls(self, item0):
		rv = MultiTabPage.init_controls(self, item0)
		# We want the fields as a dictionary, as there are many different
		# variants of this tab
		self._attr_to_field = {}
		for f in self.fieldlist:
			name = f.getname()
			self._attr_to_field[name] = f
		return rv
		
	def close(self):
		del self._attr_to_field
		MultiTabPage.close(self)
		
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

	def _option_click(self):
		self._fixbutton()
		
	def update(self):
		OptionTabPage.update(self)
		self._fixbutton()
		
	def _fixbutton(self):
		name = self._option.getselectvalue()
		self.attreditor._setsensitive([self.item0+self.ITEM_CHATTRS], 
				self.fieldlist[0].channelexists(name))

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
	ITEM_AUTHOR=5
	ITEM_COPYRIGHT=7
	ITEM_ABSTRACT=9
	ITEM_ALT=11
	ITEM_LONGDESC=13
	N_ITEMS=13
	_attr_to_item = {
		'title': ITEM_TITLE,
		'author': ITEM_AUTHOR,
		'copyright': ITEM_COPYRIGHT,
		'abstract': ITEM_ABSTRACT,
		'alt': ITEM_ALT,
		'longdesc': ITEM_LONGDESC,
	}
	attrs_on_page = ['title', 'author', 'copyright', 'abstract', 'alt', 'longdesc']
	_items_on_page = _attr_to_item.values()
	
class InteriorInfoTabPage(InfoTabPage):
	"""Info page without the alt and longdesc items"""
	items_to_hide = [10, 11, 12, 13]
	attrs_on_page = ['title', 'author', 'copyright', 'abstract']

class DocumentInfoTabPage(InfoTabPage):
	"""Info page without the abstract, alt and longdesc items"""
	items_to_hide = [8, 9, 10, 11, 12, 13]
	attrs_on_page = ['title', 'author', 'copyright']

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
	attrs_on_page = ['duration', 'loop', 'begin']
	_items_on_page = _attr_to_item.values()

class UploadTabPage(MultiStringTabPage):
	TAB_LABEL='Upload'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_UPLOAD
	ITEM_GROUP=1
	ITEM_WEBGROUP=2
	ITEM_WEBHOST=4
	ITEM_WEBUSER=6
	ITEM_WEBDIR=8
	ITEM_MEDIAGROUP=9
	ITEM_MEDIAHOST=11
	ITEM_MEDIAUSER=13
	ITEM_MEDIADIR=15
	N_ITEMS=15
	_attr_to_item = {
		'project_ftp_host': ITEM_WEBHOST,
		'project_ftp_user': ITEM_WEBUSER,
		'project_ftp_dir': ITEM_WEBDIR,
		'project_ftp_host_media': ITEM_MEDIAHOST,
		'project_ftp_user_media': ITEM_MEDIAUSER,
		'project_ftp_dir_media': ITEM_MEDIADIR,
	}
	attrs_on_page = ['project_ftp_host', 'project_ftp_user', 'project_ftp_dir',
		'project_ftp_host_media', 'project_ftp_user_media', 'project_ftp_dir_media']
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
	attrs_on_page = ['clipbegin', 'clipend']
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

class ImageConversionTabPage(MultiTabPage):
	TAB_LABEL='Conversion'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_IMAGE_CONVERSION
	ITEM_GROUP=1
	ITEM_CONVERT=2
	ITEM_QUALITY=4
	N_ITEMS=4
	attrs_on_page = ['project_convert', 'project_quality']
	
	def close(self):
		self._qualitypopup.delete()
		MultiTabPage.close(self)
		
	def init_controls(self, item0):
		rv = SingleTabPage.init_controls(self, item0)
		self._qualitypopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_QUALITY, [], None)
		return rv

	def do_itemhit(self, item, event):
		if item-self.item0 == self.ITEM_CONVERT:
			self.attreditor._togglebutton(item)
			return 1
		elif item-self.item0 == self.ITEM_QUALITY:
			return 1
		return 0
		
	def update(self):
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setbutton(self.item0+self.ITEM_CONVERT, value=='on')
		self.update_popup(self.fieldlist[1], self._qualitypopup)
		
	def update_popup(self, field, popup):
		value = field._getvalueforpage()
		list = field.getoptions()
		popup.setitems(list, value)
		
	def save(self):
		value = self.attreditor._getbutton(self.item0+self.ITEM_CONVERT)
		self.fieldlist[0]._savevaluefrompage(['off', 'on'][value])
		self.save_popup(self.fieldlist[1], self._qualitypopup)

	def save_popup(self, field, popup):
		value = popup.getselectvalue()
		field._savevaluefrompage(value)

class ConversionTabPage(MultiDictTabPage):
	TAB_LABEL='Conversion'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_CONVERSION
	ITEM_GROUP=1
	ITEM_CONVERT=2
	ITEM_TARGET_GROUP=3
	ITEM_28K8=4
	ITEM_56K=5
	ITEM_ISDN=6
	ITEM_2ISDN=7
	ITEM_CABLE=8
	ITEM_LAN=9
	ITEM_AUDIOTYPE=11
	ITEM_VIDEOTYPE=13
	ITEM_PERFECTPLAY=14
	ITEM_MOBILEPLAY=15
	N_ITEMS=15
	# Toggle button items
	_attr_to_item = {
		'project_convert': ITEM_CONVERT,
		'project_perfect': ITEM_PERFECTPLAY,
		'project_mobile': ITEM_MOBILEPLAY,
	}
	# Note: the keys here are the values in AttrEdit.RMTargetsAttrEditorField
	_value_to_item = {
		'28k8 modem': ITEM_28K8,
		'56k modem': ITEM_56K,
		'Single ISDN': ITEM_ISDN,
		'Double ISDN': ITEM_2ISDN,
		'Cable modem': ITEM_CABLE,
		'LAN': ITEM_LAN,
	}
	attrs_on_page = ['project_convert', 'project_targets', 'project_videotype',
		'project_audiotype', 'project_mobile', 'project_perfect']
	_items_on_page = _value_to_item.values() + _attr_to_item.values()
	
	def close(self):
		if self._videopopup:
			self._videopopup.delete()
		if self._audiopopup:
			self._audiopopup.delete()
		MultiDictTabPage.close(self)
		
	def init_controls(self, item0):
		rv = MultiDictTabPage.init_controls(self, item0)
		if self._attr_to_field.has_key('project_videotype'):
			self._videopopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_VIDEOTYPE, [], None)
		else:
			self._videopopup = None
		if self._attr_to_field.has_key('project_audiotype'):
			self._audiopopup = windowinterface.SelectWidget(self.attreditor._dialog,
				self.item0+self.ITEM_AUDIOTYPE, [], None)
		else:
			self._audiopopup = None
		return rv

	def do_itemhit(self, item, event):
		if item-self.item0 == self.ITEM_AUDIOTYPE:
			return 1
		elif item-self.item0 == self.ITEM_VIDEOTYPE:
			return 1
		elif item-self.item0 in self._items_on_page:
			# The rest are all toggle buttons
			self.attreditor._togglebutton(item)
			return 1
		return 0
		
	def update(self):
		self.update_target()
		for attr, item in self._attr_to_item.items():
			if self._attr_to_field.has_key(attr):
				field = self._attr_to_field[attr]
				self.attreditor._setbutton(self.item0+item, field._getvalueforpage()=='on')
		if self._attr_to_field.has_key('project_videotype'):
			self.update_popup(self._attr_to_field['project_videotype'], self._videopopup)
		if self._attr_to_field.has_key('project_audiotype'):
			self.update_popup(self._attr_to_field['project_audiotype'], self._audiopopup)
		
	def update_popup(self, field, popup):
		value = field._getvalueforpage()
		list = field.getoptions()
		popup.setitems(list, value)
		
	def update_target(self):
		field = self._attr_to_field['project_targets']
		attr = field._getvalueforpage()
		targets = string.split(attr, ',')
		for t, item in self._value_to_item.items():
			self.attreditor._setbutton(self.item0+item, (t in targets))

	def save(self):
		self.save_target()
		for attr, item in self._attr_to_item.items():
			if self._attr_to_field.has_key(attr):
				field = self._attr_to_field[attr]
				value = self.attreditor._getbutton(self.item0+item)
				field._savevaluefrompage(['off', 'on'][value])
		if self._attr_to_field.has_key('project_videotype'):
			self.save_popup(self._attr_to_field['project_videotype'], self._videopopup)
		if self._attr_to_field.has_key('project_audiotype'):
			self.save_popup(self._attr_to_field['project_audiotype'], self._audiopopup)

	def save_target(self):
		field = self._attr_to_field['project_targets']
		targets = []
		for t, item in self._value_to_item.items():
			if self.attreditor._getbutton(self.item0+item):
				targets.append(t)
		field._savevaluefrompage(string.join(targets, ','))
		
	def save_popup(self, field, popup):
		value = popup.getselectvalue()
		field._savevaluefrompage(value)

class Conversion1TabPage(ConversionTabPage):
	# audio: no videotype
	items_to_hide = [12, 13]
	attrs_on_page = ['project_convert', 'project_targets', 
		'project_audiotype', 'project_mobile', 'project_perfect']

class Conversion2TabPage(ConversionTabPage):
	# Lightweight video: no convert/mobile/perfect buttons
	items_to_hide = [2, 14, 15]
	attrs_on_page = ['project_targets', 'project_videotype',
		'project_audiotype']

class Conversion3TabPage(ConversionTabPage):
	# Lightweight audio: no convert/mobile/perfect buttons, no video
	items_to_hide = [2, 12, 13, 14, 15]
	attrs_on_page = ['project_targets', 'project_audiotype']

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
	attrs_on_page = ['name', 'channel', '.type']
	
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
			self._fixbutton()
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
		self._fixbutton()

	def save(self):
		value = self.attreditor._getlabel(self.item0+self.ITEM_NODENAME)
		self.fieldlist[0]._savevaluefrompage(value)
		value = self._channelpopup.getselectvalue()
		self.fieldlist[1]._savevaluefrompage(value)
		value = self._typepopup.getselectvalue()
		self.fieldlist[2]._savevaluefrompage(value)

		
	def _fixbutton(self):
		name = self._channelpopup.getselectvalue()
		self.attreditor._setsensitive([self.item0+self.ITEM_CHANNELPROPS], 
				self.fieldlist[1].channelexists(name))

class ChGeneralTabPage(MultiTabPage):
	TAB_LABEL='General'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_CH_GENERAL
	ITEM_GROUP=1
	ITEM_CHNAME=3
	ITEM_CHTYPE=5
	ITEM_TITLE=7
	N_ITEMS=7
	_attr_to_item = {
		'.cname': ITEM_CHNAME,
		'type': ITEM_CHTYPE,
		'title': ITEM_TITLE,
	}
	attrs_on_page = ['.cname', 'type', 'title']
	
	def init_controls(self, item0):
		rv = MultiTabPage.init_controls(self, item0)
		self._typepopup = windowinterface.SelectWidget(self.attreditor._dialog,
				self.item0+self.ITEM_CHTYPE, [], None)
		return rv

	def close(self):
		self._typepopup.delete()
		TabPage.close(self)
		
	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_CHNAME:
			return 1
		elif item == self.item0+self.ITEM_CHTYPE:
			return 1
		elif item == self.item0+self.ITEM_TITLE:
			return 1
		return 0
		
	def update(self):
		value = self.fieldlist[0]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_CHNAME, value)
		value = self.fieldlist[1]._getvalueforpage()
		list = self.fieldlist[1].getoptions()
		self._typepopup.setitems(list, value)
		value = self.fieldlist[2]._getvalueforpage()
		self.attreditor._setlabel(self.item0+self.ITEM_TITLE, value)

	def save(self):
		value = self.attreditor._getlabel(self.item0+self.ITEM_CHNAME)
		self.fieldlist[0]._savevaluefrompage(value)
		value = self._typepopup.getselectvalue()
		self.fieldlist[1]._savevaluefrompage(value)
		value = self.attreditor._getlabel(self.item0+self.ITEM_TITLE)
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

		if len(self.fieldlist) > 4:
			value = self.fieldlist[4]._getvalueforpage()
			self.attreditor._setlabel(self.item0+self.ITEM_REQUIRED, value)

		if len(self.fieldlist) > 5:
			value = self.fieldlist[5]._getvalueforpage()
			self.attreditor._setlabel(self.item0+self.ITEM_SCREENDEPTH, value)

		if len(self.fieldlist) > 6:
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
		
		if len(self.fieldlist) > 4:
			value = self.attreditor._getlabel(self.item0+self.ITEM_REQUIRED)
			self.fieldlist[4]._savevaluefrompage(value)
			
		if len(self.fieldlist) > 5:
			value = self.attreditor._getlabel(self.item0+self.ITEM_SCREENDEPTH)
			self.fieldlist[5]._savevaluefrompage(value)
			
		if len(self.fieldlist) > 6:
			value = self.attreditor._getlabel(self.item0+self.ITEM_SCREENSIZE)
			self.fieldlist[6]._savevaluefrompage(value)
		
class SystemPropertiesPrefTabPage(SystemPropertiesTabPage):
	items_to_hide = (6, 13, 16, 17, 18, 19, 20, 21)
	attrs_on_page = [
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
	]
	ITEM_CAPTION_OFF=SystemPropertiesTabPage.ITEM_CAPTION_OFF
	ITEM_CAPTION_ON=SystemPropertiesTabPage.ITEM_CAPTION_ON
	ITEM_OVERDUB_CAPTION_OVERDUB=SystemPropertiesTabPage.ITEM_OVERDUB_CAPTION_OVERDUB
	ITEM_OVERDUB_CAPTION_CAPTION=SystemPropertiesTabPage.ITEM_OVERDUB_CAPTION_CAPTION
	ILIST_CAPTION=(ITEM_CAPTION_OFF, ITEM_CAPTION_ON)
	ILIST_OVERDUB_CAPTION=(ITEM_OVERDUB_CAPTION_OVERDUB, ITEM_OVERDUB_CAPTION_CAPTION)

class TransitionTabPage(MultiDictTabPage):
	TAB_LABEL='Transition'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_TRANSITION
	ITEM_GROUP=1
	ITEM_TYPE=3
	ITEM_BEGIN=5
	ITEM_DUR=7
	ITEM_COLOR=9
	ITEM_PICK=10
	N_ITEMS=10
	_attr_to_item = {
		'start': ITEM_BEGIN,
		'tduration': ITEM_DUR,
		'color': ITEM_COLOR,
	}
	attrs_on_page = ['tag', 'start', 'tduration', 'color']
	_items_on_page = _attr_to_item.values()
	
	def close(self):
		self._typepopup.delete()
		MultiDictTabPage.close(self)
		
	def init_controls(self, item0):
		rv = MultiDictTabPage.init_controls(self, item0)
		self._typepopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_TYPE, [], None)
		return rv

	def do_itemhit(self, item, event):
		if item-self.item0 == self.item0+self.ITEM_TYPE:
			return 1
		elif item-self.item0 in self._items_on_page:
			# text field
			return 1
		elif item-self.item0 == self.ITEM_PICK:
			self._select_color()
			return 1
		return 0
		
	def _select_color(self):
		import ColorPicker
		value = self.attreditor._getlabel(self.item0+self.ITEM_COLOR)
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
			self.attreditor._setlabel(self.item0+self.ITEM_COLOR, value)
			self.attreditor._selectinputfield(self.item0+self.ITEM_COLOR)

	def update(self):
		for attr, item in self._attr_to_item.items():
			if self._attr_to_field.has_key(attr):
				field = self._attr_to_field[attr]
				value = field._getvalueforpage()
				self.attreditor._setlabel(self.item0+item, value)
		self.update_popup(self._attr_to_field['tag'], self._typepopup)
		
	def update_popup(self, field, popup):
		value = field._getvalueforpage()
		list = field.getoptions()
		popup.setitems(list, value)

	def save(self):
		for attr, item in self._attr_to_item.items():
			if self._attr_to_field.has_key(attr):
				field = self._attr_to_field[attr]
				value = self.attreditor._getlabel(self.item0+item)
				field._savevaluefrompage(value)
		self.save_popup(self._attr_to_field['tag'], self._typepopup)

	def save_popup(self, field, popup):
		value = popup.getselectvalue()
		field._savevaluefrompage(value)

class Transition1TabPage(TransitionTabPage):
	# Without duration
	items_to_hide = [6, 7]
	attrs_on_page = ['tag', 'start', 'color']
	
class Transition2TabPage(TransitionTabPage):
	# Without color
	items_to_hide = [8, 9, 10]
	attrs_on_page = ['tag', 'start', 'tduration']
	
class WipeTabPage(MultiTabPage):
	TAB_LABEL='Wipe'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_WIPE
	ITEM_GROUP=1
	ITEM_TYPE=3
	ITEM_DIRECTION=5
	N_ITEMS=5
	_attr_to_item = {
		'wipetype': ITEM_TYPE,
		'direction': ITEM_DIRECTION,
	}
	attrs_on_page = ['wipetype', 'direction']
	
	def init_controls(self, item0):
		rv = MultiTabPage.init_controls(self, item0)
		self._typepopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_TYPE, [], None)
		self._directionpopup = windowinterface.SelectWidget(self.attreditor._dialog,
				self.item0+self.ITEM_DIRECTION, [], None)
		return rv

	def close(self):
		self._typepopup.delete()
		self._directionpopup.delete()
		TabPage.close(self)
		
	def do_itemhit(self, item, event):
		if item == self.item0+self.ITEM_TYPE:
			return 1
		elif item == self.item0+self.ITEM_DIRECTION:
			# popup
			return 1
		return 0
		
	def update(self):
		value = self.fieldlist[0]._getvalueforpage()
		list = self.fieldlist[0].getoptions()
		self._typepopup.setitems(list, value)
		value = self.fieldlist[1]._getvalueforpage()
		list = self.fieldlist[1].getoptions()
		self._directionpopup.setitems(list, value)

	def save(self):
		value = self._typepopup.getselectvalue()
		self.fieldlist[0]._savevaluefrompage(value)
		value = self._directionpopup.getselectvalue()
		self.fieldlist[1]._savevaluefrompage(value)

class AreaTabPage(MultiDictTabPage):
	"""Not useable on its own: subclassed further down"""
			
	def do_itemhit(self, item, event):
		if item-self.item0 in self._checkboxes:
			self.attreditor._togglebutton(item)
			return 1
		elif item-self.item0 in self._otherfields:
			return 1
		return 0
		
	def update(self):
		for name, item in self._attr_to_checkbox.items():
			field = self._attr_to_field[name]
			value = field._getvalueforpage()
			self.attreditor._setbutton(self.item0+item, value=='on')
		x, y, w, h = self._getxywh()
		self.attreditor._setlabel(self.item0+self.ITEM_X, `x`)
		self.attreditor._setlabel(self.item0+self.ITEM_Y, `y`)
		self.attreditor._setlabel(self.item0+self.ITEM_W, `w`)
		self.attreditor._setlabel(self.item0+self.ITEM_H, `h`)
		
	def _getxywh(self):
		x, y = self._getpoint(self._xyfield)
		w, h = self._getpoint(self._whfield)
		return x, y, w, h
		
	def _getpoint(self, fieldname):
		str = self._attr_to_field[fieldname]._getvalueforpage()
		if not str:
			return 0, 0
		[f1, f2] = string.split(str)
		return string.atoi(f1), string.atoi(f2)

	def save(self):
		for name, item in self._attr_to_checkbox.items():
			field = self._attr_to_field[name]
			value = self.attreditor._getbutton(self.item0+item)
			field._savevaluefrompage(['off','on'][value])
		x = self.attreditor._getlabel(self.item0+self.ITEM_X)
		y = self.attreditor._getlabel(self.item0+self.ITEM_Y)
		w = self.attreditor._getlabel(self.item0+self.ITEM_W)
		h = self.attreditor._getlabel(self.item0+self.ITEM_H)
		self._savexywh(x, y, w, h)
		
	def _savexywh(self, x, y, w, h):
		self._attr_to_field[self._xyfield]._savevaluefrompage(x+' '+y)
		self._attr_to_field[self._whfield]._savevaluefrompage(w+' '+h)

class SourceAreaTabPage(AreaTabPage):
	TAB_LABEL='Source area'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_SOURCE_AREA
	ITEM_GROUP=1
	ITEM_WHOLE=2
	ITEM_X=5
	ITEM_Y=7
	ITEM_W=9
	ITEM_H=11
	N_ITEMS=11
	_attr_to_checkbox = {
		'fullimage': ITEM_WHOLE,
	}
	_xyfield = 'imgcropxy'
	_whfield = 'imgcropwh'
	attrs_on_page = ['fullimage', 'imgcropxy', 'imgcropwh']
	_checkboxes = (ITEM_WHOLE, )
	_otherfields = (ITEM_X, ITEM_Y, ITEM_W, ITEM_H)
			
class DestinationAreaTabPage(AreaTabPage):
	TAB_LABEL='Destination area'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_DESTINATION_AREA
	ITEM_GROUP=1
	ITEM_WHOLE=2
	ITEM_X=5
	ITEM_Y=7
	ITEM_W=9
	ITEM_H=11
	ITEM_ASPECT=12
	N_ITEMS=12
	_attr_to_checkbox = {
		'displayfull': ITEM_WHOLE,
		'aspect': ITEM_ASPECT,
	}
	_xyfield = 'subregionxy'
	_whfield = 'subregionwh'
	attrs_on_page = ['displayfull', 'aspect', 'subregionxy', 'subregionwh']
	_checkboxes = (ITEM_WHOLE, ITEM_ASPECT)
	_otherfields = (ITEM_X, ITEM_Y, ITEM_W, ITEM_H)
	
class Destination1AreaTabPage(DestinationAreaTabPage):
	# Destination area without "keep aspect" checkbox (fadeout)
	items_to_hide=(12,)
	_attr_to_checkbox = {
		'displayfull': DestinationAreaTabPage.ITEM_WHOLE,
	}
	attrs_on_page = ['displayfull', 'subregionxy', 'subregionwh']
	_checkboxes = (DestinationAreaTabPage.ITEM_WHOLE, )
	
class ChannelAreaTabPage(AreaTabPage):
	TAB_LABEL='Position and Size'
	
	ID_DITL=mw_resources.ID_DIALOG_ATTREDIT_CH_AREA
	ITEM_GROUP=1
	ITEM_X=3
	ITEM_Y=5
	ITEM_W=7
	ITEM_H=9
	ITEM_UNITS=11
	ITEM_Z=13
	N_ITEMS=13
	_attr_to_checkbox = {
	}
	_attr_to_string = {
		'z': ITEM_Z,
	}
	_xywhfield = 'base_winoff'
	attrs_on_page = ['base_winoff', 'units', 'z']
	_checkboxes = ()
	_otherfields = (ITEM_X, ITEM_Y, ITEM_W, ITEM_H, ITEM_UNITS, ITEM_Z)

	def init_controls(self, item0):
		rv = AreaTabPage.init_controls(self, item0)
		self._unitspopup = windowinterface.SelectWidget(self.attreditor._dialog, 
				self.item0+self.ITEM_UNITS, [], None)
		return rv
		
	def update(self):
		value = self._attr_to_field['units']._getvalueforpage()
		list = self._attr_to_field['units'].getoptions()
		self._unitspopup.setitems(list, value)
		for name, item in self._attr_to_string.items():
			value = self._attr_to_field[name]._getvalueforpage()
			self.attreditor._setlabel(self.item0+item, value)
		AreaTabPage.update(self)
		
	def _getxywh(self):
		str = self._attr_to_field[self._xywhfield]._getvalueforpage()
		if not str:
			return 0, 0, 0, 0
		[f1, f2, f3, f4] = string.split(str)
		return string.atoi(f1), string.atoi(f2), string.atoi(f3), string.atoi(f4)
		
	def save(self):
		value = self._unitspopup.getselectvalue()
		self._attr_to_field['units']._savevaluefrompage(value)
		for name, item in self._attr_to_string.items():
			value = self.attreditor._getlabel(self.item0+item)
			self._attr_to_field[name]._savevaluefrompage(value)
		AreaTabPage.update(self)

	def _savexywh(self, x, y, w, h):
		self._attr_to_field[self._xywhfield]._savevaluefrompage(x+' '+y+' '+w+' '+h)
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
	ChGeneralTabPage,
	ChannelAreaTabPage,
	GeneralTabPage,
	TimingTabPage,
	TransitionTabPage,
	Transition1TabPage,
	Transition2TabPage,
	XXFileTabPage,
	InfoTabPage,
	InteriorInfoTabPage,
	DocumentInfoTabPage,
	ChannelTabPage,
	CaptionChannelTabPage,
	SystemPropertiesTabPage,
	SystemPropertiesPrefTabPage,
	ConversionTabPage,
	Conversion1TabPage,
	Conversion2TabPage,
	Conversion3TabPage,
	ImageConversionTabPage,
	SourceAreaTabPage,
	DestinationAreaTabPage,
	Destination1AreaTabPage,
	TargetAudienceTabPage,
	ClipTabPage,
	UploadTabPage,
	WipeTabPage,
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
	for wtd in cl.attrs_on_page:
		for a in attrfields:
			if a.getname() == wtd:
				rv.append(a)
				break
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
