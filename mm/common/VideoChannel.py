__version__ = "$Id$"

import Channel
import MMAttrdefs
from MMExc import *			# exceptions
from AnchorDefs import *
import windowinterface
import urllib
import Xlib

class VideoChannel(Channel.ChannelWindowAsync):
	node_attrs = Channel.ChannelWindowAsync.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'loop']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__context = None
		self.played_movie = self.armed_movie = None
		self.__stopped = 0
		self.__qid = None

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
		self.__context = widget.CreateContext(visual, None, GL_TRUE)

	def do_hide(self):
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
			f = urllib.urlretrieve(file)[0]
		except IOError, arg:
			self.errormsg(node, 'Cannot resolve URL "%s": %s' % (file, arg[1]))
			return 1
		if not mv.IsMovieFile(f):
			self.errormsg(node, '%s: Not a movie' % file)
			return 1
		try:
			self.armed_movie = movie = mv.OpenFile(f, 0)
		except mv.error, msg:
			self.errormsg(node, '%s: %s' % (file, msg))
			return 1
		_mvmap[movie] = self
		movie.SetPlaySpeed(1)
		scale = MMAttrdefs.getattr(node, 'scale')
		self.armed_scale = scale
		x, y, w, h = self.window._rect
		if scale > 0:
			track = movie.FindTrackByMedium(mv.DM_IMAGE)
			width = track.GetImageWidth()
			height = track.GetImageHeight()
			self.armed_size = width, height
			width = min(width * scale, w)
			height = min(height * scale, h)
			movie.SetViewSize(width, height)
			width, height = movie.QueryViewSize(width, height)
			movie.SetViewOffset(x + (w - width) / 2,
					    self.window._form.height - y - (h + height) / 2,
					    mv.DM_TRUE)
		else:
			movie.SetViewSize(w, h)
			# X coordinates don't work, so use GL coordinates
			movie.SetViewOffset(x,
					    self.window._form.height - y - h,
					    mv.DM_TRUE)
			self.armed_size = None
		bg = self.getbgcolor(node)
		movie.SetViewBackground(bg)
		self.armed_bg = self.window._convert_color(bg)
		self.armed_loop = self.getloop(node)
		self.armed_duration = MMAttrdefs.getattr(node, 'duration')
		try:
			alist = node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
			alist = []
		self.armed_display.fgcolor(self.getbucolor(node))
		hicolor = self.gethicolor(node)
		for a in alist:
			if a[A_TYPE] in DestOnlyAnchors:
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
		window.setredrawfunc(self.redraw)
		movie.BindOpenGLWindow(self.window._form, self.__context)
		loop = self.armed_loop
		if loop == 0:
			movie.SetPlayLoopLimit(mv.MV_LIMIT_FOREVER)
		else:
			movie.SetPlayLoopLimit(loop)
		if loop != 1:
			movie.SetPlayLoopMode(mv.MV_LOOP_CONTINUOUSLY)
		if self.armed_duration:
			self.__qid = self._scheduler.enter(
				self.armed_duration, 0, self.__stopplay, ())
		movie.Play()
		self.__stopped = 0
		r = Xlib.CreateRegion()
		r.UnionRectWithRegion(0, 0, window._form.width, window._form.height)
		r.SubtractRegion(window._region)
		window._topwindow._do_expose(r)

	def __stopplay(self):
		if self.played_movie:
			self.played_movie.Stop()
			self.played_movie = None
			self.__qid = None
			self.playdone(0)

	def playstop(self):
		if self.__qid:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		if self.played_movie:
			self.played_movie.Stop()
			self.played_movie = None
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
			self.__qid = None
			self.played_movie = None
			self.playdone(0)

def _selcb():
	while mv.PendingEvents():
		event = mv.NextEvent()
		if event[0] == mv.MV_EVENT_STOP:
			if _mvmap.has_key(event[1]):
				_mvmap[event[1]].stopped()

try:
	import mv, glX
	from glconst import *
	from glXconst import *
except ImportError:
	from MpegChannel import *
	VideoChannel = MpegChannel
else:
	_fd = mv.GetEventFD()
	windowinterface.select_setcallback(_fd, _selcb, ())
	mv.SetSelectEvents(mv.MV_EVENT_MASK_STOP)

	_mvmap = {}			# map of MVid to channel
