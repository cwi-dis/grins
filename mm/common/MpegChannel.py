from Channel import ChannelWindowThread

class MpegChannel(ChannelWindowThread):
	def __repr__(self):
		return '<MpegChannel instance, name=' + `self._name` + '>'

	def threadstart(self):
		import mpegchannel
		return mpegchannel.init()

	def errormsg(self, msg):
		parms = self.armed_display.fitfont('Times-Roman', msg)
		w, h = self.armed_display.strsize(msg)
		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
		self.armed_display.fgcolor(255, 0, 0)		# red
		box = self.armed_display.writestr(msg)

	def do_arm(self, node):
		if node.type != 'ext':
			self.errormsg('node must be external')
			return 1
		filename = self.getfilename(node)
		try:
			fp = open(filename, 'r')
		except IOError, msg:
			if type(msg) == type(()):
				msg = msg[1]
			self.errormsg(filename + ':\n' + msg)
			return 1
		except IOError, msg:
			print 'IO Error: ' + `msg`
			return 1
		try:
			import MMAttrdefs, GLLock
			arminfo = {'scale': MMAttrdefs.getattr(node, 'scale'),
				   'wid': self.window._window_id,
				   'bgcolor': self.getbgcolor(node),
				   'gl_lock': GLLock.gl_rawlock}
			self.threads.arm(fp, 0, 0, arminfo, None,
				  self.syncarm)
		except RuntimeError, msg:
			print 'Bad mpeg file', `vfile.filename`, msg
			return 1
		return self.syncarm

	#
	# It appears that there is a bug in the cl mpeg decompressor
	# which disallows the use of two mpeg decompressors in parallel.
	#
	# Redefining play() and playdone() doesn't really solve the problem,
	# since two mpeg channels will still cause trouble,
	# but it will solve the common case of arming the next file while
	# the current one is playing.
	#
	# XXXX This problem has to be reassesed with the 5.2 cl. See also
	# the note in mpegchannelmodule.c
	#
	def play(self, node):
		self.play_0(node)
		if not self.is_showing() or self.syncplay:
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
			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		thread_play_called = 0
		if self.threads.armed:
			self.threads.play()
			thread_play_called = 1
		self.do_play(node)
		if not thread_play_called:
			self.playdone(0)

	def playdone(self, dummy):
		self.armdone()
		ChannelWindowThread.playdone(self, dummy)
