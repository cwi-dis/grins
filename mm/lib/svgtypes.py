__version__ = "$Id$"

#
#	SVG data types
#

import re
import string

################
# common patterns

_S = '[ \t\r\n]+'
_opS = '[ \t\r\n]*'

intPat = r'(?P<int>\d+)'
numberPat = r'(?P<int>\d+)([.](?P<dec>\d+))?'
lengthUnitsPat = r'(?P<units>(px)|(pt)|(pc)|(mm)|(cm)|(in)|(%))'
opLengthUnitsPat = r'(?P<units>(px)|(pt)|(pc)|(mm)|(cm)|(in)|(%))?'
angleUnitsPat = r'(?P<units>(deg)|(grad)|(rad))'
freqUnitsPat = r'(?P<units>(Hz)|(kHz))'
timeUnitsPat = r'(?P<time>(s)|(ms))'

################
# utilities

def actof(intg, decg):
	if intg is None and decg is None:
		return None
	if intg is None:
		intg = '0'
	if decg is None:
		decg = '0'
	return string.atof('%s.%s' % (intg, decg))

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
	classre = re.compile(_opS + intPat + _opS)
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
	classre = re.compile(_opS + numberPat + _opS)
	def __init__(self, str):
		self._value = None
		if str:
			str = string.strip(str)
			mo = SVGNumber.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('int'), decg = mo.group('dec'))
	def getValue(self):
		return self._value

class SVGLength:
	classre = re.compile(_opS + numberPat + opLengthUnitsPat + _opS)
	svgunits = ('px', 'pt', 'pc', 'mm', 'cm', 'in', '%')
	unitstopx = {'px':1.0, 'pt':1.25, 'pc':15.0, 'mm':3.543307, 'cm':35.43307, 'in':90.0}
	def __init__(self, str):
		self._units = None
		self._value = None
		if str:
			str = string.strip(str)
			str = string.lower(str) # allow PX, PT,... in place of px, pt, ...?
			mo = SVGLength.classre.match(str)
			if mo is not None:
				self._value = actof(mo.group('int'), decg = mo.group('dec'))
				if self._value is not None:
					units = mo.group('units')
					if units is None:
						units = 'px'
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

class SVGCoordinate(SVGLength):
	pass

class SVGAngle:
	classre = re.compile(_opS + numberPat + angleUnitsPat + _opS)

class SVGColor:
	pass

class SVGPaint:
	pass

class SVGPercentage:
	pass

class SVGTransformList:
	pass

class SVGFrequency:
	classre = re.compile(_opS + numberPat + freqUnitsPat + _opS)

class SVGTime:
	classre = re.compile(_opS + numberPat + timeUnitsPat + _opS)

# default: opS + comma + opS | S separated list
class SVGList:
	pass
