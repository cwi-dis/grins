# Generic channel window

import gl

from Dialog import GLDialog

class ChannelWindow() = GLDialog():
	#
	# Initialization function.
	#
	def init(self, (title, attrdict)):
		self.attrdict = attrdict
		return GLDialog.init(self, title)
	#
	def show(self):
		if self.wid <> 0: return
		GLDialog.show(self)
		self.get_geometry() # Make sure self.last_geometry is set
		# Use RGB mode
		gl.RGBmode()
		gl.gconfig()
	#
	def load_geometry(self):
		# Get the window size
		if self.attrdict.has_key('winsize'):
			width, height = self.attrdict['winsize']
		else:
			width, height = 0, 0
		# Get the window position
		if self.attrdict.has_key('winpos'):
			h, v = self.attrdict['winpos']
		else:
			h, v = -1, -1
		self.last_geometry = h, v, width, height
	#
	def save_geometry(self):
		if self.last_geometry:
			h, v, width, height = self.last_geometry
			# XXX transaction!
			self.attrdict['winpos'] = h, v
			self.attrdict['winsize'] = width, height
	#
