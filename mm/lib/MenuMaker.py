# A class to build SGI style hierarchical menus.
# A command list is a list of (shortcut, itemtext, function) tuples,
# where function can be either a function object or a command list
# (in the latter case defining a submenu).
# Interface:
#  m = MenuObject(title, commandlist)
#  func = m.popup(x, y)
#  func = m.shortcut(c)
# Note that the function isn't called here, it is only returned!

import gl


class MenuObject:

	# Initialize the object
	def __init__(self, title, commandlist):
		self.menuids = []
		self.menuprocs = []
		self.keymap = {}
		self.menu = self.makesubmenu(title, commandlist)

	# Destroy the object
	def close(self):
		for menu in self.menuids:
			gl.freepup(menu)
		self.menuids = []
		self.menuprocs = []
		self.keymap = {}
		self.menu = None

	# Do mouse interaction.  X and y are the mouse coordinates
	# (as returned by the mouse event).  Return a function or None.
	def popup(self, x, y):
		if not self.menu:
			return None
		i = gl.dopup(self.menu)
		if 0 < i <= len(self.menuprocs):
			return self.menuprocs[i-1]
		else:
			return None

	# Look up a keyboard shortcut and return the corresponding
	# function, or None if the shortcut is undefined.
	def shortcut(self, c):
		if self.keymap.has_key(c):
			return self.keymap[c]
		else:
			return None

	# Internal function to make a (sub)menu
	def makesubmenu(self, title, commandlist):
		menu = gl.newpup()
		self.menuids.append(menu)
		if title:
			gl.addtopup(menu, title + '%t', 0)
		for char, text, proc in commandlist:
			if char: self.keymap[char] = proc
			else: char = '  '
			if not text: continue
			text = char + ' ' + text
			if proc is None:
				gl.addtopup(menu, text, 0)
			elif type(proc) is type([]):
				submenu = self.makesubmenu('', proc)
				gl.addtopup(menu, text + '%m', submenu)
			else:
				text = text + '%x' + `1+len(self.menuprocs)`
				gl.addtopup(menu, text, 0)
				self.menuprocs.append(proc)
		return menu
