__version__ = "$Id$"

#
#	SVG data types
#

import re
import string
import math

################
# common patterns

_S = '[ \t\r\n]+'
_opS = '[ \t\r\n]*'
_D = '[ ,\t\r\n]+'
_opD = '[ ,\t\r\n]*'
_sign = r'(?P<sign>[+-]?)'

intPat = r'(?P<int>\d+)'
signedIntPat = _sign + _opS + intPat
numberPat = r'(?P<int>\d+)?([.](?P<dec>\d+))?'
signedNumberPat = _sign + _opS + numberPat
lengthUnitsPat = r'(?P<units>(px)|(pt)|(pc)|(mm)|(cm)|(in)|(%))'
opLengthUnitsPat = r'(?P<units>(px)|(pt)|(pc)|(mm)|(cm)|(in)|(%))?'
angleUnitsPat = r'(?P<units>(deg)|(grad)|(rad))'
freqUnitsPat = r'(?P<units>(Hz)|(kHz))'
timeUnitsPat = r'(?P<time>(s)|(ms))'

fargPat = r'(?P<arg>[(][^)]*[)])'
transformPat = _opD + r'(?P<op>matrix|translate|scale|rotate|skewX|skewY)' + _opS + fargPat 
percentPat = numberPat + _opS + '%'

from svgcolors import svgcolors
color = re.compile('(?:'
		   '#(?P<hex>[0-9a-fA-F]{3}|'		# #f00
			    '[0-9a-fA-F]{6})|'		# #ff0000
			   'rgb' + _opS + r'\(' +		# rgb(R,G,B)
			   _opS + '(?:(?P<ri>[0-9]+)' + _opS + ',' + # rgb(255,0,0)
			   _opS + '(?P<gi>[0-9]+)' + _opS + ',' +
			   _opS + '(?P<bi>[0-9]+)|' +
			   _opS + '(?P<rp>[0-9]+)' + _opS + '%' + _opS + ',' + # rgb(100%,0%,0%)
			   _opS + '(?P<gp>[0-9]+)' + _opS + '%' + _opS + ',' +
			   _opS + '(?P<bp>[0-9]+)' + _opS + '%)' + _opS + r'\))$')

# style type="text/css" parsing
bracketsPat = r'(?P<arg>[{][^}]*[}])' # braces content
classdefPat = r'[.](?P<cname>[a-zA-Z_:][-a-zA-Z0-9._]*)' + _opS + bracketsPat
textcssPat = _opS + classdefPat + _opS

# <!ENTITY parsing
entityNamePat = r'(?P<name>[a-zA-Z_:][-a-zA-Z0-9._:]*)' # entity name
quoteDef = r'(?P<arg>["][^"]*["])' # quote content
entityPat = _opS + '<!ENTITY' + _S + entityNamePat + _S + quoteDef + _opS + '>'

################
# utilities

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
			raise None
		start = self.__pos
		while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])<0:
			self.__pos = self.__pos + 1
		if start == self.__pos and self.__delim.find(self.__str[self.__pos])>=0:
			self.__pos = self.__pos + 1
		return self.__str[start:self.__pos]

class StringSplitter:
	def __init__(self, str, delim=' ,'):
		self.__str = str
		self.__delim = delim
		self.__pos = 0
		self.__maxpos = len(str)
	def hasMoreTokens(self):
		while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])>=0:
			self.__pos = self.__pos + 1
		return (self.__pos < self.__maxpos)
	def nextToken(self):
		while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])>=0:
			self.__pos = self.__pos + 1
		if self.__pos == self.__maxpos:
			return None
		start = self.__pos
		while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])<0:
			self.__pos = self.__pos + 1
		return self.__str[start:self.__pos]

def splitlist(str, delims=' ,'):
	st = StringSplitter(str, delims)
	L = []
	token = st.nextToken()
	while token:
		L.append(token)
		token = st.nextToken()
	return L

