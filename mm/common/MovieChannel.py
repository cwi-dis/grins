__version__ = "$Id$"

from Channel import ChannelWindowThread
import urllib

class MovieChannel(ChannelWindowThread):
	def threadstart(self):
		import moviechannel
		return moviechannel.init()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		import MMAttrdefs, GLLock, VFile
		filename = self.getfileurl(node)
		filename = urllib.urlretrieve(filename)[0]
		try:
			vfile = VFile.RandomVinFile(filename)
		except (EOFError, IOError, VFile.Error), msg:
			if type(msg) is type(()):
				msg = msg[1]
			self.errormsg(node, filename + ':\n' + msg)
			print 'Error: ' + filename + ': ' + msg
			return 1
##		except IOError, msg:
##			print 'IO Error: ' + `msg`
##			return 1
		try:
			vfile.readcache()
		except VFile.Error:
			print `filename` + ': no cached index'
		arminfo = {'width': vfile.width,
			   'height': vfile.height,
			   'format': vfile.format,
			   'index': vfile.index,
			   'c0bits': vfile.c0bits,
			   'c1bits': vfile.c1bits,
			   'c2bits': vfile.c2bits,
			   'offset': vfile.offset,
			   'scale': MMAttrdefs.getattr(node, 'scale'),
			   'bgcolor': self.getbgcolor(node)}
		if vfile.format == 'compress':
			arminfo['compressheader'] = vfile.compressheader
		try:
			self.threads.arm(vfile.fp, 0, 0, arminfo, None,
				  self.syncarm)
		except RuntimeError, msg:
			print 'Bad movie file', `vfile.filename`, msg
			return 1
		return self.syncarm
