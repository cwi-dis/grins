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
			return PathSeg.commands[self._type]
		else:
			return ''

	def setTypeFromLetter(self, letter):
		if not letter:
			self._type = PathSeg.SVG_PATHSEG_UNKNOWN
			return
		index = PathSeg.commands.find(letter)
		if index<0: self._type = PathSeg.SVG_PATHSEG_UNKNOWN
		elif letter == 'z' or letter == 'Z': self._type = PathSeg.SVG_PATHSEG_CLOSEPATH
		else: self._type = index

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

class SVGPath:
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
		s = ''
		first = 1
		for seq in self._pathSegList:
			if first:
				s = repr(seq)
				first = 0
			else:
				s = s + ' ' + repr(seq)
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


	def createPath(self, path):
		points = []
		lastX = 0
		lastY = 0
		lastC = None
		startP = None
		isstart = 1
		i = 0
		n = len(self._pathSegList)
		while i < n:
			seg = self._pathSegList[i]
			if isstart:
				badCmds = 'HhVvZz'
				while badCmds.find(seg.getTypeAsLetter())>=0 and i<n:
					print 'ignoring cmd ', seg.getTypeAsLetter()
					i = i + 1
					seg = self._pathSegList[i]
				if badCmds.find(seg.getTypeAsLetter())<0:
					if seg._type != PathSeg.SVG_PATHSEG_MOVETO_ABS and \
						seg._type != PathSeg.SVG_PATHSEG_MOVETO_REL:
						print 'assuming abs moveto'
					if seg._type == PathSeg.SVG_PATHSEG_MOVETO_REL:
						lastX, lastY = lastX + seg._x, lastY + seg._y
						startP = (lastX, lastY)
						points.append(startP)
						path.moveTo(startP)
					else:
						lastX, lastY = seg._x, seg._y
						startP = (lastX, lastY)
						points.append(startP)
						path.moveTo(startP)
				isstart = 0
			else:
				if seg._type == PathSeg.SVG_PATHSEG_CLOSEPATH:
					if startP:
						lastX, lastY = startP
						points.append(startP)
						startP = None
					lastC = None
					isstart = 1
					path.closePath()

				elif seg._type == PathSeg.SVG_PATHSEG_MOVETO_ABS:
					lastX, lastY = seg._x, seg._y
					points.append((lastX, lastY))
					lastC = None
					path.moveTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_MOVETO_REL:
					lastX, lastY = lastX + seg._x, lastY + seg._y
					points.append((lastX, lastY))
					lastC = None
					path.moveTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_LINETO_ABS:
					lastX, lastY = seg._x, seg._y
					points.append((lastX, lastY))
					lastC = None
					path.lineTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_LINETO_REL:
					lastX, lastY = lastX + seg._x, lastY + seg._y
					points.append((lastX, lastY))
					lastC = None
					path.lineTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS:
					lastX = seg._x
					points.append((lastX, lastY))
					lastC = None
					path.lineTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL:
					lastX = lastX + seg._x
					points.append((lastX, lastY))
					lastC = None
					path.lineTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS:
					lastY = seg._y
					points.append((lastX, lastY))
					lastC = None
					path.lineTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL:
					lastY = lastY + seg._y
					points.append((lastX, lastY))
					lastC = None
					path.lineTo((lastX, lastY))

				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_ARC_ABS:
					pass
				elif seg._type == PathSeg.SVG_PATHSEG_ARC_REL:
					pass
			i = i + 1
		return points
										
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

def tocomplex(pt):
	return complex(pt[0],pt[1])

class Path:
	SEG_MOVETO = 0
	SEG_LINETO = 1
	SEG_QUADTO = 2
	SEG_CUBICTO = 3
	SEG_CLOSE = 4

	def __init__(self, pathstr=''):
		self.__ptTypes = []
		self.__ptCoords = []
		self._svgpath = None
		self._points = []
		self.__length = 0
		if pathstr:
			self._svgpath = SVGPath(pathstr)
			self._points = self._svgpath.createPath(self)
			self.__length = self.__getLength()

	def constructFromSVGPathString(self, pathstr):
		self._svgpath = SVGPath(pathstr)
		self._points = self._svgpath.createPath(self)
		self.__length = self.__getLength()

	def constructFromPoints(self, coords):
		n = len(coords)
		if n==0: return
		self.moveTo(coords[0])
		for i in range(1,n):
			self.lineTo(coords[i])
		self.__length = self.__getLength()
		
	# main query method
	# get point at length t
	def getPointAt(self, t):
		n = len(self.__ptTypes)
		if n==0: return complex(0, 0)
		elif n==1: return tocomplex(self.__ptCoords[0])
		if t<=0: return tocomplex(self.__ptCoords[0])
		elif t>=self.__length: return tocomplex(self.__ptCoords[n-1])

		d = 0.0
		xq, yq = self.__ptCoords[0] 
		for i in range(n):
			if self.__ptTypes[i] == Path.SEG_MOVETO:
				xp, yp = 	self.__ptCoords[i]
			elif self.__ptTypes[i] == Path.SEG_LINETO:
				x, y = self.__ptCoords[i]
				dx = x - xp; dy = y - yp
				ds = math.sqrt(dx*dx+dy*dy)
				if t>=d and t <= (d + ds):
					f = (t-d)/ds
					xq, yq = xp + f*(x-xp), yp + f*(y-yp)	
					break
				d = d + ds
				xp, yp = x, y
		return complex(xq, yq)

	def getLength(self):
		return self.__length
	
	def __getLength(self):
		d = 0.0
		n = len(self.__ptTypes)
		for i in range(n):
			if self.__ptTypes[i] == Path.SEG_MOVETO:
				xp, yp = 	self.__ptCoords[i]
			elif self.__ptTypes[i] == Path.SEG_LINETO:
				x, y = self.__ptCoords[i]
				dx = x - xp; dy = y - yp
				d = d + math.sqrt(dx*dx+dy*dy)
				xp, yp = x, y
		return d
	
	def __repr__(self):
		return 'path = "' + `self._svgpath` + '"'
	
	def moveTo(self, pt):
		n = len(self.__ptTypes)
		if n>0 and self.__ptTypes[n - 1] == Path.SEG_MOVETO:
			self.__ptCoords[n - 1] = pt
		else:
			self.__ptTypes.append(Path.SEG_MOVETO)
			self.__ptCoords.append(pt)						

	def lineTo(self, pt):
		self.__ptTypes.append(Path.SEG_LINETO)
		self.__ptCoords.append(pt)						

	def curveTo(self, pt1, pt2, pt):
		pass

	def quadTo(self, pt1, pt2, pt):
		pass

	def appendArc(self, arc):
		pass

	def closePath(self):
		pass

	def getCoords(self, i):
		return None


