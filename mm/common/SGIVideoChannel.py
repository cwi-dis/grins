__version__ = "$Id$"

import Channel
import MMAttrdefs
from MMExc import *			# exceptions
from AnchorDefs import *
import windowinterface
import MMurl
import mv
import Xlib
import string

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
	_our_attrs = ['bucolor', 'hicolor', 'scale', 'center']
	node_attrs = Channel.ChannelWindowAsync.node_attrs + [
		'clipbegin', 'clipend',
		'project_audiotype', 'project_videotype', 'project_targets',
		'project_perfect', 'project_mobile']
	if Channel.CMIF_MODE:
		node_attrs = node_attrs + _our_attrs
	else:
		chan_attrs = Channel.ChannelWindowAsync.chan_attrs + _our_attrs

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__context = None
		self.played_movie = self.armed_movie = None
		self.__stopped = 0
		self.__qid = None

	def getaltvalue(self, node):
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
			d = d / 1000.0
			if hasattr(movie, 'GetCurrentTime'):
				t = movie.GetCurrentTime(1000) / 1000.0
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
		url = self.getfileurl(node)
		if not url:
			self.errormsg(node, 'No URL set on this node')
			return 1
		try:
			f, hdr = MMurl.urlretrieve(url)
		except IOError, arg:
			self.errormsg(node, 'Cannot resolve URL "%s": %s' % (url, arg[1]))
			return 1
		if string.find(hdr.subtype, 'real') >= 0:
			self.errormsg(node, 'No playback support for RealVideo in this version')
			return 1
		if not mv.IsMovieFile(f):
			self.errormsg(node, '%s: Not a movie' % url)
			return 1
		if MMAttrdefs.getattr(node, 'clipbegin') or \
		   MMAttrdefs.getattr(node, 'clipend'):
			flag = 0
		else:
			flag = mv.MV_MPEG1_PRESCAN_OFF
		flag = 0	# MV_MPEG1_PRESCAN_OFF does not work well
		self.armed_flag = flag
		try:
			self.armed_movie = movie = mv.OpenFile(f, flag)
		except mv.error, msg:
			self.errormsg(node, '%s: %s' % (url, msg))
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
				imbox = float((w - width) / 2)/w, float((h - height) / 2)/h, float(width)/w, float(height)/h
				x = x + (w - width) / 2
				y = self.window._form.height - y - (h + height) / 2
			else:
				imbox = 0, 0, float(width)/w, float(height)/h
				y = self.window._form.height - y - height
			movie.SetViewOffset(x, y, mv.DM_TRUE)
		else:
			imbox = 0, 0, 1, 1
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

		drawbox = MMAttrdefs.getattr(node, 'drawbox')
		if drawbox:
			self.armed_display.fgcolor(self.getbucolor(node))
		else:
			self.armed_display.fgcolor(self.getbgcolor(node))

		self.setArmBox(imbox)
		
# NOW this part is in ChannelWindow.arm_1
			
#		hicolor = self.gethicolor(node)
#		for a in node.GetRawAttrDef('anchorlist', []):
#			atype = a.atype
#			if atype not in SourceAnchors or atype in (ATYPE_AUTO, ATYPE_WHOLE):
#				continue
#			args = a.aargs
#			if len(args) == 0:
#				args = [0,0,1,1]
#			elif len(args) == 4:
#				args = self.convert_args(f, args)
#			if len(args) != 4:
#				print 'VideoChannel: funny-sized anchor'
#				continue
#			x, y, w, h = args[0], args[1], args[2], args[3]
			# convert coordinates from image to window size
#			x = x * imbox[2] + imbox[0]
#			y = y * imbox[3] + imbox[1]
#			w = w * imbox[2]
#			h = h * imbox[3]
#			b = self.armed_display.newbutton((x,y,w,h), times = a.atimes)
#			b.hiwidth(3)
#			if drawbox:
#				b.hicolor(hicolor)
#			self.setanchor(a.aid, a.atype, b, a.atimes)
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
		duration = node.GetAttrDef('duration', None)
		repeatdur = MMAttrdefs.getattr(node, 'repeatdur')
		loop = node.GetAttrDef('loop', None)
		self.played_loop = loop
		if loop is None:
			if repeatdur:
				loop = 0
			else:
				loop = 1
		if loop == 0:
			movie.SetPlayLoopLimit(mv.MV_LIMIT_FOREVER)
		else:
			movie.SetPlayLoopLimit(loop)
		if loop != 1:
			movie.SetPlayLoopMode(mv.MV_LOOP_CONTINUOUSLY)
		begin = 0
		if self.__begin:
			movie.SetStartFrame(self.__begin)
		t0 = self._scheduler.timefunc()
		if t0 > self._played_node.start_time:
			print 'skipping',self._played_node.start_time,t0,t0-self._played_node.start_time
			track = movie.FindTrackByMedium(mv.DM_IMAGE)
			movie.SetCurrentFrame(self.__begin + (t0 - self._played_node.start_time) * track.GetImageRate())
		begin = movie.GetStartTime(1000) / 1000.0
		if self.__end:
			movie.SetEndFrame(self.__end)
			end = movie.GetEndTime(1000) / 1000.0
		else:
			end = 0
		if duration is not None and duration > 0 and \
		   (not end or (end > begin and duration < end - begin)):
			movie.SetEndTime(long(1000L * (begin + duration)), 1000)
		elif duration is not None:
			# XXX need special code to freeze temporarily at
			# the end of each loop
			pass
		if repeatdur > 0:
			self.__qid = self._scheduler.enter(
				repeatdur, 0, self.__stopplay, ())
		self.event('beginEvent')
		movie.Play()
		self.__stopped = 0
		r = Xlib.CreateRegion()
		r.UnionRectWithRegion(0, 0, window._form.width, window._form.height)
		r.SubtractRegion(window._region)
		window._topwindow._do_expose(r)
		if loop == 0 and not repeatdur:
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

	def stopplay(self, node, no_extend = 0):
		if node and self._played_node is not node:
##			print 'node was not the playing node '+`self,node,self._played_node`
			return
		Channel.ChannelWindowAsync.stopplay(self, node, no_extend)
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
				if paused == 'hide':
					self.played_movie.UnbindOpenGLWindow()
				self.__stopped = 1
			else:
				if self._paused == 'hide':
					self.played_movie.BindOpenGLWindow(self.window._form, self.__context)
				self.played_movie.Play()
				self.__stopped = 0
		self._paused = paused

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

	# Convert pixel offsets into relative offsets.
	# If the offsets are in the range [0..1], we don't need to do
	# the conversion since the offsets are already fractions of
	# the image.
#	def convert_args(self, file, args):
#		need_conversion = 1
#		for a in args:
#			if a != int(a):	# any floating point number
#				need_conversion = 0
#				break
#		if not need_conversion:
#			return args
#		if args == (0, 0, 1, 1) or args == [0, 0, 1, 1]:
			# special case: full image
#			return args
#		import Sizes
#		xsize, ysize = Sizes.GetSize(file)
#		return float(args[0]) / float(xsize), \
#		       float(args[1]) / float(ysize), \
#		       float(args[2]) / float(xsize), \
#		       float(args[3]) / float(ysize)
