__version__ = "$Id$"


import MMAttrdefs

class Animator:
	def __init__(self, attr, domval):
		self._attr = attr
		self._domval = domval

	def getValue(self, t):
		return self._domval

	def getDOMValue(self):
		return self._domval

	def getAttrName(self):
		return self._attr

class ConstAnimator(Animator):
	def __init__(self, attr, domval, val):
		Animator.__init__(self, attr, domval)
		self.__val = val

	def getValue(self, t):
		return self.__val

class LinearAnimator(Animator):
	def __init__(self, attr, domval, fromval, toval, dur):
		Animator.__init__(self, attr, domval)
		self._from = fromval
		self._to = toval
		self._dur = dur

	def getValue(self, t):
		if dur>0:
			return self._from + (self._to - self._from)*t/self._dur
		return self.getDOMValue()

class URLPairAnimator(LinearAnimator):
	def __init__(self, attr, domval, fromval, toval, dur):
		LinearAnimator.__init__(self, attr, domval, fromval, toval, dur)

	def getValue(self, t):
		if t < self._dur/2.0:
			return self._from
		else:
			return self._to


# take into account sum, acc
class CompositeAnimator:
	def __init__(self, animlist):
		self.__animators = animlist


class AnimateElementParser:
	# args anim and target are MMNode objects
	# anim  represents the animate element node
	def __init__(self, anim, target):
		self.__anim = anim
		self.__target = target

		self.__attrname = ''
		self.__domval = None
		self.__enable = 0

		self.__hasValidTarget = self.__checkTarget()
		self.__getEnumAttrs()

	def getAnimator(self):
		if not self.__hasValidTarget:
			return None

		v1 = self.getFrom()
		if not v1:
			v1 = self.__domval

		v2 = self.getTo()

		dv = self.getBy()

		dt = self.getDuration()

		if dt and v2 and self.__attrname=='file' and self.__calcMode=='linear':
			return URLPairAnimator(self.__attrname, self.__domval,
				v1, v2, dt)
		
		# ....

		return Animator(self.__attrname, self.__domval)

	def getAttrName(self):
		return self.__attrname

	def __checkTarget(self):
		self.__attrname = MMAttrdefs.getattr(self.__anim, 'attributeName')
		if not self.__attrname:
			print 'failed to get targetAttr', self.__anim
			return 0

		self.__domval = MMAttrdefs.getattr(self.__target, self.__attrname)
		if self.__domval==None:
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

	def getLoop(self):
		return MMAttrdefs.getattr(self.__anim, 'loop')

	def _dump(self):
		print 'animate attr:', self.__attrname
		for name, value in self.__anim.attrdict.items():
			print `name`, '=', `value`
