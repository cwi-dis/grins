__version__ = "$Id$"


import MMAttrdefs
import MMNode
import string
import math
import svgpath
import re

# units, messages
import windowinterface

# conditional behaviors
import settings

debug = 0

# An Animator represents an animate element at run time.
# An Animator entity implements interpolation taking into 
# account the calc mode, the 'accumulate' attr and 
# the time manipulations: speed, accelerate-decelerate and autoReverse
class Animator:
	def __init__(self, attr, domval, values, dur, mode='linear', 
			times=None, splines=None, accumulate='none', additive='replace'): 
		self._attr = attr
		self._domval = domval
		self._dur = float(dur)
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
		self._range = None

		# construct boundaries of time intervals
		self._efftimes = []
		if not times:
			n = len(values)
			if mode == 'paced':
				# create intervals proportional to values
				# values may be not monotonic, so use segments:
				tl = 0.0
				for i in range(1,n):
					tl = tl + self.distValues(values[i-1],values[i])
				f = dur/tl
				d = 0.0
				self._efftimes.append(0)
				for i in range(1,n-1):
					d = d + self.distValues(values[i-1],values[i])
					self._efftimes.append(f*d)
				self._efftimes.append(dur)
			else:
				# create uniform intervals
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
		self._accValue = None

		# current values
		self._curvalue = None
		self._time = None

		# time manipulators
		self._speed = 1.0
		self._accelerate = 0.0
		self._decelerate = 0.0
		self._autoReverse = 0
		self._direction = 1

		# composition context of this animator
		self.__effectiveAnimator = None

	def getDOMValue(self):
		return self._domval

	def getAttrName(self):
		return self._attr

	def getTimeManipulatedDur(self):
		dur = self._dur
		if self._autoReverse:
			dur = 2*dur
		dur = dur/self._speed
		return dur

	# return the current local time in [0, dur] 
	# after time manipulations
	def getLocalTime(self):
		return self._time

	# set local time to t and return value at t
	def getValue(self, t):
		# time manipulate transform
		t = self._transformTime(t)
		self._time = t

		# assert that t is in [0,dur)
		# i.e. assert end-point exclusive model 
		if t<0 or t>self._dur or (t==self._dur and not self._autoReverse):
			raise AssertionError
			
		# compute interpolated value according to calcMode
		v = self._inrepol(t)

		# accumulate
		if self._accumulate=='sum' and self.__accValue:
			v = self._accValue + v
		
		self._curvalue = v
		return v

	def getCurrValue(self):
		return self._curvalue

	# mainly for freeze and accumulate calculations 
	def setToEnd(self):
		# set local time to end
		if self._autoReverse:t = 0
		else: t = self._dur
		self._time = t

		# compute interpolated value according to calcMode
		v = self._inrepol(t)

		# set current value taking into account accumulate
		self._repeatCounter = self._repeatCounter + 1
		if self._accumulate=='sum':
			if self._repeatCounter == 1:
				self._accValue = v
			else:
				self._accValue = self.addValues(self._accValue, v)
			self._curvalue = self._accValue
		else:
			self._curvalue = v

	# reset
	def restart(self):
		self._repeatCounter = 0
		self._accValue = None
		self._curvalue = None
		self._time = None

	def isAdditive(self):
		return self._additive=='sum'

	def addCurrValue(self, v):
		return self.addValues(v, self._curvalue)

	# redefine this method to override addition (for additive attributes)
	def addValues(self, v1, v2):
		return v1 + v2

	# redefine this method to override metrics (for paced mode)
	def distValues(self, v1, v2):
		return math.fabs(v2-v1)

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
		# since intervals are proportional to values
		# by construction, linear results to paced
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

	def _calcto(self, t):
		if not self.__effectiveAnimator:
			return self._postinterpol(t)
		self._values[0] = self.__effectiveAnimator.getcurrentbasevalue(self)
		return self._postinterpol(t)

	# set legal attr values range
	def setRange(self, range):
		self._range = range

	# the following method will be called by the EffectiveAnimator
	# to clamp the results at the top of the animation stack to the legal range 
	# before applying them to the presentation value
	def clamp(self, v):
		if not self._range:
			return v
		if v < self._range[0]: return self._range[0]
		elif v > self._range[1]:return self._range[1]
		else: return v

	# the following method will be called by the EffectiveAnimator
	# to convert final value
	def convert(self, v):
		if self._convert:
			v = self._convert(v)
		return v

	def _setAccumulate(self, acc):
		if acc not in ('none', 'sum'):
			print 'invalid accumulate value:',acc
			self._accumulate = 'none'
		else:
			self._accumulate = acc

	def setRetunedValuesConverter(self, cvt):
		self._convert = cvt

	def setEffectiveAnimator(self, ea):
		self.__effectiveAnimator = ea

	def _setAutoReverse(self,f):
		if f: self._autoReverse = 1
		else: self._autoReverse = 0

	def _setAccelerateDecelerate(self, a, b):
		if a <0.0 or b<0.0:
			print 'invalid accelerate/decelerate values'		
		a = math.fabs(a)
		b = math.fabs(b)
		s = a + b
		if s==0:
			self._accelerate = 0
			self._decelerate = 0
		elif s>1.0:
			print 'invalid accelerate/decelerate values'
			self._accelerate = a / s
			self._decelerate = b / s
		else:
			self._accelerate = a
			self._decelerate = b

	# can be called two times
	# one to set speed attribute and 
	# two to set implicit speed from the container
	def _setSpeed(self,s):
		if s == 0:
			print 'invalid zero speed value'
			s = 1.0
		self._speed = self._speed * math.fabs(s)
		self._direction = 1
		if self._speed<0.0:
			self._direction = -1

	def _transformTime(self, t):
		# first apply time scaling
		if self._speed!=1.0:
			t = self._applySpeed(t)

		# then t mod dur
		if self._autoReverse:
			t = self._applyAutoReverse(t)

		# then speed direction
		if self._direction<0:
			t = self._applyReflect(t)

		# apply acc/dec for t is [0,dur]
		if (self._accelerate+self._decelerate)>0.0:
			t = self._applyAccelerateDecelerate(t)

		return t

	# t in [0,dur]
	# to preserve duration max speed m should be:
	# d = accTriangle + constRectangle + decTriangle = a*d*m/2 + (d-b*d-a*d)*m + b*d*m/2
	# therefore max speed m = 1 / (1 - a/2 - b/2)
	def _applyAccelerateDecelerate(self, t):
		if t<0 or t>self._dur:
			raise AssertionError
		a = self._accelerate
		b = self._decelerate
		d = self._dur
		ad = a*d
		bd = b*d
		t2 = t*t
		dt2 = (d-t)*(d-t)
		m = 1.0/(1.0 - 0.5*a - 0.5*b)
		if t>=0 and t<=ad:
			tp = 0.5*m*t2/ad
		elif t>=a*d and t<=(d-bd):
			tp = 0.5*m*ad + (t-ad)*m
		elif t>=(d-bd) and t<=d:
			tp = d - 0.5*m*dt2/bd
		if tp<0 or tp>d:
			raise AssertionError
		return tp

	# t in [0,2*dur]
	def _applyAutoReverse(self, t):
		if t<0 or t>2.0*self._dur:
			raise AssertionError
		if t > self._dur:
			return self._dur - (t - self._dur)
		else:
			return t

	def _applySpeed(self, t):
		return self._speed*t

	# t in [0, dur]
	def _applyReflect(self, t):
		return self._dur - t

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
# 'set' element animator
class SetAnimator(Animator):
	def __init__(self, attr, domval, value, dur):
		Animator.__init__(self, attr, domval, (value, ), dur, mode ='discrete') 

