__version__ = "$Id$"


import MMAttrdefs
import string
import math
import svgpath

# An Animator represents an animate element at run time.
# An Animator entity implements interpolation taking into 
# account the calc mode, the 'accumulate' attr and 
# the time manipulations: speed, accelerate-decelerate and autoReverse
class Animator:
	def __init__(self, attr, domval, values, dur, mode='linear', 
			times=None, splines=None, accumulate='none', additive='replace'): 
		self._attr = attr
		self._domval = domval
		self._dur = dur
		self._mode = mode
		self._values = values
		self._times = times
		self._splines = splines
		self._accumulate = accumulate
		self._additive = additive

		# assertions
		if len(values)==0: raise AssertionError
		if len(values)==1 and mode != 'discrete': raise AssertionError
		if times:
			if len(times)!=len(values): raise AssertionError
		if splines and times:
			if len(splines) != len(times)-1: raise AssertionError

		# set calc mode
		if mode=='discrete': self._inrepol = self._discrete
		elif mode=='paced': self._inrepol = self._paced
		elif mode=='spline': self._inrepol = self._spline
		else: self._inrepol = self._linear

		# return value convertion (for example int())
		self._convert = None

		# construct boundaries of time intervals
		self._efftimes = []
		if not times:
			# create uniform intervals
			# for now assume also uniform intervals for 'paced' mode
			n = len(values)
			# for discrete mode n is the number of intervals
			if mode == 'discrete': n = n + 1
			if n <= 2:
				self._efftimes = [0, dur]
			else:
				tau = dur/float(n-1)
				t = 0.0
				for i in range(n):
					self._efftimes.append(t)
					t = t + tau
		else:
			# scale times to dur
			self._efftimes = []
			for p in times:
				self._efftimes.append(p*dur)	

		# accumulate attribute
		self._accumulate = 'none'

		# repeat counter
		self._repeatCounter = 0

		# cashed acc value
		self._accValue = 0

		# current value
		self._curvalue = None

		# time manipulators
		self._speed = 1.0
		self._accelerate = 0.0
		self._decelerate = 0.0
		self._autoReverse = 0

	def getDOMValue(self):
		return self._domval

	def getAttrName(self):
		return self._attr

	# set local time to t and return value at t
	def getValue(self, t):
		# time manipulate transform
		t = self._transformTime(t)

		# boundary values
		if t<0 or t>self._dur:
			return self._domval
		if self._dur == 0:
			return self._values[0]

		# calcMode
		v = self._inrepol(t)

		# accumulate
		if self._accumulate=='sum' and self.__accValue:
			v = self._accValue + v

		# convertion
		if self._convert:
			v = self._convert(v)
		
		self._curvalue = v
		return v

	def getCurrValue(self):
		return self._curvalue

	def isAdditive(self):
		return self._additive=='sum'

	# redefine this method to override addition
	def addCurrValue(self, v):
		return v + self._curvalue

	# t in [0, dur]
	def _getinterval(self, t):
		tl = self._efftimes
		n = len(tl)
		for i in range(n-1):
			if t >= tl[i] and t < tl[i+1]:
				return i, (t - tl[i]) / (tl[i+1] - tl[i])
		# t == dur
		return n-2, 1.0

	def _discrete(self, t):
		n = len(self._values)
		if n==1: return self._values[0]
		ix, pdt = self._getinterval(t)
		return self._values[ix]

	def _linear(self, t):
		vl = self._values
		dur = self._dur
		n = len(vl)
		if t==dur:
			return vl[n-1]
		elif t==0 or n==1:
			return vl[0]
		ix, pdt = self._getinterval(t)
		return vl[ix] + (vl[ix+1]-vl[ix])*pdt

	def _paced(self, t):
		return self._linear(t) 

	def _spline(self, t):
		vl = self._values
		dur = self._dur
		el = self._splines
		n = len(vl)
		if t==dur: 
			return vl[len(vl)-1]
		elif t==0:
			return vl[0]
		ix, pdt = self._getinterval(t)
		return vl[ix] + (vl[ix+1]-vl[ix])*self.bezier(pdt, el[ix])

	# set legal attr values range
	def setRange(self, range):
		self._range = range
	def hasRange(self):
		return hasattr(self, '_range')

	# the following method will be called by the EffectiveAnimator
	# to clamp the results at the top of the animation stack to the legal range 
	# before applying them to the presentation value
	def clamp(self, v):
		if v < self._range[0]: return self._range[0]
		elif v > self._range[1]:return self._range[1]
		else: return v

	def _setAccumulate(self, acc):
		if acc not in ('none', 'sum'):
			print 'invalid accumulate value:',acc
			self._accumulate = 'none'
		else:
			self._accumulate = acc

	def repeat(self):
		self._repeatCounter = self._repeatCounter + 1
		if self._accumulate=='sum':
			n = len(self._values)
			last = self._values[n-1]
			self._accValue = self._repeatCounter*last

	def setRetunedValuesConverter(self, cvt):
		self._convert = cvt

	#
	# begin time manipulation section
	#
	def getTimeManipulatedDur(self):
		dur = self._dur
		if self._autoReverse:
			dur = 2*self._dur
		if self._speed!=1.0:
			dur = self._speed*dur
		return dur
		
	def _setAutoReverse(self,t=0):
		self._autoReverse = t

	def _setAccelerateDecelerate(self, a, b):
		self._accelerate = a
		self._decelerate = b

	def _setSpeed(self,s):
		self._speed = s

	def _transformTime(self, t):
		if self._autoReverse:
			t = self._autoReverse(t)
		if (self._accelerate+self._decelerate)>0.0:
			t = self._accelerate_decelerate(t)
		if self._speed!=1.0:
			t = self._speed(t)
		return t

	def _accelerate_decelerate(self, t):
		a = self._accelerate
		b = self._decelerate
		d = self._dur
		ad = a*d
		bd = b*t
		t2 = t*t
		r = 1.0/(1.0 - 0.5*a - 0.5*b)
		if t>=0 and t<=ad:
			tp = 0.5*r*t2/ad
		elif t>a*d and t<=(d-bd):
			 tp = r*t
		elif t>(d-bd) and t<=d:
			tp = r * ((0.5*t2 - (d-bd))/bd)
		else:
			tp = t
		return tp

	def _autoReverse(self, t):
		if t > 2*self._dur: 
			return 0
		elif t > self._dur:
			return t - dur
		else:
			return t

	def _speed(self, t):
		if self._speed<0:
			t = self._dur - t
		return math.fabs(self._speed)*t

	#
	# temporary parametric form
	#
	def bezier(self, t, e = (0,0,1,1)):
		res = 20
		step = 1.0/float(res)
		s = 0.0
		for i in range(res+1):
			sc = 1.0-s
			b = 3.0*sc*sc*s
			c = 3.0*sc*s*s
			d = s*s*s
			tp = b*e[0] + c*e[2] + d
			if tp >= t: 
				return b*e[1] + c*e[3] + d
			s = s + step

