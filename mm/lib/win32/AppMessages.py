__version__ = "$Id$"


# Objects:
# class showmessage:
# class _Question:
# def showquestion(text):
# class _MultChoice:
# def multchoice(prompt, list, defindex):


import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2

_end_loop = '_end_loop'	# exception for ending a loop

class showmessage:
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'information',
		     title = 'message'):
		#if grab:
		#		dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
		#		w = grab
		#		if type(w) is IntType:
		#			w = toplevel
		#		while 1:
		#			if hasattr(w, '_shell'):
		#				w = w._shell
		#				break
		#			if hasattr(w, '_main'):
		#				w = w._main
		#				break
		#			w = w._parent
		#else:
		#	dialogStyle = Xmd.DIALOG_MODELESS
		#	w = toplevel._main
		#if mtype == 'error':
		#	func = w.CreateErrorDialog
		#elif mtype == 'warning':
		#	func = w.CreateWarningDialog
		#elif mtype == 'information':
		#	func = w.CreateInformationDialog
		#elif mtype == 'question':
		#	func = w.CreateQuestionDialog
		#else:
		#	func = w.CreateMessageDialog
		self._grab = grab
		#w = func(name, {'messageString': text,
		#		'title': title,
		#		'dialogStyle': dialogStyle,
		#		'resizePolicy': Xmd.RESIZE_NONE,
		#		'visual': toplevel._default_visual,
		#		'depth': toplevel._default_visual.depth,
		#		'colormap': toplevel._default_colormap})
		#w.MessageBoxGetChild(Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		#if mtype == 'question' or cancelCallback:
		#	w.AddCallback('cancelCallback',
		#			  self._callback, cancelCallback)
		#else:
		#	w.MessageBoxGetChild(Xmd.DIALOG_CANCEL_BUTTON).UnmanageChild()
		#w.AddCallback('okCallback', self._callback, callback)
		#w.AddCallback('destroyCallback', self._destroy, None)
		#w.ManageChild()
		#self._widget = w
		
		res = 0
		style = " "
		
		if mtype == 'error':
			style = style+"e"
		
		if mtype == 'warning':
			style = style+"w"
		
		if mtype == 'information':
			style = style+"i"
		
		if mtype == 'message':
			style = style+"m"
		
		if mtype == 'question':
			style = style+"q"
		
		if mtype != 'question' and cancelCallback:
			style = style+"c"

		if grab:
			res = cmifex2.MesBox(text,title,style)
		else:
			#ls = string.splitfields(text ,'\n')
			#max = 0;
			#for line in ls:
			#	length = len(line)
			#	if length>max:
			#		max = length
			#height = (len(ls)+1)*15
			#width = max*13
			
			#dwidth = width + 2*win32api.GetSystemMetrics(win32con.SM_CXBORDER)
			#dheight = height + 3*win32api.GetSystemMetrics(win32con.SM_CYBORDER) + win32api.GetSystemMetrics(win32con.SM_CYCAPTION) + 70
			#dx = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN)-dwidth)/2
			#dy = (win32api.GetSystemMetrics(win32con.SM_CYSCREEN)-dheight)/2

			#print title
			#print dx, dy
			#w = cmifex2.CreateDialogbox(title,0,dx,dy,dwidth,dheight,1)
			#mes = cmifex2.CreateStatic("",w,0,0,width,height,'center')
			#cmifex2.SetFont(mes,"Arial",10)
			#cmifex2.SetCaption(mes,text)
			
			if mtype == 'question' or cancelCallback:
				st = win32con.MB_OKCANCEL
			else:
				st = win32con.MB_OK

			if mtype == 'error':
				st = st|win32con.MB_ICONERROR
		
			if mtype == 'warning':
				st = st|win32con.MB_ICONWARNING
			
			if mtype == 'information':
				st = st|win32con.MB_ICONINFORMATION
			
			if mtype == 'message':
				st = st|win32con.MB_ICONINFORMATION
			
			if mtype == 'question':
				st = MB_YESNO|win32con.MB_ICONQUESTION
			
			res = win32ui.MessageBox(text,title,st)
			

		if res==win32con.IDOK or res==win32con.IDYES:
			if callback:
				apply(callback[0], callback[1])
		elif res==win32con.IDCANCEL or res==win32con.IDNO:
			if cancelCallback:
				apply(cancelCallback[0], cancelCallback[1])

			

	def close(self):
		if self._widget:
			w = self._widget
			self._widget = None
			w.UnmanageChild()
			w.DestroyWidget()

	def _callback(self, widget, callback, call_data):
		if not self._widget:
			return
		if callback:
			apply(callback[0], callback[1])
		if self._grab:
			self.close()

	def _destroy(self, widget, client_data, call_data):
		self._widget = None


class _Question:
	def __init__(self, text):
		self.looping = FALSE
		self.answer = None
		showmessage(text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)))

	def run(self):
		try:
			self.looping = TRUE
			Xt.MainLoop()
		except _end_loop:
			pass
		return self.answer

	def callback(self, answer):
		self.answer = answer
		if self.looping:
			raise _end_loop

#def showquestion(text):
#	return _Question(text).run()

def showquestion(text):
	return _Question(text).answer


##################################################################
class _MultChoice:
	def __init__(self, prompt, msg_list, defindex):
		self.looping = FALSE
		self.answer = 0
		self.selection_made = 0
		self.msg_list = msg_list
		list = []
		_cb = None
		for msg in msg_list:
			if msg != 'Cancel':
				list.append(msg, (self.callback, (msg,)), 'r')
			else:
				_cb = (self.callback, ('Cancel',))	
		self.dialog = Dialog(list, title = None, prompt = prompt,
				     grab = TRUE, vertical = TRUE, canclose = FALSE)
		showmessage("Select an item and press 'OK'.\nThe first item is the default", 
					mtype = 'information', cancelCallback = _cb, grab=0)
		#if not self.selection_made:
		self.dialog.close()

	def run(self):
		try:
			self.looping = TRUE
#			Xt.MainLoop()
		except _end_loop:
			pass
#		return self.answer
		return 2

	def callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				if msg != 'Cancel':
					self.selection_made = 1
				#if self.looping:
				#	raise _end_loop
				return

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).answer


