__version__ = "$Id$"

from ChannelThread import ChannelWindowThread, CMIF_MODE
import MMurl
from MMExc import *			# exceptions
from AnchorDefs import *


class VideoChannel(ChannelWindowThread):
	attrs = ['bucolor', 'hicolor', 'scale', 'project_videotype', 'project_targets']
	node_attrs = ChannelWindowThread.node_attrs + [
		'clipbegin', 'clipend',
		'project_audiotype', 'project_videotype', 'project_targets',
		'project_perfect', 'project_mobile']
	if CMIF_MODE:
		node_attrs = node_attrs + attrs
	else:
		chan_attrs = ChannelWindowThread.chan_attrs + attrs

	def threadstart(self):
		import mpegchannel
		return mpegchannel.init()

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
			filename = MMurl.urlretrieve(url)[0]
			fp = open(filename, 'rb')
		except IOError, msg:
			self.errormsg(node, url + ':\n' + msg[1])
			return 1
		try:
			import MMAttrdefs, GLLock
			arminfo = {'scale': float(MMAttrdefs.getattr(node, 'scale')),
				   'bgcolor': self.getbgcolor(node),
				   'center': MMAttrdefs.getattr(node, 'center'),
				   }
			self.threads.arm(fp, 0, 0, arminfo, None,
				  self.syncarm)
		except RuntimeError, msg:
			if type(msg) is type(self):
				msg = msg.args[0]
			print 'Bad mpeg file', `url`, msg
			return 1

		drawbox = MMAttrdefs.getattr(node, 'drawbox')
		if drawbox:
			self.armed_display.fgcolor(self.getbucolor(node))
		else:
			self.armed_display.fgcolor(self.getbgcolor(node))
		hicolor = self.gethicolor(node)
		for a in node.GetRawAttrDef('anchorlist', []):
			atype = a[A_TYPE]
			if atype not in SourceAnchors or atype == ATYPE_AUTO:
				continue
			args = a[A_ARGS]
			if len(args) == 0:
				args = [0,0,1,1]
			elif len(args) == 4:
				args = self.convert_args(f, args)
			if len(args) != 4:
				print 'VideoChannel: funny-sized anchor'
				continue
			x, y, w, h = args[0], args[1], args[2], args[3]
##			# convert coordinates from image to window size
##			x = x * self._arm_imbox[2] + self._arm_imbox[0]
##			y = y * self._arm_imbox[3] + self._arm_imbox[1]
##			w = w * self._arm_imbox[2]
##			h = h * self._arm_imbox[3]
			b = self.armed_display.newbutton((x,y,w,h), times = a[A_TIMES])
			b.hiwidth(3)
			if drawbox:
				b.hicolor(hicolor)
			self.setanchor(a[A_ID], a[A_TYPE], b, a[A_TIMES])
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
		import windowinterface
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [0,0,1,1], anchor[3]))

	def stoparm(self):
		self.need_armdone = 0
		ChannelWindowThread.stoparm(self)

	# Convert pixel offsets into relative offsets.
	# If the offsets are in the range [0..1], we don't need to do
	# the conversion since the offsets are already fractions of
	# the image.
	def convert_args(self, file, args):
		need_conversion = 1
		for a in args:
			if a != int(a):	# any floating point number
				need_conversion = 0
				break
		if not need_conversion:
			return args
		if args == (0, 0, 1, 1) or args == [0, 0, 1, 1]:
			# special case: full image
			return args
		import Sizes
		xsize, ysize = Sizes.GetSize(file)
		return float(args[0]) / float(xsize), \
		       float(args[1]) / float(ysize), \
		       float(args[2]) / float(xsize), \
		       float(args[3]) / float(ysize)