###########################
# values convertions methods
def _round(val):
	return int(val+0.5)


###########################
class FeatureNotImplementedException:
    def __init__(self, msg=''):
        self.__msg = msg
    def __repr__(self):
        return self.__msg

###########################
# 'set' element animator
class SetAnimator(Animator):
	def __init__(self, attr, domval, value, dur):
		Animator.__init__(self, attr, domval, (value, ), dur, mode ='discrete') 

###########################
# A special animator to manage to-only additive animate elements
class EffValueAnimator(Animator):
	pass
	
###########################
class TupleAnimator(Animator):
	def __init__(self, attr, domval, values, dur, mode='linear', 
			times=None, splines=None, accumulate='none', additive='replace'):
		Animator.__init__(self, attr, domval, values, dur, mode, 
			times, splines, accumulate, additive)
		self._animators = ()

	def setComponentAnimators(self, animators):
		self._animators = animators

	def getValue(self, t):
		v = []
		for a in self._animators:
			v.append(a.getValue(t))
		self._curvalue = tuple(v)
		return self._curvalue

	def _setAutoReverse(self,f=0):
		Animator._setAutoReverse(self,f)
		for a in self._animators:
			a._setAutoReverse(f)

	def _setAccelerateDecelerate(self, a, b):
		Animator._setAccelerateDecelerate(self, a, b)
		for a in self._animators:
			a._setAccelerateDecelerate(a, b)

	def _setSpeed(self,s):
		Animator._setSpeed(self,s)
		for a in self._animators:
			a._setSpeed(s)

	def setRetunedValuesConverter(self, cvt):
		Animator.setRetunedValuesConverter(self,cvt)
		for a in self._animators:
			a.setRetunedValuesConverter(cvt)

	def setRange(self, range):
		Animator.setRange(self,range)
		for a in self._animators:
			a.setRange(range)

	def addCurrValue(self, v):
		nv = []
		for i in range(len(self._animators)):
			a = self._animators[i]
			nv.append(a.addCurrValue(v[i]))
		return tuple(nv)

	def clamp(self, v):
		nv = []
		for i in range(len(self._animators)):
			a = self._animators[i]
			nv.append(a.clamp(v[i]))
		return tuple(nv)

