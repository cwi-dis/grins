__version__ = "$Id$"

import Channel
import MMAttrdefs
import MMurl

# for timer support
import windowinterface

# wince playback module
import winmm

error = 'VideoChannel.error'

class VideoChannel(Channel.ChannelWindowAsync):
	_our_attrs = ['fit']
	node_attrs = Channel.ChannelWindow.node_attrs + [
		'clipbegin', 'clipend',
		'project_audiotype', 'project_videotype', 'project_targets',
		'project_perfect', 'project_mobile']
	chan_attrs = Channel.ChannelWindow.chan_attrs + _our_attrs

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__video_player = None
		self.__video_surf = None
		self.__fiber_id = None
		self.__update_box = None

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		return 1

	def do_hide(self):
		if self.__video_player:
			self.__video_player = None
			self.__unregister_for_timeslices()
		Channel.ChannelWindowAsync.do_hide(self)

	def do_arm(self, node, same=0):
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external.')
			return 1
		f = self.getfileurl(node)
		if not f:
			self.errormsg(node, 'No URL set on node.')
			return 1
		try:
			f = MMurl.urlretrieve(f)[0]
		except IOError, arg:
			if type(arg) is type(self):
				arg = arg.strerror
			self.errormsg(node, 'Cannot open: %s\n\n%s.' % (f, arg))
			return 1
		
		# remember coordinates for anchor editing (and only for that!)
		fit = MMAttrdefs.getattr(node, 'fit')
		
		try:
			self.__video_player = winmm.CreateVideoPlayerFromFile(f)
		except winmm.error, msg:
			self.__video_player = None
			self.errormsg(node, 'Cannot play: %s\n\n%s.' %(f, msg))
			return 1

		try:
			self.__video_surf = self.__video_player.PreparePlayback()
		except winmm.error, msg:
			self.__video_player = None
			self.__video_surf = None
			self.errormsg(node, 'Cannot play: %s\n\n%s.' %(f, msg))
			return 1

		try:
			imbox = self.armed_display.display_image_from_file(
					self.__video_surf, fit = fit, coordinates=self.getmediageom(node), center = 0)
		except windowinterface.error, msg:
			self.errormsg(node, 'Cannot display: %s\n\n%s.' %(f, msg))
			return 1
		self.setArmBox(imbox)

		# construct video box for faster updates
		x, y, w, h = self.armed_display._convert_coordinates(imbox, units = self.armed_display._units)
		dx, dy = self.window.getwindowpos()[:2]
		self.__update_box = x+dx, y+dy, w, h

		return 1

	def play(self, node, curtime):
		if node.GetType() == 'anchor':
			self.play_anchor(node, curtime)
			return
		self.need_armdone = 1
		self.play_0(node, curtime)
		if not self._armcontext:
			return
		if self._is_shown and node.ShouldPlay() \
		   and self.window and not self.syncplay:
			self.check_popup()
			self.schedule_transitions(node, curtime)
			if self.armed_display.is_closed():
				# assume that we are going to get a
				# resize event
				pass
			else:
				self.armed_display.render()
			if self.played_display:
				self.played_display.close()
			self.played_display = self.armed_display
			self.do_play(node, curtime)
			self.armdone()
		else:
			self.play_1(curtime)

	def do_play(self, node, curtime):
		Channel.ChannelWindowAsync.do_play(self, node, curtime)
		if self.__video_player is None:
			self.playdone(0, curtime)
			return
		self.__video_player.ResumePlayback()
		self.__register_for_timeslices()

	def setpaused(self, paused, timestamp):
		Channel.ChannelWindowAsync.setpaused(self, paused, timestamp)
		if self.__video_player:
			if paused:
				self.__video_player.SuspendPlayback()
				self.__unregister_for_timeslices()
			else:
				self.__video_player.ResumePlayback()
				self.__register_for_timeslices()

	def stopplay(self, node, curtime):
		if self.__video_player:
			self.__video_player = None
			self.__unregister_for_timeslices()
		Channel.ChannelWindowAsync.stopplay(self, node, curtime)

	def defanchor(self, node, anchor, cb):
		if not self.window:
			windowinterface.showmessage('The window is not visible.\nPlease make it visible and try again.')
			return
		if self._armstate != AIDLE:
			raise error, 'Arm state must be idle when defining an anchor'
		if self._playstate != PIDLE:
			raise error, 'Play state must be idle when defining an anchor'
		self._anchor_context = AnchorContext()
		self.startcontext(self._anchor_context)
		save_syncarm = self.syncarm
		self.syncarm = 1
		if hasattr(self, '_arm_imbox'):
			del self._arm_imbox
		self.arm(node)
		if not hasattr(self, '_arm_imbox'):
			self.syncarm = save_syncarm
			self.stopcontext(self._anchor_context, 0)
			windowinterface.showmessage("Can't display image, so can't edit anchors", parent = self.window)
			return
		save_syncplay = self.syncplay
		self.syncplay = 1
		self.play(node, 0)
		self._playstate = PLAYED
		self.syncarm = save_syncarm
		self.syncplay = save_syncplay
		self._anchor = anchor
		box = anchor.aargs
		self._anchor_cb = cb
		msg = 'Draw anchor in ' + self._name + '.'
		if box == []:
			self.window.create_box(msg, self._box_cb)
		else:
			f = self.getfileurl(node)
			try:
				f = urlretrieve(f)[0]
			except IOError:
				pass

			# convert coordinates to relative image size
			box = self.convertCoordinatesToRelatives(f, box)
			# convert coordinates from relative image to relative window size
			windowCoordinates = self.convertCoordinatesToWindow(box)

			shapeType = box[0]
			# for instance we manage only the rect shape
			if shapeType == 'rect':
				x = windowCoordinates[1]
				y = windowCoordinates[2]
				w = windowCoordinates[3] - x
				h = windowCoordinates[4] - y
				self.window.create_box(msg, self._box_cb, (x, y, w, h))
			else:
				print 'Shape type not supported yet for editing'

	def _box_cb(self, *box):
		self.stopcontext(self._anchor_context, 0)
		# for now, keep the compatibility with old structure
		if len(box) == 4:
			x, y, w, h = box
			winCoordinates = ['rect', x ,y ,x+w, y+h]
			
			# convert coordinates from window size to image size.
			relativeCoordinates = self.convertShapeRelWindowToRelImage(winCoordinates)
			from MMNode import MMAnchor
			arg = MMAnchor(self._anchor.aid, self._anchor.atype, relativeCoordinates, self._anchor.atimes, self._anchor.aaccess)
		else:
			arg = self._anchor
		apply(self._anchor_cb, (arg,))
		del self._anchor_cb
		del self._anchor_context
		del self._anchor

	def onIdle(self):
		if self.window and not self.window.is_closed():
			self.window.updateNow(self.__update_box)
				
	def __register_for_timeslices(self):
		if self.__fiber_id is None:
			self.__fiber_id = windowinterface.setidleproc(self.onIdle)

	def __unregister_for_timeslices(self):
		if self.__fiber_id is not None:
			windowinterface.cancelidleproc(self.__fiber_id)
			self.__fiber_id = None
