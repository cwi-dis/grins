import Menu
MenuMODULE=Menu  # Silly name clash with FrameWork.Menu
import MenuTemplate

#
# Stuff imported from other mw_ modules
#
import mw_globals

#
# Our menus are pretty similar to FrameWork menus, but we handle
# dispatching a bit different. So, we inherit the FrameWork menus
# but override a few methods.
#

from FrameWork import Menu, PopupMenu, MenuItem, SubMenu

class MyMenuMixin:
	# We call our callbacks in a simpler way...
	def dispatch(self, id, item, window, event):
		title, shortcut, callback, type = self.items[item-1]
		if callback:
			apply(callback[0], callback[1])

	def addsubmenu(self, label, title=''):
		sub = MyMenu(self.bar, title, -1)
		item = self.additem(label, '\x1B', None, 'submenu')
		self.menu.SetItemMark(item, sub.id)
		return sub

class MyMenu(MyMenuMixin, Menu):
	pass

class MyPopupMenu(MyMenuMixin, PopupMenu):
	"""This is either a cascading or button-triggered popup menu"""
	pass
	
class FullPopupMenu:
	"""This is a contextual (right-mouse) popup menu"""
	def __init__(self, list, title = None, accelerators=None):
		self._themenu = mw_globals.toplevel._addpopup()
		self._fill_menu(self._themenu, list, accelerators)
		
	def delete(self):
		self._themenu.delete()
		self._themenu = None
		
	def _fill_menu(self, menu, list, accelerators):
		self.toggle_values = []
		self.toggle_entries = []
		for item in list:
			if item is None:
				menu.addseparator()
			else:
				is_toggle_item = 0
				if len(item) > 3:
					char, itemstring, callback, tp = \
					      item[:4]
					if tp == 't':
						is_toggle_item = 1
						callback = (self.toggle_callback, (len(self.toggle_values), callback))
						if len(item) > 4:
							self.toggle_values.append(item[4])
						else:
							self.toggle_values.append(0)
				elif len(item) == 3:
					char, itemstring, callback = item
				else:
					itemstring, callback = item
					char = ''
				if type(callback) == type([]):
					# Submenu
					m = menu.addsubmenu(itemstring)
					self._fill_menu(m, callback, accelerators)
				else:
					m = MenuItem(menu, itemstring, '',
						     callback)
					if char and not accelerators is None:
						accelerators[char] = callback
						# We abuse the mark position for the shortcut (sigh...)
						m.setmark(ord(char))
					if is_toggle_item:
						self.toggle_entries.append(m)
						m.check(self.toggle_values[-1])
						
	def toggle_callback(self, index, (cbfunc, cbargs)):
		self.toggle_values[index] = not self.toggle_values[index]
		self.toggle_entries[index].check(self.toggle_values[index])
		apply(cbfunc, cbargs)
						
	def popup(self, x, y, event, window=None):
		self._themenu.popup(x, y, event, window=window)

class SelectPopupMenu(PopupMenu):
	def __init__(self, list):
		PopupMenu.__init__(self, mw_globals.toplevel._menubar)
		self.additemlist(list)

	def additemlist(self, list):
		for item in list:
			self.additem(item)
			
	def getpopupinfo(self):
		return self.menu, self.id

class _SpecialMenu:
	"""_SpecialMenu - Helper class for CommandHandler Window and Document menus"""
	
	def __init__(self, title, callbackfunc):
		self.items = []
		self.menus = []
		self.cur = None
		self.title = title
		self.callback = callbackfunc
		self.menu = mw_globals.toplevel._addmenu(self.title)
		
	def set(self, list, cur):
		if list != self.items:
			# If the list isn't the same we have to modify it
			if list[:len(self.items)] != self.items:
				# And if the old list isn't a prefix we start from scratch
				self.menus.reverse()
				for m in self.menus:
					m.delete()
				self.menus = []
				self.items = []
				self.cur = None
			list = list[len(self.items):]
			for item in list:
				self.menus.append(MenuItem(self.menu, item, None, (self.callback, (item,))))
				self.items.append(item)
		if cur != self.cur:
			if self.cur != None:
				self.menus[self.cur].check(0)
			if cur != None:
				self.menus[cur].check(1)
			self.cur = cur
		self.menu.enable(not not self.items)