###########################
# A special animator to manage to-only additive animate elements
class EffValueAnimator(Animator):
	def __init__(self, attr, domval, value, dur):
		Animator.__init__(self, attr, domval, (domval, value,), dur, mode='linear',
			times=None, splines=None, accumulate='none', additive='replace') 
		self._postinterpol = self._inrepol
		self._inrepol = self._calcto
		self._values = list(self._values)


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

	def addValues(self, v1, v2):
		if len(v1)!=len(v2):
			raise AssertionError
		nv = []
		for i in range(len(v1)):
			a = self._animators[i]
			nv.append(a.addValues(v1[i],v2[i]))
		return tuple(nv)

	def distValues(self, v1, v2):
		if len(v1)!=len(v2):
			raise AssertionError
		ss = 0.0
		for i in range(len(v1)):
			a = self._animators[i]
			dl = a.distValues(v1[i],v2[i])
			ss = ss + dl*dl
		return math.sqrt(ss)

		return math.fabs(v2-v1)

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
		self.setRange((0, 255))

	# the following method will be called by the EffectiveAnimator
	# to convert final value
	def convert(self, v):
		r, g, b = v
		return _round(r), _round(g), _round(b)

class FloatTupleAnimator(TupleAnimator):
	def __init__(self, attr, domval, values, dur, mode='linear', 
			times=None, splines=None, accumulate='none', additive='replace'):
		TupleAnimator.__init__(self, attr, domval, values, dur, mode, 
			times, splines, accumulate, additive)
		tvalues = []
		n = len(domval)
		for i in range(n):
			tvalues.append([])
		for t in values:
			for i in range(n):
				tvalues[i].append(t[i])
		animators = []
		for i in range(n):
			anim = Animator(attr, domval[i], tvalues[i], dur, mode, 
				times, splines, accumulate, additive)
			animators.append(anim)
		self.setComponentAnimators(animators)

class IntTupleAnimator(FloatTupleAnimator):
	def convert(self, v):
		n = len(v)
		l = []
		for i in range(n):
			l.append(_round(v[i]))
		return tuple(l)

