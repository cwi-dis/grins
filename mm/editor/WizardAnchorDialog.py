import Win32_window, cmifex2, win32api, win32con

DEFAULT_EDIT_WIDTH = 120

class WizardAnchorDialog:
	def __init__(self, title, nodelist, **options):
		self.__window = w = Win32_window.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))
		self.anc_ls = []
		self.from_flag = 0
		self.to_flag = 0
		self.prev_anc_ls = []
		try:
			self.def_callback = options['DefCallback']
		except KeyError:
			self.def_callback = None
		
		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = 400 #constant2
		self._h = 300 #constant
		
		text = 'Define the anchors you want and then press Ok'
		label = w.Label(text, justify = 'left',
				left = 5, right = self._w-10, top = 0, bottom = 60)
		
		self.__from_select = w.OptionMenu('From: ',
				nodelist, 0, (self.from_selected_callback, ()),
				left = 5, right = self._w-10, top = 65, bottom = 125)
		
		self.__to_select = w.OptionMenu('To: ',
					nodelist, 0, (self.to_selected_callback, ()),
					left = 5, right = self._w-10, top = 95, bottom = 125)
		self.__anchors_select = w.OptionMenu('Anchors: ',
					['None'], 0, (self.anchor_selected_callback, ()),
					left = 5, right = self._w-10, top = 125, bottom = 125)
		
		self.buttons = w.ButtonRow(
			[('Add Anchor', (self.add_callback, ())),
			('Delete Anchor', (self.delete_callback, ())),
			('Ok', (self.ok_callback, ())),
			('Cancel', (self.cancel_callback, ())),
			('Help', (self.helpcall, ()))],
			left = 5, right = self._w-5, top = 155, bottom = 30, vertical = 0)
		self.buttons.setsensitive(0,0)
		self.buttons.setsensitive(1,0)
		cmifex2.ResizeWindow(w._hWnd, self._w, 220)
		self.__window._hWnd.HookKeyStroke(self.helpcall,104)
		w.show()
		
	def helpcall(self, params=None):
		import Help
		Help.givehelp(self.__window._hWnd, 'Wizard')

	
	def close(self):
		self.__window.close()
		del self.__window
		del self.anc_ls
		del self.prev_anc_ls

	def pop(self):
		self.__window.pop()

	def settitle(self, title):
		self.__window.settitle(title)


	def getfromvalue(self):
		return self.__from_select.getvalue()

	def setfromvalue(self, name):
		self.__from_select.setvalue(name)


	def gettovalue(self):
		return self.__to_select.getvalue()

	def settovalue(self, name):
		self.__to_select.setvalue(name)

	def getanchor(self):
		return self.__anchors_select.getvalue()

	def setanchor(self, name):
		self.__anchors_select.setvalue(name)

	def show(self):
		for i in self.anc_ls: 
			self.prev_anc_ls.append(i)
		print self.prev_anc_ls 
		self.__window.show()
	
	def from_selected_callback(self):
		self.from_flag = 1
		if self.to_flag:
			self.buttons.setsensitive(0,1) 

	def to_selected_callback(self):
		self.to_flag = 1
		if self.from_flag:
			self.buttons.setsensitive(0,1) 

	def anchor_selected_callback(self):
		self.buttons.setsensitive(1,1) 
	
	def add_callback(self):
		if self.getfromvalue() == self.gettovalue():
			import windowinterface
			windowinterface.showmessage("Destination and target nodes are the same.", mtype = 'error')
			return
		self.to_flag = 0
		self.from_flag = 0
		self.buttons.setsensitive(0,0)
		tup = (self.getfromvalue(), self.gettovalue())
		if tup not in self.anc_ls:
			if self.anc_ls == ['None']:
				self.anc_ls = []
			self.anc_ls.append(tup)
		else:
			import windowinterface
			windowinterface.showmessage("Anchor allready defined", mtype = 'error')
			return
		tmp = []
		for i in self.anc_ls:
			tmp.append(i[0]+'->'+i[1]) 
		self.__anchors_select.setoptions(tmp,0)
	
	def delete_callback(self):
		import string
		a = self.getanchor()
		ls = string.splitfields(a, '->')
		anc = (ls[0], ls[1])
		if anc in self.anc_ls:
			self.anc_ls.remove(anc)
			self.buttons.setsensitive(1,0)
			tmp = []
			for i in self.anc_ls:
				tmp.append(i[0]+'->'+i[1])
			if tmp == []:
				tmp = ['None']
			self.__anchors_select.setoptions(tmp,0)
	
	def cancel_callback(self):
		self.anc_ls = []
		for i in self.prev_anc_ls:
			self.anc_ls.append(i)
		tmp = []
		for i in self.prev_anc_ls:
			tmp.append(i[0]+'->'+i[1])
		if tmp == []:
			tmp = ['None']
		self.__anchors_select.setoptions(tmp,0)
		self.prev_anc_ls = []
		self.__window.hide()

	def ok_callback(self):
		self.prev_anc_ls = []
		self.__window.hide()
		if self.def_callback != None:
			f = self.def_callback
			apply(f,(self.anc_ls,))
