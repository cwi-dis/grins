__version__ = "$Id$"

#
# WIN32 Video channel
#

# the core
import Channel

# common component
from MediaChannel import MediaChannel
from RealChannel import RealChannel

# node attributes
import MMAttrdefs

# channel types and message
import windowinterface

debug=0

class VideoChannel(Channel.ChannelWindowAsync):
	_our_attrs = ['bucolor', 'hicolor', 'scale', 'center']
	node_attrs = Channel.ChannelWindow.node_attrs + \
		      ['clipbegin', 'clipend', 'project_videotype', 'project_targets']
	if Channel.CMIF_MODE:
		node_attrs = node_attrs + _our_attrs
	else:
		chan_attrs = Channel.ChannelWindow.chan_attrs + _our_attrs
	_window_type = windowinterface.MPEG

	def __init__(self, name, attrdict, scheduler, ui):
		self.__mc = None
		self.__rc = None
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		try:
			self.__rc = RealChannel(self)
		except:
			pass
		self.__mc = MediaChannel(self)
		self.__mc.showit(self.window)
		return 1

	def do_hide(self):
		self.__mc.unregister_for_timeslices()
		self.__mc.release_res()
		self.__mc.paint()
		self.__mc = None
		if self.__rc is not None:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		Channel.ChannelWindowAsync.do_hide(self)

	def do_arm(self, node, same=0):
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		url = self.getfileurl(node)
		import mimetypes, string
		mtype = mimetypes.guess_type(url)[0]
		node.__type = ''
		if string.find(mtype, 'real') >= 0:
			node.__type = 'real'
		self.prepare_armed_display(node)
		if node.__type == 'real':
			if self.__rc is None:
				self.errormsg(node, 'No playback support for RealVideo in this version')
			else:
				self.__rc.prepare_player(node)
		else:
			res=self.__mc.prepare_player(node)
			if res==0:
				self.showwarning(node,'System missing infrastructure to playback')
			elif res==-1:
				import MMurl, urllib
				url = MMurl.canonURL(url)
				url=urllib.unquote(url)
				self.showwarning(node,'Failed to render file %s' % url)
		return 1

	def do_play(self, node):
		self.__type = node.__type
		if node.__type == 'real':
			if self.__rc is None or not self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
				self.playdone(0)
		elif not self.__mc.playit(node,self.window):
			windowinterface.settimer(5,(self.playdone,(0,)))

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		if self.__mc is not None:
			self.__mc.pauseit(paused)
		if self.__rc is not None:
			self.__rc.pauseit(paused)

	# Part of stop sequence. Stop and remove last frame 
	def stopplay(self, node):
		if self.__type == 'real':
			if self.__rc is not None:
				self.__rc.stopit()
		else:
			self.__mc.stopit()
		if self.window:
			self.window.RedrawWindow()
		Channel.ChannelWindowAsync.stopplay(self, node)

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
		if node.__type != 'real':
			self.armed_display.drawvideo(self.__mc.update)


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

	def _getoswindow(self):
		return self.window.GetSafeHwnd()
			
	def _getoswinpos(self):
		return None
