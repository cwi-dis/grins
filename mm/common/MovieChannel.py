from Channel import ChannelWindowThread

class MovieChannel(ChannelWindowThread):
	def __repr__(self):
		return '<MovieChannel instance, name=' + `self._name` + '>'

	def threadstart(self):
		import moviechannel
		return moviechannel.init()

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
			import VFile
			vfile = VFile.RandomVinFile().init(filename)
		except (EOFError, VFile.Error), msg:
			if type(msg) == type(()):
				msg = msg[1]
			self.errormsg(filename + ':\n' + msg)
			return 1
		except IOError, msg:
			print 'IO Error: ' + `msg`
			return 1
		try:
			vfile.readcache()
		except VFile.Error:
			print `filename` + ': no cached index'
		try:
			import MMAttrdefs, GLLock
			arminfo = {'width': vfile.width,
				   'height': vfile.height,
				   'format': vfile.format,
				   'index': vfile.index,
				   'c0bits': vfile.c0bits,
				   'c1bits': vfile.c1bits,
				   'c2bits': vfile.c2bits,
				   'offset': vfile.offset,
				   'scale': MMAttrdefs.getattr(node, 'scale'),
				   'wid': self.window._window_id,
				   'bgcolor': self.getbgcolor(node),
				   'gl_lock': GLLock.gl_rawlock}
			if vfile.format == 'compress':
				arminfo['compressheader'] = vfile.compressheader
			self.threads.arm(vfile.fp, 0, 0, arminfo, None,
				  self.syncarm)
		except RuntimeError, msg:
			print 'Bad movie file', `vfile.filename`, msg
			return 1
		return self.syncarm
