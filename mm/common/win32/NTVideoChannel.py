__version__ = "$Id$"

#
# WIN32 Video channel
#

# the core
import Channel

# common component
import MediaChannel

# node attributes
import MMAttrdefs

# channel types and message
import windowinterface

debug=0

class VideoChannel(Channel.ChannelWindowAsync,MediaChannel.MediaChannel):
	node_attrs = Channel.ChannelWindowAsync.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'center',
		      'clipbegin', 'clipend']
	_window_type = windowinterface.MPEG

	def __init__(self, name, attrdict, scheduler, ui):
		MediaChannel.MediaChannel.__init__(self)
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		self.showit(self.window)
		return 1

	def do_hide(self):
		self.release_res()
		Channel.ChannelWindowAsync.do_hide(self)

	def destroy(self):
		self.unregister_for_timeslices()
		self.release_res()
		Channel.ChannelWindowAsync.destroy(self)
		
	def do_arm(self, node, same=0):
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		self.prepare_armed_display(node)
		res=self.prepare_player(node)
		if res==0:
			self.showwarning(node,'System missing infrastructure to playback')
		elif res==-1:
			self.showwarning(node,'Failed to render file')
		return 1

	def do_play(self, node):
		if not self.playit(node,self.window):
			windowinterface.settimer(5,(self.playdone,(0,)))

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		self.pauseit(paused)

	# Part of stop sequence. Stop and remove last frame 
	def stopplay(self, node):
		Channel.ChannelWindowAsync.stopplay(self, node)
		self.stopit()
		if self.window:self.window.RedrawWindow()

	# interface for anchor creation
	def defanchor(self, node, anchor, cb):
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [0,0,1,1]))

	def prepare_armed_display(self,node):
		self.armed_display._bgcolor=self.getbgcolor(node)
		drawbox = MMAttrdefs.getattr(node, 'drawbox')
		if drawbox:
			self.armed_display.fgcolor(self.getbucolor(node))
		else:
			self.armed_display.fgcolor(self.getbgcolor(node))
		hicolor = self.gethicolor(node)
		for a in node.GetRawAttrDef('anchorlist', []):
			atype = a[Channel.A_TYPE]
			if atype not in Channel.SourceAnchors or atype == Channel.ATYPE_AUTO:
				continue
			b = self.armed_display.newbutton((0,0,1,1))
			b.hiwidth(3)
			if drawbox:
				b.hicolor(hicolor)
			self.setanchor(a[Channel.A_ID], a[Channel.A_TYPE], b)
		self.armed_display.drawvideo(self.update)


	# showwarning if the infrastucture is missing.
	# The user should install Windows Media Player
	# since then this infrastructure is installed
	def showwarning(self,node,inmsg):
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		chtype = self.__class__.__name__[:-7] # minus "Channel"
		msg = 'Warning:\n%s\n' \
		      '%s node %s on channel %s' % (inmsg, chtype, name, self._name)
		parms = self.armed_display.fitfont('Times-Roman', msg)
		w, h = self.armed_display.strsize(msg)
		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
		self.armed_display.fgcolor((255, 0, 0))		# red
		box = self.armed_display.writestr(msg)



