__version__ = "$Id$"

import string

import MMAttrdefs

from fmtfloat import fmtfloat, round

import colors

debug = 0

# abstraction of animation target 
# represents MMNode and MMRegion targets 
# makes explicit what is needed by AnimationData
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


# AnimationData arguments:
# root: document root (MMNode)
# target: animation target element (MMNode or MMRegion)
# animparent: animations will be read and written under this node (MMNode)
# animparent can be target

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

class AnimationParWrapper(AnimationDefaultWrapper):
	KEY_TIMES_EPSILON = 0.0001

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
		
		times = []
		animateMotionValues = []
		animateWidthValues = []
		animateHeightValues = []
		animateColorValues = []
		
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
		path = svgpath.Path()
		path.constructFromPoints(animateMotionValues)
		domval = complex(self._domrect[0],self._domrect[1])
		self._animateMotion = Animators.MotionAnimator('position', domval, path, dur, mode='linear', times=times)
		
		# animate width and height
		self._animateWidth = Animators.Animator('width', self._domrect[2], animateWidthValues, dur, mode='linear', times=times)
		self._animateHeight = Animators.Animator('height', self._domrect[3], animateHeightValues, dur, mode='linear', times=times)

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
		keyTime = self._clampKeyTime(keyTime)
		if self._animateColor is not None:
			return self._animateColor.getValue(keyTime)
		return AnimationDefaultWrapper.getColorAt(self)

	def getPosAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateMotion is not None:
			z = self._animateMotion.getValue(keyTime)
			left, top = self._animateMotion.convert(z)
			left = round(int(left))
			top = round(int(top))
			return left, top
		return AnimationDefaultWrapper.getPosAt(self)

	def getWidthAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateWidth is not None:
			return round(int(self._animateWidth.getValue(keyTime)))
		return AnimationDefaultWrapper.getWidthAt(self)

	def getHeightAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateHeight is not None:
			return round(int(self._animateHeight.getValue(keyTime)))
		return AnimationDefaultWrapper.getHeightAt(self)

	#
	#  private
	#		

	def _clampKeyTime(self, keyTime):
		if keyTime<0.0:
			keyTime = 0.0
		elif keyTime>=1.0:
			keyTime = 1.0 - AnimationParWrapper.KEY_TIMES_EPSILON
		return keyTime

def getAnimationWrapper(animnode):
	type = animnode.GetType()
	if type == 'animpar':
		return AnimationParWrapper()
	else:
		return AnimationDefaultWrapper()
	