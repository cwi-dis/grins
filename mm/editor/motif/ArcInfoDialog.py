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

import windowinterface

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

		self.__window = windowinterface.Window(title, resizable = 1,
					deleteCallback = (self.cancel_callback, ()))
		s = self.__window.SubWindow(top = None, left = None, right = None)
		s1 = s.SubWindow(top = None, left = None)
		self.__src_choice = s1.OptionMenu('From:',
					srclist, srcinit,
					None, top = None, left = None,
						  right = None)
		b1 = s1.Button('Push focus', (self.pushsrcfocus_callback, ()),
			       top = self.__src_choice, left = None,
			       right = None, bottom = None)
		s2 = s.SubWindow(top = None, left = s1, right = None)
		self.__dst_choice = s2.OptionMenu('To:',
					dstlist, dstinit,
					None, top = None,
					left = None, right = None)
		b2 = s2.Button('Push focus', (self.pushdstfocus_callback, ()),
			       top = self.__dst_choice, left = None,
			       right = None, bottom = None)
		if delay > 10.0:
			rangeinit = 2
		elif delay > 1.0:
			rangeinit = 1
		else:
			rangeinit = 0
		range = float(10 ** rangeinit)
		ss = self.__window.SubWindow(top = s, left = None, right = None)
		self.__delay_slider = ss.Slider(None, 0, delay, range,
					None,
					top = None, left = None, bottom = None)
		self.__range_choice = ss.OptionMenu(None,
					self.__rangelist,
					rangeinit, (self.__range_callback, ()),
					top = None,
					left = self.__delay_slider, right = None, bottom = None)
		buttons = self.__window.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			left = None, top = ss, right = None, bottom = None,
			vertical = 0)
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
		self.__delay_slider.setvalue(0)
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
