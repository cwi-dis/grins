# A class to handle standard geometry loading and saving for views etc.
# This works both with BasicDialog or GLDialog as base class.
# Specify this as the first base class, before the *Dialog base class.

import MMAttrdefs

class ViewDialog():
	#
	def init(self, geom_name):
		self.geom_name = geom_name
		return self
	#
	def load_geometry(self):
		name = self.geom_name
		h, v = MMAttrdefs.getattr(self.root, name + 'winpos')
		width, height = MMAttrdefs.getattr(self.root, name + 'winsize')
		self.last_geometry = h, v, width, height
	#
	def save_geometry(self):
		self.get_geometry()
		if self.last_geometry = None:
			return
		name = self.geom_name
		h, v, width, height = self.last_geometry
		# XXX need transaction here!
		if h >= 0 and v >= 0:
			self.root.SetAttr(name + 'winpos', (h, v))
		if width <> 0 and height <> 0:
			self.root.SetAttr(name + 'winsize', (width, height))
	#