###########################
# 'animateColor'  element animator
class ColorAnimator(TupleAnimator):
	def __init__(self, attr, domval, values, dur, mode='linear', 
			times=None, splines=None, accumulate='none', additive='replace'):
		TupleAnimator.__init__(self, attr, domval, values, dur, mode, 
			times, splines, accumulate, additive)
		rvalues = []
		gvalues = []
		bvalues = []
		for r, g, b in values:
			rvalues.append(r)
			gvalues.append(g)
			bvalues.append(b)
		rdomval, gdomval, bdomval = domval
		ranim = Animator(attr, rdomval, rvalues, dur, mode, 
			times, splines, accumulate, additive)
		ganim = Animator(attr, gdomval, gvalues, dur, mode, 
			times, splines, accumulate, additive)
		banim = Animator(attr, bdomval, bvalues, dur, mode, 
			times, splines, accumulate, additive)
		self.setComponentAnimators((ranim, ganim, banim))
		self.setRetunedValuesConverter(_round)
		self.setRange((0, 255))


###########################
# 'animateMotion' element animator
class MotionAnimator(Animator):
	def __init__(self, attr, domval, path, dur, mode='paced', 
			times=None, splines=None, accumulate='none', additive='replace'):		
		self._path = path

		# values will be used if duration is undefined
		l = path.getLength()
		values = (path.getPointAt(0), path.getPointAt(l))
		Animator.__init__(self, attr, domval, values, dur, mode, 
			times, splines, accumulate, additive)
		
		# override acc value to be complex
		self._accValue = complex(0,0)

		# time to paced interval convertion factor
		self._time2length = path.getLength()/dur

	def _paced(self, t):
		return self._path.getPointAt(t*self._time2length)

	def _discrete(self, t):
		return self._path.getPointAt(t*self._time2length)
		
	def _linear(self, t):
		return self._path.getPointAt(t*self._time2length)

	def _spline(self, t):
		return self._path.getPointAt(t*self._time2length)


###########################
# An EffectiveAnimator is responsible to combine properly
# all animations of the same attribute and the base value 
# to give the final display value. 
# This is the entity that knows and keeps the attr display value
# taking into account all animations and the dom value.
# Implements animations composition semantics
#	'additive' attribute + priorities
#  and is an entity at a higher level than animators (and thus channels).

