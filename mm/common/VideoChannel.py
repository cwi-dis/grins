__version__ = "$Id$"

try:
	import mv, glX
except ImportError:
	import MpegChannel
	VideoChannel = MpegChannel.MpegChannel
else:
	import Channel
	import MMAttrdefs
	import windowinterface
	import urllib
	import mv
	import glX
	from glconst import *
	from glXconst import *

	def _selcb():
		while mv.PendingEvents():
			event = mv.NextEvent()
			if event[0] == mv.MV_EVENT_STOP:
				_mvmap[event[1]].stopped()

	_fd = mv.GetEventFD()
	windowinterface.select_setcallback(_fd, _selcb, ())
	mv.SetSelectEvents(mv.MV_EVENT_MASK_STOP)

	_mvmap = {}				# map of MVid to channel

	class VideoChannel(Channel.ChannelWindowAsync):
		node_attrs = Channel.ChannelWindowAsync.node_attrs + ['scale']

		def __init__(self, name, attrdict, scheduler, ui):
			windowinterface.toplevel._main.Display().Synchronize(1)
			Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
			self.__context = None
			self.__widget = None
			self.__gc = None
			self.played_movie = self.armed_movie = None
			self.__stopped = 0

		def do_show(self, pchan):
			if not Channel.ChannelWindowAsync.do_show(self, pchan):
				return 0
			window = self.window
			x, y, w, h = window._rect
			widget = window._form.CreateMDrawingArea('video',
						{'x': x, 'y': y,
						 'width': w, 'height': h,
						 'visualInfo': window._visual,
						 'colormap': window._colormap,
						 'mappedWhenManaged': 0})
			self.__widget = widget
			widget.AddCallback('ginitCallback', self.__ginitCB,
					   window._visual)
			widget.AddCallback('exposeCallback', self.__exposeCB, None)
			widget.ManageChild()
			self.__gc = widget.CreateGC({})
			return 1

		def __ginitCB(self, widget, visual, calldata):
			self.__context = widget.CreateContext(visual, None, GL_TRUE)

		def __exposeCB(self, widget, userdata, calldata):
			if self.played_movie:
				w, h = self.window._rect[2:4]
				self.__gc.foreground = self.played_bg
				self.__gc.FillRectangle(0, 0, w, h)
				self.played_movie.ShowCurrentFrame()

		def do_hide(self):
			if self.__context:
				self.__context.DestroyContext()
				self.__context = None
			if self.__widget:
				self.__widget.DestroyWidget()
				self.__widget = None
				self.__gc = None
			Channel.ChannelWindowAsync.do_hide(self)

		def do_arm(self, node, same=0):
			if same and self.armed_display:
				return 1
			if node.type != 'ext':
				self.errormsg(node, 'Node must be external')
				return 1
			file = self.getfileurl(node)
			f = urllib.urlretrieve(file)[0]
			if not mv.IsMovieFile(f):
				self.errormsg(node, '%s: Not a movie' % file)
				return 1
			self.armed_movie = movie = mv.OpenFile(f, 0)
			_mvmap[movie] = self
			movie.SetPlaySpeed(1)
			scale = MMAttrdefs.getattr(node, 'scale')
			self.armed_scale = scale
			w, h = self.window._rect[2:]
			if scale > 0:
				track = movie.FindTrackByMedium(mv.DM_IMAGE)
				width = track.GetImageWidth()
				height = track.GetImageHeight()
				self.armed_size = width, height
				movie.SetViewSize(width * scale,
						  height * scale)
				width, height = movie.QueryViewSize(
					width * scale, height * scale)
				movie.SetViewOffset((w - width) / 2,
						    (h - height) / 2,
						    mv.DM_TRUE)
			else:
				movie.SetViewSize(w, h)
				self.armed_size = None
			bg = self.getbgcolor(node)
			movie.SetViewBackground(bg)
			self.armed_bg = self.window._convert_color(bg)
			return 1

		def do_play(self, node):
			self.played_movie = self.armed_movie
			self.armed_movie = None
			self.played_scale = self.armed_scale
			self.played_size = self.armed_size
			self.played_bg = self.armed_bg
			if self.played_movie is None:
				self.playdone(0)
				return
			self.__gc.foreground = self.played_bg
			w, h = self.window._rect[2:4]
			self.__gc.FillRectangle(0, 0, w, h)
			self.__widget.MapWidget()
			self.played_movie.BindOpenGLWindow(self.__widget, self.__context)
			self.played_movie.Play()
			self.__stopped = 0

		def playstop(self):
			if self.played_movie:
				self.played_movie.Stop()
			self.playdone(1)

		def stopplay(self, node):
			Channel.ChannelWindowAsync.stopplay(self, node)
			if self.played_movie:
				self.played_movie.UnbindOpenGLWindow()
				del _mvmap[self.played_movie]
				self.played_movie = None
			if self.__widget:
				self.__widget.UnmapWidget()

		def resize(self, arg, window, event, value):
			x, y, w, h = window._rect
			if self.__widget:
				self.__widget.SetValues({'x': x, 'y': y,
							 'width': w, 'height': h})
			movie = self.played_movie
			if not movie:
				return
			scale = self.played_scale
			if scale > 0:
				width, height = self.played_size
				movie.SetViewSize(width * scale,
						  height * scale)
				width, height = movie.QueryViewSize(
					width * scale, height * scale)
				movie.SetViewOffset((w - width) / 2,
						    (h - height) / 2,
						    mv.DM_TRUE)
			else:
				movie.SetViewSize(w, h)
			self.__gc.foreground = self.played_bg
			self.__gc.FillRectangle(0, 0, w, h)
			movie.ShowCurrentFrame()

		def setpaused(self, paused):
			if self.played_movie:
				if paused:
					self.played_movie.Stop()
					self.__stopped = 1
				else:
					self.played_movie.Play()
					self.__stopped = 0

		def stopped(self):
			if not self.__stopped:
				self.playdone(0)
