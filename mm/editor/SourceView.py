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
			return
		SourceViewDialog.SourceViewDialog.show(self)
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

	def close_source_callback(self):
		saveme = windowinterface.GetYesNoCancel("Do you want to keep your changes?", self.toplevel.window)
		if saveme==0:		# Which means "YES"
			self.write_text()

	def kill(self):
		self.destroy()
