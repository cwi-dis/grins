__version__ = "$Id$"


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
		return self.__from + (self.__to - self.__from)*t/dur


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


# map: attr -> (MMNode_AttrName, enable)
animAttrs = {'src': ('file', 1),
		}


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

	def getAnimator(self):
		if self.__hasValidTarget:
			return Animator(self.__attrname, self.__domval)
		return None

	def getAttrName(self):
		return self.__attrname

	def __checkTarget(self):
		anim = self.__anim
		target = self.__target
		self.__attrname = targetAttr  = anim.GetAttrDef('attributeName','')
		if not targetAttr:
			print 'failed to get targetAttr', anim
			return 0

		descr = animAttrs.get(targetAttr)
		if not descr:
			print 'failed to get attribute description',targetAttr
			return 0

		mmattrname, self.__enable = descr
		if not self.__enable:
			print 'animations are dissabled for attribute',targetAttr 
			return 0

		self.__domval = target.GetAttrDef(mmattrname, None)
		if self.__domval==None:
			print 'Failed to get original DOM value for attr',mmattrname,'from node',target
			return 0
		return 1
							
