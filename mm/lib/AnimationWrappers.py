__version__ = "$Id$"

import string

import MMAttrdefs

from fmtfloat import fmtfloat, round

import colors

debug = 0

# abstraction of animation target 
# represents MMNode and MMRegion targets 
# makes explicit what is needed by AnimationTarget
class AnimationTarget:
	def __init__(self, node):
		animparent = None
		target = None
		if hasattr(node, 'targetnode'):
			target = node.targetnode
		if target is None:
			target = node.GetParent()
		self._root = node.GetRoot()
		self._mmobj = target
		
	# return the underlying MMObj
	def getMMObj(self):
		return self._mmobj

	def getRoot(self):
		return self._root

	def getContext(self):
		return self._root.GetContext()

	# return animationNode.targetnode or None
	def getTargetNode(self):
		if self._isRegion():
			return None
		return self._mmobj

	# return dom values
	def getDomValues(self):
		if self._isRegion():
			try:
				rc = self._mmobj.getPxGeom()
			except:
				rc = None
			color = self._mmobj.get('bgcolor')
		else:
			try:
				rc = self._mmobj.getPxGeom()
			except:
				rc = None
			color = self._mmobj.attrdict.get('bgcolor')
		return rc, color
	
	# return targetElement attribute
	def getUID(self):
		if self._isRegion():
			return self._mmobj.GetUID()
		return self._mmobj.GetRawAttrDef('name', None)

	def _isRegion(self):
		return self._mmobj.getClassName() in ('Region', 'Viewport')

	def __getSelfAnimations(self, parent, children):
		uid = self.getUID()
		for node in parent.GetChildren():
			ntype = node.GetType()
			if ntype == 'animate':
				anim = None
				if node.targetnode == self._mmobj:
					anim = node
				elif node.GetParent() == self._mmobj:
					anim = node
				else:
					te = MMAttrdefs.getattr(node, 'targetElement')
					if te and te == uid:
						anim = node
				if anim is not None and anim not in children: 
					children.append(anim)
			self.__getSelfAnimations(node, children)

class AnimationDefaultWrapper:
	def createAnimators(self, animnode):
		self._target = AnimationTarget(animnode) # animation target
		self._domrect, self._domcolor = self._target.getDomValues()

	def updateAnimators(self, node):
		# for use re-create animators
		self.createAnimators(node)

	def getRectAt(self, keyTime):
		return self._domrect
	
	def getColorAt(self, keyTime):
		self._domcolor
		
	def getPosAt(self, keyTime):
		return self._domrect[:2]

	def getWidthAt(self, keyTime):
		return self._domrect[2]

	def getHeightAt(self, keyTime):
		return self._domrect[3]

	def getKeyTimeList(self):
		return [0, 1]
	
class AnimationParWrapper(AnimationDefaultWrapper):
	def __init__(self):
		self._animateMotion = None
		self._animateWidth = None
		self._animateHeight = None
		self._animateColor = None

	def createAnimators(self, animnode):
		import svgpath
		import Animators

		AnimationDefaultWrapper.createAnimators(self, animnode)

		animvals = animnode.GetAttrDef('animvals', [])

		if debug:
			print 'Create animator, animvals=',animvals
		
		self._times = times = []
		self._animateMotionValues = animateMotionValues = []
		self._animateWidthValues = animateWidthValues = []
		self._animateHeightValues = animateHeightValues = []
		self._animateColorValues = animateColorValues = []
		
		# XXX check that the list of values are consistents
		for time, vals in animvals:
			times.append(time)
			left = vals.get('left')
			top = vals.get('top')
			if left is not None and top is not None:
				animateMotionValues.append((left, top))
			width = vals.get('width')
			if width is not None:
				animateWidthValues.append(width)
			height = vals.get('height')
			if height is not None:
				animateHeightValues.append(height)
			bgcolor = vals.get('bgcolor')
			if bgcolor is not None:
				animateColorValues.append(bgcolor)

		if debug:
			print '**************************'
			print 'Create animator, values='
			print 'animateMotion:',animateMotionValues
			print 'animateWidth:',animateWidthValues
			print 'animateHeight:',animateHeightValues
			print 'animateColor:',animateColorValues
			print '**************************'
																				
		dur = 1.0

		# animateMotion
		if len(animateMotionValues) >= 2:
			path = svgpath.Path()
			path.constructFromPoints(animateMotionValues)
			domval = complex(self._domrect[0],self._domrect[1])
			self._animateMotion = Animators.MotionAnimator('position', domval, path, dur, mode='linear', times=times)
		else:
			self._animateMotion = None
			
		# animate width and height
		if len(animateWidthValues) >= 2:
			self._animateWidth = Animators.Animator('width', self._domrect[2], animateWidthValues, dur, mode='linear', times=times)
		else:
			self._animateWidth = None
			
		if len(animateHeightValues) >= 2:
			self._animateHeight = Animators.Animator('height', self._domrect[3], animateHeightValues, dur, mode='linear', times=times)
		else:
			self._animateHeight = None
			
		# animate color
		try:
			self._animateColor = Animators.ColorAnimator('backgroundColor', self._domcolor, animateColorValues, dur, mode='linear', times=times)
		except:
			self._animateColor = None

	def getRectAt(self, keyTime):
		x, y = self.getPosAt(keyTime)
		w = self.getWidthAt(keyTime)
		h = self.getHeightAt(keyTime)
		return x, y, w, h
	
	def getColorAt(self, keyTime):
		if self._animateColor is not None and len(self._animateColorValues) > 0 and keyTime >= 0:
			if keyTime >= 1:
				return self._animateColorValues[-1]
			return self._animateColor.getValue(keyTime)
		return AnimationDefaultWrapper.getColorAt(self, keyTime)

	def getPosAt(self, keyTime):
		if self._animateMotion is not None and len(self._animateMotionValues) > 0 and keyTime >= 0:
			if keyTime >= 1:
				return self._animateMotionValues[-1]
			z = self._animateMotion.getValue(keyTime)
			left, top = self._animateMotion.convert(z)
			left = round(int(left))
			top = round(int(top))
			return left, top
		return AnimationDefaultWrapper.getPosAt(self, keyTime)

	def getWidthAt(self, keyTime):
		if self._animateWidth is not None and len(self._animateWidthValues) > 0 and keyTime >= 0:
			if keyTime >= 1:
				return self._animateWidthValues[-1]
			return round(int(self._animateWidth.getValue(keyTime)))
		return AnimationDefaultWrapper.getWidthAt(self, keyTime)

	def getHeightAt(self, keyTime):
		if self._animateHeight is not None and len(self._animateHeightValues) > 0 and keyTime >= 0:
			if keyTime >= 1:
				return self._animateHeightValues[-1]
			return round(int(self._animateHeight.getValue(keyTime)))
		return AnimationDefaultWrapper.getHeightAt(self, keyTime)

	def getKeyTimeList(self):
		return self._times

def getAnimationWrapper(animnode):
	type = animnode.GetType()
	if type == 'animpar':
		return AnimationParWrapper()
	else:
		return AnimationDefaultWrapper()
	