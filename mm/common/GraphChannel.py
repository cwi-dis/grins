from Channel import *
from MMExc import *			# exceptions
from AnchorDefs import *
import windowinterface			# for windowinterface.error
import string
from urllib import urlopen

XBORDER = 0.05
YBORDER = 0.05

XOFF = XBORDER
YOFF = YBORDER

XRANGE = (1.0-2*XBORDER)
YRANGE = (1.0-2*YBORDER)

class GraphChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + ['gtype', 'fgcolor', 'align',
						 'axis']

	def init(self, name, attrdict, scheduler, ui):
		return ChannelWindow.init(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<GraphChannel instance, name=' + `self._name` + '>'

	def errormsg(self, msg):
		parms = self.armed_display.fitfont('Times-Roman', msg)
		w, h = self.armed_display.strsize(msg)
		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
		self.armed_display.fgcolor(255, 0, 0)		# red
		box = self.armed_display.writestr(msg)

	def do_arm(self, node):
		str = self.getstring(node)
		toks = self.tokenizestring(str)
		self.parsetokens(toks)
		# XXXX For lines
		maxy = 0.0
		miny = 999999999.0
		length = 1
		for d in self.datapoints:
			if not d:
				continue
			if len(d) > length:
				length = len(d)
			mind, maxd = min(d), max(d)
			miny = min(miny, mind)
			maxy = max(maxy, maxd)
		if miny == maxy:
			miny = miny - 0.5
			maxy = maxy + 0.5
		leftalign = (MMAttrdefs.getattr(node, 'align') == 'left')
		axis_x, axis_y = MMAttrdefs.getattr(node, 'axis')
		if axis_y >= 0:
			miny, maxy = min(miny, 0), max(maxy, 0)
		for d in self.datapoints:
			if len(d) < length:
				d2 = [None]*(length-len(d))
				if leftalign:
					d[len(d):] = d2
				else:
					d[:0] = d2
		self.ranges = (0, length-1, miny, maxy)
		tp = MMAttrdefs.getattr(node, 'gtype')
		if axis_x >= 0:
			self.do_xaxis(axis_x, (tp in ('bar', 'hline')))
		if axis_y >= 0:
			self.do_yaxis(axis_y)
		if tp == 'line':
			self.do_line(node)
		elif tp == 'hline':
			self.do_hline(node)
		elif tp == 'bar':
			self.do_bar(node)
		else:
			self.errormsg('Unknown graphtype '+tp)
		return 1

	def do_xaxis(self, step, isbar):
		minx, maxx, miny, maxy = self.ranges
		xstepsize = XRANGE / (maxx-minx+isbar)
		ystepsize = YRANGE / (maxy-miny)
		y = maxy*ystepsize
		y = y+YOFF
		self.armed_display.drawline((0,0,0), [(XOFF, y),
						      (1.0-XOFF, y)])
		i = int(minx/step)*step
		while i <= maxx:
			self.armed_display.drawline((0,0,0),
				[(i*xstepsize+XOFF, y),
				 (i*xstepsize+XOFF, y+0.025)])
			i = i + step

	def do_yaxis(self, step):
		minx, maxx, miny, maxy = self.ranges
		xstepsize = XRANGE / (maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		x = XOFF
		self.armed_display.drawline((0,0,0),[(x, YOFF), (x, 1.0-YOFF)])
		i = int(miny/step)*step
		while i <= maxy:
			self.armed_display.drawline((0,0,0),
				[(x, (maxy-i)*ystepsize+YOFF),
				 (x-0.025, (maxy-i)*ystepsize+YOFF)])
			i = i + step

	def do_line(self, node):
		minx, maxx, miny, maxy = self.ranges
		minx = 0.0
		xstepsize = XRANGE / (maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		colorlist = self.needcolors(len(self.datapoints))
		for d in self.datapoints:
			x = minx
			d2 = []
			for i in range(len(d)):
				if d[i] <> None:
					d2.append(XOFF+x,
						  YOFF+(maxy-d[i])*ystepsize)
				x = x + xstepsize
			c = colorlist[0]
			del colorlist[0]
			self.armed_display.drawline(c, d2)

	def do_bar(self, node):
		minx, maxx, miny, maxy = self.ranges
		minx = 0.0
		if miny > 0.0:
			miny = 0.0
		xstepsize = XRANGE / (1+maxx-minx)
		xsmallstep = xstepsize / (len(self.datapoints)+1)
		xstartstep = xsmallstep / 2.0
		ystepsize = YRANGE / (maxy-miny)
		colorlist = self.needcolors(len(self.datapoints))
		for d in self.datapoints:
			x = xstartstep+XOFF
			xstartstep = xstartstep + xsmallstep
			c = colorlist[0]
			del colorlist[0]
			for yorg in d:
				if yorg <> None:
					ytop = YOFF+(maxy-yorg)*ystepsize
					ysize = yorg*ystepsize
					self.armed_display.drawfbox(c,
						  (x, ytop, xsmallstep, ysize))
				x = x + xstepsize
			
	def do_hline(self, node):
		minx, maxx, miny, maxy = self.ranges
		minx = 0.0
		xstepsize = XRANGE / (1+maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		colorlist = self.needcolors(len(self.datapoints))
		for d in self.datapoints:
			d2 = []
			x = minx
			for i in range(len(d)):
				if d[i] <> None:
					y = YOFF+(maxy-d[i])*ystepsize
					d2.append(XOFF+x, y)
					d2.append(XOFF+x+xstepsize, y)
				x = x + xstepsize
			c = colorlist[0]
			del colorlist[0]
			self.armed_display.drawline(c, d2)

	def defanchor(self, node, anchor):
		return anchor

	def getstring(self, node):
		if node.type == 'imm':
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.getfilename(node)
			try:
				fp = urlopen(filename)
			except IOError:
				print 'Cannot open text file', `filename`
				return ''
			text = fp.read()
			fp.close()
			if text[-1:] == '\n':
				text = text[:-1]
			return text
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`


	def tokenizestring(self, str):
		items = string.split(str)
		for i in range(len(items)):
			try:
				items[i] = string.atof(items[i])
			except string.atof_error:
				pass
		return items

	def parsetokens(self, str):
		self.datapoints = []
		curdatapoints = []
		for i in str:
			if type(i) in (type(0.0), type(0)):
				curdatapoints.append(i)
			elif type(i) == type(''):
				if i == 'next':
					if curdatapoints:
						self.datapoints.append(
							  curdatapoints)
						curdatapoints = []
				else:
					print 'GraphChannel: unknown cmd:', i
		if curdatapoints:
			self.datapoints.append(curdatapoints)

	# This can be done better by spacing the colors out in HLS space
	def needcolors(self, num):
		cl = [(255,0,0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
			  (255, 0, 255), (0, 255, 255), (255, 255, 255)]
		while len(cl) < num:
			cl = cl + cl
		return cl[:num]