def actof(nsign, intg, decg):
	if intg is None and decg is None:
		return None
	if intg is None:
		intg = '0'
	if decg is None:
		decg = '0'
	if not nsign or nsign=='+':
		return string.atof('%s.%s' % (intg, decg))
	else:
		return -string.atof('%s.%s' % (intg, decg))

def ff(val):
	if val < 0:
		val = -val
		sign = '-'
	else:
		sign = ''
	str = '%f' % val
	if '.' in str:
		while str[-1] == '0':
			str = str[:-1]
		if str[-1] == '.':
			str = str[:-1]
	while len(str) > 1 and str[0] == '0' and str[1] in '0123456789':
		str = str[1:]
	if not str:
		str = '0'
	return sign + str

def deg2rad(deg):
	return (deg/180.0)*math.pi
	
################
# svg types

# import path related svg types
from svgpath import PathSeg, SVGPath

class SVGInteger:
	classre = re.compile(_opS + signedIntPat + _opS)
	def __init__(self, node, str, default=None):
		self._node = node
		self._value = None
		self._default = default
		if str:
			str = string.strip(str)
			mo = SVGInteger.classre.match(str)
			if mo is not None:
				self._value = mo.group('int')

	def getValue(self):
		if self._value is not None:
			return self._value
		return self._default

	def isDefault(self):
		return self._value == self._default

class SVGNumber:
	classre = re.compile(_opS + signedNumberPat + _opS)
	def __init__(self, node, str, default=None):
		self._node = node
		self._value = None
		self._default = default
		if str:
			str = string.strip(str)
			mo = SVGNumber.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('sign'), mo.group('int'), mo.group('dec'))
	def getValue(self):
		if self._value is not None:
			return self._value
		return self._default

	def isDefault(self):
		return self._value == self._default

class SVGNumberList:
	def __init__(self, node, str, default=None):
		self._node = node
		self._value = None
		self._default = default
		if str:
			sl = splitlist(str)
			self._value = []
			for s in sl:
				self._value.append(string.atoi(s))

	def __repr__(self):
		s = ''
		for num in self._value:
			s = s + '%s ' % ff(num)
		return s[:-1]

	def getValue(self):
		if self._value is not None:
			return self._value
		return self._default

	def isDefault(self):
		return self._value is None or len(self._value)==0

class SVGPercent:
	classre = re.compile(_opS + percentPat + _opS)
	def __init__(self, node, str, default=None):
		self._node = node
		self._value = None
		self._default = default
		if str:
			str = string.strip(str)
			mo = SVGPercent.classre.match(str)
			if mo is not None:
				self._value = actof(None, mo.group('int'), decg = mo.group('dec'))

	def __repr__(self):
		return '%s' % ff(self._value) + '%'

	def getValue(self):
		if self._value is not None:
			return self._value
		return self._default

	def isDefault(self):
		return self._value == self._default

class SVGLength:
	classre = re.compile(_opS + signedNumberPat + opLengthUnitsPat + _opS)
	#unitstopx = {'px':1.0, 'pt':1.25, 'pc':15.0, 'mm': 3.543307, 'cm':35.43307, 'in':90.0}
	unitstopx = {'px': 1.0, 'pt': 1.0, 'pc': 12.0, 'mm': 2.8346456, 'cm': 28.346456, 'in': 72.0}
	defaultunit = 'px'
	def __init__(self, node, str, default=None):
		self._node = node
		self._units = None
		self._value = None
		self._default = default
		if str is None:
			return
		if str == 'none':
			self._value = 'none'
			return
		if str:
			str = string.strip(str)
			str = string.lower(str) # allow PX, PT,... in place of px, pt, ...?
			mo = SVGLength.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('sign'), mo.group('int'), mo.group('dec'))
				if self._value is not None and self._value<0 and self.__class__ == SVGLength:
					print 'length can not be negative'
				if self._value is not None:
					self._units = mo.group('units')

	def __repr__(self):
		if self._value is None:
			return ''
		elif self._value is 'none':
			return 'none'
		elif self._units is None:
			return '%s' % ff(self._value)
		else:	
			return '%s%s' % (ff(self._value), self._units)
	
	def getValue(self, units='px'):
		if self._value is not None:
			if self._units=='%':
				pass # find parent size
			f1 = self.unitstopx.get(self._units or 'px')
			pixels = f1*self._value
			if units == 'px':
				return int(pixels)
			f2 = self.unitstopx.get(units)
			return pixels/f2
		return self._default

	def getUnits(self):
		return self._units

	def isDefault(self):
		return self._value == self._default

	def getDeviceValue(self, tm, f):
		val = self.getValue()
		if self._units is not None:
			tm = tm.copy()
			tm.inverse()
			if f == 'w':
				return int(tm.UWtoDW(val))
			elif f == 'h':
				return int(tm.UHtoDH(val))
		return val