# impl rem: 
# *lower priority if previously started
# if sync: lower priority if sync base source else lower if first in doc
# 'first in doc' is a common case and easy to implement
# restart element raises priority but not repeat
# *animators should be kept for all their effective dur: ED = AD + frozenDur
# so, whats the best way to implement 'freeze'?
# we must have a way to monitor animations for all ED not only AD
# * we must either assert that onAnimateBegin are called in the proper order
# or implement within EffectiveAnimator a proper ordering method
# 
class EffectiveAnimator:
	def __init__(self, attr, domval):
		self.__attr = attr
		self.__domval = domval

		self.__animators = []

		self.__node = None
		self.__chan = None
		self.__currvalue = None

	def getDOMValue(self):
		return self.__domval

	def getAttrName(self):
		return self.__attr
	
	def getCurrValue(self):
		return self.__currvalue

	def onAnimateBegin(self, targChan, targNode, animator):
		for a in self.__animators:
			if id(a) == id(animator):
				self.__animators.remove(animator)			
		self.__animators.append(animator)
		if not self.__node:
			self.__node = targNode
		if not self.__chan:
			self.__chan = targChan
		if self.__node != targNode:
			raise AssertionError
		if self.__chan != targChan:
			raise AssertionError

	def onAnimateEnd(self, animator):
		self.__animators.remove(animator)			
		self.update()

	# compute and apply animations composite effect
	# this method is a notification from some animator 
	# or some other knowledgeable entity that something has changed
	def update(self):
		cv = self.__domval
		for a in self.__animators:
			if a.isAdditive():
				cv = a.addCurrValue(cv)
			else:
				cv = a.getCurrValue()
		if self.__chan:
			displayValue = cv
			for a in self.__animators:
				if a.hasRange():
					displayValue = a.clamp(cv)
					break
			self.__chan.updateattr(self.__node, self.__attr, displayValue)
		self.__currvalue = cv
	

###########################
# AnimateContext is an EffectiveAnimator repository
# We need a well-known repository so that we can find EffectiveAnimators
# from Animators (channel) context.
# Implements also operations that apply to all EffectiveAnimator objects
# and is a document level entity.

class AnimateContext:
	def __init__(self):
		self._effAnimators = {}

	def getEffectiveAnimator(self, targnode, targattr, domval):
		key = "n%d-%s" % (id(targnode), targattr)
		if self._effAnimators.has_key(key):
			return self._effAnimators[key]
		else:
			ea = EffectiveAnimator(targattr, domval)
			self._effAnimators[key] = ea
			return ea

# rem: should be defined at doc level
animateContext = AnimateContext()


###########################
# Gen impl. rem:
# ** The semantics of animation timing for static docs (svg for example) seems clean
#    since they are the same as smil-boston.  
#    But, how animation timing interacts with smil timing? The draft says nothing.
#    Yes, we can interpreat this as meaning: like media elements + ?
#    For me the ? mark exists and should be filled otherwise we 'll have 
#    multiple interpretations and thus implementations of animation for smil.
# * restart doc removes all anim effects including frozen val
# * big remaining: smil-boston timing for animate elements
# * on syntax error: we can ignore animation effects but not timing
# * use f(0) if duration is undefined
# * ignore keyTimes if dur indefinite
# * attrdefs specs: additive, legal_range 
# * an animation can effect indirectly more than one attributes (for example anim 'region')
# * if 'by' and not 'from': additive='sum'
# * if 'to' and not 'from': additive= <mixed> (start from base but reach to)
# * there is an exceptional animation case that breaks std composition semantics: 
#  this is the 'to-only animation for additive attributes'
#  according to the draft the base value that should be used for the interpolation
#  is the effective value (the dynamic composite result of other animations).
#  are any other exceptions to std composition semantics?
#  implement specialization: EffValueAnimator