###########################
# 'animateMotion' element animator
class MotionAnimator(Animator):
	def __init__(self, attr, domval, path, dur, mode='paced', 
			times=None, splines=None, accumulate='none', additive='sum'):
		self._path = path

		# get values from path to support modes other than paced
		values = path.getPoints()
		Animator.__init__(self, attr, domval, values, dur, mode, 
			times, splines, accumulate, additive)
		
		# time to paced interval convertion factor
		self._time2length = path.getLength()/dur
		
	def _paced(self, t):
		return self._path.getPointAt(t*self._time2length)

	def convert(self, v):
		x, y = v.real, v.imag
		return _round(x), _round(y)
	
	def distValues(self, v1, v2):
		dx = math.fabs(v2.real-v1.real)
		dy = math.fabs(v2.imag-v1.imag)
		return math.sqrt(dx*dx+dy*dy)

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
# we must monitor animations for all ED not only AD
# * we must either assert that onAnimateBegin are called in the proper order
# or implement within EffectiveAnimator a proper ordering method
# 
class EffectiveAnimator:
	def __init__(self, targnode, attr, domval):
		self.__node = targnode
		self.__attr = attr
		self.__domval = domval

		self.__animators = []

		self.__chan = None
		self.__currvalue = None

		# keep tag for exceptions
		self.__tag = tag = MMAttrdefs.getattr(targnode, 'tag')
			
		# we need a temporary instance of the
		# last animator removed from self.__animators
		self.__lastanimator = None
		
		# helper variables
		self.__region = None
		self.__regionContents = []

	def getDOMValue(self):
		return self.__domval

	def getAttrName(self):
		return self.__attr
	
	def getCurrValue(self):
		return self.__currvalue

	def getTargetNode(self):
		return self.__node

	def onAnimateBegin(self, targChan, animator):
		for a in self.__animators:
			if id(a) == id(animator):
				self.__animators.remove(animator)			
		self.__animators.append(animator)
		animator.setEffectiveAnimator(self)
		if debug: print 'adding animator', animator

		if not self.__chan:
			self.__chan = targChan

	def onAnimateEnd(self, targChan, animator):
		self.__animators.remove(animator)
		if debug: print 'removing animator',animator
		if not self.__animators:		
			self.__lastanimator = animator
		self.update(targChan)
		self.__lastanimator = None

	# compute and apply animations composite effect
	# this method is a notification from some animator 
	# or some other knowledgeable entity that something has changed
	def update(self, targChan):
		if not self.__chan:
			self.__chan = targChan

		cv = self.__domval
		for a in self.__animators:
			if a.isAdditive():
				cv = a.addCurrValue(cv)
			else:
				cv = a.getCurrValue()
		
		# keep a copy
		self.__currvalue = cv

		# convert and clamp display value
		displayValue = cv
		a = None
		if self.__animators:
			a = self.__animators[0]
		elif self.__lastanimator:
			a = self.__lastanimator
		if a:
			displayValue = a.convert(displayValue)
			displayValue = a.clamp(displayValue)
		
		# update presentation value

		# handle regions and areas separately
		if self.__tag == 'region':
			self.__updateregion(displayValue)
			return
		elif self.__tag == 'area':
			self.__updatearea(displayValue)
			return
		elif self.__attr in ('top','left','width','height','right','bottom','position'):
			self.__updatesubregion(displayValue)
			return
	
		# normal proccessing
		self.__node.SetPresentationAttr(self.__attr, displayValue)

		# notify/update display value if we have a channel
		if self.__chan:
			self.__chan.updateattr(self.__node, self.__attr, displayValue)
			if debug:
				if cv == self.__domval:
					print 'update',self.__attr,'of channel',self.__chan._name,'to',displayValue,'(domvalue)'
				else:
					print 'update',self.__attr,'of channel',self.__chan._name,'to',displayValue
		elif debug:
			name = MMAttrdefs.getattr(self.__node, 'name')
			if cv == self.__domval:
				print 'update',self.__attr,'of node',name,'to',displayValue,'(domvalue)'
			else:
				print 'update',self.__attr,'of node',name,'to',displayValue		
	
	# update region attributes display value
	def __updateregion(self, value):
		attr = self.__attr
		ch = self.__node.GetChannel()
		regionname = ch.name

		# locate region and its contents (once)
		if not self.__region:
			from Channel import channels
			for chan in channels:
				type = chan._attrdict.get('type')
				if type == 'layout' and chan._name == regionname:
					self.__region = chan
				else:
					base_window = chan._attrdict.get('base_window')
					if base_window == regionname:
						self.__regionContents.append(chan)
		
		mmregion = self.__region._attrdict

		# implemented fit='meet' (0) and fit='hidden' (1)

		if settings.activeFullSmilCss:
			scale = mmregion.getCssAttr('scale', 1)
			coordinates = mmregion.getPxGeom()
		else:
			scale = mmregion['scale']
			coordinates = mmregion.GetPresentationAttr('base_winoff')

		if coordinates and attr in ('position','left','top','width','height','right','bottom'):
			x, y, w, h = coordinates
			units = ch.get('units')
			if attr=='position':
				x, y = value
				newcoordinates = x, y, w, h
			elif attr=='left':
				if scale==0:
					newcoordinates = value, y, w-value, h
				else:
					newcoordinates = value, y, w, h
			elif attr=='top':
				if scale==0:
					newcoordinates = x, value, w, h-value
				else:
					newcoordinates = x, value, w, h
			elif attr=='right': 
				if scale==0:
					newcoordinates = x, y, w-value, h
				else:
					newcoordinates = value-w, y, w, h
			elif attr=='bottom': 
				if scale==0:
					newcoordinates = x, y, w, h-value
				else:
					newcoordinates = x, value-h, w, h
			elif attr=='width': 
				newcoordinates = x, y, value, h
			elif attr=='height': 
				newcoordinates = x, y, w, value
			self.__updatecoordinates(newcoordinates, units, scale)

		elif attr=='z':
			self.__updatezindex(value)

		elif attr=='bgcolor':
			self.__updatebgcolor(value)

		elif attr=='soundLevel':
			self.__updatesoundlevel(value)

		else:
			print 'update',attr,'of region',regionname,'to',value,'(unsupported)'

		mmregion.SetPresentationAttr(attr, value)
		if debug: 
			print 'update',attr,'of region',regionname,'to',value


	def __updatecoordinates(self, coordinates, units, scale):
		if self.__region and self.__region.window:
			self.__region.window.updatecoordinates(coordinates, units, scale)

	def __updatezindex(self, z):
		if self.__region and self.__region.window:
			self.__region.window.updatezindex(z)

	def __updatebgcolor(self, color):
		if self.__region and self.__region.window:
			self.__region.window.updatebgcolor(color)
	
	def __updatesoundlevel(self, level):
		for chan in self.__regionContents:
			if hasattr(chan,'updatesoundlevel'):
				chan.updatesoundlevel(level)
	
	# update area attributes display value
	def __updatearea(self, value):
		attr = self.__attr
		node = self.__node
		name = node.attrdict.get('name')
		# notify/update display value if we have a channel
		if self.__chan:
			if self.__chan._played_anchor2button.has_key(name):
				button = self.__chan._played_anchor2button[name]
				if attr == 'coords':
					button.updatecoordinates(value)
			if debug:
				print 'update area',self.__attr,'of channel',self.__chan._name,'to',value
		elif debug:
			name = MMAttrdefs.getattr(self.__node, 'name')
			print 'update area',self.__attr,'of node',name,'to',value		
	

	# rem: scales = {-1:'slice', 0:'meet',1:'hidden', }
	def __updatesubregion(self, value):
		if not self.__chan:
			return # channel not ready yet
		attr = self.__attr
		chan = self.__chan
		mmchan = chan._attrdict

		# implemented fit='meet' (0) and fit='hidden' (1)
		if settings.activeFullSmilCss:
			scale = 1 # mmchan.getCssAttr('scale', 1)
			coordinates = self.__node.getPxGeom()
		else:
			scale = mmchan['scale']
			coordinates = mmchan.GetPresentationAttr('base_winoff')

		if coordinates and attr in ('position','left','top','width','height','right','bottom'):
			x, y, w, h = coordinates
			units = mmchan.get('units')
			if attr=='position':
				x, y = value
				newcoordinates = x, y, w, h
			elif attr=='left':
				if scale==0:
					newcoordinates = value, y, w-value, h
				else:
					newcoordinates = value, y, w, h
			elif attr=='top':
				if scale==0:
					newcoordinates = x, value, w, h-value
				else:
					newcoordinates = x, value, w, h
			elif attr=='right': 
				if scale==0:
					newcoordinates = x, y, w-value, h
				else:
					newcoordinates = value-w, y, w, h
			elif attr=='bottom': 
				if scale==0:
					newcoordinates = x, y, w, h-value
				else:
					newcoordinates = x, value-h, w, h
			elif attr=='width': 
				newcoordinates = x, y, value, h
			elif attr=='height': 
				newcoordinates = x, y, w, value
			if chan.window:
				chan.window.updatecoordinates(newcoordinates, units, scale)
		mmchan.SetPresentationAttr(attr, value)
		if debug:
			print 'update',self.__attr,'of channel',self.__chan._name,'to',value
			
	def getcurrentbasevalue(self, animator=None):
		cv = self.__domval
		for a in self.__animators:
			if animator and id(a) == id(animator):
				break
			if a.isAdditive():
				cv = a.addCurrValue(cv)
			else:
				cv = a.getCurrValue()
		return cv

