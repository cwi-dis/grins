# Module to build SGI style hierarchical menus from a command list.
# A command list is a list of (shortcut, itemtext, procedure) tuples,
# where procedure can be either a function object or a command list
# (in the latter case defining a submenu).

# XXX This should be made more object-oriented.

import gl

# Make a menu, a list of menuprocs, and a keymap.
def makemenu(title, commandlist):
	menuprocs = []
	keymap = {}
	if title:
		commandlist = commandlist[:]
		commandlist.insert(0, (None, title + '%t', None))
	menu = makesubmenu(commandlist, menuprocs, keymap)
	return menu, menuprocs, keymap

# Make a (sub)menu (subroutine for makemenu)
def makesubmenu(commandlist, menuprocs, keymap):
	menu = gl.newpup()
	for char, text, proc in commandlist:
		if char: keymap[char] = proc
		else: char = '  '
		if not text: continue
		text = char + ' ' + text
		if proc is None:
			gl.addtopup(menu, text, 0)
		elif type(proc) is type([]):
			submenu = makesubmenu(proc, menuprocs, keymap)
			gl.addtopup(menu, text + '%m', submenu)
		else:
			gl.addtopup(menu, text + '%x' + `1+len(menuprocs)`, 0)
			menuprocs.append(proc)
	return menu
