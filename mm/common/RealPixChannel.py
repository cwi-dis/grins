__version__ = "$Id$"

from Channel import ChannelWindow

class RealPixChannel(ChannelWindow):
	def do_arm(self, node, same = 0):
		import MMAttrdefs
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		msg = 'Warning:\nNo playback support for RealPix in this version\n' \
		      'node %s on channel %s' % (name, self._name)
		parms = self.armed_display.fitfont('Times-Roman', msg)
		w, h = self.armed_display.strsize(msg)
		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
		self.armed_display.fgcolor((255, 0, 0))		# red
		box = self.armed_display.writestr(msg)
		return 1
