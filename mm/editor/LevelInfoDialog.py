import Win32_window, cmifex2, win32api, win32con

DEFAULT_EDIT_WIDTH = 120

class LevelInfoDialog:
	def __init__(self, title, typelist, **options):
		self.__window = w = Win32_window.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))
		try:
			self.type_callback = options['TypeCallback']
		except KeyError:
			self.type_callback = None
		
		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = 300 #constant2
		self._h = 300 #constant
		
		self.buttons = w.ButtonRow(
			[('Ok', (self.ok_callback, ())),
			('Cancel', (self.cancel_callback, ())),
			('Help', (self.helpcall, ()))],
			left = 5, right = self._w-5, top = self._w-constant-30, bottom = 30, vertical = 0)

		text = 'Give the type of the level.'
		label = w.Label(text, justify = 'left',
				left = 5, right = self._w-10, top = 0, bottom = 60)
		
		self.__name_input = w.TextInput('Name: ',
				'', None, None,
				left = 5, right = 105, top = 65, bottom = 25)
		
		self.__name_input.seteditable(0) 
		
		self.__type_select = w.OptionMenu('Type: ',
					typelist, 0, None,
					left = 5, right = self._w-10, top = 95, bottom = 125)
		
		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.__window._hWnd.HookKeyStroke(self.helpcall,104)
		w.show()
		
	def helpcall(self, params=None):
		import Help
		Help.givehelp(self.__window._hWnd, 'Wizard')

	
	def close(self):
		self.__window.close()
		del self.__window

	def pop(self):
		self.__window.pop()

	def settitle(self, title):
		self.__window.settitle(title)


	def getleveltype(self):
		return self.__type_select.getvalue()

	def setleveltype(self, name):
		self.__type_select.setvalue(name)

	def getlevel(self):
		return self.__name_input.gettext()

	def setlevel(self, name):
		return self.__name_input.settext(name)

	def show(self):
		self.__window.show()
	
	def cancel_callback(self):
		self.__name_input.settext('')
		self.__window.hide()

	def ok_callback(self):
		type = (self.getlevel(), self.getleveltype()[:3]) 
		self.__window.hide()
		if self.type_callback != None:
			f = self.type_callback
			apply(f,(type,))
