#	showdialog(message, buttons...) -> button_text
#		Show a dialog window with the specified message (may
#		contain newlines) and buttons with the specified
#		texts.  The window stays up until one of the buttons
#		is clicked.  The value of the button is then returned.
#		One button may start with '!'.  This button is the
#		default answer and is returned when the user types a
#		RETURN.
#
#	showmessage(message)
#		Show a dialog box with the given message and a Done
#		button.  The function does not return a value.
#
#	showquestion(question)
#		Show a dialog box with the given question and Yes and
#		No buttons.  The value returned is 1 if the Yes
#		buttons was pressed and 0 if the No button was
#		pressed.
#
#	multchoice(message, buttonlist, defindex)
#		Show a dialog box with the given message and list of
#		buttons.  Defindex is the index in the list of the
#		default button.  The value returned is the index of
#		the button which was pressed.
#
# The presentation can be changed by setting any of the variables in
# the configuration section.  See the comments near the variables.

# some configuration variables
BGCOLOR = 255, 255, 0			# background color of window: yellow
FGCOLOR = 0, 0, 0			# foreground color of window: black
HICOLOR = 255, 0, 0			# highlight color of window: red
INTERBUTTONGAP = '   '			# space between buttons
BUTTONFILLER = ' '			# extra space added before and
					# after button text
FONT = 'Times-Roman'			# font used for texts
POINTSIZE = 14				# point size used for texts
WINDOWTITLE = None			# title of pop-up window
DEFLINEWIDTH = 3			# linewidth round default button
WINDOWMARGIN = 1			# margin around text and buttons
CENTERLINES = 0				# whether to center all lines
DONEMSG = ' Done '			# text in button of showmessage
YESMSG = ' Yes '			# text of "Yes" answer of showquestion
NOMSG = ' No '				# text of "No" answer of showquestion
# changing any of the following changes the interface to the user/programmer
DEFBUTTON = '!'				# indicates this is default button
DEFANSWER = '\r', '\n'			# keys that trigger default answer

import windowinterface, EVENTS, string

