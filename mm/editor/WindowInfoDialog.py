import Win32_window, cmifex2, win32api, win32con

DEFAULT_EDIT_WIDTH = 120

class WindowInfoDialog:
	def __init__(self, title, chlist, **options):
		self.ch_names = ['']
		self.winlist = ['None']
		self.__window = w = Win32_window.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))
		try:
			self.file_callback = options['FileCallback']
		except KeyError:
			self.file_callback = None
		
		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = 300 #constant2
		self._h = 300 #constant
		
		self.buttons = w.ButtonRow(
			[('Ok', (self.ok_callback, ())),
			('Cancel', (self.cancel_callback, ())),
			('Help', (self.helpcall, ()))],
			left = 5, right = self._w-5, top = self._w-constant-30, bottom = 30, vertical = 0)

		text = 'Give a name to the window and also give type for it.'
		label = w.Label(text, justify = 'left',
				left = 5, right = self._w-10, top = 0, bottom = 60)
		
		self.__name_input = w.TextInput('Name: ',
				'', None, None,
				left = 5, right = self._w-10, top = 65, bottom = 25)
		
		self.__window_select = w.OptionMenu('Type: ',
					chlist, 0, None,
					left = 5, right = self._w-10, top = 95, bottom = 125)
		#self.__level_input = w.TextInput('Level: ',
		#		'', None, None,
		#		left = 5, right = self._w-10, top = 130, bottom = 25)
		self.__parent_select = w.OptionMenu('Parent: ',
					['None'], 0, None,
					left = 5, right = self._w-10, top = 130, bottom = 125)
		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.__window._hWnd.HookKeyStroke(self.helpcall,104)
		w.show()
		
	def helpcall(self, params=None):
		import Help
		Help.givehelp(self.__window._hWnd, 'Wizard')

	
	def close(self):
		self.__window.close()
		del self.__window
		del self.ch_names

	def pop(self):
		self.__window.pop()

	def settitle(self, title):
		self.__window.settitle(title)

	def setwindowsnames(self, windowsnames):
		self.__window_select.setoptions(windowsnames, 0)

	def getwindowtype(self):
		return self.__window_select.getvalue()

	#def getwindowlevel(self):
	#	return self.__level_input.gettext()

	def getwindowparent(self):
		return self.__parent_select.getvalue()

	def setwindowtype(self, name):
		self.__window_select.setvalue(name)

	def getwindow(self):
		return self.__name_input.gettext()

	def setwindow(self, name):
		return self.__name_input.settext(name)

	def show(self):
		self.__window.show()
	
	def cancel_callback(self):
		self.__name_input.settext('')
		self.__window.hide()

	def ok_callback(self):
		import string
		name = string.strip(self.getwindow())
		type = self.getwindowtype()
		#level = string.strip(self.getwindowlevel())
		parent = self.getwindowparent()
		#tup = (name,type,level,parent)
		tup = (name,type,parent)
		if not string.strip(self.getwindow()):
			import windowinterface
			windowinterface.showmessage("You must give a name", mtype = 'error')
			return
		#if not string.strip(self.getwindowlevel()):
		#	import windowinterface
		#	windowinterface.showmessage("You must give a level", mtype = 'error')
		#	return
		self.__window.hide()
		if self.file_callback != None:
			self.winlist.append(string.strip(self.getwindow()))
			tmp = []
			for i in self.winlist:
				tmp.append(i)
			self.__parent_select.setoptions(tmp,0)
			f = self.file_callback
			apply(f,(tup,))

	