# like SVGLength but can be negative
class SVGCoordinate(SVGLength):
	pass

class SVGAngle:
	classre = re.compile(_opS + signedNumberPat + angleUnitsPat + _opS)
	svgunits = ('deg', 'grad', 'rad',)
	unitstorad = {'deg':math.pi/180.0, 'grad':math.pi/200.0, 'rad':1.0}
	defaultunit = 'deg'
	def __init__(self, node, str, default=None):
		self._node = node
		self._units = None
		self._value = None
		self._default = default
		if str:
			str = string.strip(str)
			str = string.lower(str) # allow DEG, GRAD,RAD in place of deg, grad, rad?
			mo = SVGAngle.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('sign'), mo.group('int'), decg = mo.group('dec'))
				if self._value is not None:
					units = mo.group('units')
					if units is None:
						units = SVGAngle.defaultunit
					self._units = units

	def __repr__(self):
		return '%s%s' % (ff(self._value), self._units)
	
	def getValue(self, units='rad'):
		if self._value is not None:
			f1 = self.unitstorad.get(self._units)
			val = f1*self._value
			if units == 'rad':
				return val
			f2r = 1.0/self.unitstorad.get(units)
			return val*f2r
		return self._default

	def isDefault(self):
		return self._value == self._default

class SVGColor:
	classre = color
	def __init__(self, node, val, default=None):
		self._node = node
		self._value = None
		self._default = default
		if val is None:
			return
		if val == 'none':
			self._value = 'none'
			return
		val = string.lower(val)
		if svgcolors.has_key(val):
			self._value = svgcolors[val]
			return
		res = SVGColor.classre.match(val)
		if res is None:
			print 'bad color specification', val
			return
		else:
			hex = res.group('hex')
			if hex is not None:
				if len(hex) == 3:
					r = string.atoi(hex[0]*2, 16)
					g = string.atoi(hex[1]*2, 16)
					b = string.atoi(hex[2]*2, 16)
				else:
					r = string.atoi(hex[0:2], 16)
					g = string.atoi(hex[2:4], 16)
					b = string.atoi(hex[4:6], 16)
			else:
				r = res.group('ri')
				if r is not None:
					r = string.atoi(r)
					g = string.atoi(res.group('gi'))
					b = string.atoi(res.group('bi'))
				else:
					r = int(string.atof(res.group('rp')) * 255 / 100.0 + 0.5)
					g = int(string.atof(res.group('gp')) * 255 / 100.0 + 0.5)
					b = int(string.atof(res.group('bp')) * 255 / 100.0 + 0.5)
		if r > 255: r = 255
		if g > 255: g = 255
		if b > 255: b = 255
		self._value = r, g, b

	def __repr__(self):
		if self._value is None or self._value == 'none':
			return 'none'
		return 'rgb(%d, %d, %d)' % self._value

	def getValue(self):
		if self._value is not None:
			return self._value
		return self._default

	def isDefault(self):
		return self._value is None or self.value == self._default

