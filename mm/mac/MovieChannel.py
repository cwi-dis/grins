from Channel import ChannelWindow
import windowinterface
import time
import urllib
import os
import Qt
import QuickTime

debug = os.environ.has_key('CHANNELDEBUG')

class MovieChannel(ChannelWindow):
	def __repr__(self):
		return '<MacMovieChannel instance, name=' + `self._name` + '>'

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'MovieChannel: init', name
		self.arm_movie = None
		self.play_movie = None
		self.has_callback = 0
		Qt.EnterMovies()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'MovieChannel: arm', node

		fn = self.getfileurl(node)
		fn = urllib.url2pathname(fn)

		movieResRef = Qt.OpenMovieFile(fn, 1)
		self.arm_movie, dummy = Qt.NewMovieFromFile(movieResRef, QuickTime.newMovieActive)

		return 1
		
	def _playsome(self, *dummy):
		if debug: print 'MovieChannel: playsome'
		if not self.play_movie:
			return
		
		self.play_movie.MoviesTask(0)
		
		if self.play_movie.IsMovieDone():
			self.play_movie = None
			# XXXX done callback
			windowinterface.cancelidleproc(self._playsome)
			return
			
	def do_play(self, node):
		if not self.arm_movie:
			self.play_movie = None
			return
			
		if debug: print 'MovieChannel: play', node
		self.play_movie = self.arm_movie
		self.arm_movie = None

		# XXXX Some of these should go to arm...
		movieBox = self.window.qdrect()
		self.play_movie.SetMovieBox(movieBox)
		self.play_movie.GoToBeginningOfMovie()
		self.play_movie.MoviesTask(0)
		self.play_movie.StartMovie()
		
		windowinterface.setidleproc(self._playsome)
		
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

	def playstop(self):
		if debug: print 'MovieChannel: playstop'
		pass # XXXX Stop playing

	def setpaused(self, paused):
		pass # XXXX pause!
