# Placeholder.

import SourceViewDialog
import windowinterface
import SMILTreeRead, SMILTreeWrite

class SourceView(SourceViewDialog.SourceViewDialog):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		SourceViewDialog.SourceViewDialog.__init__(self)

	def fixtitle(self):
		pass
	def get_geometry(self):
		pass
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		SourceViewDialog.SourceViewDialog.destroy(self)

	def show(self):
		if self.is_showing():
			SourceViewDialog.SourceViewDialog.show(self)
		else:
			SourceViewDialog.SourceViewDialog.show(self) # creates the text widget
			self.read_text()
			self.editmgr.register(self)

	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		SourceViewDialog.SourceViewDialog.hide(self)

	def transaction(self,type):
		# check for changes. then return 1.
		# There are changes
		q = windowinterface.GetOKCancel("You have unsaved changes in the source view.\nIs it OK to discard these?", self.toplevel.window)
		return not q

	def rollback(self):
		pass

	def commit(self, type=None):
		self.read_text()

	def read_text(self):
		# Converts the MMNode structure into SMIL and puts it in the window.
		text = SMILTreeWrite.WriteString(self.root)
		self.set_text(text)

	def write_text(self):
		# Writes the text back to the MMNode structure.
		self.toplevel.save_source_callback(self.get_text())
		
	# self.get_text is defined to be system-dependant - it reads from the widget.

	def write_text_and_close(self):
		text = self.get_text()
		self.hide()
		self.toplevel.save_source_callback(text)

	def close_callback(self):
		#self.toplevel.save_source_callback(text)
		if self.is_changed():
			saveme = windowinterface.GetYesNoCancel("Do you wish to keep the changes in the source view?\n(This will not save your document to disk.)", self.toplevel.window)
			if saveme == 0:		# Which means "YES"
				self.write_text_and_close() # Which will close all windows.
			elif saveme == 1: # Which means "No"
				self.hide()
		else:
			self.hide()

	def kill(self):
		self.destroy()