###########################
# AnimateContext is an EffectiveAnimator repository
# We need a well-known repository so that we can find EffectiveAnimators
# from Animators (channel) context.
# Implements also operations that apply to all EffectiveAnimator objects
# and is a document level entity.

class AnimateContext:
	def __init__(self):
		self._effAnimators = {}
		self._id2key = {}

	def getEffectiveAnimator(self, targnode, targattr, domval):
		key = "n%d-%s" % (id(targnode), targattr)
		if self._effAnimators.has_key(key):
			return self._effAnimators[key]
		else:
			ea = EffectiveAnimator(targnode, targattr, domval)
			self._effAnimators[key] = ea
			self._id2key[id(ea)] = key
			return ea
	
	def removeEffectiveAnimator(self, ea):
		eaid = id(ea)
		if self._id2key.has_key(eaid):
			key = self._id2key[eaid]
			if debug: print 'removing eff animator', key
			del self._effAnimators[key]
			del self._id2key[eaid]

###########################
# Gen impl. rem:
# * restart doc removes all anim effects including frozen val
# * on syntax error: we can ignore animation effects but not timing
# * attrdefs specs: additive, legal_range 
# * an animation can effect indirectly more than one attributes (for example anim 'region')

###########################
# Animation semantics parser helpers:
# a set of functions that return a tuple 
# (domval, grins_attrname, type)

