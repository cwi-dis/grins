__version__ = "$Id$"
# XXXX clip_begin and clip_end not yet implemented
from Channel import ChannelWindow, CMIF_MODE
import windowinterface
import time
import MMurl
import MMAttrdefs
import os
import Qt
import QuickTime

QT_AVAILABLE = windowinterface._qtavailable()
if not QT_AVAILABLE:
	Qt = None

debug = 0 # os.environ.has_key('CHANNELDEBUG')

class VideoChannel(ChannelWindow):
	_our_attrs = ['bucolor', 'hicolor', 'scale', 'center', 'project_videotype', 'project_targets']
	node_attrs = ChannelWindow.node_attrs + \
		     ['clipbegin', 'clipend', 'project_videotype', 'project_targets']
	if CMIF_MODE:
		node_attrs = node_attrs + _our_attrs
	else:
		chan_attrs = ChannelWindow.chan_attrs + _our_attrs

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'VideoChannel: init', name
		self.arm_movie = None
		self.play_movie = None
		self.arm_loop = -1
		self.play_loop = -1
		self.has_callback = 0
		self.idleprocactive = 0
		self._paused = 0
		if QT_AVAILABLE:
			Qt.EnterMovies()
		self.DBGcolor = (0xffff, 0, 0)
		self.__rc = None
		
	def do_show(self, pchan):
		if not ChannelWindow.do_show(self, pchan):
			return 0
		try:
			from RealChannel import RealChannel
			self.__rc = RealChannel(self)
		except:
			pass

	def redraw(self):
		if self.play_movie:
			self.play_movie.UpdateMovie()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'VideoChannel: arm', node
		fn = self.getfileurl(node)
		import mimetypes, string
		mtype = mimetypes.guess_type(url)[0]
		node.__type = ''
		if string.find(mtype, 'real') >= 0:
			node.__type = 'real'
			if self.__rc is None:
				self.errormsg(node, 'No playback support for RealVideo in this version')
			else:
				self.__rc.prepare_player(node)
			return 1
		if not QT_AVAILABLE:
			self.errormsg(node, "QuickTime not available")
			return 1
		try:
			fn = MMurl.urlretrieve(fn)[0]
		except IOError, arg:
			if type(arg) == type(()):
				arg = arg[-1]
			self.errormsg(node, 'Cannot open %s: %s'%(fn, arg))
		self.window._macsetwin()
		
		try:
			movieResRef = Qt.OpenMovieFile(fn, 1)
		except (ValueError, Qt.Error), arg:
			if type(arg) == type(()):
				arg = arg[-1]
			self.errormsg(node, 'QuickTime cannot open %s: %s'%(fn, arg))
			return 1
		try:
			self.arm_movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0,
					0)
##					QuickTime.newMovieActive)
		except (ValueError, Qt.Error), arg:
			Qt.CloseMovieFile(movieResRef)
			if type(arg) == type(()):
				arg = arg[-1]
			self.errormsg(node, 'QuickTime cannot parse %s: %s'%(fn, arg))
			return 1
		self.__begin = self.getclipbegin(node, 'sec')
		self.__end = self.getclipend(node, 'sec')
		self.arm_loop = self.getloop(node)
		self.place_movie(node, self.arm_movie)
		self.make_ready(self.arm_movie)
		return 1
		
	def make_ready(self, movie):
		# First convert begin/end to movie times
		dummy, (value, tbrate, base) = movie.GetMovieTime()
		if self.__begin:
			begin = self.__begin*tbrate
		else:
			begin = 0
		if self.__end:
			end = self.__end*tbrate
			dur = end - begin
		else:
			dur = movie.GetMovieDuration()
		# Next preroll
		rate = movie.GetMoviePreferredRate()
		movie.PrerollMovie(begin, rate)
		# Now set active area
		movie.SetMovieActiveSegment(begin, dur)
		# And go to the beginning of it.
		movie.GoToBeginningOfMovie()
