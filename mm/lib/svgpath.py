__version__ = '$Id$'

# Minimum svg path related code to support animateMotion

import string
import math

class PathSeg:
	SVG_PATHSEG_UNKNOWN                      = 0
	SVG_PATHSEG_CLOSEPATH                    = 1
	SVG_PATHSEG_MOVETO_ABS                   = 2
	SVG_PATHSEG_MOVETO_REL                   = 3
	SVG_PATHSEG_LINETO_ABS                   = 4
	SVG_PATHSEG_LINETO_REL                   = 5
	SVG_PATHSEG_CURVETO_CUBIC_ABS            = 6
	SVG_PATHSEG_CURVETO_CUBIC_REL            = 7
	SVG_PATHSEG_CURVETO_QUADRATIC_ABS        = 8
	SVG_PATHSEG_CURVETO_QUADRATIC_REL        = 9
	SVG_PATHSEG_ARC_ABS                      = 10
	SVG_PATHSEG_ARC_REL                      = 11
	SVG_PATHSEG_LINETO_HORIZONTAL_ABS        = 12
	SVG_PATHSEG_LINETO_HORIZONTAL_REL        = 13
	SVG_PATHSEG_LINETO_VERTICAL_ABS          = 14
	SVG_PATHSEG_LINETO_VERTICAL_REL          = 15
	SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS     = 16
	SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL     = 17
	SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS = 18
	SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL = 19

	# order is important to current implementation
	commands = 'ZzMmLlCcQqAaHhVvSsTt'

	def __init__(self,segtype=''):
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
		self.setTypeFromLetter(segtype)

	def setType(self, seqtype):
		self._type = seqtype

	def getTypeAsLetter(self):
		if self._type == PathSeg.SVG_PATHSEG_UNKNOWN:
			return ''
		elif self._type==PathSeg.SVG_PATHSEG_CLOSEPATH:
			return 'z'
		elif self._type<=PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
			return commands[self._type]
		else:
			return ''

	def setTypeFromLetter(self, letter):
		if not letter:
			self._type = PathSeg.SVG_PATHSEG_UNKNOWN
			return
		index = commands.find(letter)
		if index<0: self._type = PathSeg.SVG_PATHSEG_UNKNOWN
		elif letter == 'z' or letter == 'Z': self._type = PathSeg.SVG_PATHSEG_CLOSEPATH
		else: self._type = index

	def getPointAt(self, t):
		return complex(0, 0)

	def getLength(self):
		return 0.0

	def __repr__(self):
		t = self._type
		if t == PathSeg.SVG_PATHSEG_CLOSEPATH: return 'z'
		elif t == PathSeg.SVG_PATHSEG_MOVETO_ABS: return 'M %f %f' % (self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_MOVETO_REL: return 'm %f %f' % (self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_LINETO_ABS: return 'L %f %f' % (self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_LINETO_REL: return 'l %f %f' % (self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS: 
			return 'C %f %f %f %f %f %f' % (self._x1, self._y1, self._x2, self._y2, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL: 
			return 'c %f %f %f %f %f %f' % (self._x1, self._y1, self._x2, self._y2, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS: 
			return 'Q %f %f %f %f %f %f' % (self._x1, self._y1, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL: 
			return 'q %f %f %f %f %f %f' % (self._x1, self._y1, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_ARC_ABS:
			sweep = self._sweepFlag
			largeArc = self._largeArcFlag
			return 'A %f %f %f %d %d %f %f' % (self._r1, self._r2, self._angle, largeArc, sweep, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_ARC_REL:
			sweep = self._sweepFlag
			largeArc = self._largeArcFlag
			return 'a %f %f %f %d %d %f %f' % (self._r1, self._r2, self._angle, largeArc, sweep, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS: return 'H %f' % self._x
		elif t == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL: return 'h %f' % self._x
		elif t == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS: return 'V %f' % self._y
		elif t == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL: return 'v %f' % self._y
		elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS: 
			return 'S %f %f %f %f' % (self._x2, self._y2, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL: 
			return 's %f %f %f %f' % (self._x2, self._y2, self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS: 
			return 'T %f %f' % (self._x, self._y)
		elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL: 
			return 't %f %f' % (self._x, self._y)
		else:
			return ''

class Path:
	def __init__(self,  pathstr):
		self._pathSegList = []
		self.__constructors = {'z':self.__addClosePath,
			'm':self.__addMoveTo,
			'l':self.__addLineTo,
			'c':self.__addCurveTo,
			'q':self.__addQuadraticBezierCurveTo,
			'a':self.__addEllipticArc,
			'h':self.__addHorizontalLineTo,
			'v':self.__addVerticalLineTo,
			's':self.__addSmoothCurveTo,
			't':self.__addTruetypeQuadraticBezierCurveTo,
			}
		self.constructPathSegList(pathstr)

	def __repr__(self):
		s = 'path = "'
		for seq in self._pathSegList:
			s = s + ' ' + repr(seq)
		s = s + '"'
		return s

	# main method
	# create a path from a string description
	def constructPathSegList(self, pathstr):
		self._pathSegList = []
		commands = PathSeg.commands
		st = StringTokenizer(pathstr, commands)
		while st.hasMoreTokens():
			cmd = st.nextToken()
			while commands.find(cmd) < 0 and st.hasMoreTokens():
				cmd = st.nextToken()
			if commands.find(cmd) >= 0:
				if cmd == 'z' or cmd == 'Z':
					self.__addCommand(cmd, None)
				else:
					if st.hasMoreTokens():
						params = st.nextToken()
						self.__addCommand(cmd, params)

	# main query method
	# get point at length t
	def getPointAt(self, t):
		return complex(0, 0)

	def getLength(self):
		return 0.0

	def __addCommand(self, cmd, params):
		lcmd = cmd.lower()
		method = self.__constructors.get(lcmd)
		if method:
			apply(method, (cmd, params))
		else:
			raise AssertionError, 'Invalid path command'

	def __addClosePath(self, cmd, params):
		self._pathSegList.append(PathSeg('z'))
				 
	def __addMoveTo(self, cmd, params):
		absolute = (cmd=='M')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		counter = 0
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._x = x
			seg._y = y
			if counter==0:
				if absolute: seg.setType(PathSeg.SVG_PATHSEG_MOVETO_ABS)
				else: seg.setType(PathSeg.SVG_PATHSEG_MOVETO_REL)
			else:
				if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_ABS)
				else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_REL)
			self._pathSegList.append(seg)
			counter = counter + 1

	def __addLineTo(self, cmd, params):
		absolute = (cmd=='L')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._x = x
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_REL)
			self._pathSegList.append(seg)

	def __addCurveTo(self, cmd, params):
		absolute = (cmd=='C')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x1 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y1 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			x2 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y2 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._x1 = x1
			seg._y1 = y1
			seg._x2 = x2
			seg._y2 = y2
			seg._x = x
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL)
			self._pathSegList.append(seg)

	def __addSmoothCurveTo(self, cmd, params):
		absolute = (cmd=='S')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x2 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y2 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._x2 = x2
			seg._y2 = y2
			seg._x = x
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL)
			self._pathSegList.append(seg)

	def __addHorizontalLineTo(self, cmd, params):
		absolute = (cmd=='H')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			seg = PathSeg()
			seg._x = x
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL)
			self._pathSegList.append(seg)

	def __addVerticalLineTo(self, cmd, params):
		absolute = (cmd=='V')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL)
			self._pathSegList.append(seg)

	def __addEllipticArc(self, cmd, params):
		absolute = (cmd=='A')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			# r1,r2,angle,largeArc,sweep,x,y
			token = self.__getNextToken(st, delims, '0')
			r1 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			r2 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			a = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			large = string.atoi(token)
			token = self.__getNextToken(st, delims, '0')
			sweep = string.atoi(token)
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._r1 = r1
			seg._r2 = r2
			seg._angle = a
			seg._largeArcFlag = large
			seg._sweepFlag = sweep
			seg._x = x
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_ARC_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_ARC_REL)
			self._pathSegList.append(seg)

	def __addQuadraticBezierCurveTo(self, cmd, params):
		absolute = (cmd=='Q')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x1 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y1 = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._x1 = x1
			seg._y1 = y1
			seg._x = x
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL)
			self._pathSegList.append(seg)

	def __addTruetypeQuadraticBezierCurveTo(self, cmd, params):
		absolute = (cmd=='T')
		params = params.strip()
		self.__strip(params,',')
		delims = ' ,-\n\t\r'
		st = StringTokenizer(params, delims)
		while st.hasMoreTokens():
			token = self.__getNextToken(st, delims, '0')
			x = string.atof(token)
			token = self.__getNextToken(st, delims, '0')
			y = string.atof(token)
			seg = PathSeg()
			seg._x = x
			seg._y = y
			if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS)
			else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL)
			self._pathSegList.append(seg)

	def __strip(self, params, ch):
		ret = params
		while ret[0]==ch:ret = ret[1:]
		while ret[-1]==ch:ret = ret[:-1]
	
	def __getNextToken(self, st, delims, default):
		neg = 0
		try:
			token = st.nextToken()
			while st.hasMoreTokens() and delims.find(token)>=0:
				if token == '-': neg = 1
				else: neg = 0
				token = st.nextToken()
			if delims.find(token) >=0:
				token = default
		except:
			token = default
		if neg: token = '-' + token
		if token[-1]=='e' or token[-1]=='E':
			try:
				e = st.nextToken()
				e = e + st.nextToken()
				token = token + e
			except:
				token = token + '0'
		return token

class StringTokenizer:
	def __init__(self, str, delim=' \t\n\r\f'):
		self.__str = str
		self.__delim = delim
		self.__pos = 0
		self.__maxpos = len(str)
	def hasMoreTokens(self):
		return (self.__pos < self.__maxpos)
	def nextToken(self):
		if self.__pos >= self.__maxpos:
			raise AssertionError
		start = self.__pos
		while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])<0:
			self.__pos = self.__pos + 1
		if start == self.__pos and self.__delim.find(self.__str[self.__pos])>=0:
			self.__pos = self.__pos + 1
		return self.__str[start:self.__pos]