def getregionattr(node, attr):
	v = None
	if node._type == 'mmnode':
		d = node.attrdict
	else:
		d = node._region.attrdict

	if settings.activeFullSmilCss:
		if attr in ('position', 'size', 'left', 'top', 'width', 'height','right','bottom'):
			if node._type == 'mmnode':
				r = node.getPxGeom()
			elif node._type == 'region':
				r = node._region.getPxGeom()
			else:
				return None, attr, ''	
			if attr == 'position':
				return complex(r[0], r[1]), attr, 'position'
			elif attr == 'size':
				v = r[2], r[3]
			elif attr == 'left':
				v = r[0]
			elif attr=='top':
				v = r[1]
			elif attr == 'right':
				v = r[0] + r[2]
			elif attr == 'bottom':
				v = r[1] + r[3]
			elif attr == 'width':
				v = r[2]
			elif attr == 'height':
				v = r[3]
			return v, attr, 'int'

		elif attr == 'bgcolor':
			if d.has_key('bgcolor'):
				return d['bgcolor'], attr, 'color'
			else:
				return (0, 0, 0), attr, 'color'

		elif attr == 'z':
			if d.has_key('z'):
				return d['z'], attr, 'int'
			else:
				return 0, attr, 'int'

		elif attr == 'soundLevel':
			if d.has_key('soundLevel'):
				return d['soundLevel'], attr, 'float'
			else:
				return 0, attr, 'float'
		return None, attr, ''


	if attr in ('position', 'size', 'left', 'top', 'width', 'height','right','bottom'):
		if d.has_key('base_winoff'):
			r = d['base_winoff']
			if attr == 'position':
				return complex(r[0], r[1]), attr, 'position'
			elif attr == 'size':
				v = r[2], r[3]
			elif attr == 'left':
				v = r[0]
			elif attr=='top':
				v = r[1]
			elif attr == 'right':
				v = r[0] + r[2]
			elif attr == 'bottom':
				v = r[1] + r[3]
			elif attr == 'width':
				v = r[2]
			elif attr == 'height':
				v = r[3]
			return v, attr, 'int'
		
	elif attr == 'bgcolor':
		if d.has_key('bgcolor'):
			return d['bgcolor'], attr, 'color'
		else:
			return (0, 0, 0), attr, 'color'

	elif attr == 'z':
		if d.has_key('z'):
			return d['z'], attr, 'int'
		else:
			return 0, attr, 'int'

	elif attr == 'soundLevel':
		if d.has_key('soundLevel'):
			return d['soundLevel'], attr, 'float'
		else:
			return 0, attr, 'float'

	return None, attr, ''

def getareaattr(node, attr):
	d = node.attrdict
	if attr=='coords':
		if d.has_key('coords'):
			coords = d['coords']
			# use grins convention
			shape, coords = coords[0], coords[1:]
			return coords, attr, 'inttuple'
		else:
			return (0,0,1,1), attr, 'inttuple' 
	return None, attr, ''

def gettransitionattr(node, attr):
	return None, attr, ''

def getrenamed(node, attr):
	return MMAttrdefs.getattr(node, attr, 1), attr, MMAttrdefs.getattrtype(attr) 

smil_attrs = {'left':(lambda node:getregionattr(node,'left')),
	'top':(lambda node:getregionattr(node,'top')),
	'width':(lambda node:getregionattr(node,'width')),
	'height':(lambda node:getregionattr(node,'height')),
	'right':(lambda node:getregionattr(node,'right')),
	'bottom':(lambda node:getregionattr(node,'bottom')),
	'position':(lambda node:getregionattr(node,'position')),
	'backgroundColor': (lambda node:getregionattr(node,'bgcolor')),
	'z-index':(lambda node:getregionattr(node,'z')),
	'soundLevel':(lambda node:getregionattr(node,'soundLevel')),

	'coords':(lambda node:getareaattr(node,'coords')),
	'src': (lambda node:getrenamed(node,'file')),
	}

additivetypes = ['int','float','color','position','inttuple','floattuple']
alltypes = ['string',] + additivetypes

# implNote
# main decision attrs:
# valuesType, attrType, additivity
# elementTag
# syntaxError:	invalidTarget, invalidValues, invalidKeyTimes, invalidKeySplines,
#				invalidEnumAttr, invalidTimeManipAttr,
# notSMILBostonAnimTarget