class SVGFrequency:
	classre = re.compile(_opS + numberPat + freqUnitsPat + _opS)
	svgunits = ('Hz', 'kHz')
	defaultunit = 'Hz'
	def __init__(self, node, str, default=None):
		self._node = node
		self._units = None
		self._value = None
		self._default = default
		if str:
			str = string.strip(str)
			mo = SVGFrequency.classre.match(str)
			if mo is not None:
				self._value = actof(None, mo.group('int'), decg = mo.group('dec'))
				if self._value is not None:
					units = mo.group('units')
					if units is None:
						units = SVGFrequency.defaultunit
					self._units = units

	def __repr__(self):
		return '%s%s' % (ff(self._value), self._units)
	
	def getValue(self, units='Hz'):
		if self._value is not None:
			if self._units == 'kHz':
				f1 = 1000.0
			val = f1*self._value
			if units == 'Hz':
				return val
			f2r = 0.001
			return 0.001*val
		return self._default

	def isDefault(self):
		return self._value == self._default

class SVGTime:
	classre = re.compile(_opS + numberPat + timeUnitsPat + _opS)
	svgunits = ('s', 'ms')
	defaultunit = 's'
	def __init__(self, node, str, default=None):
		self._node = node
		self._units = None
		self._value = None
		self._default = default
		if str:
			str = string.strip(str)
			mo = SVGTime.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('sign'), mo.group('int'), mo.group('dec'))
				if self._value is not None:
					units = mo.group('units')
					if units is None:
						units = SVGTime.defaultunit
					self._units = units

	def __repr__(self):
		return '%s%s' % (ff(self._value), self._units)
	
	def getValue(self, units='s'):
		if self._value is not None:
			if self._units == 'ms':
				val = 0.001*self._value
			if units == 's':
				return val
			return 1000.0*val
		return self._default

	def isDefault(self):
		return self._value == self._default

# fill:none; stroke:blue; stroke-width: 20
class SVGStyle:
	def __init__(self, node, str, default=None):
		self._node = node
		self._styleprops = {}
		self._default = default
		if not str:
			return
		stylelist = string.split(str, ';')
		for propdef in stylelist:
			if propdef:
				try:
					prop, val = string.split(propdef, ':')
					prop, val = string.strip(prop), string.strip(val)
				except:
					pass
				else:
					self._styleprops[prop] = val		
		for prop, val in self._styleprops.items():
			if prop == 'fill' or prop == 'stroke':
				if val is not None and val!='none':
					self._styleprops[prop] = SVGColor(self._node, val)
			elif prop == 'stroke-width' or prop == 'font-size':
				if val is not None and val != 'none':
					self._styleprops[prop] = SVGLength(self._node, val)

	def __repr__(self):
		s = ''
		for prop, val in self._styleprops.items():
			if val is not None and type(val) != type(''):
				val = val.getValue()
			if val:
				s = s + prop + ':' + self.toString(prop, val) + '; '
		return s[:-2]

	def toString(self, prop, val):
		if prop == 'fill' or prop == 'stroke':
			if val == 'none':
				return 'none'
			else:
				return 'rgb(%d, %d, %d)' % val
		elif prop == 'stroke-width' or prop == 'font-size':
			return '%s' % ff(val)
		return val

	def getValue(self):
		return self._styleprops

	def isDefault(self):
		return self._styleprops is None or len(self._styleprops)==0

class SVGTextCss:
	classre = re.compile(textcssPat)
	def __init__(self, node, str, default=None):
		self._node = node
		self._textcssdefs = {}
		self._default = default
		mo = SVGTextCss.classre.match(str)
		while mo is not None:
			str = str[mo.end(0):]
			classname = mo.group(1)
			stylestr = mo.group(2)[1:-1] # remove brackets
			self._textcssdefs[classname] = SVGStyle(self._node, stylestr)
			mo = SVGTextCss.classre.match(str)
	
	def __repr__(self):
		return ''

	def getValue(self):
		return self._textcssdefs

	def isDefault(self):
		return self._textcssdefs is None or len(self._textcssdefs)==0

