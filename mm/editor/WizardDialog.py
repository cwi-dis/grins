import Win32_window, cmifex2, win32api, win32con, imageex
import cmifex

DEFAULT_EDIT_WIDTH = 120

class WizardDialog:
	def __init__(self, title, file):
		self.directory = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifDoc")
		self.filename = self.directory + "\\" + file
		self.name = ''
		self.save = 0
		self.dialogs_list = []
		self.ext_windows = ['movie','image','mpeg','sound','midi','label','html']
		self.imm_windows = ['cmif']
		self.cur_dialog = 0
		self.ch_names = [('None','None')]
		self.__anchors = []
		self.level_num = 0
		self.levels = [('None', 'seq')]
		self.__window = w = Win32_window.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))

		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = 400 #constant2
		self._h = 400 #constant

		self.buttons = w.ButtonRow(
			[('<<Back', (self.back_callback, ())),
			('Next>>', (self.next_callback, ())),
			('Finish', (self.finish_callback, ())),
			('Cancel', (self.cancel_callback, ())),
			('Help', (self.helpcall, ()))],
			left = 5, right = self._w-5, top = self._w-constant-30, bottom = 30, vertical = 0)

		midd = w.SubWindow(left = 5, right = self._w-5, top = 5, bottom = self._w-constant-30-5)
		alter = midd.AlternateSubWindow(left = 0, right = self._w-10, top = 0, bottom = self._w-constant-40)
		welcome_group = alter.SubWindow(left = 0, right = self._w-10, top = 0, bottom = self._w-constant-40)
		start_group = alter.SubWindow(left = 0, right = self._w-10, top = 0, bottom = self._w-constant-40)
		current_group = alter.SubWindow(left = 0, right = self._w-10, top = 0, bottom = self._w-constant-40)
		finish_group = alter.SubWindow(left = 0, right = self._w-10, top = 0, bottom = self._w-constant-40)

		welcome_group_im = welcome_group.SubWindow(left = 0, right = 130, top = 0, bottom = 260)
		img1 = imageex.PrepareImage(welcome_group_im._hWnd, "c:\\chameleon\\images\\welcome.bmp", 0)[0]
		welcome_group_im._hWnd.HookMessage(self.show_image, win32con.WM_PAINT)

		start_group_im = start_group.SubWindow(left = 0, right = 130, top = 0, bottom = 260)
		img2 = imageex.PrepareImage(start_group_im._hWnd, "c:\\chameleon\\images\\welcome.bmp", 0)[0]
		start_group_im._hWnd.HookMessage(self.show_image, win32con.WM_PAINT)

		current_group_im = current_group.SubWindow(left = 0, right = 130, top = 0, bottom = 260)
		img3 = imageex.PrepareImage(current_group_im._hWnd, "c:\\chameleon\\images\\welcome.bmp", 0)[0]
		current_group_im._hWnd.HookMessage(self.show_image, win32con.WM_PAINT)

		finish_group_im = finish_group.SubWindow(left = 0, right = 130, top = 0, bottom = 260)
		img4 = imageex.PrepareImage(finish_group_im._hWnd, "c:\\chameleon\\images\\finish.bmp", 0)[0]
		finish_group_im._hWnd.HookMessage(self.show_image, win32con.WM_PAINT)

		self.dialogs_list.append(((0,1,0,1,1),welcome_group,(welcome_group_im,img1)))
		self.dialogs_list.append(((0,1,0,1,1),start_group,(start_group_im,img2)))
		self.dialogs_list.append(((1,1,1,1,1),current_group,(current_group_im,img3)))
		self.dialogs_list.append(((1,0,1,1,1),finish_group,(finish_group_im,img4)))

		start_group.hide()
		current_group.hide()
		finish_group.hide()

		text = 'This tool will help you to create a simple document.\nFor more complicate documents you must use the standard tools.'
		label = welcome_group.Label(text, justify = 'left',
				left = 130, right = self._w-10-130, top = 0, bottom = self._w-constant-40)

		self.__file_input = start_group.TextInput('Destination:',
				self.filename,
				(self.file_callback, ()), None,
				left = 5, right = self._w-10-5, top = self._w-constant-100, bottom = 25)
		label = start_group.Label(text, justify = 'left',
				left = 130, right = self._w-10-130, top = 0, bottom = self._w-constant-135)
		butt = start_group.ButtonRow(
			[('Browse...', (self.browser_callback, ()))],
			left = self._w-10-100, right = 100, top = self._w-constant-65, bottom = 30,
			vertical = 0)

		self.__window_select = current_group.OptionMenu('Windows: ',
					['None'], 0,
					(self.channel_callback, ()),
					left = 130, right = self._w-10-130, top = 0, bottom = 125)
		butt = current_group.ButtonRow(
			[('New...', (self.new_callback, ()))],
			left = self._w-10-80, right = 80, top = 30, bottom = 30,
			vertical = 0)
		self.__file_input2 = current_group.TextInput('Filename:',
				'',
				(self.file_callback2, ()), None,
				left = 130, right = self._w-10-130, top = 65, bottom = 25)
		self.cur_br_but = current_group.ButtonRow(
			[('Browse...', (self.browser_callback2, ()))],
			left = self._w-10-100, right = 100, top = 100, bottom = 30,
			vertical = 0)

		self.cur_type_but = current_group.ButtonRow(
			[('imm', (self.type_callback, ('imm',)), 'r'),
			('ext', (self.type_callback, ('ext',)), 'r')],
			left = 130, right = 100, top = 135, bottom = 65,
			vertical = 1)

		self.__level_select = current_group.OptionMenu('Level: ',
				['0'], 0, None,
				left = 130, right = self._w-10-130, top = 205, bottom = 125)
		butt = current_group.ButtonRow(
			[('New...', (self.new_callback2, ()))],
			left = self._w-10-80, right = 80, top = 235, bottom = 30,
			vertical = 0)
		self.__name_input = current_group.TextInput('Name:', '',
				(self.name_callback, ()), None,
				left = 130, right = self._w-10-130, top = 270, bottom = 25)

		text = 'This tool will help you to create a simple document.\nFor more complicate documents you must use the standard tools.'
		label = finish_group.Label(text, justify = 'left',
				left = 130, right = self._w-10-130, top = 0, bottom = 100)
		self.fin_save_but = finish_group.ButtonRow(
			[("Create '.cmif' file", (self.save_callback, (1,)), 'r'),
			("Don't create '.cmif' file", (self.save_callback, (0,)), 'r')],
			left = 130, right = self._w-130, top = 105, bottom = 65,
			vertical = 1)
		self.fin_save_but.setbutton(1,1)
		butt = finish_group.ButtonRow(
			[('Define Anchors...', (self.def_anch_callback, ()))],
			left = 130, right = self._w-130, top = 175, bottom = 30,
			vertical = 0)

		w._not_shown.append(start_group)
		w._not_shown.append(current_group)
		w._not_shown.append(finish_group)

		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.__window._hWnd.HookKeyStroke(self.helpcall,104)
		w.show()


	def helpcall(self, params=None):
		import Help
		Help.givehelp(self.__window._hWnd, 'Wizard')


	def close(self):
		for item in self.dialogs_list:
			sub, im = item[2]
			imageex.Destroy(im)
		self.__window.close()
		del self.__window
		del self.dialogs_list
		del self.buttons
		del self.ch_names
		del self.levels

	def pop(self):
		self.__window.pop()

	def settitle(self, title):
		self.__window.settitle(title)

	def setwindowsnames(self, windowsnames):
		tmp = []
		for item in windowsnames:
			tmp.append(item[0])
		self.__window_select.setoptions(tmp, 0)

	def getwindow(self):
		text = self.__window_select.getvalue()
		it = None
		for item in self.ch_names:
			if item[0] == text:
				it = item
				break
		return it

	def getwindowlevel(self):
		text = self.__level_select.getvalue()
		lev = None
		for i in self.levels:
			if text == i[0]:
				lev = i
				break
		if lev==None:
			lev = ('None', '')
		return lev

	def setwindowlevel(self, type=None):
		if type != None:
			if self.level_num == 0:
				del self.levels[0]
			if eval(type[0]) > self.level_num:
				self.level_num = self.level_num + 1
				self.levels.append((`self.level_num`, type[1]))
				tmp = []
				for i in self.levels:
					tmp.append(i[0])
				self.__level_select.setoptions(tmp,`self.level_num`)
				self.__level_select.setvalue(`self.level_num`)
			else:
				if type[0] != 'None':
					self.__level_select.setvalue(type[0])
		else:
			self.__level_select.setpos(`self.level_num`)


	def setanchors(self, ls):
		for i in ls:
			self.__anchors.append(i)

	def getanchors(self):
		return self.__anchors


	def setwindow(self, name):
		if name != '':
			ls = []
			for it in self.ch_names:
				ls.append(it[0])
			if name[0] not in ls:
				if self.ch_names[0][0] == 'None':
					del self.ch_names[0]
				self.ch_names.append(name)
				self.setwindowsnames(self.ch_names)
			if name[1] in self.ext_windows:
				self.cur_type_but.setsensitive(0,0)
				self.cur_type_but.setsensitive(1,0)
				#self.cur_type_but.setbutton(0,0)
				#self.cur_type_but.setbutton(1,1)
				self.settype('ext')
			elif name[1] in self.imm_windows:
				self.cur_type_but.setsensitive(0,0)
				self.cur_type_but.setsensitive(1,0)
				#self.cur_type_but.setbutton(0,1)
				#self.cur_type_but.setbutton(1,0)
				self.settype('imm')
			else:
				self.cur_type_but.setsensitive(0,1)
				self.cur_type_but.setsensitive(1,1)
				self.settype('ext')
			self.__window_select.setvalue(name[0])


	def gettype(self):
		return self.type

	def settype(self, type):
		self.type = type
		if type == 'imm':
			self.__file_input2.seteditable(0)
			self.cur_br_but.setsensitive(0,0)
			self.cur_type_but.setbutton(0,1)
			self.cur_type_but.setbutton(1,0)
			self.setfilename2('')
		else:
			self.__file_input2.seteditable(1)
			self.cur_br_but.setsensitive(0,1)
			self.cur_type_but.setbutton(1,1)
			self.cur_type_but.setbutton(0,0)

	def getsave(self):
		return self.save

	def setsave(self, yesno):
		self.save = yesno


	def show_image(self, params):
		tup, dialog, tup2 = self.dialogs_list[self.cur_dialog]
		sub, im = tup2
		cmifex.BeginPaint(sub._hWnd, 0)
		r, g, b = cmifex.GetSysColor(win32con.COLOR_BTNFACE)
		imageex.PutImage(sub._hWnd,im,r,g,b,0)
		cmifex.EndPaint(sub._hWnd, 0)

	def show_group(self):
		if self.dialogs_list:
			tup, dialog, tup2 = self.dialogs_list[self.cur_dialog]
			dialog.show()
			for i in range(5):
				if tup[i]==0:
					self.buttons.hide(i)
				else:
					self.buttons.show(i)
			sub, im = tup2
			import cmifex
			r, g, b = cmifex.GetSysColor(win32con.COLOR_BTNFACE)
			imageex.PutImage(sub._hWnd,im,r,g,b,0)


	def setfilename(self, filename):
		self.__file_input.settext(filename)

	def setfilename2(self, filename):
		self.__file_input2.settext(filename)

	def getfilename(self):
		return self.__file_input.gettext()

	def getfilename2(self):
		return self.__file_input2.gettext()

	def getname(self):
		return self.__name_input.gettext()

	def setname(self, name):
		self.__name_input.settext(name)

	def cancel_callback(self):
		pass

	def back_callback(self):
		pass

	def next_callback(self):
		pass

	def channel_callback(self):
		name = self.getwindow()
		if name[1] in self.ext_windows:
				self.cur_type_but.setsensitive(0,0)
				self.cur_type_but.setsensitive(1,0)
				#self.cur_type_but.setbutton(0,0)
				#self.cur_type_but.setbutton(1,1)
				self.settype('ext')
		elif name[1] in self.imm_windows:
				self.cur_type_but.setsensitive(0,0)
				self.cur_type_but.setsensitive(1,0)
				#self.cur_type_but.setbutton(0,1)
				#self.cur_type_but.setbutton(1,0)
				self.settype('imm')
		else:
				self.cur_type_but.setsensitive(0,1)
				self.cur_type_but.setsensitive(1,1)

	def new_callback(self):
		pass

	def new_callback2(self):
		pass

	def def_anch_callback(self):
		pass

	def ok_callback(self):
		pass

	def finish_callback(self):
		pass

	def type_callback(self, type):
		pass

	def save_callback(self, yesno):
		pass

	def attributes_callback(self):
		pass

	def file_callback(self):
		pass

	def file_callback2(self):
		pass

	def name_callback(self):
		pass

	def browser_callback(self):
		pass

	def browser_callback2(self):
		pass
