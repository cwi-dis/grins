from Channel import ChannelWindowThread

class MpegChannel(ChannelWindowThread):
	def __repr__(self):
		return '<MpegChannel instance, name=' + `self._name` + '>'

	def threadstart(self):
		import mpegchannel
		return mpegchannel.init()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		filename = self.getfilename(node)
		try:
			fp = open(filename, 'r')
		except IOError, msg:
			if type(msg) == type(()):
				msg = msg[1]
			self.errormsg(node, filename + ':\n' + msg)
			return 1
		except IOError, msg:
			print 'IO Error: ' + `msg`
			return 1
		try:
			import MMAttrdefs, GLLock
			arminfo = {'scale': MMAttrdefs.getattr(node, 'scale'),
				   'bgcolor': self.getbgcolor(node)}
			self.threads.arm(fp, 0, 0, arminfo, None,
				  self.syncarm)
		except RuntimeError, msg:
			print 'Bad mpeg file', `filename`, msg
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
		self.need_armdone = 0
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()
		if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
#		else:
#			self.armed_display.render()
#		if self.played_display:
#			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		thread_play_called = 0
		if self.threads.armed:
			self.window.setredrawfunc(self.threads.resized)
			self.threads.play()
			thread_play_called = 1
		self.do_play(node)
		self.need_armdone = 1
		if not thread_play_called:
			self.playdone(0)

	def playdone(self, dummy):
		if self.need_armdone:
			self.armdone()
			self.need_armdone = 0
		ChannelWindowThread.playdone(self, dummy)
