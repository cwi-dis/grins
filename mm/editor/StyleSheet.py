# Style list editor

# This displays the list of defined style names.
# It is possible to add / delete styles, and to edit the attributes
# of a style.

import gl
import fl
from FL import *
import glwindow
from MMExc import *
import MMAttrdefs
import AttrEdit

WIDTH, HEIGHT = 300, 320

class StyleEditor():
	#
	def init(self, root):
		self.root = root
		self.context = root.GetContext()
		self.makeform()
		return self
	#
	def show(self):
		#
		# Use the winpos attribute of the root to place the panel
		#
		h, v = MMAttrdefs.getattr(self.root, 'style_winpos')
		glwindow.setgeometry(h, v, WIDTH, HEIGHT)
		#
		self.form.show_form(PLACE_SIZE, TRUE, 'Style List Editor')
	#
	def hide(self):
		self.form.hide_form()
	#
	def destroy(self):
		self.hide()
	#
	#
	#
	def makeform(self):
		form = fl.make_form(FLAT_BOX, WIDTH, HEIGHT)
		#
		x, y, w, h = 0, 0, 300, 250
		self.browser = form.add_browser(HOLD_BROWSER,x,y,w,h,'Styles')
		self.browser.set_call_back(self.browser_callback, None)
		#
		stylenames = self.context.styledict.keys()
		stylenames.sort()
		for name in stylenames:
			self.browser.add_browser_line(name)
		#
		x, y, w, h = 0, 250, 75, 39
		self.addbutton = form.add_button(RETURN_BUTTON,x,y,w,h, 'Add')
		self.addbutton.set_call_back(self.add_callback, None)
		#
		x, y, w, h = 75, 250, 75, 39
		self.deletebutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'Delete')
		self.deletebutton.set_call_back(self.delete_callback, None)
		#
		x, y, w, h = 150, 250, 75, 39
		self.renamebutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'Rename')
		self.renamebutton.set_call_back(self.rename_callback, None)
		#
		x, y, w, h = 225, 250, 75, 39
		self.editbutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'Edit')
		self.editbutton.set_call_back(self.edit_callback, None)
		#
		x, y, w, h = 50, 290, 250, 30
		self.nameinput = form.add_input(NORMAL_INPUT,x,y,w,h, 'Name')
		self.nameinput.set_call_back(self.name_callback, None)
		#
		self.form = form
	#
	def browser_callback(self, (obj, arg)):
		i = obj.get_browser()
		name = obj.get_browser_line(i)
		self.nameinput.set_input(name)
	#
	def add_callback(self, (obj, arg)):
		# Add a new style.
		# Its name is taken from the name input box.
		newname = self.nameinput.get_input()
		# (1) check that the name isn't empty
		if not newname:
			fl.show_message( \
				'Cannot add empty style name', '', '')
			return
		# (2) check that the name doesn't already exist
		if self.context.styledict.has_key(newname):
			fl.show_message( \
				'That name already exists', newname, '')
			return
		# (3) make a new style; use current selected style as base
		attrdict = {}
		i, base = self.getselected()
		if base: attrdict['style'] = [base]
		self.context.addstyles({newname: attrdict})
		# (4) add it to the browser and select it
		self.browser.addto_browser(newname)
		n = self.browser.get_browser_maxline()
		self.browser.select_browser_line(n)
		# XXX Should sort it!
		# (5) edit the style
		# XXX later...
	#
	def delete_callback(self, (obj, arg)):
		# Delete the style selected in the browser.
		# Ignore the input boxes.
		i, name = self.getselected()
		# (0) check that a style is indeed selected
		if i = 0 or name = '':
			fl.show_message( \
				'No style selected to delete', '', '')
			return
		# (1) check that the selected name indeed exists
		# XXX this check is redundant
		if not self.context.styledict.has_key(name):
			fl.show_message( \
				'That style does not exist!?!?', name, '')
			return
		# (2) XXX check that the style is unused in the tree?!?!
		# (3) delete it from the styledict
		del self.context.styledict[name]
		# (4) delete it from the browser and select neighbour
		self.browser.delete_browser_line(i)
		n = self.browser.get_browser_maxline()
		if 1 <= i <= n:
			self.browser.select_browser_line(i)
		elif 1 <= n < i:
			self.browser.select_browser_line(n)
	#
	def rename_callback(self, (obj, arg)):
		# Rename the style selected in the browser.
		# The new name is taken from the name input box.
		newname = self.nameinput.get_input()
		# (1) check that the new name isn't empty
		if not newname:
			fl.show_message( \
				'Cannot rename to empty style name', '', '')
			return
		# (2) check that the new name doesn't already exist
		# XXX this check is redundant
		if self.context.styledict.has_key(newname):
			fl.show_message( \
				'That name already exists', newname, '')
			return
		# (3) check that the old name indeed exists
		i = self.browser.get_browser()
		oldname = self.browser.get_browser_line(i)
		if not self.context.styledict.has_key(oldname):
			fl.show_message( \
				'That style does not exist!?!?', oldname, '')
			return
		# (4) do the rename in the channeldict
		attrdict = self.context.styledict[oldname]
		self.context.styledict[newname] = attrdict
		del self.context.styledict[oldname]
		# (5) update the browser and select it
		self.browser.replace_browser_line(i, newname)
		self.browser.select_browser_line(i)
		# (6) XXX Rename all uses in the tree?
	#
	def edit_callback(self, (obj, arg)):
		print 'edit callback'
	#
	def name_callback(self, (obj, arg)):
		pass
	#
	def getselected(self):
		i = self.browser.get_browser()
		if i = 0: return 0, ''
		name = self.browser.get_browser_line(i)
		return i, name
	#
