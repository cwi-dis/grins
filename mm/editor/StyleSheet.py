# Style sheet editor

# This displays the list of defined style names.
# It is possible to add, delete and rename styles,
# and to edit the attributes of a style.

import gl
import fl
from FL import *
import glwindow
from MMExc import *
import MMAttrdefs
from Dialog import BasicDialog
from ViewDialog import ViewDialog

class StyleSheet(ViewDialog, BasicDialog):
	#
	def init(self, toplevel):
		self = ViewDialog.init(self, 'style_')
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		width, height = MMAttrdefs.getattr(self.root, 'style_winsize')
		title = 'Style sheet (' + toplevel.basename + ')'
		return BasicDialog.init(self, width, height, title)
	#
	def fixtitle(self):
		self.settitle('Style sheet (' + self.toplevel.basename + ')')
	#
	def __repr__(self):
		return '<StyleSheet instance, root=' + `self.root` + '>'
	#
	def transaction(self):
		return 1
	#
	def rollback(self):
		pass
	#
	def commit(self):
		self.load_styles()
	#
	def kill(self):
		self.destroy()
	#
	def show(self):
		if not self.showing:
			self.load_styles()
			BasicDialog.show(self)
			self.toplevel.checkviews()
			self.editmgr.register(self)
	#
	def hide(self):
		if self.showing:
			self.editmgr.unregister(self)
			BasicDialog.hide(self)
			self.toplevel.checkviews()
	#
	def make_form(self):
		# XXX should fdesign...
		self.width, self.height = glwindow.pixels2mm(300, 320)
		BasicDialog.make_form(self) # Make form & Cancel...OK buttons
		form = self.form
		#
		x, y, w, h = 0, 0, 300, 250
		self.browser = form.add_browser(HOLD_BROWSER,x,y,w,h,'Styles')
		self.browser.set_call_back(self.browser_callback, None)
		#
		x, y, w, h = 0, 250, 75, 39
		self.newbutton = form.add_button(NORMAL_BUTTON,x,y,w,h, 'New')
		self.newbutton.set_call_back(self.new_callback, None)
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
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'Edit...')
		self.editbutton.set_call_back(self.edit_callback, None)
		#
		x, y, w, h = 50, 290, 250, 30
		self.nameinput = form.add_input(NORMAL_INPUT,x,y,w,h, 'Name')
		self.nameinput.set_call_back(self.name_callback, None)
		#
	#
	def load_styles(self):
		self.form.freeze_form()
		i, oldname = self.getselected()
		#
		self.browser.clear_browser()
		stylenames = self.context.styledict.keys()
		stylenames.sort()
		for name in stylenames:
			self.browser.add_browser_line(name)
		#
		i, name = 0, ''
		while i < len(stylenames):
			if stylenames[i] >= oldname:
				name = stylenames[i]
				i = i+1
				break
			i = i+1
		if i > 0:
			self.browser.select_browser_line(i)
			line = self.browser.get_browser_line(i)
			self.nameinput.set_input(line)
		else:
			self.nameinput.set_input('')
		#
		self.form.unfreeze_form()
	#
	def browser_callback(self, obj, arg):
		# When an item is selected in the browser,
		# copy its name to the input box.
		i, name = self.getselected()
		self.nameinput.set_input(name)
	#
	def new_callback(self, obj, arg):
		# Add a new style whose name is taken from the input box.
		newname = self.nameinput.get_input()
		# (1) check that the name isn't empty
		if not newname:
			fl.show_message( \
				'Cannot add empty style name', '', '')
			return
		# (2) check that the name doesn't already exist
		if self.context.styledict.has_key(newname):
			fl.show_message( \
				'Style name already exists', newname, '')
			return
		# (3) Add it, using the edit manager
		if not self.editmgr.transaction():
			return
		self.editmgr.addstyle(newname)
		# (3a) Before committing, add it to the browser and select it
		self.browser.freeze_object()
		self.browser.add_browser_line(newname)
		i = self.browser.get_browser_maxline()
		self.browser.select_browser_line(i)
		# (3b) Commit the transaction
		self.editmgr.commit()
		self.browser.unfreeze_object()
		# (4) Immediately open a style editor for it
		import AttrEdit
		AttrEdit.showstyleattreditor(self.context, newname)
	#
	def delete_callback(self, obj, arg):
		# Delete the currently selected style in the browser.
		# (Ignore the input box.)
		i, name = self.getselected()
		# (1) check that a style is indeed selected
		if i == 0 or name == '':
			fl.show_message( \
				'No style selected to delete', '', '')
			return
		# (2) XXX Should check that the style is unused in the tree?!?!
		# (3) delete it, using the edit manager
		if not self.editmgr.transaction():
			return
		self.editmgr.delstyle(name)
		self.editmgr.commit()
		# Rely on our commit callback to fix the browser
	#
	def rename_callback(self, obj, arg):
		# Rename the style selected in the browser.
		# The new name is taken from the input box.
		newname = self.nameinput.get_input()
		# (1) fetch the old name
		i, oldname = self.getselected()
		if i == 0:
			fl.show_message( \
				'No style selected to rename', '', '')
			return
		# (2) check that the new name isn't empty
		if not newname:
			fl.show_message( \
				'Cannot rename to empty style name', '', '')
			return
		# (2a) check that the old and the new name differ
		if oldname == newname:
			fl.show_message( \
			  'Please edit the input box to the new name', '', '')
			return
		# (3) check that the new name doesn't already exist
		if self.context.styledict.has_key(newname):
			fl.show_message( \
				'That name already exists', newname, '')
			return
		# (4) rename it, using the transaction manager
		if not self.editmgr.transaction():
			return
		self.editmgr.setstylename(oldname, newname)
		# (4a) Fix the browser display
		self.browser.replace_browser_line(i, newname)
		# (4b) Commit the transaction
		self.editmgr.commit()
	#
	def edit_callback(self, obj, arg):
		i, name = self.getselected()
		if i == 0:
			fl.show_message( \
				'No style selected to edit', '', '')
			return
		import AttrEdit
		AttrEdit.showstyleattreditor(self.context, name)
	#
	def name_callback(self, obj, arg):
		# When the user presses TAB or RETURN,
		# search the browser for a matching name and select it.
		name = self.nameinput.get_input()
		for i in range(self.browser.get_browser_maxline()):
			if self.browser.get_browser_line(i+1) == name:
				self.browser.select_browser_line(i+1)
				break
	#
	def getselected(self):
		i = self.browser.get_browser()
		if i == 0: return 0, ''
		name = self.browser.get_browser_line(i)
		return i, name
	#
