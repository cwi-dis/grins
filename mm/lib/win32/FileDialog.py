__version__ = "$Id$"

import win32ui, win32con, win32api

# New version using win32ui functions
# REM: extend function in order to set directory
class FileDialog:
	def __init__(self, prompt,directory,filter,file, cb_ok, cb_cancel,existing = 0):
		
		if existing: 
			flags=win32con.OFN_HIDEREADONLY|win32con.OFN_FILEMUSTEXIST
		else:
			flags=win32con.OFN_OVERWRITEPROMPT

		if not filter or filter=='*':
			filter = 'All files (*.*)|*.*||'
		else:
			filter = 'smil files (*.smi;*.smil)|*.smi;*.smil|cmif files (*.cmif)|*.cmif|All files *.*|*.*||'
			
		dlg = win32ui.CreateFileDialog(existing,None,file,flags,filter,None)
		dlg.SetOFNTitle(prompt)

		if dlg.DoModal()==win32con.IDOK:
			cb_ok(dlg.GetPathName())
		else:
			if cb_cancel!=None: cb_cancel()


##################################################################
""" OLD VERSION USING cmifex2
class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel, existing = 0):
		import os

		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel
		
		#print 'PARAMETERS ARE:----------------'
		print 'prompt-directory-filter-file'
		print prompt, "  ",  directory, "  ", filter, " ", file
		
		self._form = None
		
		# formerly the class converted the given filter to a format understandable by the extension
		# module Htmlex (see the following lines)
		# currently we rely on the functions that call the class to provide the filter in a proper format
		# Example of proper format : file type 1 (*.1)|*.1|file type 2 (*.2)|*.2|...|filetype n (*.n)|*.n||

		#import string
		if not filter or filter=='*':
			filter = 'All files *.*|*.*||'
		else:
			filter = 'smil files (*.smi;*.smil)|*.smi;*.smil|cmif files (*.cmif)|*.cmif|All files *.*|*.*||'
		
		self.filter = filter
		if file == None or file == '':
			file = ' '
		if directory == None or directory == '' or directory=='.':
			directory = ' '
		if prompt == None or prompt == '':
			prompt=' '
		import nturl2path
		directory = nturl2path.url2pathname(directory)
		file = nturl2path.url2pathname(file)
		if existing == OPEN_FILE:
			#id, flname, directory, fltr = cmifex2.CreateFileOpenDlg(prompt,file,directory,fltr)
			print 'GIVEN TO F DIALOG: ', file, '---', filter
			#id, flname, fltr =  Htmlex.FDlg(prompt, file, filter)
			win32ui.MessageBox("windowinterface.py OpenFile")
			id, flname, fltr = cmifex2.CreateFileOpenDlg(prompt,file,filter)
			directory, name = os.path.split(flname)
			print id, flname, directory, fltr
		#if type == SAVE_CMIF:
		else:
			id, flname, fltr = cmifex2.CreateFileSaveDlg(prompt,file,filter)
			l = len(flname)
			tmp = flname[(l-5):]
			import string, os
			tmp = string.lower(tmp)
			if (tmp != '.cmif'):
				flname = flname #+ '.cmif'		
		
		if id==1:
			self._ok_callback(flname, directory, fltr)
		else:
			self._cancel_callback()
		
		del self

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			#self._form.UnmanageChild()
			#self._form.DestroyWidget()
			self._dialog = None
			self._form = None

	#def setcursor(self, cursor):
	#	WIN32_windowbase._win_setcursor(self._form, cursor)

	def is_closed(self):
		return self._form is None

	def _cancel_callback(self):
		print "Cancel button pressed!!!"
		self.close()


	def old_cancel_callback(self, *rest):
		if self.is_closed():
			return
		must_close = TRUE
		try:
			if self.cb_cancel:
				ret = self.cb_cancel()
				if ret:
					if type(ret) is StringType:
						showmessage(ret, mtype = 'error')
					must_close = FALSE
					return
		finally:
			if must_close:
				self.close()

	def _ok_callback(self, file, directory, pattern):
		import string
		file = string.lower(file)
		filename = file
		dir = directory
		filter = pattern
				
		if (self.cb_ok!=None):
			ret = self.cb_ok(filename)
			if ret:
				print "ret-->", ret;
				if type(ret) is StringType:
					win32ui.MessageBox(ret, "Warning !", win32con.MB_OK)
				return
	
	
	def old_ok_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		import os
		filename = call_data.value
		dir = call_data.dir
		filter = call_data.pattern
		filename = os.path.join(dir, filename)
		if not os.path.isfile(filename):
			if os.path.isdir(filename):
				filter = os.path.join(filename, filter)
				self._dialog.FileSelectionDoSearch(filter)
				return
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()
"""

