__version__ = "$Id$"

import winuser
import wincon
import string
import os
import MMmimetypes
import grins_mimetypes

class showmessage:
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'GRiNS', parent = None, identity = None):
		# XXXX If identity != None the user should have the option of not
		# showing this message again
		self._wnd = None
		if grab == 0:
			pass
			#self._wnd = ModelessMessageBox(text,title,parent)
			#return
		if cancelCallback:
			style = wincon.MB_OKCANCEL
		else:
			style = wincon.MB_OK

		if mtype == 'error':
			style = style |wincon.MB_ICONERROR
				
		elif mtype == 'warning':
			style = style | wincon.MB_ICONWARNING
			
		elif mtype == 'information':
			style = style | wincon.MB_ICONINFORMATION
	
		elif mtype == 'message':
			style = style | wincon.MB_ICONINFORMATION
			
		elif mtype == 'question':
			style = wincon.MB_OKCANCEL|wincon.MB_ICONQUESTION
		
		elif mtype == 'yesno':
			style = wincon.MB_YESNO|wincon.MB_ICONQUESTION
		
		if not parent or not hasattr(parent,'MessageBox'):	
			self._res = winuser.MessageBox(text, title, style)
		else:
			self._res = parent.MessageBox(text, title, style)
		if callback and self._res == wincon.IDOK:
			apply(apply,callback)
		elif cancelCallback and self._res == wincon.IDCANCEL:
			apply(apply,cancelCallback)

	# Returns user response
	def getresult(self):
		return self._res

def showquestion(text, parent = None):
	return showmessage(text, mtype = 'yesno', parent = parent)

class ProgressDialog:
	def __init__(self, *args):
		print 'ProgressDialog', args

	def set(self, *args):
		print 'ProgressDialog', args


class FileDialog:
	# Remember last location when the program does not request a specific
	# location
	last_location = None

	# Class constructor. Creates abd displays a std FileDialog
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel, existing = 0,parent=None):
		
		if existing: 
			flags = wincon.OFN_HIDEREADONLY | wincon.OFN_FILEMUSTEXIST
		else:
			flags = wincon.OFN_HIDEREADONLY | wincon.OFN_OVERWRITEPROMPT
		if not parent:
			import __main__
			parent = __main__.toplevel.getactivedocframe()
		if not filter or type(filter) == type('') and not '/' in filter:
			# Old style (pattern) filter
			if not filter or filter == '*':
				filter = 'All files (*.*)|*.*||'
				dftext = None
			else:
				filter = '%s|%s||'%(filter, filter)
				dftext = string.split(filter, '.')[-1]
		else:
			# New-style mimetype filter
			descr = None
			if type(filter) == type(''):
				filter = [filter]
			elif filter and filter[0][:1] == '/':
				descr = filter[0][1:]
				filter = filter[1:]
			dftext = None
			newfilter = []
			allext = []
			for f in filter:
				extlist = MMmimetypes.get_extensions(f)
				if not extlist:
					extlist = ('.*',)
				else:
					if not dftext:
						dftext = extlist[0]
					allext = allext + extlist
				description = grins_mimetypes.descriptions.get(f, f)
				# Turn the extension list into the ; separated pattern list
				extlist = string.join(map(lambda x:"*"+x, extlist), ';')
				newfilter.append('%s (%s)|%s'%(description, extlist, extlist))
			if descr:
				extlist = string.join(map(lambda x:"*"+x, allext), ';')
				newfilter.insert(0, '%s|%s'%(descr, extlist))
				if len(newfilter) == 2:
					# special case: don't display two
					# entries that are basically the same
					del newfilter[1]
			elif file and dftext:
				# remove extension
				file = os.path.splitext(file)[0]
			newfilter.append('All files (*.*)|*.*')
			filter = string.join(newfilter, '|') + '||'
##		else:
##			if existing:
##				filter = 'smil files (*.smil;*.smi)|*.smil;*.smi|cmif files (*.cmif)|*.cmif|All files *.*|*.*||'
##			else:
##				filter = 'smil or cmif file (*.smil;*.smi;*.cmif)|*.smil;*.smi;*.cmif|All files *.*|*.*||'
##			dftext = '.smil'
		self._dlg =dlg= winuser.CreateFileDialog(existing,dftext,file,flags,filter,parent.GetSafeHwnd())
		dlg.SetOFNTitle(prompt)

		# get/set current directory since the core assumes remains the same
		# The Windows filebrowser modifies the current directory, and
		# since the rest of GRiNS doesn't expect that we save/restore
		# it,
		#
		curdir = os.getcwd()
		default_dir = directory in ('.', '')
		if default_dir and FileDialog.last_location:
			directory = FileDialog.last_location
		dlg.SetOFNInitialDir(directory)
		result=dlg.DoModal()
		if default_dir:
			FileDialog.last_location = os.getcwd()
		os.chdir(curdir)
		if result==wincon.IDOK:
			if cb_ok: cb_ok(dlg.GetPathName())
		else:
			if cb_cancel: cb_cancel()
	# Returns the filename selected. Must be called after the dialog dismised.
	def GetPathName(self):
		return self._dlg.GetPathName()
