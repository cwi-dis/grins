from Channel import *
from MMExc import *			# exceptions
from AnchorDefs import *

class ImageChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + ['scale', 'scalefilter']

	def init(self, name, attrdict, scheduler, ui):
		return ChannelWindow.init(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<ImageChannel instance, name=' + `self._name` + '>'

	def do_arm(self, node):
		f = self.getfilename(node)
		# remember coordinates for anchor editing (and only for that!)
		try:
			self._arm_imbox = self.armed_display.display_image_from_file(f)
		except IOError, msg:
			msg = f + ':\n' + msg[1]
			parms = self.armed_display.fitfont('Times-Roman', msg)
			w, h = self.armed_display.strsize(msg)
			self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
			self.armed_display.fgcolor(255, 0, 0)		# red
			box = self.armed_display.writestr(msg)
			return 1
		try:
			alist = node.GetRawAttr('anchorlist')
			modanchorlist(alist)
		except NoSuchAttrError:
			alist = []
		self.armed_display.fgcolor(self.gethicolor(node))
		for a in alist:
			args = a[A_ARGS]
			if len(args) == 0:
				args = [0,0,1,1]
			elif len(args) == 4:
				args = self.convert_args(f, args)
			if len(args) != 4:
				print 'ImageChannel: funny-sized anchor'
				continue
			x, y, w, h = args[0], args[1], args[2], args[3]
			# convert coordinates from image size to window size
			x = x * self._arm_imbox[2] + self._arm_imbox[0]
			y = y * self._arm_imbox[3] + self._arm_imbox[1]
			w = w * self._arm_imbox[2]
			h = h * self._arm_imbox[3]
			b = self.armed_display.newbutton(x, y, w, h)
			b.hiwidth(3)
##			b.hicolor(self.getfgcolor(node))
			self.setanchor(a[A_ID], a[A_TYPE], b)
		return 1

	def defanchor(self, node, anchor):
		import boxes, windowinterface
		if self._armstate != AIDLE:
			raise error, 'Arm state must be idle when defining an anchor'
		if self._playstate != PIDLE:
			raise error, 'Play state must be idle when defining an anchor'
		windowinterface.setcursor('watch')
		context = AnchorContext().init()
		self.startcontext(context)
		self.syncarm = 1
		self.arm(node)
		self.syncplay = 1
		self.play(node)
		self._playstate = PLAYED
		self.syncarm = 0
		self.syncplay = 0
		box = anchor[2]
		windowinterface.setcursor('')
		msg = 'Draw anchor in ' + self._name + '.'
		if box == []:
			box = boxes.create_box(self.window, msg)
		else:
			box = self.convert_args(self.getfilename(node), box)
			# convert coordinates from image size to window size.
			x = box[0] * self._arm_imbox[2] + self._arm_imbox[0]
			y = box[1] * self._arm_imbox[3] + self._arm_imbox[1]
			w = box[2] * self._arm_imbox[2]
			h = box[3] * self._arm_imbox[3]
			box = boxes.create_box(self.window, msg, (x, y, w, h))
		self.stopcontext(context)
		if box:
			# convert coordinates from window size to image size.
			x = (box[0] - self._arm_imbox[0]) / self._arm_imbox[2]
			y = (box[1] - self._arm_imbox[1]) / self._arm_imbox[3]
			w = box[2] / self._arm_imbox[2]
			h = box[3] / self._arm_imbox[3]
			return (anchor[0], anchor[1], [x, y, w, h])
		return None

	# Hack to convert pixel offsets into relative offsets and to make
	# the coordinates relative to the upper-left corner instead of
	# lower-left.  This only works for RGB images.
	# If the offsets are in the range [0..1], we don't need to do
	# the conversion since the offsets are already fractions of
	# the image.
	def convert_args(self, file, args):
		need_conversion = 0
		for a in args:
			if a > 1:
				need_conversion = 1
				break
		if not need_conversion:
			return args
		xsize, ysize = self.window._image_size(file)
		x0, y0, x1, y1 = args[0], args[1], args[2], args[3]
		y0 = ysize - y0
		y1 = ysize - y1
		if x0 > x1:
			x0, x1 = x1, x0
		if y0 > y1:
			y0, y1 = y1, y0
		return float(x0)/float(xsize), float(y0)/float(ysize), \
			  float(x1-x0)/float(xsize), float(y1-y0)/float(ysize)