# Animation semantics parser
class AnimateElementParser:
	def __init__(self, anim):
		self.__anim = anim			# the animate element node
		self.__elementTag = anim.attrdict['tag']
		self.__attrname = ''		# target attribute name
		self.__attrtype = ''		# in alltypes (see above)
		self.__domval = None		# document attribute value
		self.__target = None		# target node
		self.__hasValidTarget = 0	# valid target node and attribute

		self.__grinsattrname = ''	# grins internal target attribute name

		# locate target node
		# for some elements not represented by nodes (region, area, transition)
		# create a virtual node
		self.__isstdnode = 1
		if not hasattr(anim,'targetnode') or not anim.targetnode:
			te = MMAttrdefs.getattr(anim, 'targetElement')
			if te:
				root = anim.GetRoot()
				anim.targetnode = root.GetChildByName(te)
				if not anim.targetnode:
					self.__checkNotNodeElementsTargets(te)
			else:
				anim.targetnode = anim.GetParent()
				anim.targetnode._type = 'mmnode'	
		else:
			anim.targetnode._type = 'mmnode'
				
		if not anim.targetnode:
			# the target node does not exist within grins
			# maybe it is an element not represented as a node
			te = MMAttrdefs.getattr(anim, 'targetElement')
			print 'Failed to locate target element', te
			print '\t',self
			return
		else:
			self.__target = anim.targetnode

		# do we have a valid target node and attribute?
		self.__hasValidTarget = self.__checkTarget()

		# Read enumeration attributes
		self.__additive = MMAttrdefs.getattr(anim, 'additive')
		self.__calcMode = MMAttrdefs.getattr(anim, 'calcMode')
		self.__accumulate = MMAttrdefs.getattr(anim, 'accumulate')

		# Read time manipulation attributes
		# speed="1" is a no-op, and speed="-1" means play backwards
		# This speed is relative to parent.
		# The context absolute speed is set elsewhere.  
		self.__speed = MMAttrdefs.getattr(anim, 'speed')
		if self.__speed==0.0: # not allowed
			self.__speed=1.0
		self.__accelerate = MMAttrdefs.getattr(anim, 'accelerate')
		self.__decelerate = MMAttrdefs.getattr(anim, 'decelerate')
		dt =  self.__accelerate + self.__decelerate
		if dt>1.0:
			# *the timing module draft says accelerate is clamped to 1 and decelerate=1-accelerate
			self.__accelerate = self.__accelerate/dt
			self.__decelerate = self.__decelerate/dt
		self.__autoReverse = MMAttrdefs.getattr(anim, 'autoReverse')

	def __repr__(self):
		import SMILTreeWrite
		return SMILTreeWrite.WriteBareString(self.__anim)

	def getAnimator(self):
		if not self.__hasValidTarget:
			return None

		attr = self.__grinsattrname
		domval = self.__domval

		# set elements
		if self.__elementTag=='set':
			return self.__getSetAnimator()

		# to-only animation for additive attributes
		if self.__isToOnly() and self.__canBeAdditive() and self.__calcMode!='discrete':
			v = self.getTo()
			v = string.atof(v)
			anim = EffValueAnimator(attr, domval, v, self.getDuration())
			if self.__attrtype=='int':
				anim.setRetunedValuesConverter(_round)
			return anim

		# 1. Read animation attributes
		dur = self.getDuration()
		mode = self.__calcMode
		if mode == 'paced':
			# ignore times and splines for 'paced' animation
			times = splines = ()
		else:
			times = self.__getInterpolationKeyTimes() 
			splines = self.__getInterpolationKeySplines()
		accumulate = self.__accumulate
		additive = self.__additive

		# 1+: force first value display (fulfil: use f(0) if duration is undefined)
		if not dur or dur<0 or (type(dur)==type('') and dur=='indefinite'): dur=0

		# 2. return None on syntax or logic error

		if self.__elementTag != 'animateMotion':
			nvalues = self.__countInterpolationValues()
			if nvalues==0 or (nvalues==1 and mode!='discrete'):
				print 'values syntax error'
				return None

		# 3. Return explicitly animators for special attributes

		# for 'by-only animation' force: additive = 'sum' 
		if self.__isByOnly(): additive = 'sum'

		if self.__elementTag == 'animateColor' or self.__attrtype=='color':
			values = self.__getColorValues()
			anim = ColorAnimator(attr, domval, values, dur, mode, times, splines,
				accumulate, additive)
			self.__setTimeManipulators(anim)
			return anim

		if self.__elementTag=='animateMotion' or self.__attrtype=='position':
			strpath = MMAttrdefs.getattr(self.__anim, 'path')
			path = svgpath.Path()
			if strpath:
				path.constructFromSVGPathString(strpath)
			else:
				coords = self.__getNumPairInterpolationValues()
				path.constructFromPoints(coords)
			if path.getLength():
				anim = MotionAnimator(attr, domval, path, dur, mode, times, splines,
					accumulate, additive)
				self.__setTimeManipulators(anim)
				return anim
			else:
				return None

		# 4. Return an animator based on the attr type
		if debug: print 'Guessing animator for attribute',`self.__attrname`,'(', self.__attrtype,')'
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
		
		elif self.__attrtype == 'inttuple':
			values = self.__getNumTupleInterpolationValues()
			anim = IntTupleAnimator(attr, domval, values, dur, mode, times, splines,
				accumulate, additive)

		elif self.__attrtype == 'floattuple':
			values = self.__getNumTupleInterpolationValues()
			anim = FloatTupleAnimator(attr, domval, values, dur, mode, times, splines,
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
			return None
		attr = self.__attrname
		domval = self.__domval
		dur = self.getDuration()
		if not dur or dur<0 or (type(dur)==type('') and dur=='indefinite'): dur=0
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
		elif self.__attrtype == 'inttuple':
			value = self.__split(value)
			value = map(string.atoi, value)
			anim = SetAnimator(attr, domval, value, dur)	
		else:
			anim = SetAnimator(attr, domval, domval, dur)
		self.__setTimeManipulators(anim)
		return anim

	def getAttrName(self):
		return self.__attrname

	def getGrinsAttrName(self):
		return self.__grinsattrname

	def getDOMValue(self):
		return self.__domval
							
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

	def getPath(self):
		return MMAttrdefs.getattr(self.__anim, 'path')

	def getKeyTimes(self):
		return MMAttrdefs.getattr(self.__anim, 'keyTimes')

	def getKeySplines(self):
		return MMAttrdefs.getattr(self.__anim, 'keySplines')

	def getTargetNode(self):
		return self.__target
			
	# set time manipulators to the animator
	def __setTimeManipulators(self, anim):
		if self.__autoReverse:
			anim._setAutoReverse(1)
		if (self.__accelerate+self.__decelerate)>0.0:
			anim._setAccelerateDecelerate(self.__accelerate, self.__decelerate)
		if self.__speed!=1.0:
			anim._setSpeed(self.__speed)

	# check that we have a valid target
	def __checkTarget(self):
		# for animate motion the implicit target attribute is region.position
		if self.__elementTag=='animateMotion':
			self.__grinsattrname = self.__attrname = 'position'
			if settings.activeFullSmilCss:
				rc = None
				if self.__target._type == 'mmnode':
					rc = self.__target.getPxGeom()
				elif self.__target._type == 'region':
					ch = self.__target._region
					rc = ch.getPxGeom()
				if rc:
					x, y, w, h = rc
					self.__domval = complex(x, y)
					return 1
				return 0
			else:
				d = self.__target.GetChannel().attrdict
				if d.has_key('base_winoff'):
					base_winoff = d['base_winoff']
					self.__domval = complex(base_winoff[0], base_winoff[1])
					return 1
			return 0
				
		self.__attrname = MMAttrdefs.getattr(self.__anim, 'attributeName')
		if not self.__attrname:
			print 'failed to get attributeName'
			print '\t',self
			return 0

		if smil_attrs.has_key(self.__attrname):
			func = smil_attrs[self.__attrname]
			self.__domval, self.__grinsattrname, self.__attrtype = func(self.__target)
		else:
			self.__domval = MMAttrdefs.getattr(self.__target, self.__attrname)
			self.__grinsattrname = self.__attrname
			self.__attrtype = MMAttrdefs.getattrtype(self.__attrname)
			
		if self.__domval==None:
			print 'Failed to get original DOM value for attr',self.__attrname,'from node',self.__target
			print '\t',self
			return 0
		return 1

	def __isByOnly(self):
		values =  self.getValues()
		if values: return 0
		v1 = self.getFrom()
		if v1!='': return 0
		v2 = self.getTo()
		if v2!='': return 0
		return 1

	def __isToOnly(self):
		values =  self.getValues()
		if values: return 0
		v1 = self.getFrom()
		if v1!=None and v1!='': return 0
		v2 = self.getTo()
		if v2!=None and v2!='': return 1
		return 0

	def __canBeAdditive(self):
		return self.__attrtype == 'int' or self.__attrtype == 'float'

	# animation (value) types
	VALUES_ERROR, VALUES, FROM_TO, FROM_BY, NONE_TO, NONE_BY = range(6)
	def getAnimationType(self):
		if self.getValues()!=None or self.getPath()!=None:
			return AnimateElementParser.VALUES

		v1 = self.getFrom()
		v2 = self.getTo()
		dv = self.getBy()
		
		# if we don't have 'values' then 'to' or 'by' must be given
		if v2==None and dv==None:
			return AnimateElementParser.VALUES_ERROR

		if v1!=None:
			if v2!=None:			
				return AnimateElementParser.FROM_TO
			else:
				return AnimateElementParser.FROM_BY
		else:
			if v2!=None:			
				return AnimateElementParser.NONE_TO
			else:
				return AnimateElementParser.NONE_BY

	def safeatof(self, s):
		if s[-1]=='%':
			return 0.01*string.atof(s[:-1])
		else:
			return string.atof(s)
				
	# return list of interpolation values
	def __getNumInterpolationValues(self):	
		# if 'values' are given ignore 'from/to/by'
		values =  self.getValues()
		if values:
			try:
				return tuple(map(self.safeatof, string.split(values,';')))
			except ValueError:
				return ()
							
		# 'from' is optional
		# use 'zero' value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = 0
		if type(v1) == type(''): 
			v1 = self.safeatof(v1)

		# we must have a 'to' value (expl or through 'by')
		v2 = self.getTo()
		dv = self.getBy()
		if v2:
			v2 = self.safeatof(v2)
		elif dv:
			dv = self.safeatof(dv)
			v2 = v1 + dv
		else:
			return ()
		return v1, v2

	def __getNumPair(self, v):
		if not v: return None
		if type(v)==type(complex(0,0)):
			return v.real, v.imag
		v = v.strip()
		vl = self.__split(v)
		if len(vl)==2:
			x, y = vl
			return self.safeatof(x), self.safeatof(y)
		else:
			return None

	# return list of interpolation numeric pairs
	def __getNumPairInterpolationValues(self):	
		# if 'values' are given ignore 'from/to/by'
		values =  self.getValues()
		if values:
			strcoord = string.split(values,';')
			coords = []
			for str in strcoord:
				pt = self.__getNumPair(str)
				if pt!=None:
					coords.append(pt)
			return tuple(coords)

		# 'from' is optional
		# use 'zero' value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = complex(0,0)
		pt1 = self.__getNumPair(v1)
		if pt1==None: return ()

		v2 = self.getTo()
		dv = self.getBy()
		if v2:
			pt2 = self.__getNumPair(v2)
			if pt2!=None:
				return pt1, pt2
		if dv:
			dpt = self.__getNumPair(dv)
			if dpt:
				dx, dy = dpt
				x1, y1 = pt1
				return (x1, y1), (x1+dx,y1+dy)
		return ()

	# return list of interpolation numeric tuples
	def __getNumTupleInterpolationValues(self):	
		# if 'values' are given ignore 'from/to/by'
		values =  self.getValues()
		if values:
			strcoord = string.split(values,';')
			L = []
			for str in strcoord:
				t = self.__splitf(str)
				if t!=None:
					L.append(t)
			return tuple(L)

		# 'from' is optional
		# use 'zero' value if missing
		v1 = self.getFrom()
		if not v1:
			v1 = self.__domval
			L = []
			for i in range(len(self.__domval)):
				L.append(0)
			t1 = tuple(L)
		else:
			t1 = self.__splitf(v1)
		if t1==None: return ()

		v2 = self.getTo()
		dv = self.getBy()
		if v2:
			t2 = self.__splitf(v2)
			if t2!=None:
				return tuple(t1), tuple(t2)
		if dv:
			dt = self.__splitf(dv)
			if dt:
				ts = []
				for i in range(len(dt)):
					ts.append(t1[i]+dt[i])
				return t1, tuple(ts)
		return ()


	# return list of interpolation strings
	def __getAlphaInterpolationValues(self):
		
		# if values are given ignore from/to/by
		values =  self.getValues()
		if values:
			return string.split(values,';')
		
		v1 = self.getFrom()
		v2 = self.getTo()

		# a 'to' value must exist for string attributes
		if v2:
			if v1:
				return v1, v2
			else:
				return v2
		else:
			return ()


	# copy from SMILTreeRead
	def __convert_color(self, val):
		from colors import colors
		from SMILTreeRead import color
		val = string.lower(val)
		if colors.has_key(val):
			return colors[val]
		if val in ('transparent', 'inherit'):
			return 0, 0, 0 # XXX: val
		res = color.match(val)
		if res is None:
			print 'syntax error: bad color specification', val
			return  0, 0, 0 #XXX: 'transparent'
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
		if v1: 
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
		elif self.__calcMode != 'discrete': n = n + 1

		v2 = self.getTo()
		dv = self.getBy()
		if v2 or dv: n = n + 1
		return n

	# return keyTimes or an empty list on failure
	def __getInterpolationKeyTimes(self):
		keyTimes = self.getKeyTimes()
		if not keyTimes: return ()
		tl = string.split(keyTimes,';')

		# len of values must be equal to len of keyTimes
		lvl = self.__countInterpolationValues()
		if self.__calcMode=='discrete': lvl = lvl + 1
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
		sl = string.split(keySplines,';')
		
		# len of keySplines must be equal to num of intervals (=len(keyTimes)-1)
		tt = self.__getInterpolationKeyTimes()
		if tt and len(sl) != len(tt)-1:
			print 'intervals vs splines mismatch'
			return []
		if not tt and len(sl) != 1:
			print 'intervals vs splines mismatch'
			return []
		rl = []
		for e in sl:
			vl = self.__split(e)
			if len(vl)==4:
				x1, y1, x2, y2 = map(string.atof, vl)
			else:
				print 'splines syntax error'
			if x1<0.0 or x1>1.0 or x2<0.0 or x2>1.0 or y1<0.0 or y1>1.0 or y2<0.0 or y2>1.0:
				print 'splines syntax error'
			rl.append((x1, y1, x2, y2))
		return rl

	def __checkNotNodeElementsTargets(self, te):
		anim = self.__anim
		ctx = anim.GetContext()
		if ctx.channeldict.has_key(te):
			# region
			targchan = ctx.getchannel(te)
			if hasattr(targchan,'_vnode'):
				newnode = targchan._vnode
			else:
				newnode = MMNode.MMNode('imm',ctx,ctx.newuid())
				newnode.attrdict = targchan.attrdict.copy()
				newnode.attrdict['channel'] = te
				newnode.attrdict['tag'] = 'region'
				newnode._type = 'region'
				newnode._region = targchan
				targchan._vnode = newnode
			anim.targetnode = newnode
		elif ctx.transitions.has_key(te):
			# transition
			# XXX fix: create one virtual node per transition
			tr = ctx.transitions[te]
			newnode = MMNode.MMNode('imm',ctx,ctx.newuid())
			newnode.attrdict = tr.copy()
			newnode.attrdict['channel'] = te
			newnode.attrdict['tag'] = 'transition'
			newnode._type = 'transition'
			anim.targetnode = newnode
		else:
			# is it an area?
			root = anim.GetRoot()
			area = root.GetChildWithArea(te)
			if area:
				parent, a = area
				vnodename = '_vnode%s' % te
				if hasattr(parent,vnodename):
					newnode = getattr(parent, vnodename)
				else:
					newnode = MMNode.MMNode('imm', ctx, ctx.newuid())
					newnode.attrdict = parent.attrdict.copy()
					newnode.attrdict['tag'] = 'area'
					newnode.attrdict['coords'] = a.aargs
					newnode.attrdict['name'] = a.aid
					newnode.attrdict['parent'] = parent
					newnode.attrdict['type'] = a.atype
					newnode.attrdict['times'] = a.atimes
					newnode._type = 'area'
					parent.__dict__[vnodename] = newnode
				anim.targetnode = newnode
	
	def __splitf(self, arg, f=None):
		if not f: f = self.safeatof
		if type(arg)==type(''):
			arg = self.__split(arg)
		try:
			return map(f, arg)
		except:
			return arg
		
	_sep = re.compile('[ \t\r\n,]')
	def __split(self, str):
		if type(str)!=type(''):
			return str
		l = []
		end = len(str)
		i = 0
		while i<len(str):
			m = AnimateElementParser._sep.search(str, i)
			if m:
				begin, end = m.regs[0]
				if i != begin:
					l.append(str[i:begin])
				i = end
			else:
				i = i+1
		l.append(str[end:])
		return l


		


 
 