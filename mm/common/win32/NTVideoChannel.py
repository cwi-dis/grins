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

debug = 0

import rma

# ddraw.error
import ddraw
	
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
		self.__subtype = None
		self.need_armdone = 0
		self.__playing = None
		self.__rcMediaWnd = None
		self.__windowless_real_rendering = 1
		self.__windowless_wm_rendering = 1
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		return 1

	def do_hide(self):
		self.__playing = None
		if self.__mc:
			self.__mc.stopit()
			self.__mc.destroy()
			self.__mc = None
		if self.__rc:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		if self.window:
			self.window.DestroyOSWindow()
		Channel.ChannelWindowAsync.do_hide(self)

	def do_arm(self, node, same=0):
		self.__ready = 0
		if same and self.armed_display:
			self.__ready = 1
			return 1
		node.__type = ''
		node.__subtype = ''
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
			if string.find(mtype, 'flash') >= 0:
				node.__subtype = 'flash'
		else:
			node.__type = 'wm'
			if string.find(mtype, 'x-ms-asf')>=0:
				node.__subtype = 'asf'
				if not self._exporter:
					self.__windowless_wm_rendering = 0

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
			if self.__mc is None:
				if not self.__windowless_wm_rendering:
					self.__mc = MediaChannel.MediaChannel(self)
				else:	
					self.__mc = MediaChannel.VideoStream(self)
			try:
				self.__mc.prepare_player(node, self.window)
				self.__ready = 1
			except MediaChannel.error, msg:
				self.errormsg(node, msg)

		self.prepare_armed_display(node)
		
		return 1

	def do_play(self, node):
		self.__playing = node
		self.__type = node.__type
		self.__subtype = node.__subtype

		if not self.__ready:
			# arming failed, so don't even try playing
			self.playdone(0)
			return
		if node.__type == 'real':
			bpp = self.window._topwindow.getRGBBitCount()
			if bpp not in (8, 16, 24, 32) and self.__windowless_real_rendering:
				self.__windowless_real_rendering = 0
			if self.__subtype=='flash':
				self.__windowless_real_rendering = 0
				
			if not self.__windowless_real_rendering:
				self.window.CreateOSWindow(rect=self.getMediaWndRect())
			if not self.__rc:
				self.playdone(0)
				return
			if self.__windowless_real_rendering:
				res =self.__rc.playit(node,windowless=1)
			else:
				res = self.__rc.playit(node, self._getoswindow(), self._getoswinpos())
			if not res:
				import windowinterface, MMAttrdefs
				name = MMAttrdefs.getattr(node, 'name')
				if not name:
					name = '<unnamed node>'
				chtype = self.__class__.__name__[:-7] # minus "Channel"
				windowinterface.showmessage('No playback support for %s on this system\n'
							    'node %s on channel %s' % (chtype, name, self._name), mtype = 'warning')
				self.playdone(0)
		else:
			if not self.__mc:
				self.playdone(0)
			else:
				if not self.__windowless_wm_rendering:
					self.window.CreateOSWindow(rect=self.getMediaWndRect())
				if not self.__mc.playit(node, self.window):
					windowinterface.showmessage('Failed to play media file', mtype = 'warning')
					self.playdone(0)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		if self.__mc is not None:
			self.__mc.pauseit(paused)
		if self.__rc:
			self.__rc.pauseit(paused)

	def playstop(self):
		# freeze video
		self.__freezeplayer()
		self.playdone(1)		
				
	def __stopplayer(self):
		if self.__playing:
			if self.__type == 'real':
				if self.__rc:
					self.__rc.stopit()
					if self.__windowless_real_rendering:
						self.cleanVideoRenderer()
			else:
				self.__mc.stopit()
		self.__playing = None

	def __freezeplayer(self):
		if self.__playing:
			if self.__type == 'real':
				if self.__rc:
					self.__rc.freezeit()
			else:
				self.__mc.freezeit()

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
		armbox = self.prepare_anchors(node, self.window, self.getmediageom(node))
		self.setArmBox(armbox)
		self.armed_display.setMediaBox(armbox)

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
			self.schedule_transitions(node)
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
				self.armdone()
		else:
			self.need_armdone = 0 # play_1 calls armdone()
			self.play_1()

	def playdone(self, outside_induced):
		if self.need_armdone:
			self.need_armdone = 0
			self.armdone()
		Channel.ChannelWindowAsync.playdone(self, outside_induced)
		if not outside_induced:
			self.__playing = None

	def stopplay(self, node, no_extend = 0):
		if node and self._played_node is not node:
