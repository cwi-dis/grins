__version__ = "$Id$"


import MMAttrdefs

class Animator:
	def __init__(self, attr, domval):
		self.__attr = attr
		self.__domval = domval

	def getValue(self, t):
		return self.__domval

	def getDOMValue(self):
		return self.__domval

	def getAttrName(self):
		return self.__attr

class ConstAnimator(Animator):
	def __init__(self, attr, domval, val):
		Animator.__init__(self, attr, domval)
		self.__val = val

	def getValue(self, t):
		return self.__val

class LinearAnimator(Animator):
	def __init__(self, domval, attr, fromval, toval, dur):
		Animator.__init__(self, attr, domval)
		self.__from = fromval
		self.__to = toval
		self.__dur = dur

	def getValue(self, t):
		if dur>0:
			return self.__from + (self.__to - self.__from)*t/dur
		return self.getDOMValue()

class URLPairAnimator(LinearAnimator):
	def getValue(self, t):
		if t < dur/2:
			return self.__from
		else:
			return self.__to


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
		self._dump()

	def getAnimator(self):
		if self.__hasValidTarget:
			return Animator(self.__attrname, self.__domval)
		return None

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
							
	def ___getEnumAttrs(self):
		self.__additive = MMAttrdefs.getattr(self.__anim, 'additive')
		self.__calcMode = MMAttrdefs.getattr(self.__anim, 'calcMode')
		self.__accumulate = MMAttrdefs.getattr(self.__anim, 'accumulate')

	def _dump(self):
		print 'animate attr:', self.__attrname
		for name, value in self.__anim.attrdict.items():
			print `name`, '=', `value`

		