__version__ = "$Id$"

# XXXX Movie disposal
# XXXX Resizing
# XXXX Stop play
# XXXX Pause play
# XXXX ExitMovies?
#
from Channel import ChannelWindow
import windowinterface
import time
import MMurl
import os
import Qt
import QuickTime

debug = 0 # os.environ.has_key('CHANNELDEBUG')

class MovieChannel(ChannelWindow):
	def __repr__(self):
		return '<MacMovieChannel instance, name=' + `self._name` + '>'

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'MovieChannel: init', name
		self.arm_movie = None
		self.play_movie = None
		self.has_callback = 0
		self.idleprocactive = 0
		Qt.EnterMovies()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'MovieChannel: arm', node

		fn = self.getfileurl(node)
		fn = MMurl.url2pathname(fn)
		
		try:
			movieResRef = Qt.OpenMovieFile(fn, 1)
		except (ValueError, Qt.Error), arg:
			self.errormsg(node, 'Cannot open: '+`arg`)
			return 1
		self.arm_movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0,
					QuickTime.newMovieActive)
		rate = self.arm_movie.GetMoviePreferredRate()
		self.arm_movie.PrerollMovie(0, rate)
		return 1
		
	def _playsome(self, *dummy):
		if debug: print 'MovieChannel: playsome'
		if not self.play_movie:
			return
		
		self.play_movie.MoviesTask(0)
		
		if self.play_movie.IsMovieDone():
			self.play_movie = None
			windowinterface.cancelidleproc(self._playsome)
			self.playdone(0)
			
	def do_play(self, node):
		if not self.arm_movie:
			self.play_movie = None
			self.playdone(0)
			return
			
		if debug: print 'MovieChannel: play', node
		self.play_movie = self.arm_movie
		self.arm_movie = None

		# XXXX Some of these should go to arm...
		self.window._macsetwin()
		screenBox = self.window.qdrect()
		movieBox = self.play_movie.GetMovieBox()
##		print 'SCREEN', screenBox, 'MOVIE', movieBox
		movieBox = self._scalerect(screenBox, movieBox)
##		print 'SET', movieBox
		self.play_movie.SetMovieBox(movieBox)
		self.play_movie.GoToBeginningOfMovie()
##		self.play_movie.MoviesTask(0) # This appears to be a bad idea...
		self.play_movie.StartMovie()
		
		windowinterface.setidleproc(self._playsome)
		
	def _scalerect(self, (sl, st, sr, sb), (ml, mt, mr, mb)):
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
		movleft = (maxwidth-movwidth)/2
		movtop = (maxheight-movheight)/2
		return sl+movleft, st+movtop, sl+movleft+movwidth, st+movtop+movheight
					
	# We override 'play', since we handle our own duration
	def play(self, node):
		if debug:
			print 'MacMovieChannel.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()

		self.played_display = self.armed_display
		self.armed_display = None
		self.do_play(node)
		self.armdone()

	def resize(self, arg, window, event, value):
		print 'MovieChannel: Resized, this will go wrong....'
		ChannelWindow.resize(self, arg, window, event, value)

	def do_hide(self):
		self.arm_movie = None
		if self.play_movie:
			self.play_movie.StopMovie()
			windowinterface.cancelidleproc(self._playsome)
			self.play_movie = None

	def playstop(self):
		if debug: print 'MovieChannel: playstop'
		if self.play_movie:
			self.play_movie.StopMovie()
			windowinterface.cancelidleproc(self._playsome)
		self.playdone(1)
		self.play_movie = None

	def setpaused(self, paused):
		pass # XXXX pause!