##			print 'node was not the playing node '+`self,node,self._played_node`
			return
		self.__stopplayer()
		Channel.ChannelWindowAsync.stopplay(self, node, no_extend)

	# Define the anchor area for visible medias
	def prepare_anchors(self, node, window, coordinates):
		if not window: return
	
		# GetClientRect by def returns always: 0, 0, w, h
		w_left,w_top,w_width,w_height = window.GetClientRect()

		left,top,width,height = window._convert_coordinates(coordinates)
		if width==0 or height==0:
			print 'warning: zero size media rect' 
			width, height = w_width, w_height
		self.__rcMediaWnd=(left,top,width,height)
		
		return (left/float(w_width), top/float(w_height), width/float(w_width), height/float(w_height))

	def getMediaWndRect(self):
		return self.__rcMediaWnd

	
	#############################
	def getRealVideoRenderer(self):
		self.initVideoRenderer()
		return self

	# 
	# Implement interface of real video renderer
	# 
	videofmts = { rma.RMA_RGB: 'RGB', # windows RGB
		rma.RMA_RLE8: 'RLE8',
		rma.RMA_RLE4: 'RLE4',
		rma.RMA_BITFIELDS: 'BITFIELDS',
		rma.RMA_I420: 'I420', # planar YCrCb
		rma.RMA_YV12: 'YV12', # planar YVU420
		rma.RMA_YUY2: 'YUY2', # packed YUV422
		rma.RMA_UYVY: 'UYVY', # packed YUV422
		rma.RMA_YVU9: 'YVU9', # Intel YVU9

		rma.RMA_YUV420: 'YUV420',
		rma.RMA_RGB555: 'RGB555',
		rma.RMA_RGB565: 'RGB565',
		}

	def toStringFmt(self, fmt):
		if VideoChannel.videofmts.has_key(fmt):
			return VideoChannel.videofmts[fmt]
		else:
			return 'FOURCC(%d)' % fmt

	def initVideoRenderer(self):
		self.__rmdds = None
		self.__rmrender = None
		
	def cleanVideoRenderer(self):
		if self.window:
			self.window.removevideo()
		self.__rmdds = None
		self.__rmrender = None

	def OnFormatBitFields(self, rmask, gmask, bmask):
		self.__bitFieldsMask = rmask. gmask, bmask

	def OnFormatChange(self, w, h, bpp, fmt):
		if not self.window: return
		viewport = self.window._topwindow
		screenBPP = viewport.getRGBBitCount()
		
		bltCode = ''
		if fmt==rma.RMA_RGB:
			bltCode = 'Blt_RGB%d_On_RGB%d' % (bpp, screenBPP)
		elif fmt==rma.RMA_YUV420:
			bltCode = 'Blt_YUV420_On_RGB%d' % screenBPP
		
		if debug:
			print 'Rendering real video: %s bpp=%d (%d x %d) on RGB%d' % (self.toStringFmt(fmt), bpp, w, h, screenBPP)
		
		if not bltCode:
			self.cleanVideoRenderer()
			return
			
		try:
			dymmy = getattr(viewport.getDrawBuffer(), bltCode)
		except AttributeError:
			self.cleanVideoRenderer()
		else:
			self.__rmdds = viewport.CreateSurface(w, h)
			self.__rmrender = getattr(self.__rmdds, bltCode), w, h
			self.window.setvideo(self.__rmdds, self.getMediaWndRect(), (0,0,w,h) )
			
	def Blt(self, data):
		if self.__rmdds and self.__rmrender:
			blt, w, h = self.__rmrender
			try:
				blt(data, w, h)
			except ddraw.error, arg:
				print arg
				return
			if self.window:
				self.window.update(self.window.getwindowpos())

	def EndBlt(self):
		# do not remove video yet 
		# it may be frozen
		self.__rmdds = None
		self.__rmrender = None



