# Style sheet editor

# This displays the list of defined style names.
# It is possible to add, delete and rename styles,
# and to edit the attributes of a style.

from MMExc import *
import MMAttrdefs
from ViewDialog import ViewDialog
import windowinterface

class StyleSheet(ViewDialog):
	def init(self, toplevel):
		self = ViewDialog.init(self, 'style_')
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		title = 'Style sheet (' + toplevel.basename + ')'
		self.window = w = windowinterface.Window(title)
		self.browser = w.Selection(
			'Styles', 'Name', [], None,
			left =: None, top = None, right = None)
		separator = w.Separator(
			left = None, right = None, top = self.browser)
		buttons = w.ButtonRow(
			[('New', (self.new_callback, ())),
			 ('Delete', (self.delete_callback, ())),
			 ('Rename', (self.rename_callback, ())),
			 ('Edit...', (self.edit_callback, ()))],
			left = None, right = None, top = separator,
			vertical = 0)
		self.showing = 0
		return self

	def setwaiting(self):
		pass

	def setready(self):
		pass

	def is_showing(self):
		return self.showing

	def destroy(self):
		self.hide()
		self.window.close()
		self.window = None
		self.browser = None

	def get_geometry(self):
		self.load_geometry()
		return self.last_geometry
		
	def fixtitle(self):
		if self.is_showing():
			self.window.settitle('Style sheet (' + self.toplevel.basename + ')')

	def __repr__(self):
		return '<StyleSheet instance, root=' + `self.root` + '>'

	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
		self.load_styles()

	def kill(self):
		self.destroy()

	def show(self):
		if not self.showing:
			self.load_styles()
			self.toplevel.checkviews()
			self.editmgr.register(self)
			self.window.show()
			self.showing = 1

	def hide(self):
		if self.showing:
			self.editmgr.unregister(self)
			self.toplevel.checkviews()
			self.window.hide()
			self.showing = 0

	def load_styles(self):
		i, oldname = self.getselected()

		self.browser.delalllistitems()

		stylenames = self.context.styledict.keys()
		stylenames.sort()
		self.browser.addlistitems(stylenames, -1)

		i = 0
		while i < len(stylenames):
			if stylenames[i] >= oldname:
				self.browser.selectitem(i)
				break
			i = i+1

	def new_callback(self):
		# Add a new style whose name is taken from the input box.
		newname = self.browser.getselection()
		# (1) check that the name isn't empty
		if not newname:
			windowinterface.showmessage(
				'Cannot add empty style name')
			return
		# (2) check that the name doesn't already exist
		if self.context.styledict.has_key(newname):
			windowinterface.showmessage(
				'Style name already exists\n' + newname)
			return
		# (3) Add it, using the edit manager
		if not self.editmgr.transaction():
			return
		self.editmgr.addstyle(newname)
		# (3a) Before committing, add it to the browser and select it
		self.browser.addlistitem(newname, -1)
		self.browser.selectitem(-1)
		# (3b) Commit the transaction
		self.editmgr.commit()
		# (4) Immediately open a style editor for it
		import AttrEdit
		AttrEdit.showstyleattreditor(self.context, newname)

	def delete_callback(self):
		# Delete the currently selected style in the browser.
		# (Ignore the input box.)
		i, name = self.getselected()
		# (1) check that a style is indeed selected
		if i == -1 or name == '':
			windowinterface.showmessage(
				'No style selected to delete')
			return
		# (2) XXX Should check that the style is unused in the tree?!?!
		# (3) delete it, using the edit manager
		if not self.editmgr.transaction():
			return
		self.editmgr.delstyle(name)
		self.editmgr.commit()
		# Rely on our commit callback to fix the browser

	def rename_callback(self):
		# Rename the style selected in the browser.
		# The new name is taken from the input box.
		newname = self.browser.getselection()
		# (1) fetch the old name
		i, oldname = self.getselected()
		if i == -1:
			windowinterface.showmessage(
				'No style selected to rename')
			return
		# (2) check that the new name isn't empty
		if not newname:
			windowinterface.showmessage(
				'Cannot rename to empty style name')
			return
		# (2a) check that the old and the new name differ
		if oldname == newname:
			windowinterface.showmessage(
			  'Please edit the input box to the new name')
			return
		# (3) check that the new name doesn't already exist
		if self.context.styledict.has_key(newname):
			windowinterface.showmessage(
				'That name already exists\n' + newname)
			return
		# (4) rename it, using the transaction manager
		if not self.editmgr.transaction():
			return
		self.editmgr.setstylename(oldname, newname)
		# (4a) Fix the browser display
		self.browser.replacelistitem(i, newname)
		# (4b) Commit the transaction
		self.editmgr.commit()

	def edit_callback(self):
		i, name = self.getselected()
		if i == -1:
			windowinterface.showmessage(
				'No style selected to edit')
			return
		import AttrEdit
		AttrEdit.showstyleattreditor(self.context, name)

	def name_callback(self):
		# When the user presses TAB or RETURN,
		# search the browser for a matching name and select it.
		name = self.nameinput.get_input()
		for i in range(self.browser.get_browser_maxline()):
			if self.browser.get_browser_line(i+1) == name:
				self.browser.select_browser_line(i+1)
				break

	def getselected(self):
		i = self.browser.getselected()
		if i is None:
			return -1, ''
		name = self.browser.getlistitem(i)
		return i, name