###########################
# Animation semantics parser
class AnimateElementParser:
	# args anim and target are MMNode objects
	# anim  represents the animate element node
	def __init__(self, anim, target):
		self.__anim = anim
		self.__target = target

		self.__attrname = ''
		self.__domval = None
		self.__enable = 0
		self.__grinsext = 0

		# get animate element type ('animate', 'set', 'animateMotion', 'animateColor')
		# use current convention for this
		self.__elementTag = string.split(anim.attrdict['mimetype'],'/')[1]

		self.__hasValidTarget = self.__checkTarget()
		if self.__hasValidTarget:
			self.__attrtype = MMAttrdefs.getattrtype(self.__attrname)

		self.__additive = MMAttrdefs.getattr(self.__anim, 'additive')
		self.__calcMode = MMAttrdefs.getattr(self.__anim, 'calcMode')
		self.__accumulate = MMAttrdefs.getattr(self.__anim, 'accumulate')

		# speed="1" is a no-op, and speed="-1" means play backwards
		# We have to get the absolute speed. This is relative to parent 
		self.__speed = MMAttrdefs.getattr(self.__anim, 'speed')
		if self.__speed==0.0: # not allowed
			self.__speed=1.0

		self.__accelerate = MMAttrdefs.getattr(self.__anim, 'accelerate')
		self.__decelerate = MMAttrdefs.getattr(self.__anim, 'decelerate')
		dt =  self.__accelerate + self.__decelerate
		if dt>1.0:
			# *the timing module draft says accelerate is clamped to 1 and decelerate=1-accelerate
			self.__accelerate = self.__accelerate/dt
			self.__decelerate = self.__decelerate/dt

		self.__autoReverse = MMAttrdefs.getattr(self.__anim, 'autoReverse')


	def getAnimator(self):
		if self.__elementTag=='set':
			return self.__getSetAnimator()
	
		# 1. Read animation attributes
		attr = self.__attrname
		domval = self.__domval
		dur = self.getDuration()
		mode = self.__calcMode 
		times = self.__getInterpolationKeyTimes() 
		splines = self.__getInterpolationKeySplines()
		accumulate = self.__accumulate
		additive = self.__additive

		# for animateMotion we need also 'path' and 'origin'
		#...

		# 1+: force first value display (fulfil: use f(0) if duration is undefined)
		# xxx: fix condition
		if not dur: dur=0


		# 2. return None on syntax or logic error
		if not self.__hasValidTarget:
			print 'invalid target syntax error'
			return None

		if self.__elementTag!='animateMotion':
			nvalues = self.__countInterpolationValues()
			if nvalues==0 or (nvalues==1 and mode!='discrete'):
				print 'values syntax error'
				return None

		# 3. Return explicitly animators for special attributes

		# 'by-only animation' implies sum 
		if self.__isByOnly(): additive = 'sum'

		# 'to-only animation for additive attributes' is very special
		if self.__isToOnly() and self.__canBeAdditive() and mode!='discrete':
			pass # manage special case: return EffValueAnimator(...)

		if self.__elementTag=='animateColor':
			values = self.__getColorValues()
			return ColorAnimator(attr, domval, values, dur, mode, times, splines,
				accumulate, additive)

		## Begin temp grins extensions
		# position animation
		if self.__grinsext:
			if self.__elementTag=='animateMotion':
				strpath = MMAttrdefs.getattr(self.__anim, 'path')
				path = svgpath.Path(strpath)
				return MotionAnimator(attr, domval, path, dur, mode, times, splines,
					accumulate, additive)
			values = self.__getNumInterpolationValues()
			anim = Animator(attr, domval, values, dur, mode, times, splines, 
					accumulate, additive)
			anim.setRetunedValuesConverter(_round)
			self.__setTimeManipulators(anim)
			return anim
		## End temp grins extensions

		# 4. Return an animator based on the attr type
		print 'Guessing animator for attribute',`self.__attrname`,'(', self.__attrtype,')'
		anim = None
		if self.__attrtype == 'int':
			values = self.__getNumInterpolationValues()
			anim = Animator(attr, domval, values, dur, mode, times, splines, 
				accumulate, additive)
			anim.setRetunedValuesConverter(_round)
		elif self.__attrtype == 'float':
			values = self.__getNumInterpolationValues()
			anim = Animator(attr, domval, values, dur, mode, times, splines,
				accumulate, additive)
		elif self.__attrtype == 'string' or self.__attrtype == 'enum' or self.__attrtype == 'bool':
			mode = 'discrete' # override calc mode
			values = self.__getAlphaInterpolationValues()
			anim = Animator(attr, domval, values, dur, mode, times, splines,
				accumulate, additive)
		
		# 5. Return a default if anything else failed
		if not anim:
			print 'Dont know how to animate attribute.',self.__attrname,self.__attrtype
			anim = SetAnimator(attr, domval, domval, dur)

		self.__setTimeManipulators(anim)
		return anim

	# return an animator for the 'set' animate element
	def __getSetAnimator(self):
		if not self.__hasValidTarget:
			print 'invalid target syntax error'
			return None
		attr = self.__attrname
		domval = self.__domval
		dur = self.getDuration()
		value = self.getTo()
		if value==None or value=='':
			print 'set element without attribute to'
			return None

		if self.__attrtype == 'int':
			value = string.atoi(value)
			anim = SetAnimator(attr, domval, value, dur)
			anim.setRetunedValuesConverter(_round)
		elif self.__attrtype == 'float':
			value = string.atof(value)
			anim = SetAnimator(attr, domval, value, dur)
		elif self.__attrtype == 'string' or self.__attrtype == 'enum' or self.__attrtype == 'bool':
			anim = SetAnimator(attr, domval, value, dur)
		else:
			anim = SetAnimator(attr, domval, domval, dur)
		self.__setTimeManipulators(anim)
		return anim

	def getAttrName(self):
		return self.__attrname
							
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

	def getKeyTimes(self):
		return MMAttrdefs.getattr(self.__anim, 'keyTimes')

	def getKeySplines(self):
		return MMAttrdefs.getattr(self.__anim, 'keySplines')

	# set time manipulators to the animator
	def __setTimeManipulators(self, anim):
		if self.__autoReverse=='true':
			anim._setAutoReverse(1)
		if (self.__accelerate+self.__decelerate)>0.0:
			anim._setAccelerateDecelerate(self.__accelerate, self.__decelerate)
		if self.__speed!=1.0:
			anim._setSpeed(self.__speed)

	# check that we have a valid target
	def __checkTarget(self):
		self.__attrname = MMAttrdefs.getattr(self.__anim, 'attributeName')
		if not self.__attrname:
			print 'failed to get attributeName', self.__anim
			return 0

		self.__domval = MMAttrdefs.getattr(self.__target, self.__attrname)

		# check extensions
		if not self.__domval:
			d = self.__target.GetChannel().attrdict
			if self.__attrname=='backgroundColor': self.__attrname = 'bgcolor'
			if not self.__domval and d.has_key(self.__attrname):
				self.__domval = d[self.__attrname]

		if not self.__domval:
			self.__checkExtensions()
			
		if not self.__domval:
			print 'Failed to get original DOM value for attr',self.__attrname,'from node',self.__target
			return 0
		return 1

	def __isByOnly(self):
		v1 = self.getFrom()
		if v1!='': return 0
		v2 = self.getTo()
		if v2!='': return 0
		return 1

	def __isToOnly(self):
		v1 = self.getFrom()
		if v1!='': return 0
		v2 = self.getTo()
		if v2!='': return 1
		return 0

	def __canBeAdditive(self):
		 return self.__attrtype == 'int' or self.__attrtype == 'float'
	
	# return list of interpolation values
	def __getNumInterpolationValues(self):	
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
			v2 = string.atof(v2)
		elif dv:
			dv = string.atof(dv)
			v2 = v1 + dv
		else:
			return ()
		return v1, v2

	# return list of interpolation strings
	def __getAlphaInterpolationValues(self):
		
		# if values are given ignore from/to/by
		values =  self.getValues()
		if values:
			return string.split(values,';')
		
		# 'from' is optional
		# use dom value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = self.__domval

		# we must have an expl 'to' value
		v2 = self.getTo()
		if not v2:
			return ()
		return v1, v2


	# copy from SMILTreeRead
	def __convert_color(self, val):
		from colors import colors
		from SMILTreeRead import color
		val = string.lower(val)
		if colors.has_key(val):
			return colors[val]
		if val in ('transparent', 'inherit'):
			return val
		res = color.match(val)
		if res is None:
			self.syntax_error('bad color specification')
			return 'transparent'
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
		return r, g, b

	def __getColorValues(self):
		values =  self.getValues()
		if values:
			try:
				return tuple(map(self.__convert_color, string.split(values,';')))
			except ValueError:
				return ()

		# 'from' is optional
		# use dom value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = self.__domval
		if type(v1) == type(''): 
			v1 = self.__convert_color(v1)

		# we must have a 'to' value (expl or through 'by')
		v2 = self.getTo()
		dv = self.getBy()
		if v2:
			v2 = self.__convert_color(v2)
		elif dv:
			dv = self.__convert_color(dv)
			v2 = v1 + dv
		else:
			return ()
		return v1, v2


	# len of interpolation list values
	# len == 0 is a syntax error
	# len == 1 and mode != 'discrete' is a syntax error
	def __countInterpolationValues(self):
		values =  self.getValues()
		if values:
			l = string.split(values,';')
			return len(l)

		n = 0
		v1 = self.getFrom()
		if v1: n = n + 1
		elif self._mode != 'discrete': n = n + 1

		v2 = self.getTo()
		dv = self.getBy()
		if v2 or dv: n = n + 1
		return n

	# return keyTimes or an empty list on failure
	def __getInterpolationKeyTimes(self):
		keyTimes = self.getKeyTimes()
		if not keyTimes: return ()
		tl = string.split(values,';')

		# len of values must be equal to len of keyTimes
		lvl = self.__countInterpolationValues()
		if mode=='discrete': lvl = lvl + 1
		if  lvl != len(tl):
			print 'values vs times mismatch'		 
			return ()
			
		tt = tuple(map(string.atof, tl))

		# check boundary constraints
		first = tt[0]
		last = tt[len(tt)-1]
		if self.__calcMode == 'linear' or self.__calcMode == 'spline':
			if first!=0.0 or last!=1.0: 
				print 'keyTimes range error'
				return ()
		elif self.__calcMode == 'discrete':
			if first!=0.0: 
				print 'not sero start keyTime'
				return ()
		elif self.__calcMode == 'paced':
			print 'ignoring keyTimes for paced mode'
			return ()
		
		# values should be increasing and in [0,1]
		if first>1.0 or first<0:return ()
		for i in  range(1,len(tt)):
			if tt[i] < tt[i-1]:
				print 'keyTimes order mismatch'
				return ()
			if tt[i]>1.0 or tt[i]<0:
				print 'keyTimes range error'
				return ()
		return tt

	# return keySplines or an empty list on failure
	def __getInterpolationKeySplines(self):
		keySplines = self.getKeySplines()
		if not keySplines: return ()
		if self.__calcMode != 'spline':
			print 'splines while not in spline calc mode'
			return []
		sl = string.split(values,';')
		
		# len of keySplines must be equal to num of intervals (=len(keyTimes)-1)
		tt = self.getInterpolationKeyTimes()
		if tt and len(sl) != len(tt)-1:
			print 'intervals vs splines mismatch'
			return []
		if not tt and len(sl) != 1:
			print 'intervals vs splines mismatch'
			return []

		rl = []
		for e in sl:
			try:
				x1, y1, x2, y2 = map(string.atof, string.split(e))
			except:
				print 'splines parsing error'
				return []
			if x1<0.0 or x1>1.0 or x2<0.0 or x2>1.0 or y1<0.0 or y1>1.0 or y2<0.0 or y2>1.0:
				print 'splines range error'
				return []
			rl.append((x1, y1, x2, y2))
		return rl


	# temp
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
			elif self.__attrname == 'region.position':
				self.__domval = complex(base_winoff[0], base_winoff[1])

	# temp
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