class SVGEntityDefs:
	classre = re.compile(entityPat)
	def __init__(self, node, str, default=None):
		self._node = node
		self._units = None
		self._entitydefs = {}
		self._default = default
		if str:
			mo =  SVGEntityDefs.classre.match(str)
			while mo is not None:
				str = str[mo.end(0):]
				entityName = mo.group('name')
				entityDef = mo.group('arg')[1:-1]
				self._entitydefs[entityName] = entityDef
				mo =  SVGEntityDefs.classre.match(str)

	def __repr__(self):
		s = ''
		for key, val in self._entitydefs.items():
			s = s + '<!ENTITY ' + key + ' \"' + val + '\">\n'
		return s

	def getValue(self):
		return self._entitydefs

	def isDefault(self):
		return self._entitydefs is None or len(self._entitydefs)==0

class SVGPoints:
	def __init__(self, node, str, default=None):
		self._node = node
		self._points = []
		self._default = default
		st = StringSplitter(str, delim=' ,\t\n\r\f')
		while st.hasMoreTokens():
			x = st.nextToken()
			if st.hasMoreTokens():
				y = st.nextToken()
				try:
					x, y = string.atoi(x), string.atoi(y)
				except:
					pass
				else:
					self._points.append((x, y))

	def __repr__(self):
		s = ''
		for point in self._points:
			s = s + '%d, %d ' % point
		return s[:-1]

	def getValue(self):
		return self._points

	def isDefault(self):
		return self._points is None or len(self._points)==0

class SVGAspectRatio:
	aspectRatioPat = r'(?P<align>[a-zA-Z_:][-a-zA-Z0-9._:]*)' + '([ ]+(?P<meetOrSlice>[a-zA-Z_:][-a-zA-Z0-9._:]*))?'
	classre = re.compile(_opS + aspectRatioPat + _opS)
	alignEnum = ('none', 
		'xMinYMin', 'xMidYMin', 'xMaxYMin', 
		'xMinYMid', 'xMidYMid', 'xMaxYMid', 
		'xMinYMax', 'xMidYMax', 'xMaxYMax',)
	meetOrSliceEnum = ('meet', 'slice')
	alignDefault = 'xMidYMid'
	meetOrSliceDefault = 'meet'
	def __init__(self, node, str, default=None):
		self._node = node
		self._align = None
		self._meetOrSlice = None
		self._default = default
		if str:
			mo =  self.classre.match(str)
			if mo is not None:
				self._align = mo.group('align')
				self._meetOrSlice = mo.group('meetOrSlice')
				if self._align not in self.alignEnum:
					self._align = None
				if self._meetOrSlice not in self.meetOrSliceEnum:
					self._meetOrSlice = None

	def __repr__(self):
		s = ''
		if self._align is not None and self._align != self.alignDefault:
			s = s + self._align
		if self._meetOrSlice is not None and self._meetOrSlice != self.meetOrSliceDefault:
			s = s + ' ' + self._meetOrSlice
		return s

	def getValue(self):
		if self._align is None:
			align = self.alignDefault
		else:
			align = self._align
		if self._meetOrSlice is None:
			meetOrSlice = self.meetOrSliceDefault
		else:
			meetOrSlice = self._meetOrSlice
		return align, meetOrSlice

	def isDefault(self):
		return self._align is None or (self._align == self.alignDefault and (self._meetOrSlice is None or self._meetOrSlice=='meet'))

class SVGTransformList:
	classre = re.compile(transformPat)
	classtransforms = ('matrix', 'translate', 'scale', 'rotate', 'skewX' , 'skewY',) 
	def __init__(self, node, str, default=None):
		self._node = node
		self._tflist = []
		self._default = default
		mo = SVGTransformList.classre.match(str)
		while mo is not None:
			str = str[mo.end(0):]
			arg = mo.group(2)[1:-1] # remove parens
			arg = splitlist(arg, ' ,')
			try:
				arg = map(string.atof, arg)
			except ValueError, arg:
				pass #print arg
			else:
				tfname = mo.group(1)
				if tfname in ('rotate', 'skewX', 'skewY'):
					arg = [(arg[0]/180.0)*math.pi,]
				self._tflist.append((tfname, arg))
			mo = SVGTransformList.classre.match(str)

	def __repr__(self):
		return ''

	def getValue(self):
		return self._tflist

	def isDefault(self):
		return self._tflist is None or len(self._tflist)==0


