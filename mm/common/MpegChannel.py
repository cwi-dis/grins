from Channel import ChannelWindowThread
import urllib
import windowinterface
from MMExc import *			# exceptions
from AnchorDefs import *


class MpegChannel(ChannelWindowThread):
	node_attrs = ChannelWindowThread.node_attrs + ['bucolor', 'hicolor']

	def threadstart(self):
		import mpegchannel
		return mpegchannel.init()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		filename = self.getfileurl(node)
		try:
			filename = urllib.urlretrieve(filename)[0]
			fp = open(filename, 'rb')
		except IOError, msg:
			if type(msg) is type(()):
				msg = msg[1]
			self.errormsg(node, filename + ':\n' + msg)
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

		try:
			alist = node.GetRawAttr('anchorlist')
			modanchorlist(alist)
		except NoSuchAttrError:
			alist = []
		for a in alist:
			b = self.armed_display.newbutton((0,0,1,1))
			#b.hiwidth(3)
			#b.hicolor(hicolor)
			self.setanchor(a[A_ID], a[A_TYPE], b)
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
		else:
			self.armed_display.render()
		if self.played_display:
			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		thread_play_called = 0
		if self.threads.armed:
			w = self.window
			w.setredrawfunc(self.do_redraw)
			try:
				w._gc.SetRegion(w._clip)
				w._gc.foreground = w._convert_color(self.getbgcolor(node))
			except AttributeError:
				pass
			self.threads.play()
			thread_play_called = 1
		if self._is_shown:
			self.do_play(node)
		self.need_armdone = 1
		if not thread_play_called:
			self.playdone(0)

	def playdone(self, dummy):
		if self.need_armdone:
			self.armdone()
			self.need_armdone = 0
		ChannelWindowThread.playdone(self, dummy)

	def defanchor(self, node, anchor, cb):
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [0,0,1,1]))