##		movie.MoviesTask(0)  
	
	def place_movie(self, node, movie):
		# XXXX This always scales or positions, but it should look at the scale
		# attribute
		self.window._macsetwin()
		screenBox = self.window.qdrect()
		l, t, r, b = movie.GetMovieBox()
		if node:
			scale = MMAttrdefs.getattr(node, 'scale')
			center = MMAttrdefs.getattr(node, 'center')
		else:
			# This happens during a resize: we don't know scale/center anymore.
			scale = 1
			center = 1
		# Compute real scale for scale-to-fit
		if scale <= 0:
			sl, st, sr, sb = screenBox
			print 'movie', l, t, r, b
			print 'screen', sl, st, sr, sb
			if l == r:
				maxxscale = 1  # Empty window, so don't divide by 0
			else:
				maxxscale = float(sr-sl)/(r-l)
			if t == b:
				maxyscale = 1  # Empty window, so don't divide by 0
			else:
				maxyscale = float(sb-st)/(b-t)
			scale = min(maxxscale, maxyscale)
			print 'scale=', scale, maxxscale, maxyscale
				
		movieBox = l, t, int(l+(r-l)*scale), int(t+(b-t)*scale)
		nMovieBox = self._scalerect(screenBox, movieBox, center)
		if nMovieBox != screenBox:
			movie.SetMovieBox(nMovieBox)
		
	def _playsome(self, *dummy):
		if debug: print 'VideoChannel: playsome'
		if not self.play_movie:
			return
		
		if self.play_movie.IsMovieDone():
			if self.play_loop == 0 or self.play_loop > 1:
				# Either looping infinitely, or more loops to be done
				if self.play_loop != 0:
					self.play_loop = self.play_loop - 1
				self.play_movie.GoToBeginningOfMovie()
				return
			self.play_loop = -1	# Truly finished
			self.play_movie.StopMovie()
			self.play_movie = None
			if self.window:
				self.window.setredrawfunc(None)
			self.fixidleproc()
			self.playdone(0)
			
	def do_play(self, node):
		self.__type = node.__type
		if node.__type == 'real':
			if self.__rc is None or not self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
				self.playdone(0)
			return
		if not self.arm_movie:
			if self.play_movie:
				self.play_movie.StopMovie()
			self.play_movie = None
			self.playdone(0)
			return
			
		if debug: print 'VideoChannel: play', node
		self.play_movie = self.arm_movie
		self.play_loop = self.arm_loop
		self.arm_movie = None
		self.arm_loop = -1

		self.play_movie.SetMovieActive(1)
		self.play_movie.MoviesTask(0)
		self.play_movie.StartMovie()
		self.window.setredrawfunc(self.redraw)
		
		self.fixidleproc()
		
	def _scalerect(self, (sl, st, sr, sb), (ml, mt, mr, mb), center):
		maxwidth, maxheight = sr-sl, sb-st
		movwidth, movheight = mr-ml, mb-mt
		if movwidth > maxwidth:
			# Movie is too wide. Scale.
			movheight = movheight*maxwidth/movwidth
			movwidth = maxwidth
		if movheight > maxheight:
			# Movie is too high. Scale.
			movwidth = movwidth*maxheight/movheight
			movheight = maxheight
		if center:
			movleft = (maxwidth-movwidth)/2
			movtop = (maxheight-movheight)/2
		else:
			movleft = movtop = 0
		return sl+movleft, st+movtop, sl+movleft+movwidth, st+movtop+movheight
					
	# We override 'play', since we handle our own duration
	def play(self, node):
		if debug:
			print 'VideoChannel.play('+`self`+','+`node`+')'
		if node.__type == 'real':
			# no special case here for RealVideo
			ChannelWindow.play(self, node)
			return
		self.play_0(node)
		if not self._is_shown or not node.ShouldPlay() or self.syncplay:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()

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
		self.armdone()

	def resize(self, arg, window, event, value):
		ChannelWindow.resize(self, arg, window, event, value)
		if self.arm_movie:
			self.place_movie(self.arm_movie)
		if self.play_movie:
			self.place_movie(self.play_movie)

	def do_hide(self):
		if self.window:
			self.window.setredrawfunc(None)
		self.arm_movie = None
		if self.play_movie:
			self.play_movie.StopMovie()
			self.play_movie = None
			self.fixidleproc()
		if self.__rc is not None:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None

	def playstop(self):
		if debug: print 'VideoChannel: playstop'
		if self.__type == 'real':
			if self.__rc is not None:
				self.__rc.stopit()
		elif self.play_movie:
			self.play_movie.StopMovie()
			self.play_movie = None
			self.fixidleproc()
		self.playdone(1)
		if self.window:
			self.window.setredrawfunc(None)

	def fixidleproc(self):
		if self.window:
			self.window._set_movie_active(not not self.play_movie)
		wantone = not not ((not self._paused) and self.play_movie)
		if wantone == self.idleprocactive:
			return
		if wantone:
			windowinterface.setidleproc(self._playsome)
		else:
			windowinterface.cancelidleproc(self._playsome)
		self.idleprocactive = wantone
		
	def setpaused(self, paused):
		self._paused = paused
		if self.__rc is not None:
			self.__rc.pauseit(paused)
		if self.play_movie:
			if self._paused:
				self.play_movie.StopMovie()
			else:
				self.play_movie.StartMovie()
		self.fixidleproc()

	def _getoswindow(self):
		return self.window._wid

	def _getoswinpos(self):
		x0, y0, x1, y1 = self.window.qdrect()
		return ((x0, y0), (x1-x0, y1-y0))