# SVG transformation matrix
# TM = [a, b, c, d, e, f]
# x = a*xu + c*yu + e
# y = b*xu + d*yu + f
# U: user coordinates
# V: viewport (or device) coordinates
# transform: ('matrix', 'translate', 'scale', 'rotate', 'skewX , 'skewY',) 
# reverse: [a b c d]^(-1) = [d -b -c  a]/det
# xu = ((+d)*x +(-c)*y + (c*f-d*e))/(a*d-b*c)
# yu = ((-b)*x +(+a)*y + (b*e-a*f))/(a*d-b*c)

class TM:
	identity = 1, 0, 0, 1, 0, 0
	def __init__(self, elements=None):
		if elements is not None:
			assert len(elements)==6, 'invalid argument'
			self.elements = elements[:]
		else:
			self.elements = TM.identity[:]
			
	def getElements(self):
		return self.elements
			
	def getTransform(self):
		return 'matrix', self.elements
			
	def __repr__(self):
		return '[' + '%s %s %s %s %s %s' % tuple(map(ff, self.elements)) + ']'
	
	# svg transforms
	def matrix(self, et):
		a1, b1, c1, d1, e1, f1 = self.elements
		a2, b2, c2, d2, e2, f2 = tm.elements
		self.elements = a1*a2+c1*b2, b1*a2+d1*b2, a1*c2+c1*d2, b1*c2+d1*d2, a1*e2+c1*f2+e1, b1*e2+d1*f2+f1

	def translate(self, tt):
		assert len(tt)>0 and len(tt)<=2, 'invalid translate transformation'
		tx = tt[0]
		if len(tt)>1: ty = tt[1]
		else: ty = 0
		a, b, c, d, e, f = self.elements
		self.elements = a, b, c, d, e+a*tx+c*ty, f+b*tx+d*ty

	def scale(self, st):
		assert len(st)>0 and len(st)<=2, 'invalid scale transformation'
		sx = st[0]
		if len(st)>1: sy = st[1]
		else: sy = sx
		a, b, c, d, e, f = self.elements
		self.elements = a*sx, b*sx, c*sy, d*sy, e, f

	def rotate(self, at):
		r = at[0]
		a, b, c, d, e, f = self.elements
		sin, cos = math.sin(r), math.cos(r)
		self.elements = a*cos+c*sin, b*cos+d*sin, -a*sin+c*cos, -b*sin+d*cos, e, f

	def skewX(self, at):
		r = at[0]
		a, b, c, d, e, f = self.elements
		tan = math.tan(r)
		self.elements = a, b, c+a*tan, d+b*tan, e, f

	def skewY(self, at):
		r = at[0]
		a, b, c, d, e, f = self.elements
		tan = math.tan(r)
		self.elements = a+c*tan, b+d*tan, c, d, e, f
	
	def inverse(self):
		a, b, c, d, e, f = self.elements
		det = float(a*d - b*c)
		self.elements = d/det, -b/det, -c/det, a/det, (c*f-d*e)/det, (b*e-a*f)/det

	def apply(self, tf, arg):
		try:
			fo = getattr(self, tf)
			tm = fo(arg)
		except AttributeError, arg: 
			print 'invalid transform', `tf`
			print '(', arg, ')'

	def applyTfList(self, tflist):
		if not tflist: return
		for tf, arg in tflist:
			self.apply(tf, arg)
	
	# tm is a TM instance 
	def multiply(self, tm):
		matrix(tm.elements)

	# helpers
	def UPtoDP(self, point):
		a, b, c, d, e, f = self.elements
		xu, yu = point
		return a*xu + c*yu + e, b*xu + d*yu + f

	def URtoDR(self, rc):
		x, y = self.UPtoDP(rc[:2])
		w, h = self.UPtoDP(rc[2:])
		return x, y, w, h

	def UWtoDW(self, w):
		return self.UPtoDP((w, 0))[0]

	def UHtoDH(self, h):
		return self.UPtoDP((0, h))[1]

	def copy(self):
		return TM(self.elements)