class Dialog:
	def init(self, text):
		if len(text) <= 1:
			raise TypeError, 'arg count mismatch'
		# self.events is used to remember events that we are
		# not interested in but that may be important for
		# whoever calls us.
		self.events = []
		self.message = text[0]
		self.buttons = text[1:]
		font = windowinterface.findfont(FONT, POINTSIZE)
		if type(self.message) == type(''):
			width, height = font.strsize(self.message)
			height = height + font.fontheight()
		elif self.message == None:
			width, height = 0, 0
		else:
			raise TypeError, 'message must be text or `None\''
		mw = 0
		mh = 0
		self.defstr = None
		for bt in self.buttons:	# loops at least once
			if bt[0:len(DEFBUTTON)] == DEFBUTTON:
				if self.defstr:
					raise error, 'no two defaults allowed'
				self.defstr = bt
				bt = bt[len(DEFBUTTON):]
			butstrs = string.splitfields(bt, '\n')
			for bt in butstrs:	# loops at least once
				txt = BUTTONFILLER + bt + BUTTONFILLER
				bw, bh = font.strsize(txt)
				if bw > mw:
					mw = bw
					self.widest_button = txt
			if len(butstrs) > mh:
				mh = len(butstrs)
		self.buttonlines = mh
		buttonwidth = len(self.buttons) * mw
		buttonheight = self.buttonlines * bh
		sw, sh = font.strsize(INTERBUTTONGAP)
		buttonwidth = buttonwidth + (len(self.buttons) - 1) * sw
		if buttonwidth > width:
			width = buttonwidth
		height = height + buttonheight
		winwidth = width + WINDOWMARGIN * 2
		winheight = height + WINDOWMARGIN * 2
		scrwidth, scrheight = windowinterface.getsize()
		buttonwidth = float(buttonwidth) / width
		buttonheight = float(buttonheight) / height
		mw = float(mw) / width
		sw = float(sw) / width
		self.window = windowinterface.newwindow( \
			  float(scrwidth - winwidth) / 2, \
			  float(scrheight - winheight) / 2, \
			  winwidth, winheight, WINDOWTITLE)
		self.window.bgcolor(BGCOLOR)
		# remember these settings since we may need them later
		self.INTERBUTTONGAP = INTERBUTTONGAP
		self.CENTERLINES = CENTERLINES
		self.DEFBUTTON = DEFBUTTON
		self.DEFLINEWIDTH = DEFLINEWIDTH
		self.DEFANSWER = DEFANSWER
		self.HICOLOR = HICOLOR
		self.FGCOLOR = FGCOLOR
		self.FONT = FONT
		self.draw_window()
		return self

	def draw_window(self):
		d = self.window.newdisplaylist()
		d.fgcolor(self.FGCOLOR)
		bm = (self.widest_button + self.INTERBUTTONGAP) * (len(self.buttons) - 1) + self.widest_button
		if type(self.message) == type(''):
			m = self.message + '\n' + '\n' * self.buttonlines + bm
		else:
			m = '\n' * (self.buttonlines - 1) + bm
		bl, fh, ps = d.fitfont(self.FONT, m, 0.10)
		if type(self.message) == type(''):
			w, h = d.strsize(self.message)
			yorig = 0.05 + bl
			if self.CENTERLINES:
				for str in string.splitfields(self.message, '\n'):
					dx, dy = d.strsize(str)
					d.setpos((1.0 - dx) / 2, yorig)
					x, y, dx, dy = d.writestr(str)
					yorig = yorig + dy
			else:
				d.setpos((1.0 - w) / 2, yorig)
				x, y, dx, dy = d.writestr(self.message)
		mw, h = d.strsize(self.widest_button)
		mh = h * self.buttonlines	# height of the buttons
		sw, h = d.strsize(self.INTERBUTTONGAP)
		w, h = d.strsize(bm)
		xbase = (1.0 - w) / 2
		if type(self.message) == type(''):
			ybase = 1.0 - 0.05 - mh
		else:
			ybase = (1.0 - mh) / 2
		self.buttonboxes = []
		for i in range(len(self.buttons)):
			butstr = self.buttons[i]
			if butstr[0:len(self.DEFBUTTON)] == self.DEFBUTTON:
				butstr = butstr[len(self.DEFBUTTON):]
				d.linewidth(self.DEFLINEWIDTH)
			else:
				d.linewidth(1)
			w, h = d.strsize(butstr)
			ypos = ybase + float(mh - h) / 2 + bl
			if self.CENTERLINES:
				for bt in string.splitfields(butstr, '\n'):
					w, h = d.strsize(bt)
					d.setpos(xbase + (mw - w) / 2, ypos)
					box = d.writestr(bt)
					ypos = ypos + fh
			else:
				d.setpos(xbase + (mw - w) / 2, ypos)
				box = d.writestr(butstr)
			buttonbox = d.newbutton(xbase, ybase, mw, mh)
			buttonbox.hicolor(self.HICOLOR)
			self.buttonboxes.append(buttonbox)
			xbase = xbase + mw + sw
		d.render()
		self.highlighted = []

	def checkevent(self, window, event, value):
		if event == EVENTS.Mouse0Press:
			for but in value[2]:
				try:
					i = self.buttonboxes.index(but)
					but.highlight()
					self.highlighted.append(but)
					return self.buttons[i]
				except:
					pass
			windowinterface.beep()
		elif event == EVENTS.Mouse0Release:
			for but in self.highlighted:
				if not but.is_closed():
					but.unhighlight()
			self.highlighted = []
		elif event == EVENTS.KeyboardInput:
			if self.defstr and value in self.DEFANSWER:
				return self.defstr
			windowinterface.beep()
		elif event in (EVENTS.Mouse1Press, EVENTS.Mouse2Press):
			windowinterface.beep()
		elif event in (EVENTS.Mouse1Release, EVENTS.Mouse2Release):
			# ignore these
			pass
		elif (window, event) == (self.window, EVENTS.ResizeWindow):
			self.draw_window()
		else:
			self.events.append(window, event, value)
		return None

	def eventloop(self):
		windowinterface.startmonitormode()
		self.events = []
		while 1:
			window, event, value = windowinterface.readevent()
			retval = self.checkevent(window, event, value)
			if retval:
				for (window, event, value) in self.events:
					windowinterface.enterevent(window, \
						  event, value)
				self.events = []
				windowinterface.endmonitormode()
				return retval

	def close(self):
		self.window.close()

def showdialog(*text):
	d = Dialog().init(text)
	r = d.eventloop()
	d.close()
	return r

def showmessage(text):
	dummy = showdialog(text, DEFBUTTON + DONEMSG)

def showquestion(text):
	answer = showdialog(text, YESMSG, NOMSG)
	if answer == YESMSG:
		return 1
	else:
		return 0

def multchoice(prompt, list, defindex):
	args = (prompt,)
	for ai in range(len(list)):
		answer = list[ai]
		if type(answer) == type(()):
			answer = answer[0]
		if ai == defindex:
			answer = DEFBUTTON + answer
		args = args + (answer,)
	rv = apply(showdialog, args)
	if type(rv) == type(''):
		for i in range(len(args)):
			if rv == args[i]:
				return i - 1	# offset due to prompt
	return None
		
