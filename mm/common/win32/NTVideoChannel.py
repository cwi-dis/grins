__version__ = "$Id$"

#
# WIN32 Video channel
#

# the core
import Channel

# common component
import MediaChannel
import RealChannel

# node attributes
import MMAttrdefs
from AnchorDefs import *

# channel types and message
import windowinterface

debug=0

class VideoChannel(Channel.ChannelWindowAsync):
	_our_attrs = ['bucolor', 'hicolor', 'scale', 'center']
	node_attrs = Channel.ChannelWindow.node_attrs + [
		'clipbegin', 'clipend',
		'project_audiotype', 'project_videotype', 'project_targets',
		'project_perfect', 'project_mobile']
	if Channel.CMIF_MODE:
		node_attrs = node_attrs + _our_attrs
	else:
		chan_attrs = Channel.ChannelWindow.chan_attrs + _our_attrs
	_window_type = windowinterface.MPEG

	def __init__(self, name, attrdict, scheduler, ui):
		self.__mc = None
		self.__rc = None
		self.__type = None
		self.need_armdone = 0
		self.__playing = None
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		self.__mc = MediaChannel.MediaChannel(self)
		self.__mc.showit(self.window)
		return 1

	def do_hide(self):
		self.__playing = None
		self.__mc.unregister_for_timeslices()
		self.__mc.release_res()
		self.__mc.paint()
		self.__mc = None
		if self.__rc:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		Channel.ChannelWindowAsync.do_hide(self)

	def do_arm(self, node, same=0):
		self.__ready = 0
		if same and self.armed_display:
			self.__ready = 1
			return 1
		node.__type = ''
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		url = self.getfileurl(node)
		if not url:
			self.errormsg(node, 'No URL set on node')
			return 1
		import MMmimetypes, string
		mtype = MMmimetypes.guess_type(url)[0]
		if mtype and (string.find(mtype, 'real') >= 0 or string.find(mtype, 'flash') >= 0):
			node.__type = 'real'
		if node.__type == 'real':
			if self.__rc is None:
				try:
					self.__rc = RealChannel.RealChannel(self)
				except RealChannel.error, msg:
					# can't do RealAudio
##					self.__rc = 0 # don't try again
					self.errormsg(node, msg)
			if self.__rc:
				if self.__rc.prepare_player(node):
					self.__ready = 1
		else:
			try:
				self.__mc.prepare_player(node)
				self.__ready = 1
			except MediaChannel.error, msg:
				self.errormsg(node, msg)

		self.prepare_armed_display(node)
		
		return 1

	def do_play(self, node):
		self.__playing = node
		self.__type = node.__type
		if not self.__ready:
			# arming failed, so don't even try playing
			self.playdone(0)
			return
		if node.__type == 'real':
			if not self.__rc:
				self.playdone(0)
			elif not self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
				import windowinterface, MMAttrdefs
				name = MMAttrdefs.getattr(node, 'name')
				if not name:
					name = '<unnamed node>'
				chtype = self.__class__.__name__[:-7] # minus "Channel"
				windowinterface.showmessage('No playback support for %s on this system\n'
							    'node %s on channel %s' % (chtype, name, self._name), mtype = 'warning')
				self.playdone(0)
		elif not self.__mc.playit(node, self.window):
			self.errormsg(node,'Can not play')
			self.playdone(0)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		if self.__mc is not None:
			self.__mc.pauseit(paused)
		if self.__rc:
			self.__rc.pauseit(paused)

	def playstop(self):
		self.__stopplayer()
		self.playdone(1)		
				
	def __stopplayer(self):
		if self.__playing:
			if self.__type == 'real':
				if self.__rc:
					self.__rc.stopit()
			else:
				self.__mc.stopit()
		self.__playing = None

	def endoftime(self):
		self.__stopplayer()
		self.playdone(0)

	# interface for anchor creation
	def defanchor(self, node, anchor, cb):
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [A_SHAPETYPE_RECT,0.0,0.0,1.0,1.0], anchor[3]))

	def prepare_armed_display(self,node):
		self.armed_display._bgcolor=self.getbgcolor(node)
		drawbox = MMAttrdefs.getattr(node, 'drawbox')
		if drawbox:
			self.armed_display.fgcolor(self.getbucolor(node))
		else:
			self.armed_display.fgcolor(self.getbgcolor(node))
		if self.__mc:
			armbox = self.__mc.prepare_anchors(node, self.window, self.getmediageom(node))
			self.setArmBox(armbox)
		# WARNING: for real not implemented yet
		

#		hicolor = self.gethicolor(node)
		
#		for a in node.GetRawAttrDef('anchorlist', []):
#			atype = a[A_TYPE]
#			if atype not in Channel.SourceAnchors or atype == ATYPE_AUTO:
#				continue
#			anchor = node.GetUID(), a[A_ID]
#			if not self._player.context.hyperlinks.findsrclinks(anchor):
#				continue
#			b = self.armed_display.newbutton((0,0,1,1), times = a[A_TIMES])
#			b.hiwidth(3)
#			if drawbox:
#				b.hicolor(hicolor)
#			self.setanchor(a[A_ID], a[A_TYPE], b, a[A_TIMES])
		if node.__type != 'real':
			self.armed_display.drawvideo(self.__mc.update)

	def _getoswindow(self):
		return self.window.GetSafeHwnd()
			
	def _getoswinpos(self):
		x, y, w, h = self.window._rect
		return (x, y), (w, h)

	def play(self, node):
		self.need_armdone = 1
		self.play_0(node)
		if self._is_shown and node.ShouldPlay() \
		   and self.window and not self.syncplay:
			self.check_popup()
			if self.armed_display.is_closed():
				# assume that we are going to get a
				# resize event
				pass
			else:
				self.armed_display.render()
			if self.played_display:
				self.played_display.close()
			self.played_display = self.armed_display
			self.armed_display = None
			self.do_play(node)
			if self.need_armdone and node.__type != 'real':
				self.need_armdone = 0
				if not self.syncarm:
					self.armdone()
		else:
			self.need_armdone = 0 # play_1 calls armdone()
			self.play_1()

	def playdone(self, outside_induced):
		if self.need_armdone:
			self.need_armdone = 0
			if not self.syncarm:
				self.armdone()
		Channel.ChannelWindowAsync.playdone(self, outside_induced)
		if not outside_induced:
			self.__playing = None

	def stopplay(self, node):
		if self.__mc is not None:
			self.__mc.stopit()
		if self.__rc:
			self.__rc.stopit()
		Channel.ChannelWindowAsync.stopplay(self, node)
