__version__ = "$Id$"

# A class to handle standard geometry loading and saving for views etc.
# This works both with BasicDialog or GLDialog as base class.
# Specify this as the first base class, before the *Dialog base class.
# (Now this also defines dummy versions of methods that every view
# should have such as getfocus().)

import MMAttrdefs
import sys

class ViewDialog:
	#
	def __init__(self, geom_name):
		self.geom_name = geom_name
	#
	def __repr__(self):
		return '<ViewDialog instance, geom_name=' \
			+ `self.geom_name` + '>'
	#
	def load_geometry(self):
		name = self.geom_name
		posname = name + 'winpos'
		sizename = name + 'winsize'
		h, v = MMAttrdefs.getattr(self.root, posname)
		width, height = MMAttrdefs.getattr(self.root, sizename)
		self.last_geometry = h, v, width, height
		# Experimental code, currently mac-only
		if sys.platform == 'mac':
			if (h, v) == (-1, -1):
				# We got default values. Try to obtain previous applicationwide settings
				import settings
				if settings.has_key(posname) and settings.has_key(sizename):
					h, v = settings.get(posname)
					width, height = settings.get(sizename)
					self.last_geometry = h, v, width, height
					# And clear (so next window appears staggered again)
					settings.set(name + 'winpos', (-1, -1))
					settings.save()
	#
	def save_geometry(self):
		self.get_geometry()
		if self.last_geometry is None:
			return
		name = self.geom_name
		h, v, width, height = self.last_geometry
		# XXX need transaction here!
		if h >= 0 and v >= 0:
			self.root.SetAttr(name + 'winpos', (h, v))
		if width <> 0 and height <> 0:
			self.root.SetAttr(name + 'winsize', (width, height))
		MMAttrdefs.flushcache(self.root)
		if sys.platform == 'mac':
			import settings
			settings.set(name + 'winpos', (h, v))
			settings.set(name + 'winsize', (width, height))
	#
	def getfocus(self):
		# views can override this to return their focus node
		return None
	#
	def globalsetfocus(self, node):
		# views can override this to allow their focus to be 'pushed'
		pass
	#
	def fixtitle(self):
		# views can override this to fix their title after the
		# filename has changed
		pass
