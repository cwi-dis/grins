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
		self.updateFocus()

	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		SourceViewDialog.SourceViewDialog.hide(self)

	def updateFocus(self):
		focustype, focusobject = self.editmgr.getglobalfocus()
		self.__setFocus(focustype, focusobject)
		
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

	def raiseError(self):
		parseErrors = self.context.getParseErrors()
		if parseErrors != None:
			# get first error
			firstError = parseErrors.getErrorList()[0]
			msg, line = firstError
			if line != None:
				# for now, make selection working only when the source is unmodified
				# to avoid some position re-computations adter each modification
				if not self.is_changed():
					self.select_lines(line, line+1)
			# XXX pop the source view
			# to do
				
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
		# update root
		self.setRoot(self.toplevel.root)
		self.read_text()
		self.updateFocus()
		
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
			self.raiseError()
			
	def write_text(self):
		# Writes the text back to the MMNode structure.
		self.toplevel.save_source_callback(self.get_text())
		
	def __applySource(self, wantToHide, autoFixErrors=0):
		self.myCommit = 1
		if self.editmgr.transaction('source'):
			text = self.get_text()

			root = self.toplevel.change_source(text)
			root = self.toplevel.checkParseErrors(root)
			context = root.GetContext()
			parseErrors = context.getParseErrors()
			if parseErrors != None:
				# XXX note: the choices may be different for 'fatal error'
				if not autoFixErrors:
					ret = windowinterface.GetYesNoCancel("The source document contains some errors\nDo you wish to accept GRiNS' automatic fixes?", self.toplevel.window)
				else:
					ret = 0
				if ret == 0: # yes
					# accept the errors automaticly fixed by GRiNS
					context.setParseErrors(None)
					# update edit manager
					self.editmgr.deldocument(self.root) # old root
					self.editmgr.adddocument(root) # new root
				elif ret == 1: # no
					# update edit manager
					# in this case, update juste the source file with the parse errors
					self.editmgr.delparsestatus(self.context.getParseErrors()) # old errors
					self.editmgr.addparsestatus(context.getParseErrors()) # new errors
					# default treatement: accept errors and don't allow to edit another view
				else: # cancel
					self.editmgr.rollback()
					# destroy the new root
					self.toplevel.destroyRoot(root)
					self.myCommit= 0
					return
			else:
				# no error
				if wantToHide:
					# allow to hide only if no error
					self.hide()
				# update edit manager 
				self.editmgr.deldocument(self.root) # old root
				self.editmgr.adddocument(root) # new root
				
			self.editmgr.commit()
						
		self.myCommit= 0

	def apply_callback(self):
		# apply source, not hide, and ask to the user if he wants an automatic GRiNS's fixes
		self.__applySource(0, 0)

	# this method is called by the framework when the user try to close the window
	def close_callback(self):
		if self.is_changed():
			parseErrors = self.context.getParseErrors()
			if parseErrors == None:
				# the source contains some datas not applied, and the original source contains mo error
				saveme = windowinterface.GetYesNoCancel("Do you wish to keep the changes in the source view?\n(This will not save your document to disk.)", self.toplevel.window)
				if saveme == 0:
					# Which means "YES"
					self.__applySource(1) # Which will close all windows.
				elif saveme == 1:
					# Which means "No"
					self.hide()
				else:
					# "Cancel"
					# Pass through to the end of this method.
					pass	# I know, it's extraneous, but it's here for completion so it's not a hidden option.
			else:
				# the source contains some datas not applied, and the original source contains some errors
				# in this case, if the user don't want to apply the changes, we can't close the view
				saveme = windowinterface.GetOKCancel("Do you wish to keep the changes in the source view?\n(This will not save your document to disk.)", self.toplevel.window)
				if saveme == 0:
					# Which means "OK"
					self.__applySource(1) # Which will close all windows.
				else:
					# cancel
					pass
		else:
			# no change
			parseErrors = self.context.getParseErrors()
			if parseErrors == None:
				# no error, so the view can be closed
				self.hide()
			else:
				# there are some, error. So maybe the user want to leave grins fix automaticly the errors
				ret = windowinterface.GetYesNo("The source document still contains some errors.\nDo you wish to accept GRiNS' automatic fixes?", self.toplevel.window)
				if ret == 0:
					# yes
					# apply the source, hide the window, and accept automaticly the GRiNS's fixes
					self.__applySource(1, 1)
				else:
					# otherwise, we don't allow to close the window, and we re-raise the error
					self.raiseError()

	def kill(self):
		self.destroy()

	def __appendNodeList(self, node, list):
		list.append(node)
		for child in node.GetChildren():
			self.__appendNodeList(child, list)

	def onRetrieveNode(self):
		if self.is_changed():
			windowinterface.showmessage("You must apply or revert the last modifications before to be able to use this function.", mtype = 'error')
			return
			
		parseErrors = self.context.getParseErrors()
		if parseErrors != None:
			windowinterface.showmessage("The source document contains some errors. \n You must fix them before to be able to use this function.", mtype = 'error')
			return
		
		charIndex = self.getCurrentCharIndex()
		objectListToInspect = []
		
		# make a list of objects to inspect
		# 1) mmnode
		self.__appendNodeList(self.root, objectListToInspect)
		# 2) viewport/regions
		viewportList = self.context.getviewports()
		for viewport in viewportList:
			self.__appendNodeList(viewport, objectListToInspect)
		# ... XXX to complete the list (regpoint, anchor, ...) for selectable objects
		
		# find all objects which surround the current pointed char
		objectFoundList = []
		for object in objectListToInspect:
			if hasattr(object, 'char_positions') and object.char_positions:
				begin, end = object.char_positions
				if charIndex >= begin and charIndex < end:
					objectFoundList.append(object)

		# figure out the most interior object
		objectToSelect = None
		maxInd = -1
		for object in objectFoundList:
			if object.char_positions > maxInd:
				objectToSelect = object
				maxInd = object.char_positions

		# at last select object
		if objectToSelect != None:
			className = objectToSelect.getClassName()
			self.editmgr.setglobalfocus(className, objectToSelect)
		else:
			# if no object, show a warning
			windowinterface.showmessage("Node not found", mtype = 'error')
			