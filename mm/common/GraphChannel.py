__version__ = "$Id$"

from Channel import *
from MMExc import *			# exceptions
from AnchorDefs import *
import string
from urllib import urlopen

XBORDER = 0.05
YBORDER = 0.05

XOFF = XBORDER
YOFF = YBORDER

XRANGE = (1.0-2*XBORDER)
YRANGE = (1.0-2*YBORDER)

class GraphChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + ['bucolor', 'hicolor',
						 'gtype', 'fgcolor', 'align',
						 'axis']

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

	def do_arm(self, node, same=0):
	        if same and self.armed_display:
		    return 1
		self.limits = None
		self.armed_type = MMAttrdefs.getattr(node, 'gtype')
		try:
			str = self.getstring(node)
		except error, arg:
			print arg
			str = ''
		toks = self.tokenizestring(str)
		self.parsetokens(toks)

		minx, maxx, miny, maxy = self.findminmax()

		leftalign = (MMAttrdefs.getattr(node, 'align') == 'left')
		axis_x, axis_y = MMAttrdefs.getattr(node, 'axis')
		if axis_y >= 0:
			miny, maxy = min(miny, 0), max(maxy, 0)
		if miny == maxy:
			miny = miny - 0.5
			maxy = maxy + 0.5
		if self.armed_type <> 'scatter':
			length = int(maxx-minx+1)
			for d in self.datapoints:
				if len(d) < length:
					d2 = [None]*(length-len(d))
					if leftalign:
						d[len(d):] = d2
					else:
						d[:0] = d2
		self.ranges = (minx, maxx, miny, maxy)
		if axis_x >= 0:
			self.do_xaxis(axis_x,
				      (self.armed_type in ('bar', 'hline')))
		if axis_y >= 0:
			self.do_yaxis(axis_y)
		if self.armed_type == 'line':
			self.do_line()
		elif self.armed_type == 'hline':
			self.do_hline()
		elif self.armed_type == 'bar':
			self.do_bar()
		elif self.armed_type == 'scatter':
			self.do_scatter()
		else:
			self.errormsg(node,
				      'Unknown graphtype '+self.armed_type)

		try:
			alist = node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
			alist = []
		for a in alist:
			b = self.armed_display.newbutton((0,0,1,1))
			self.setanchor(a[A_ID], a[A_TYPE], b)
			
		return 1

	def findminmax(self):
		if self.armed_type == 'scatter':
			if self.limits:
				return self.limits
			minx = miny = maxx = maxy =None
			for d in self.datapoints:
				if not d: continue
				for x, y in d:
					if minx == None: minx = x
					if miny == None: miny = y
					if maxx == None: maxx = x
					if maxy == None: maxy = y
					minx = min(minx, x)
					miny = min(miny, y)
					maxx = max(maxx, x)
					maxy = max(maxy, y)
		else:
			if self.limits:
				print 'Sorry, limits only for scatterplots'
			minx = 0
			miny = maxx = maxy =None
			for d in self.datapoints:
				if not d: continue
				if miny == None: miny = d[0]
				if maxx == None: maxx = len(d)
				if maxy == None: maxy = d[0]
				miny = min(miny, min(d))
				maxy = max(maxy, max(d))
				maxx = max(maxx, len(d))
		return minx, maxx, miny, maxy
				

	def do_xaxis(self, step, isbar):
		minx, maxx, miny, maxy = self.ranges
		xstepsize = XRANGE / (maxx-minx+isbar)
		ystepsize = YRANGE / (maxy-miny)
		y = maxy*ystepsize
		y = y+YOFF
		self.armed_display.drawline((0,0,0), [(XOFF, y),
						      (1.0-XOFF, y)])
		if not step: return
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
		if not step: return
		i = int(miny/step)*step
		while i <= maxy:
			self.armed_display.drawline((0,0,0),
				[(x, (maxy-i)*ystepsize+YOFF),
				 (x-0.025, (maxy-i)*ystepsize+YOFF)])
			i = i + step

	def do_line(self):
		minx, maxx, miny, maxy = self.ranges
		minx = 0.0
		xstepsize = XRANGE / (maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		colorlist = self.needcolors(len(self.datapoints))
		for d in self.datapoints:
			x = minx
			d2 = []
			for i in range(len(d)):
				if d[i] is not None:
					d2.append(XOFF+x,
						  YOFF+(maxy-d[i])*ystepsize)
				x = x + xstepsize
			c = colorlist[0]
			del colorlist[0]
			self.armed_display.drawline(c, d2)

	def do_scatter(self):
		minx, maxx, miny, maxy = self.ranges
		xstepsize = XRANGE / (maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		colorlist = self.needcolors(len(self.datapoints))
		for d in self.datapoints:
			c = colorlist[0]
			del colorlist[0]
			for point in d:
				if point is None: continue
				x, y = point
				x = XOFF+((x-minx)*xstepsize)
				y = YOFF+((maxy-y)*ystepsize)
				self.armed_display.drawmarker(c, (x,y))

	def do_bar(self):
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
				if yorg is not None:
					ytop = YOFF+(maxy-yorg)*ystepsize
					ysize = yorg*ystepsize
					self.armed_display.drawfbox(c,
						  (x, ytop, xsmallstep, ysize))
				x = x + xstepsize
			
	def do_hline(self):
		minx, maxx, miny, maxy = self.ranges
		minx = 0.0
		xstepsize = XRANGE / (1+maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		colorlist = self.needcolors(len(self.datapoints))
		for d in self.datapoints:
			d2 = []
			x = minx
			for i in range(len(d)):
				if d[i] is not None:
					y = YOFF+(maxy-d[i])*ystepsize
					d2.append(XOFF+x, y)
					d2.append(XOFF+x+xstepsize, y)
				x = x + xstepsize
			c = colorlist[0]
			del colorlist[0]
			self.armed_display.drawline(c, d2)

	def defanchor(self, node, anchor, cb):
		apply(cb, (anchor,))

	def setanchorargs(self, (node, nametypelist, args), button, value):
		# Called when an anchor is pressed, supply arguments
		# to the hyperjump.
		x, y, buttonlist = value

		# Convert back to dataspace coordinates
		minx, maxx, miny, maxy = self.ranges
		xstepsize = XRANGE / (maxx-minx)
		ystepsize = YRANGE / (maxy-miny)
		x = (x - XOFF)/xstepsize+minx
		y = -((y - YOFF)/ystepsize-maxy)
		return (node, nametypelist, (('x', x), ('y', y)))
		
	def tokenizestring(self, str):
		items = string.split(str)
		for i in range(len(items)):
			if ',' in items[i]:
				subitems = string.split(items[i], ',')
				try:
					subitems = map(string.atof, subitems)
					items[i] = tuple(subitems)
				except string.atof_error:
					pass
			else:
				try:
					items[i] = string.atof(items[i])
				except string.atof_error:
					pass
		return items

	def parsetokens(self, str):
		self.datapoints = []
		curdatapoints = []
		tuples = (self.armed_type == 'scatter')
		limits = []
		in_limits = 0
		for i in str:
			if type(i) in (type(0.0), type(0)):
				if tuples:
					print 'GraphChannel: x,y expected:',i
				else:
					curdatapoints.append(i)
			elif type(i) == type(()):
				if in_limits:
					limits.append(i[0])
					limits.append(i[1])
					continue
				if tuples:
					curdatapoints.append(i)
				else:
					print 'GraphChannel: single value expected:', i
			elif type(i) is type(''):
				if i == 'next':
					in_limits = 0
					if curdatapoints:
						self.datapoints.append(
							  curdatapoints)
						curdatapoints = []
				elif i == 'limits':
					in_limits = 1
				else:
					print 'GraphChannel: unknown cmd:', i
		if curdatapoints:
			self.datapoints.append(curdatapoints)
		if limits:
			self.limits = tuple(limits)

	# This can be done better by spacing the colors out in HLS space
	def needcolors(self, num):
		cl = [(255,0,0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
			  (255, 0, 255), (0, 255, 255), (255, 255, 255)]
		while len(cl) < num:
			cl = cl + cl
		return cl[:num]
