__version__ = "$Id$"

try:
	import mv
except ImportError:
	import MpegChannel
	VideoChannel = MpegChannel.MpegChannel
else:
	import Channel
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
		def __init__(self, name, attrdict, scheduler, ui):
			windowinterface.toplevel._main.Display().Synchronize(1)
			Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
			self.__context = None
			self.__widget = None
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
			return 1

		def __ginitCB(self, widget, visual, calldata):
			self.__context = widget.CreateContext(visual, None, GL_TRUE)

		def __exposeCB(self, widget, userdata, calldata):
			if self.played_movie:
				self.played_movie.ShowCurrentFrame()

		def do_hide(self):
			if self.__context:
				self.__context.DestroyContext()
				self.__context = None
			if self.__widget:
				self.__widget.DestroyWidget()
				self.__widget = None
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
			self.armed_movie = mv.OpenFile(f, 0)
			_mvmap[self.armed_movie] = self
			self.armed_movie.SetPlaySpeed(1)
			return 1

		def do_play(self, node):
			self.played_movie = self.armed_movie
			self.armed_movie = None
			if self.played_movie is None:
				self.playdone(0)
				return
			self.__widget.MapWidget()
			self.played_movie.BindOpenGLWindow(self.__widget, self.__context)
			w, h = self.window._rect[2:]
			self.played_movie.SetViewSize(w, h)
			self.played_movie.SetViewBackground(self.getbgcolor(node))
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
			if self.played_movie:
				self.played_movie.SetViewSize(w, h)

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