class CommandHandler:
	def __init__(self, menubartemplate):
		self.cmd_to_menu = {}
		self.cmd_enabled = {}
		self.must_update_window_menu = 1
		self.must_update_document_menu = 1
		self.all_cmd_groups = [None, None, None]
		self.menubartraversal = []
		for menutemplate in menubartemplate:
			title, content = menutemplate
			menu = mw_globals.toplevel._addmenu(title)
			itemlist = self.makemenu(menu, content)
			self.menubartraversal.append(MenuTemplate.CASCADE,
						     menu, itemlist)
		# Create special menus
		self.document_menu = _SpecialMenu(
			'Documents', mw_globals.toplevel._pop_group)
		self.window_menu = _SpecialMenu(
			'Windows', mw_globals.toplevel._pop_window)
			
	def install_cmd(self, number, group):
		if self.all_cmd_groups[number] == group:
			return 0
		self.all_cmd_groups[number] = group
		if number == 0:
			self.must_update_window_menu = 1
		else:
			self.must_update_document_menu = 1
		# Don't update, we do that in the event loop by calling
		# update_menus_enabled
		return 1
		
	def uninstall_cmd(self, number, group):
		if self.all_cmd_groups[number] == group:
			self.install_cmd(number, None)
			return 1
		if __debug__:
			if group in self.all_cmd_groups:
				raise 'Oops, group in wrong position!'
		return 0
			
	def makemenu(self, menu, content):
		itemlist = []
		for entry in content:
			entry_type = entry[0]
			if entry_type in (MenuTemplate.ENTRY,
					  MenuTemplate.TOGGLE):
				dummy, name, shortcut, cmd = entry
				mw_globals._all_commands[cmd] = 1
				if self.cmd_to_menu.has_key(cmd):
					raise 'Duplicate menu command', \
					      (name, cmd)
				if entry_type == MenuTemplate.ENTRY:
					cbfunc = self.normal_callback
				else:
					cbfunc = self.toggle_callback
				mentry = MenuItem(menu, name, shortcut,
						  (cbfunc, (cmd,)))
				self.cmd_to_menu[cmd] = mentry
				self.cmd_enabled[cmd] = 1
				itemlist.append(entry_type, cmd)
			elif entry_type == MenuTemplate.SEP:
				menu.addseparator()
			elif entry_type == MenuTemplate.CASCADE:
				dummy, name, subcontent = entry
				submenu = SubMenu(menu, name, name)
				subitemlist = self.makemenu(submenu,
							    subcontent)
				itemlist.append(entry_type, submenu,
						subitemlist)
			else:
				raise 'Unknown menu entry type', entry_type
		return itemlist
				
	def toggle_callback(self, cmd):
		mentry = self.cmd_to_menu[cmd]
		group = self.find_toggle_group(cmd)
		if group:
			group.toggle_toggle(cmd) # Force a menubar redraw later
		else:
			print 'HUH? No group for toggle cmd', cmd
		self.normal_callback(cmd)
		
	def normal_callback(self, cmd):
		cmd = self.find_command(cmd, mustfind=1)
		if cmd:
			func, arglist = cmd
			apply(func, arglist)
		else: # debug
			print 'CommandHandler: unknown command', cmd #debug
		
	def find_command(self, cmd, mustfind=0):
		for group in self.all_cmd_groups:
			if group:
				callback = group.get_command_callback(cmd)
				if callback:
					if mustfind and not self.cmd_enabled[cmd]: # debug
						print 'CommandHandler: disabled command selected:', cmd # debug
					return callback
		return None
		
	def find_toggle_group(self, cmd):
		for group in self.all_cmd_groups:
			if group and group.has_command(cmd):
					return group
		return None
		
	def _update_one(self, items):
		any_active = 0
		for item in items:
			itemtype = item[0]
			if itemtype == MenuTemplate.CASCADE:
				itemtype, submenu, subitems = item
				must_be_enabled = self._update_one(subitems)
				submenu.enable(must_be_enabled)
			else:
				itemtype, cmd = item
				must_be_enabled = (not not self.find_command(cmd))
				if must_be_enabled != self.cmd_enabled[cmd]:
					mentry = self.cmd_to_menu[cmd]
					mentry.enable(must_be_enabled)
					self.cmd_enabled[cmd] = must_be_enabled
				if must_be_enabled and \
				   itemtype == MenuTemplate.TOGGLE:
					mentry = self.cmd_to_menu[cmd]
					group = self.find_toggle_group(cmd)
					if group:
						mentry.check(group.get_toggle(
							cmd))
			if must_be_enabled:
				any_active = 1
		return any_active

	def update_menus(self):
		self._update_one(self.menubartraversal)
		if self.must_update_window_menu:
			self.update_window_menu()
			self.must_update_window_menu = 0
		if self.must_update_document_menu:
			self.update_document_menu()
			self.must_update_document_menu = 0
				
	def update_window_menu(self):
		list, cur = mw_globals.toplevel._get_window_names()
		self.window_menu.set(list, cur)
		
	def update_document_menu(self):
		list, cur = mw_globals.toplevel._get_group_names()
		self.document_menu.set(list, cur)
