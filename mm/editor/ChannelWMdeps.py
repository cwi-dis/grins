#
# Channel stuff that is dependent on the window interface used.
# This version is for use with the mixed forms/gl/sjoerd stuff used in the
# editor.
#

# arm states
AIDLE = 1
ARMING = 2
ARMED = 3
# play states
PIDLE = 1
PLAYING = 2
PLAYED = 3

class ChannelWM:
	#
	# Methods called by CMIFed.
	#
	def check_visible(self):
		if self.may_show():
			self.show()
		else:
			self.hide()

	def setwaiting(self):
		pass
	def setready(self):
		pass
	def flip_visible(self):
		if self._attrdict.has_key('visible'):
			visible = self._attrdict['visible']
		else:
			visible = 1
		visible = (not visible)
		self._attrdict['visible'] = visible
		if visible:
			self.show()
		else:
			self.hide()
	def save_geometry(self):
		pass

class ChannelWindowWM:
	def save_geometry(self):
		if self.is_showing():
			x, y, w, h = self.window.getgeometry()
			self._attrdict['winpos'] = x, y
			self._attrdict['winsize'] = w, h

class _ChannelThreadWM:
	def do_show_wmdep(self):
		import glwindow
		import mm
		glwindow.devregister(`self._deviceno`+':'+`mm.playdone`, \
			  self._playdone, None)
		glwindow.devregister(`self._deviceno`+':'+`mm.armdone`, \
			  self._armdone, None)

	def _playdone(self, dummy):
		if self._playstate == PLAYING:
			self.playdone(None)

	def _armdone(self, dummy):
		if self._armstate == ARMING:
			self.arm_1()

	def do_hide_wmdep(self):
		pass

	def play_wmdep(self):
		pass
