__version__ = '$Id$'

# Minimum svg path related code to support animateMotion

class PathSeg:
	PATHSEG_UNKNOWN                      = 0
	PATHSEG_CLOSEPATH                    = 1
	PATHSEG_MOVETO_ABS                   = 2
	PATHSEG_MOVETO_REL                   = 3
	PATHSEG_LINETO_ABS                   = 4
	PATHSEG_LINETO_REL                   = 5
	PATHSEG_CURVETO_CUBIC_ABS            = 6
	PATHSEG_CURVETO_CUBIC_REL            = 7
	PATHSEG_CURVETO_QUADRATIC_ABS        = 8
	PATHSEG_CURVETO_QUADRATIC_REL        = 9
	PATHSEG_ARC_ABS                      = 10
	PATHSEG_ARC_REL                      = 11
	PATHSEG_LINETO_HORIZONTAL_ABS        = 12
	PATHSEG_LINETO_HORIZONTAL_REL        = 13
	PATHSEG_LINETO_VERTICAL_ABS          = 14
	PATHSEG_LINETO_VERTICAL_REL          = 15
	PATHSEG_CURVETO_CUBIC_SMOOTH_ABS     = 16
	PATHSEG_CURVETO_CUBIC_SMOOTH_REL     = 17
	PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS = 18
	PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL = 19

	# order is important to current implementation
	commands = 'ZzMmLlCcQqAaHhVvSsTt'

	def __init__(self,):
		self._type = PATHSEG_UNKNOWN
		self._x = 0
		self._y = 0
		self._x1 = 0
		self._y1 = 0
		self._x2 = 0
		self._y2 = 0
		self._r1 = 0
		self._r2 = 0
 		self._angle = 0
		self._largeArcFlag = 0
		self._sweepFlag = 0

	def setType(self, seqtype):
		self._type = seqtype

	def getTypeAsLetter(self):
		if self._type == PATHSEG_UNKNOWN:
			return ''
		elif self._type==SVG_PATHSEG_CLOSEPATH:
			return 'z'
		elif self._type<=PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
			return commands[self._type]
		else:
			return ''

	def setTypeAsLetter(self, letter):
		index = commands.find(letter)
		if index<0: self._type = PATHSEG_UNKNOWN
		elif letter == 'z' or letter == 'Z': self._type = SVG_PATHSEG_CLOSEPATH
		else: self._type = index

	def getPointAt(self, t):
		return complex(0, 0)

	def getLength(self):
		return 0.0

	def __repr__(self):
		t = self._type
		if t == SVG_PATHSEG_CLOSEPATH: return 'z'
		elif t == SVG_PATHSEG_MOVETO_ABS: return 'M %f %f' % (self._x, self._y)
		elif t == SVG_PATHSEG_MOVETO_REL: return 'm %f %f' % (self._x, self._y)
		elif t == SVG_PATHSEG_LINETO_ABS: return 'L %f %f' % (self._x, self._y)
		elif t == SVG_PATHSEG_LINETO_REL: return 'l %f %f' % (self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_CUBIC_ABS: 
			return 'C %f %f %f %f %f %f' % (self._x1, self._y1, self._x2, self._y2, self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_CUBIC_REL: 
			return 'c %f %f %f %f %f %f' % (self._x1, self._y1, self._x2, self._y2, self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_QUADRATIC_ABS: 
			return 'Q %f %f %f %f %f %f' % (self._x1, self._y1, self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_QUADRATIC_REL: 
			return 'q %f %f %f %f %f %f' % (self._x1, self._y1, self._x, self._y)
		elif t == SVG_PATHSEG_ARC_ABS:
			sweep = self._sweepFlag
			largeArc = self._largeArcFlag
			return 'A %f %f %f %d %d %f %f' % (self._r1, self._r2, self._angle, largeArc, sweep, self._x, self._y)
		elif t == SVG_PATHSEG_ARC_REL:
			sweep = self._sweepFlag
			largeArc = self._largeArcFlag
			return 'a %f %f %f %d %d %f %f' % (self._r1, self._r2, self._angle, largeArc, sweep, self._x, self._y)
		elif t == SVG_PATHSEG_LINETO_HORIZONTAL_ABS: return 'H %f' % self._x
		elif t == SVG_PATHSEG_LINETO_HORIZONTAL_REL: return 'h %f' % self._x
		elif t == SVG_PATHSEG_LINETO_VERTICAL_ABS: return 'V %f' % self._y
		elif t == SVG_PATHSEG_LINETO_VERTICAL_REL: return 'v %f' % self._y
		elif t == SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS: 
			return 'S %f %f %f %f' % (self._x2, self._y2, self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL: 
			return 's %f %f %f %f' % (self._x2, self._y2, self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS: 
			return 'T %f %f' % (self._x, self._y)
		elif t == SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL: 
			return 't %f %f' % (self._x, self._y)
		else:
			return ''


class Path:
	def __init__(self,  pathstr):
		self._pathSegList = []
		self.constructPathSegList(pathstr)

	def __repr__(self):
		s = 'path = "'
		for seq in self._pathSegList:
			s = s + seq
		s = s + '"'
		return s

	# main method
	# create a path from a string description
	def constructPathSegList(self, pathstr):
		pass
	
	# main query method
	# get point at length t
	def getPointAt(self, t):
		return complex(0, 0)

	def getLength(self):
		return 0.0

	def addCommand(self, cmd, params):
		pass
		 
	def addMoveTo(self, cmd, params):
		pass

	def addLineTo(self, cmd, params):
		pass

	def addCurveTo(self, cmd, params):
		pass

	def addSmoothCurveTo(self, cmd, params):
		pass

	def addHorizontalLineTo(self, cmd, params):
		pass

	def addVerticalLineTo(self, cmd, params):
		pass

	def addEllipticArc(self, cmd, params):
		pass

	def addQuadraticBezierCurveTo(self, cmd, params):
		pass

	def addTruetypeQuadraticBezierCurveTo(self, cmd, params):
		pass


