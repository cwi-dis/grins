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
numberPat = r'(?P<int>\d+)([.](?P<dec>\d+))?'
signedNumberPat = _sign + _opS + numberPat
lengthUnitsPat = r'(?P<units>(px)|(pt)|(pc)|(mm)|(cm)|(in)|(%))'
opLengthUnitsPat = r'(?P<units>(px)|(pt)|(pc)|(mm)|(cm)|(in)|(%))?'
angleUnitsPat = r'(?P<units>(deg)|(grad)|(rad))'
freqUnitsPat = r'(?P<units>(Hz)|(kHz))'
timeUnitsPat = r'(?P<time>(s)|(ms))'

fargPat = r'(?P<arg>[(][^)]*[)])'
transformPat = _opD + r'(?P<op>translate|rotate|scale)' + _opS + fargPat 
percentPat = numberPat + _opS + '%'

import colorsex
svgcolors = colorsex.colorsx11
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

################
class SVGInteger:
	classre = re.compile(_opS + signedIntPat + _opS)
	def __init__(self, str):
		self._value = None
		if str:
			str = string.strip(str)
			mo = SVGInteger.classre.match(str)
			if mo is not None:
				self._value = mo.group('int')
	def getValue(self):
		return self._value

class SVGNumber:
	classre = re.compile(_opS + signedNumberPat + _opS)
	def __init__(self, str):
		self._value = None
		if str:
			str = string.strip(str)
			mo = SVGNumber.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('sign'), mo.group('int'), mo.group('dec'))
	def getValue(self):
		return self._value

class SVGPercent:
	classre = re.compile(_opS + percentPat + _opS)
	def __init__(self, str):
		self._value = None
		if str:
			str = string.strip(str)
			mo = SVGPercent.classre.match(str)
			if mo is not None:
				self._value = actof(None, mo.group('int'), decg = mo.group('dec'))
	def getValue(self):
		return self._value

class SVGLength:
	classre = re.compile(_opS + signedNumberPat + opLengthUnitsPat + _opS)
	svgunits = ('px', 'pt', 'pc', 'mm', 'cm', 'in', '%')
	unitstopx = {'px':1.0, 'pt':1.25, 'pc':15.0, 'mm':3.543307, 'cm':35.43307, 'in':90.0}
	defaultunit = 'px'
	def __init__(self, str):
		self._units = None
		self._value = None
		if str:
			str = string.strip(str)
			str = string.lower(str) # allow PX, PT,... in place of px, pt, ...?
			mo = SVGLength.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('sign'), mo.group('int'), mo.group('dec'))
				if self._value is not None and self._value<0 and self.__class__ == SVGLength:
					print 'length can not be negative'
				if self._value is not None:
					units = mo.group('units')
					if units is None:
						units = SVGLength.defaultunit
					self._units = units

	def __repr__(self):
		return '%s%s' % (ff(self._value), self._units)
	
	def getLength(self, units='px', reflen=None):
		if self._value is not None:
			if self._units=='%':
				if reflen:
					return 0.01*reflen*self._value
				else:
					return None
			f1 = self.unitstopx.get(self._units)
			pixels = f1*self._value
			if units == 'px':
				return int(pixels)
			f2r = 1.0/self.unitstopx.get(units)
			return pixels*f2r
		return None

# like SVGLength but can be negative
class SVGCoordinate(SVGLength):
	pass

class SVGAngle:
	classre = re.compile(_opS + signedNumberPat + angleUnitsPat + _opS)
	svgunits = ('deg', 'grad', 'rad',)
	unitstorad = {'deg':math.pi/180.0, 'grad':math.pi/200.0, 'rad':1.0}
	defaultunit = 'deg'
	def __init__(self, str):
		self._units = None
		self._value = None
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
	
	def getAngle(self, units='rad'):
		if self._value is not None:
			f1 = self.unitstorad.get(self._units)
			val = f1*self._value
			if units == 'rad':
				return val
			f2r = 1.0/self.unitstorad.get(units)
			return val*f2r
		return None

class SVGColor:
	classre = color
	def __init__(self, val):
		self._value = None
		val = string.lower(val)
		if svgcolors.has_key(val):
			self._value = svgcolors[val]
			return
		#if val in ('transparent', 'inherit'):
		#	return val
		res = SVGColor.classre.match(val)
		if res is None:
			print 'bad color specification'
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

	def getColor(self):
		return self._value


class SVGTransformList:
	classre = re.compile(transformPat)
	transcodes= {'matrix':1, 'translate':2, 'scale':3, 'rotate':4, 'skewX':5 , 'skewY':6, } 
	def __init__(self, str):
		self.transforms = []
		pos = 0
		mo = SVGTransformList.classre.match(str)
		while mo is not None:
			str = str[mo.end(0):]
			arg = mo.group(2)[1:-1] # remove parens
			arg = splitlist(arg, ' ,')
			try:
				arg = map(string.atoi, arg)
			except ValueError, arg:
				print arg
			else:
				self.transforms.append((mo.group(1), arg))
			mo = re.match(transformPat, str)


class SVGFrequency:
	classre = re.compile(_opS + numberPat + freqUnitsPat + _opS)
	svgunits = ('Hz', 'kHz')
	defaultunit = 'Hz'
	def __init__(self, str):
		self._units = None
		self._value = None
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
	
	def getFrequency(self, units='Hz'):
		if self._value is not None:
			if self._units == 'kHz':
				f1 = 1000.0
			val = f1*self._value
			if units == 'Hz':
				return val
			f2r = 0.001
			return 0.001*val
		return None

class SVGTime:
	classre = re.compile(_opS + numberPat + timeUnitsPat + _opS)
	svgunits = ('s', 'ms')
	defaultunit = 's'
	def __init__(self, str):
		self._units = None
		self._value = None
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
	
	def getTime(self, units='s'):
		if self._value is not None:
			if self._units == 'ms':
				val = 0.001*self._value
			if units == 's':
				return val
			return 1000.0*val

# fill:none; stroke:blue; stroke-width: 20
class SVGStyle:
	def __init__(self, str):
		self.styleprops = {}
		stylelist = string.split(str, ';')
		for propdef in stylelist:
			if propdef:
				try:
					prop, val = string.split(propdef, ':')
					prop, val = string.strip(prop), string.strip(val)
				except:
					pass
				else:
					self.styleprops[prop] = val		
		for prop, val in self.styleprops.items():
			if prop == 'fill' or prop == 'stroke':
				if val != 'none':
					val = SVGColor(val).getColor()
				else:
					val = None
				self.styleprops[prop] = val
			elif prop == 'stroke-width':
				val = string.atoi(val)
				self.styleprops[prop] = val
		print self.styleprops

class SVGPoints:
	def __init__(self, str):
		self.points = []
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
					self.points.append((x, y))
	def getPoints(self):
		return self.points




