__version__ = "$Id$"

import Channel
import MMAttrdefs
from MMExc import *			# exceptions
from AnchorDefs import *
import windowinterface
import MMurl
import mv
import Xlib

_mvmap = {}			# map of MVid to channel

def _selcb():
	while mv.PendingEvents():
		event = mv.NextEvent()
		if event[0] == mv.MV_EVENT_STOP:
			if _mvmap.has_key(event[1]):
				_mvmap[event[1]].stopped()

windowinterface.select_setcallback(mv.GetEventFD(), _selcb, ())
mv.SetSelectEvents(mv.MV_EVENT_MASK_STOP)

class VideoChannel(Channel.ChannelWindowAsync):
	node_attrs = Channel.ChannelWindowAsync.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'center', 'loop',
		      'clipbegin', 'clipend']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__context = None
		self.played_movie = self.armed_movie = None
		self.__stopped = 0
		self.__qid = None

	def getaltvalue(self, node):
		import string
		url = self.getfileurl(node)
		i = string.rfind(url, '.')
		if i > 0:
			suff = url[i:]
			return suff in ('.mpg', '.mpv', '.qt', '.avi')
		return 0

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		window = self.window
		widget = window._form
		if widget.IsRealized():
			self.__ginitCB(widget, window._visual, None)
		else:
			widget.AddCallback('ginitCallback', self.__ginitCB,
					   window._visual)
		return 1

	def __ginitCB(self, widget, visual, calldata):
		self.__context = widget.CreateContext(visual, None, 1)

	def do_hide(self):
		if self.played_movie:
			movie = self.played_movie
			self.played_movie = None
			movie.Stop()
			if self.played_flag:
				d = movie.GetEstMovieDuration(1000)
			else:
				d = movie.GetMovieDuration(1000)
			d = float(d) / 1000
			if hasattr(movie, 'GetCurrentTime'):
				t = float(movie.GetCurrentTime(1000)) / 1000
			else:
				# if no GetCurrentTime, act as if at end
				t = d
			looplimit = movie.GetPlayLoopLimit()
			loopcount = movie.GetPlayLoopCount()
			movie.UnbindOpenGLWindow()
			del _mvmap[movie]
			if self.__qid is None and \
			   looplimit != mv.MV_LIMIT_FOREVER and \
			   self._playstate == Channel.PLAYING:
				t = d-t	# time remaining in current loop
				if looplimit > 1:
					# add time of remaining loops
					t = (looplimit - loopcount - 1) * d + t
				self._qid = self._scheduler.enter(
					t, 0, self.playdone, (0,))
		if self.__context:
			self.__context.DestroyContext()
			self.__context = None
		Channel.ChannelWindowAsync.do_hide(self)

	def do_arm(self, node, same=0):
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		file = self.getfileurl(node)
		try:
			f = MMurl.urlretrieve(file)[0]
		except IOError, arg:
			self.errormsg(node, 'Cannot resolve URL "%s": %s' % (file, arg[1]))
			return 1
		if not mv.IsMovieFile(f):
			self.errormsg(node, '%s: Not a movie' % file)
			return 1
		if MMAttrdefs.getattr(node, 'clipbegin') or \
		   MMAttrdefs.getattr(node, 'clipend'):
			flag = 0
		else:
			flag = mv.MV_MPEG1_PRESCAN_OFF
		self.armed_flag = flag
		try:
			self.armed_movie = movie = mv.OpenFile(f, flag)
		except mv.error, msg:
			self.errormsg(node, '%s: %s' % (file, msg))
			return 1
		_mvmap[movie] = self
		movie.SetPlaySpeed(1)
		scale = MMAttrdefs.getattr(node, 'scale')
		self.armed_scale = scale
		center = MMAttrdefs.getattr(node, 'center')
		x, y, w, h = self.window._rect
		track = movie.FindTrackByMedium(mv.DM_IMAGE)
		if scale > 0:
			width = track.GetImageWidth()
			height = track.GetImageHeight()
			self.armed_size = width, height
			width = min(width * scale, w)
			height = min(height * scale, h)
			movie.SetViewSize(width, height)
			width, height = movie.QueryViewSize(width, height)
			if center:
				x = x + (w - width) / 2
				y = self.window._form.height - y - (h + height) / 2
			else:
				y = self.window._form.height - y - h
			movie.SetViewOffset(x, y, mv.DM_TRUE)
		else:
			movie.SetViewSize(w, h)
			# X coordinates don't work, so use GL coordinates
			movie.SetViewOffset(x,
					    self.window._form.height - y - h,
					    mv.DM_TRUE)
			self.armed_size = None
		rate = track.GetImageRate()
		if rate == 30:
			units = 'smpte-30'
		elif rate == 25:
			units = 'smpte-25'
		elif rate == 24:
			units = 'smpte-24'
		else:
			units = 'smpte-30-drop'
		self.__begin = self.getclipbegin(node, units)
		self.__end = self.getclipend(node, units)
		bg = self.getbgcolor(node)
		movie.SetViewBackground(bg)
		self.armed_bg = self.window._convert_color(bg)
		self.armed_loop = self.getloop(node)
		self.armed_duration = MMAttrdefs.getattr(node, 'duration')
		self.armed_display.fgcolor(self.getbucolor(node))
		hicolor = self.gethicolor(node)
		for a in node.GetRawAttrDef('anchorlist', []):
			atype = a[A_TYPE]
			if atype not in SourceAnchors or atype in (ATYPE_AUTO, ATYPE_WHOLE):
				continue
			b = self.armed_display.newbutton((0,0,1,1))
			b.hiwidth(3)
			b.hicolor(hicolor)
			self.setanchor(a[A_ID], a[A_TYPE], b)
		return 1

	def do_play(self, node):
		window = self.window
		self.played_movie = movie = self.armed_movie
		self.armed_movie = None
		if movie is None:
			self.playdone(0)
			return
		self.played_scale = self.armed_scale
		self.played_size = self.armed_size
		self.played_bg = self.armed_bg
		self.played_flag = self.armed_flag
		window.setredrawfunc(self.redraw)
		try:
			movie.BindOpenGLWindow(self.window._form, self.__context)
		except mv.error, msg:
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			windowinterface.showmessage(
				'Cannot play movie node %s on channel %s:\n%s'%
					(name, self._name, msg),
				mtype = 'warning')
			self.playdone(0)
			return
		loop = self.armed_loop
		self.played_loop = loop
		if loop == 0:
			movie.SetPlayLoopLimit(mv.MV_LIMIT_FOREVER)
		else:
			movie.SetPlayLoopLimit(loop)
		if loop != 1:
			movie.SetPlayLoopMode(mv.MV_LOOP_CONTINUOUSLY)
		if self.__begin:
			movie.SetStartFrame(self.__begin)
			movie.SetCurrentFrame(self.__begin)
		if self.__end:
			movie.SetEndFrame(self.__end)
		if self.armed_duration:
			self.__qid = self._scheduler.enter(
				self.armed_duration, 0, self.__stopplay, ())
		movie.Play()
		self.__stopped = 0
		r = Xlib.CreateRegion()
		r.UnionRectWithRegion(0, 0, window._form.width, window._form.height)
		r.SubtractRegion(window._region)
		window._topwindow._do_expose(r)
		if loop == 0 and not self.armed_duration:
			self.playdone(0)

	def __stopplay(self):
		if self.played_movie:
			self.played_movie.Stop()
			self.played_movie.UnbindOpenGLWindow()
			del _mvmap[self.played_movie]
			self.played_movie = None
			self.__qid = None
		self.playdone(0)

	def playstop(self):
		if self.__qid:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		if self.played_movie:
			self.played_movie.Stop()
		self.playdone(1)

	def stopplay(self, node):
		Channel.ChannelWindowAsync.stopplay(self, node)
		if self.played_movie:
			self.played_movie.UnbindOpenGLWindow()
			del _mvmap[self.played_movie]
			self.played_movie = None
		window = self.window
		if window:
			window.setredrawfunc(None)
			window._topwindow._do_expose(window._region)

	def setpaused(self, paused):
		if self.played_movie:
			if paused:
				self.played_movie.Stop()
				self.__stopped = 1
			else:
				self.played_movie.Play()
				self.__stopped = 0

	def redraw(self):
		if self.played_movie:
			self.played_movie.ShowCurrentFrame()

	def resize(self, arg, window, event, value):
		x, y, w, h = window._rect
		movie = self.played_movie
		if not movie:
			return
		scale = self.played_scale
		if scale > 0:
			width, height = self.played_size
			width = min(width * scale, w)
			height = min(height * scale, h)
			movie.SetViewSize(width, height)
			width, height = movie.QueryViewSize(width, height)
			movie.SetViewOffset(x + (w - width) / 2,
					    self.window._form.height - y - (h + height) / 2,
					    mv.DM_TRUE)
		else:
			movie.SetViewSize(w, h)
			movie.SetViewOffset(x,
					    self.window._form.height - y - h,
					    mv.DM_TRUE)
			self.armed_size = None
		movie.ShowCurrentFrame()

	def stopped(self):
		if not self.__stopped:
			if self.__qid:
				return
			self.playdone(0)
