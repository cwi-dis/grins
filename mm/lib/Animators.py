__version__ = "$Id$"


import MMAttrdefs
import string

# An Animator entity implements the interpolation part
# of animate elements taking into account the calc mode.
# It also implements the semantics of the 'accumulate' attr.

# rem: we can implement also at this level time manipulations
#      (speed, accelerate-decelerate and autoReverse)
#      speed and autoReverse must be taken into account also at higher levels
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
		self.__accValue = 0

		# current value
		self.__curvalue = None

	def getDOMValue(self):
		return self._domval

	def getAttrName(self):
		return self._attr

	def getValue(self, t):
		if t<0 or t>self._dur:
			return self._domval
		if self._dur == 0:
			return self._values[0]
		if self._accumulate=='sum' and self.__accValue:
			v = self.__accValue + self._inrepol(t)
		else:
			v = self._inrepol(t)
		if self._convert:
			v = self._convert(v)
		self.__curvalue = v
		return v

	def getCurrValue(self):
		return self.__curvalue

	def isAdditive(self):
		return self._additive=='sum'

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
			self.__accValue = self._repeatCounter*last

	def setRetunedValuesConvert(self, cvt):
		self._convert = cvt
		
	# temporary parametric form
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
# a constant value animator specialization
class ConstAnimator(Animator):
	def __init__(self, attr, domval, val, dur):
		Animator.__init__(self, attr, domval, (val,), dur, mode='discrete')

# A special animator to manage to-only additive animate elements
class EffValueAnimator(Animator):
	pass

# set element animator specialization
class SetAnimator(Animator):
	pass

# animateColor animator specialization
class ColorAnimator(Animator):
	pass

# animateMotion animator specialization
class MotionAnimator(Animator):
	pass


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
# *animators should be kept for all their effective due: ED = AD + frozenDur
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
				cv = cv + a.getCurrValue()
			else:
				cv = a.getCurrValue()
		if self.__chan:
			self.__chan.updateattr(self.__node, self.__attr, cv)
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

animateContext = AnimateContext()


###########################
# Gen impl. rem:
# ** The semantics of animation timing for static docs (svg for example) seems clean
#    since they are the same as smil-boston.  
#    But, how animation timing interacts with smil timing? The draft says nothing.
#    Yes, we can interpreat this as meaning: like media elements + ?
#    For me the ? mark exists and should be filled otherwise we 'll have 
#    multiple interpretations and thus implementations of animation for smil.
# * implement specializations for elements: set, animateColor, animatePosition
# * support additive and accumulate attributes
# * restart doc removes all anim effects including frozen val
# * big remaining: smil-boston timing for animate elements
# * on syntax error: we can ignore animation effects but not timing
# * use f(0) if duration is undefined
# * ignore keyTimes if dur indefinite
# * attrdefs specs: additive
# * an animation can effect indirectly more than one attributes (for example anim 'region')
# * if 'by' and not 'from': additive='sum'
# * if 'to' and not 'from': additive= <mixed> (start from base but reach to)
# * there is an exceptional animation case that breaks std composition semantics: 
#  this is the 'to-only animation for additive attributes'
#  according to the draft the base value that should be used for the interpolation
#  is the effecive value (the dynamic composite result of other animations).
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
		if(dt>1.0)
			# *the timing module draft says accelerate is clamped to 1 and decelerate=1-accelerate
			self.__accelerate = self.__accelerate/dt
			self.__decelerate = self.__decelerate/dt

		self.__autoReverse = MMAttrdefs.getattr(self.__anim, 'autoReverse')


	def getAnimator(self):

		# 1. Read animation attributes
		attr = self.__attrname
		domval = self.__domval
		dur = self.getDuration()
		mode = self.__calcMode 
		times = self.__getInterpolationKeyTimes() 
		splines = self.__getInterpolationKeySplines()
		accumulate = self.__accumulate
		additive = self.__additive

		# 1+: force first value display (fulfil: use f(0) if duration is undefined)
		# xxx: fix condition
		if not dur: dur=0


		# 2. return None on syntax or logic error
		if not self.__hasValidTarget:
			print 'invalid target syntax error'
			return None

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

		## Begin temp grins extensions
		# position animation
		if self.__grinsext:
			values = self.__getNumInterpolationValues()
			anim = Animator(attr, domval, values, dur, mode, times, splines, 
				accumulate, additive)
			anim.setRetunedValuesConvert(_round)
			return anim
		## End temp grins extensions

		
		# 4. Return an animator based on the attr type
		print 'Guessing animator for',self.__attrname, self.__attrtype
		anim = None
		if self.__attrtype == 'int':
			values = self.__getNumInterpolationValues()
			anim = Animator(attr, domval, values, dur, mode, times, splines, 
				accumulate, additive)
			anim.setRetunedValuesConvert(_round)
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
			anim = ConstAnimator(attr, domval, domval, dur)

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

	# check that we have a valid target
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
		elif mode != 'discrete': n = n + 1

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







