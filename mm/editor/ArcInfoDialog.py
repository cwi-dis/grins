__version__ = "$Id$"

import windowinterface

class ArcInfoDialog:
	__rangelist = ['0-1 sec', '0-10 sec', '0-100 sec']

	def __init__(self, title, srclist, srcinit, dstlist, dstinit, delay):
		self.__window = windowinterface.Window(title, resizable = 1,
					deleteCallback = (self.cancel_callback, ()))
		self.__src_choice = self.__window.OptionMenu('From:',
					srclist, srcinit,
					None, top = None, left = None)
		self.__dst_choice = self.__window.OptionMenu('To:',
					dstlist, dstinit,
					None, top = None,
					left = self.__src_choice, right = None)
		if delay > 10.0:
			rangeinit = 2
		elif delay > 1.0:
			rangeinit = 1
		else:
			rangeinit = 0
		range = float(10 ** rangeinit)
		self.__delay_slider = self.__window.Slider(None, 0, delay, range,
					None,
					top = self.__src_choice, left = None)
		self.__range_choice = self.__window.OptionMenu(None,
					self.__rangelist,
					rangeinit, (self.__range_callback, ()),
					top = self.__dst_choice,
					left = self.__delay_slider, right = None)
		buttons = self.__window.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			left = None, top = self.__delay_slider, vertical = 0)
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
		self.__window.close()
		del self.__window
		del self.__src_choice
		del self.__dst_choice
		del self.__delay_slider
		del self.__range_choice

	def settitle(self, title):
		self.__window.settitle(title)

	def src_setpos(self, pos):
		self.__src_choice.setpos(pos)

	def src_getpos(self):
		return self.__src_choice.getpos()

	def dst_setpos(self, pos):
		self.__dst_choice.setpos(pos)

	def dst_getpos(self):
		return self.__dst_choice.getpos()

	def delay_setvalue(self, delay):
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
		# return delay with an accuracy of 2 digits
		d = self.__delay_slider.getvalue()
		p = 100.0 / self.__delay_slider.getrange()[1]
		return int(d*p + 0.5) / p

	#
	# callbacks -- to be overriden
	#

	def cancel_callback(self):
		pass

	def restore_callback(self):
		pass

	def apply_callback(self):
		pass

	def ok_callback(self):
		pass
