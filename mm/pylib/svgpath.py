__version__ = "$Id$"


# Minimum svg path related code to support animateMotion

# The code in this module is temporary and will be replaced 
# by a full python svg dom implementation as soon as is available.


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

	commands = 'MmLlCcZzSsHhVvQqTtAa'

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

	def setType(self, type):
		self._type = type

	def getTypeAsLetter(self):
		return 'u'

	def setTypeAsLetter(self):
		pass

	def getPointAt(self, t):
		return complex(0, 0)

	def getLength(self):
		return 0.0

	def __repr__(self):
		return '<%s instance, type=%s>' % (self.__class__.__name__, self.getTypeAsLetter())


class Path:
	def __init__(self,  pathstr):
		self._pathSegList = []
		self.constructPathSegList(pathstr)

	def __repr__(self):
		return '<%s instance>' % self.__class__.__name__

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


