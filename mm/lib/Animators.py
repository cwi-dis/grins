__version__ = "$Id$"


import MMAttrdefs
import string

class Animator:
	def __init__(self, attr, domval, fromval=None, toval=None, dur=0):
		self._attr = attr
		self._domval = domval
		self._from = fromval
		self._to = toval
		self._dur = dur
		self._inrepol = self._linear

	def getValue(self, t):
		if self._dur!=0:
			return self._inrepol(self._from, self._to, self._dur, t)
		return self.getDOMValue()

	def getDOMValue(self):
		return self._domval

	def getAttrName(self):
		return self._attr

	def _setCalcMode(self, parser, mode):
		if mode=='discrete':
			self._inrepol = self._linear
		elif mode=='paced':
			self._inrepol = self._linear
		elif mode=='spline':
			self._inrepol = self._linear
		else:
			self._inrepol = self._linear
			
	def _linear(self, v1, v2, dur, t):
		return v1 + (v2-v1)*t/dur

	def _linear_int(self, v1, v2, dur, t):
		v = v1 + (v2-v1)*t/dur
		return int(v + 0.5)

	def _setprec(self, prec=0):
		if prec == 0: 
			self._inrepol = self._linear_int
		else:
			self._inrepol = self._linear
			
class ConstAnimator(Animator):
	def __init__(self, attr, domval, val):
		Animator.__init__(self, attr, domval)
		self.__val = val

	def getValue(self, t):
		return self.__val


class SequenceAnimator(Animator):	
	def __init__(self, attr, domval, fromval, toval, dur):
		Animator.__init__(self, attr, domval, fromval, toval, dur)
		msg = 'Wrong SequenceLinearAnimator arguments'
		if type(domval)!= type( () ) or type(domval)!= type( [] ):
			raise TypeError(msg)
		if type(fromval)!= type( () ) or type(fromval)!= type( [] ):
			raise TypeError(msg)
		if type(toval)!= type( () ) or type(toval)!= type( [] ):
			raise TypeError(msg)
		if len(domval)!=len(fromval):
			raise ValueError(msg)
		if len(domval)!=len(toval):
			raise ValueError(msg)

	def getValue(self, t):
		if self._dur==0:
			return self.getDOMValue()
		l = []
		for i in range(len(self._from)):
			l.append(self._inrepol(self._from[i], self._to[i], self._dur, t))
		return l


class URLPairAnimator(Animator):
	def __init__(self, attr, domval, fromval, toval, dur):
		Animator.__init__(self, attr, domval, fromval, toval, dur)

	def getValue(self, t):
		if t < self._dur/2.0:
			return self._from
		else:
			return self._to


class CompositeAnimator:
	def __init__(self, animlist):
		self.__animators = animlist
	def getValue(self, t):
		l = []
		for anim in self.__animators:
			l.append(self.__animators.getValue(t))
		return l


# Impl. rem:
# *attr types map
# *use f(0) if duration is undefined


# Animation semantics parser
class AnimateElementParser:
	# args anim and target are MMNode objects
	# anim  represents the animate element node
	def __init__(self, anim, target):
		self.__anim = anim
		self.__target = target

		self.__attrname = ''
		self.__attrtype = 'numeric'
		self.__domval = None
		self.__enable = 0
		self.__grinsext = 0

		self.__hasValidTarget = self.__checkTarget()
		self.__getEnumAttrs()

	def getAnimator(self):
		if not self.__hasValidTarget:
			return None

		dt = self.getDuration()

		# src attribute animation
		if self.__attrname=='file':
			vs = self.getAlphaInterpolationValues()
			if dt and len(vs)>=2:
				anim = URLPairAnimator(self.__attrname, self.__domval, vs[0], vs[1], dt)
				anim._setCalcMode(self, self.__calcMode)
				return anim
		
		## Begin temp grins extensions
		if self.__grinsext:
			vs = self.getNumInterpolationValues()
			if dt and len(vs)>=2:
				anim = Animator(self.__attrname, self.__domval, vs[0], vs[1], dt)
				anim._setCalcMode(self, self.__calcMode)
				anim._setprec(0)
				return anim
		## End temp grins extensions

		return ConstAnimator(self.__attrname, self.__domval, self.__domval)

	def getAttrName(self):
		return self.__attrname

	def __checkTarget(self):
		self.__attrname = MMAttrdefs.getattr(self.__anim, 'attributeName')
		if not self.__attrname:
			print 'failed to get attributeName', self.__anim
			return 0

		self.__domval = MMAttrdefs.getattr(self.__target, self.__attrname)

		if not self.__domval:
			self.__checkExtensions()

		if not self.__domval:
			print 'Failed to get original DOM value for attr',self.__attrname,'from node',self.__target
			return 0
		return 1
							
	def __getEnumAttrs(self):
		self.__additive = MMAttrdefs.getattr(self.__anim, 'additive')
		self.__calcMode = MMAttrdefs.getattr(self.__anim, 'calcMode')
		self.__accumulate = MMAttrdefs.getattr(self.__anim, 'accumulate')

	def getDuration(self):
		return MMAttrdefs.getattr(self.__anim, 'duration')

	def getFrom(self):
		return MMAttrdefs.getattr(self.__anim, 'from')

	def getTo(self):
		return MMAttrdefs.getattr(self.__anim, 'to')

	def getBy(self):
		return MMAttrdefs.getattr(self.__anim, 'by')

	def getValues(self):
		return MMAttrdefs.getattr(self.__anim, 'values')

	def getLoop(self):
		return MMAttrdefs.getattr(self.__anim, 'loop')

	def __checkExtensions(self):
		d = self.__target.GetChannel().attrdict
		if not self.__domval and d.has_key('base_winoff'):
			# check for temp grins extensions
			self.__grinsext = 1
			base_winoff = d['base_winoff']
			if self.__attrname == 'region.left':
				self.__domval = base_winoff[0]
			elif self.__attrname == 'region.top':
				self.__domval = base_winoff[1]
			elif self.__attrname == 'region.width':
				self.__domval = base_winoff[2]
			elif self.__attrname == 'region.height':
				self.__domval = base_winoff[3]

	def _dump(self):
		print '----------------------'
		print 'animate attr:', self.__attrname
		for name, value in self.__anim.attrdict.items():
			print name, '=', `value`
		print '----------------------'
		print 'target element',self.__target		
		for name, value in self.__target.attrdict.items():
			print name, '=', `value`
		print 'target element channel'		
		for name, value in self.__target.GetChannel().attrdict.items():
			print name, '=', `value`
		print '----------------------'


	# return list of interpolation values
	def getNumInterpolationValues(self):	
		# if 'values' are given ignore 'from/to/by'
		values =  self.getValues()
		if values:
			try:
				return tuple(map(string.atof, string.split(values,';')))
			except ValueError:
				return ()
		
		# 'from' is optional
		# use dom value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = self.__domval
		if type(v1) == type(''): 
			v1 = string.atof(v1)

		# we must have a 'to' value (expl or through 'by')
		v2 = self.getTo()
		dv = self.getBy()
		if v2:
			v2 = string.atof(v1)
		elif dv:
			dv = string.atof(dv)
			v2 = v1 + dv
		else:
			return ()
		return v1, v2

	# return list of interpolation strings
	def getAlphaInterpolationValues(self):
		
		# if values are given ignore from/to/by
		values =  self.getValues()
		if values:
			return string.split(values,';')
		
		# 'from' is optional
		# use dom value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = self.__domval

		# we must have a 'to' value expl
		v2 = self.getTo()
		if not v2:
			return ()
		return v1, v2


