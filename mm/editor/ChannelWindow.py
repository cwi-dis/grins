# Generic channel window

import gl

from Dialog import GLDialog

class ChannelWindow(GLDialog):

	def init(self, (title, attrdict)):
		self.attrdict = attrdict
		return GLDialog.init(self, title)

	def show(self):
		if self.is_showing():
			self.pop()
			return
		GLDialog.show(self)
		# Use RGB mode
		gl.RGBmode()
		gl.gconfig()

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

	def save_geometry(self):
		self.get_geometry() # Make sure last_geometry is up-to-date
		if self.last_geometry:
			h, v, width, height = self.last_geometry
			# XXX transaction!
			self.attrdict['winpos'] = h, v
			self.attrdict['winsize'] = width, height
