# Placeholder.

import SourceViewDialog
import windowinterface
import SMILTreeRead, SMILTreeWrite

class SourceView(SourceViewDialog.SourceViewDialog):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.editmgr = self.toplevel.editmgr
		self.setRoot(self.toplevel.root)
		self.myCommit = 0
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
			self.editmgr.register(self, want_focus = 1)
		# set the focus, if already there
		focustype,focusobject = self.editmgr.getglobalfocus()
		self.__setFocus(focustype, focusobject)

	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		SourceViewDialog.SourceViewDialog.hide(self)

	def __setFocus(self, focustype, focusobject):
		# the normal focus is set only if there is no parsing error
		parseErrors = self.context.getParseErrors()
		if parseErrors != None:
			return
		
		if hasattr(focusobject, 'char_positions') and focusobject.char_positions:
			# for now, make selection working only when the source is unmodified
			# for now, make selection working only when the source is unmodified
			# to avoid some position re-computations adter each modification
			if not self.is_changed():
				apply(self.select_chars, focusobject.char_positions)
		
	def globalfocuschanged(self, focustype, focusobject):
		self.__setFocus(focustype, focusobject)

	def setRoot(self, root):
		self.root = root
		self.context = root.context
		
	#
	# edit manager interface
	#
	
	def transaction(self, type):
		if self.myCommit:
			return 1
		if self.is_changed():
			q = windowinterface.GetOKCancel("You have unsaved changes in the source view.\nIs it OK to discard these?", self.toplevel.window)
			return not q
		return 1

	def rollback(self):
		pass

	def commit(self, type=None):
		self.root = self.toplevel.root
		self.read_text()

	#
	#
	#
	
	def read_text(self):
		parseErrors = self.context.getParseErrors()
		if parseErrors == None:
			# Converts the MMNode structure into SMIL and puts it in the window.
			text = SMILTreeWrite.WriteString(self.root, set_char_pos = 1)
			self.set_text(text)
		else:
			self.set_text(parseErrors.getSource())
			
			# get first error
			firstError = parseErrors.getErrorList()[0]
			msg, line = firstError
			if line != None:
				# for now, make selection working only when the source is unmodified
				# to avoid some position re-computations adter each modification
				if not self.is_changed():
					self.select_line(line)
			# XXX pop the source view
			# to do
			
	def write_text(self):
		# Writes the text back to the MMNode structure.
		self.toplevel.save_source_callback(self.get_text())
		
	def __startTransaction(self, hide):
		self.myCommit = 1
		if self.editmgr.transaction('source'):
			text = self.get_text()
			if hide:
				self.hide()
			self.toplevel.change_source(text)
			# update root
			self.setRoot(self.toplevel.root)
			
			parseErrors = self.context.getParseErrors()
			if parseErrors != None:
				# XXX note: the choices may be different for 'fatal error'
				ret = windowinterface.GetYesNoCancel('The source document contains some errors\nDo you wish to leave the editor to fix automaticly the errors', self.toplevel.window)
				if ret == 0: # yes
					# accept the errors automaticly fixed by GRiNS
					self.toplevel.forgetParseErrors()
				elif ret == 1: # no
					# default treatement: accept errors and don't allow to edit another view
					pass
				else: # cancel
					self.editmgr.rollback()
					self.myCommit= 0
					return
			self.editmgr.commit()
						
		self.myCommit= 0

	def write_text_and_close(self):
		self.__startTransaction(1)

	def apply_callback(self):
		self.__startTransaction(0)

	# XXX Hack: see as well TopLevelDialog
	def close_callback(self):
		#self.toplevel.save_source_callback(text)
		if self.is_changed():
			saveme = windowinterface.GetYesNoCancel("Do you wish to keep the changes in the source view?\n(This will not save your document to disk.)", self.toplevel.window)
			if saveme == 0:		# Which means "YES"
				self.write_text_and_close() # Which will close all windows.
			elif saveme == 1: # Which means "No"
				self.hide()
			else:		# "Cancel"
				# Pass through to the end of this method.
				pass	# I know, it's extraneous, but it's here for completion so it's not a hidden option.
		else:
			self.hide()

	def kill(self):
		self.destroy()
