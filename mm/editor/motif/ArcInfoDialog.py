"""Dialog for the ArcInfo editor.

The ArcInfoDialog consists of two option menus (lists of strings of
which exactly one item is selected): the source list and the
destination list.  The contents of these lists are dynamically
determined, but don't change during the life time of a dialog window.
There are no callbacks associated with these lists, but it must be
possible to get and set the current selection.

Furthermore, there should be an interface in which a floating point
number in the range 0 .. 100 can be specified.  (Only two digits of
precision are required, so whole numbers if >= 10, one decimal if less
than 10 but >= 1, two decimals if less than 1.)  For this interface
there is also no callback.  [ In X this is implemented as a slider,
but that is not required. ]

Lastly, there are four buttons `Cancel', `Restore', `Apply', and `OK'.
For these buttons there are callbacks.

"""

__version__ = "$Id$"

import windowinterface, cmifex2, win32api, win32con

class ArcInfoDialog:
	__rangelist = ['0-1 sec', '0-10 sec', '0-100 sec']

	def __init__(self, title, srclist, srcinit, dstlist, dstinit, delay):
		"""Create the ArcInfo dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pops it up (i.e. displays it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		srclist -- list of strings
		srcinit -- 0 <= srcinit < len(srclist) -- the initial
			selction of srclist.
		dstlist -- list of strings
		dstinit -- 0 <= dstinit < len(dstlist) -- the initial
			selection of dstlist
		delay -- 0.0 <= delay <= 100.0 -- the initial value of
			the floating point value
		"""

		self.__window = w = windowinterface.Window(title, resizable = 1,
					deleteCallback = (self.cancel_callback, ()))
		#self.__src_choice = self.__window.OptionMenu('From:',
		#			srclist, srcinit,
		#			None, top = None, left = None)
		#self.__dst_choice = self.__window.OptionMenu('To:',
		#			dstlist, dstinit,
		#			None, top = None,
		#			left = self.__src_choice, right = None)
		#if delay > 10.0:
		#	rangeinit = 2
		#elif delay > 1.0:
		#	rangeinit = 1
		#else:
		#	rangeinit = 0
		#range = float(10 ** rangeinit)
		#self.__delay_slider = self.__window.Slider(None, 0, delay, range,
		#			None,
		#			top = self.__src_choice, left = None)
		#self.__range_choice = self.__window.OptionMenu(None,
		#			self.__rangelist,
		#			rangeinit, (self.__range_callback, ()),
		#			top = self.__dst_choice,
		#			left = self.__delay_slider, right = None)
		#buttons = self.__window.ButtonRow(
		#	[('Cancel', (self.cancel_callback, ())),
		#	 ('Restore', (self.restore_callback, ())),
		#	 ('Apply', (self.apply_callback, ())),
		#	 ('OK', (self.ok_callback, ()))],
		#	left = None, top = self.__delay_slider, vertical = 0)

		
		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = constant2
		self._h = constant
		hbw = 0
		lb1w = 0
		lb2w = 0
		lb3w = 0
		sbw = 200
		sbh = 50
		max = 0

		
		ls = srclist
		
		length = 0
		for item in ls:
			label = item
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			if length>lb1w:
				lb1w = length
		lb1w = lb1w + cmifex2.GetStringLength(self.__window._hWnd,'From: ')+30
		

		ls = dstlist
		
		length = 0
		for item in ls:
			label = item
			if label:
				length = cmifex2.GetStringLength(self.__window._hWnd,label)
			if length>lb2w:
				lb2w = length
		lb2w = lb2w + cmifex2.GetStringLength(self.__window._hWnd,'To: ')+30

		max = lb1w + lb2w + 15

		
		ls = [('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ())),
			 ('Help', (self.helpcall, ()))]

		length = 0
		for item in ls:
			label = item[0]
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			hbw = hbw + length + 15		
		
		if max<hbw:
			max = hbw

		ls = self.__rangelist
		
		length = 0
		for item in ls:
			label = item
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			if length>lb3w:
				lb3w = length
		lb3w = lb3w + 30

		if max<lb3w+sbw+15:
			max = lb3w+sbw+15

		self._w = self._w + max +10
		self._h = self._h + 130 
		
		
		self.__src_choice = self.__window.OptionMenu('From: ',
					srclist, srcinit,
					None, left = 5, top = 5, right = lb1w, bottom = 125)
		self.__dst_choice = self.__window.OptionMenu('To: ',
					dstlist, dstinit,
					None, left = lb1w+10, top = 5, right = lb2w, bottom = 125)
		if delay > 10.0:
			rangeinit = 2
		elif delay > 1.0:
			rangeinit = 1
		else:
			rangeinit = 0
		range = float(10 ** rangeinit)
		self.__delay_slider = self.__window.Slider(None, 0, delay, range,
					None,
					left = 5, top = 35, right = sbw, bottom = sbh)
		self.__range_choice = self.__window.OptionMenu(None,
					self.__rangelist,
					rangeinit, (self.__range_callback, ()),
					left = sbw+5, top = 35, right = lb3w, bottom = 125)
		buttons = self.__window.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ())),
			 ('Help', (self.helpcall, ()))],
			left = 5, top = 90, right = hbw, bottom = 30, vertical = 0)
		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.__window._hWnd.HookKeyStroke(self.helpcall,104)
		self.__window.show()

	def __range_callback(self):
		i = self.__range_choice.getpos()
		range = float(10 ** i)
		delay = min(range, self.__delay_slider.getvalue())
		self.__delay_slider.setvalue(0)
		self.__delay_slider.setrange(0, range)
		self.__delay_slider.setvalue(delay)

	#
	# interface methods
	#

	def helpcall(self, params=None):
		import Help
		Help.givehelp(self.__window._hWnd, 'Arc Info Dialog')
	
	def close(self):
		"""Close the dialog and free resources."""
		self.__window.close()
		del self.__window
		del self.__src_choice
		del self.__dst_choice
		del self.__delay_slider
		del self.__range_choice

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self.__window.settitle(title)

	# Interface to the source list.
	def src_setpos(self, pos):
		"""Set the current selection in the source list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(srclist) -- the requested position
		"""
		self.__src_choice.setpos(pos)

	def src_getpos(self):
		"""Return the current selection in the source list."""
		return self.__src_choice.getpos()

	# Interface to the destination list.
	def dst_setpos(self, pos):
		"""Set the current selection in the destination list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(srclist) -- the requested position
		"""
		self.__dst_choice.setpos(pos)

	def dst_getpos(self):
		"""Return the current selection in the destination list."""
		return self.__dst_choice.getpos()

	# Interface to the delay value.
	def delay_setvalue(self, delay):
		"""Set the value of the delay field.

		Arguments (no defaults):
		delay -- 0.0 <= delay <= 100.0 -- the new value of the
			delay
		"""
		if delay > 10.0:
			rangeinit = 2
		elif delay > 1.0:
			rangeinit = 1
		else:
			rangeinit = 0
		range = float(10 ** rangeinit)
		self.__range_choice.setpos(rangeinit)
		#self.__delay_slider.setvalue(0)
		self.__delay_slider.setrange(0, range)
		self.__delay_slider.setvalue(delay)

	def delay_getvalue(self):
		"""Return the current value of the delay."""
		# return delay with an accuracy of 2 digits
		d = self.__delay_slider.getvalue()
		p = 100.0 / self.__delay_slider.getrange()[1]
		return int(d*p + 0.5) / p

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def cancel_callback(self):
		"""Called when `Cancel' button is pressed."""
		pass

	def restore_callback(self):
		"""Called when `Restore' button is pressed."""
		pass

	def apply_callback(self):
		"""Called when `Apply' button is pressed."""
		pass

	def ok_callback(self):
		"""Called when `OK' button is pressed."""
		pass
