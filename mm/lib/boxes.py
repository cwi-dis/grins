import windowinterface, EVENTS

message = """\
Use left mouse button to draw a box.
Click `Done' when ready or `Cancel' to cancel."""

# symbol used for returning
_finished = '_finished'

class Boxes:
	def __init__(self, window, msg, box):
		if len(box) == 1 and type(box) == type(()):
			box = box[0]
		if len(box) not in (0, 4):
			raise TypeError, 'bad arguments'
		if len(box) == 0:
			self.box = None
		else:
			self.box = box
		self.window = window
		display = window._active_display_list
		window.pop()
		window._close_subwins()
		win = window
		fa1 = []
		fa2 = []
		while win:
			try:
				fa = windowinterface.getregister(win,
							EVENTS.Mouse0Press)
			except windowinterface.error:
				fa = None
			else:
				win.unregister(EVENTS.Mouse0Press)
			fa1.append(fa)
			try:
				fa = windowinterface.getregister(win,
							EVENTS.Mouse0Release)
			except windowinterface.error:
				fa = None
			else:
				win.unregister(EVENTS.Mouse0Release)
			fa2.append(fa)
			win = win._parent_window
		self.fa1 = fa1
		self.fa2 = fa2
		if not self.box:
			window.register(EVENTS.Mouse0Press, self.first_press,
					None)
		else:
			window.register(EVENTS.Mouse0Press, self.press, None)
		if display and not dispay.is_closed():
			d = display.clone()
		else:
			d = window.newdisplaylist()
		for win in window._subwindows:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self.display = d.clone()
		d.fgcolor(255, 0, 0)
		if box:
			d.drawbox(box)
		d.render()
		if msg:
			msg = msg + '\n\n' + message
		else:
			msg = message
		self.dialog = windowinterface.Dialog(msg, 0,
				[('', 'Done', (self.done_callback, ())),
				 ('', 'Cancel', (self.cancel_callback, ()))])

	def __del__(self):
		self.close()

	def close(self):
		self.dialog.close()

	def first_press(self, dummy, win, ev, val):
		self.box = win.sizebox((val[0], val[1], 0, 0), 0, 0)
		win.register(EVENTS.Mouse0Press, self.press, None)
		self.after_press()

	def press(self, dummy, win, ev, val):
		x, y = val[0:2]
		b = self.box
		if b[0] + b[2]/4 < x < b[0] + b[2]*3/4:
			constrainx = 1
		else:
			constrainx = 0
		if b[1] + b[3]/4 < y < b[1] + b[3]*3/4:
			constrainy = 1
		else:
			constrainy = 0
		self.display.render()
		if constrainx and constrainy:
			self.box = win.movebox(b, 0, 0)
		else:
			if x < b[0] + b[2]/2:
				x0 = b[0] + b[2]
				w = -b[2]
			else:
				x0 = b[0]
				w = b[2]
			if y < b[1] + b[3]/2:
				y0 = b[1] + b[3]
				h = -b[3]
			else:
				y0 = b[1]
				h = b[3]
			self.box = win.sizebox((x0, y0, w, h),
					       constrainx, constrainy)
		self.after_press()

	def after_press(self):
		d = self.display.clone()
		d.fgcolor(255, 0, 0)
		d.drawbox(self.box)
		d.render()

	def loop(self):
		windowinterface.startmonitormode()
		self.window.setcursor('')
		try:
			try:
				while 1:
					dummy = windowinterface.readevent()
			except _finished, val:
				if self.box and val:
					return self.box
				else:
					return None
		finally:
			windowinterface.endmonitormode()

	def done_callback(self):
		self.dialog.close()
		raise _finished, 1

	def cancel_callback(self):
		self.dialog.close()
		raise _finished, 0

def create_box(window, msg, *box):
	return Boxes(window, msg, box).loop()
