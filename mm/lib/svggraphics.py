__version__ = "$Id$"

#
#	SVG Graphics
#

import svgtypes
import svgpath

class SVGGraphics:
	def __init__(self):
		# current point
		self.cpoint = 0, 0
		
		# current path
		self.cpath = svgpath.Path()

		# current transformation matrix (CTM)
		self.ctm = svgtypes.TM()

		# current style attributes:
		# font, color, line, weight, line cap, line join
		# line miter limit, dash pattern
		# clipping region
		# ...
		# XXX:  initialize according to spec
		self.cstyle = {
			'stroke-width': svgtypes.SVGLength(None, 'stroke-width', '1'), 
			'font-family': 'Verdana', 
			'font-size':svgtypes.SVGLength(None, 'font-size', '15'),
			'fill':svgtypes.SVGColor(None, 'fill', 'black'),
			}

	def __repr__(self):
		style = ''
		for prop, val in self.cstyle.items():
			try:
				style = style + prop + ':' + val + '; '
			except:
				print  prop, val
		style = style + 'ctm' + ':' + `self.ctm` + '; '
		style = style + 'cp' + ':' + `self.cpoint` + '; '
		return style

	def applyStyle(self, style):
		if style:
			self.cstyle.update(style)

	def applyTfList(self, tflist):
		if tflist:
			self.ctm.applyTfList(tflist)

	# style arg overrides current graphics style
	def getStyleAttr(self, prop, style=None):
		if style:
			val = style.get(prop)
			if val is not None:
				return val
		return self.cstyle.get(prop)	

	def getStyle(self):
		return self.cstyle

	#
	#  clone for save/restore
	#
	def clone(self):
		new = self.__class__()
		new.cpoint = self.cpoint
		new.cpath = self.cpath.copy()
		new.ctm = self.ctm.copy()
		new.cstyle = self.cstyle.copy()
		self.tkInitInstance(new)
		return new

	#
	#  renderer notifications interface
	#

	def onBeginRendering(self):
		self.tkOnBeginRendering()

	def onEndRendering(self):
		self.tkOnEndRendering()


	#
	#  platform toolkit renderer notifications interface
	#

	# called to intialize platform toolkit before rendering
	def tkStartup(self, params):
		pass

	# called to dispose platform toolkit objects after rendering
	def tkShutdown(self):
		pass

	# we start rendering
	def tkOnBeginRendering(self, size):
		pass

	# we finished rendering
	def tkOnEndRendering(self):
		pass

	# new graphics context
	# self state reflects this new context
	def tkOnBeginContext(self):
		pass

	# end of context
	# self state reflects the restored context
	def tkOnEndContext(self):
		pass

	# copy platform toolkit objects to 'other' 
	def tkInitInstance(self, other):
		pass

	# clip box
	def tkClipBox(self, clipbox):
		pass

	#
	#  plaform line art interface
	#  renderers requests for execution
	#
	def drawRect(self, pos, size, rxy, style, tf):
		print 'rect', pos, size, style, tf

	def drawCircle(self, center, r, style, tf):
		print 'circle', center, r, style, tf

	def drawEllipse(self, center, rxy, style, tf):
		print 'ellipse', center, rxy, style, tf

	def drawLine(self, pt1, pt2, style, tf):
		print 'line', pt1, pt2, style, tf

	def drawPolyline(self, points, style, tf):
		print 'polyline', points, style, tf

	def drawPolygon(self, points, style, tf):
		print 'polygon', points, style, tf

	def drawPath(self, path, style, tf):
		print 'path', path, style, tf

	def drawText(self, text, pos, style, tf):
		print text, pos, style, tf


