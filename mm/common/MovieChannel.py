from Channel import ChannelWindowThread

class MovieChannel(ChannelWindowThread):
	def __repr__(self):
		return '<MovieChannel instance, name=' + `self._name` + '>'

	def threadstart(self):
		import moviechannel
		return moviechannel.init()

	def do_arm(self, node):
		filename = self.getfilename(node)
		try:
			import VFile
			vfile = VFile.RandomVinFile().init(filename)
		except EOFError:
			print 'Empty movie file', `filename`
			return 1
		try:
			vfile.readcache()
		except VFile.Error:
			print `filename` + ': no cached index'
		try:
			import MMAttrdefs, GLLock
			self.threads.arm(vfile.fp, 0, 0, \
				  {'width': vfile.width, \
				   'height': vfile.height, \
				   'format': vfile.format, \
				   'index': vfile.index, \
				   'c0bits': vfile.c0bits, \
				   'c1bits': vfile.c1bits, \
				   'c2bits': vfile.c2bits, \
				   'offset': vfile.offset, \
				   'scale': MMAttrdefs.getattr(node, 'scale'), \
				   'wid': self.window._window_id, \
				   'bgcolor': self.getbgcolor(node), \
				   'gl_lock': GLLock.gl_lock}, \
				  None, self.syncarm)
		except RuntimeError, msg:
			print 'Bad movie file', `vfile.filename`, msg
			return 1
		return 0
