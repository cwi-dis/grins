__version__ = "$Id$"

import winuser
import wincon

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
		if cb_cancel: cb_cancel()
	# Returns the filename selected. Must be called after the dialog dismised.
	def GetPathName(self):
		return None
