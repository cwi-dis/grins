__version__ = "$Id$"

import MMAttrdefs

# AnimationData pattern:
# <ref ...>
#   <animateMotion targetElement="xxx" values="x1, y1; x2, y2; x3, y3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
#   <animate targetElement="xxx" attributeName="width" values="w1, w2, w3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
#   <animate targetElement="xxx"  attributeName="height" values="h1, h2, h3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
#   <animateColor targetElement="xxx" attributeName="backgroundColor" values="rgb1, rgb2, rgb3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
# </ref>

class AnimationData:
	def __init__(self, node):
		self.node = node # animation target
		self.root = node.GetRoot()
		self.data = []   # a list of key frames (rect, color)
		self.times = []  # key times list

		# dom values for animated node
		# used for missing user values 
		self.dompos = None
		self.domwidth = None
		self.domheight = None
		self.domcolor = None
		self.initDomValues()
	
	#
	#  public
	#
	def isEmpty(self):
		return len(self.times)==0

	# animation editor call
	# set key times and data explicitly
	def setTimesData(self, times, data):
		assert len(times) == len(data), ''
		self.times = times
		self.data = data

	# animation editor call
	def getTimes(self):
		return self.times

	# animation editor call
	def getData(self):
		return self.data

	# read animate nodes and set self data
	def readData(self):
		children = self._getAnimateChildren()
		if not children:
			return

		str = MMAttrdefs.getattr(children[0], 'keyTimes')
		self.times = self._strToFloatList(str)

		animateMotionValues = [] 
		animateWidthValues = []
		animateHeightValues = [] 
		animateColorValues = []
		for anim in children:
			tag = anim.attrdict.get('atag')
			if tag == 'animateMotion':
				str = MMAttrdefs.getattr(anim, 'values')
				animateMotionValues = self._strToPosList(str)
			elif tag == 'animate':
				attributeName = MMAttrdefs.getattr(anim, 'attributeName')
				if attributeName == 'width':
					animateWidthValues = self._strToIntList(str)
				elif attributeName == 'height':
					animateHeightValues = self._strToIntList(str)
			elif tag == 'animateColor':
				animateColorValues = self._strToColorList(str)
		n = len(self.times)
		assert len(animateMotionValues) == n, ''
		assert len(animateWidthValues) == n, ''
		assert len(animateHeightValues) == n, ''
		assert len(animateColorValues) == n, ''
		for i in range(n):
			x, y = animateMotionValues[i]
			w = animateWidthValues[i]
			h = animateHeightValues[i]
			rect = x, y, w, h
			color = animateColorValues[i]
			self.data.append((rect, color))
	
	# create animate nodes from self data
	def applyData(self, editmgr):
		animateMotionValues, animateWidthValues,\
		animateHeightValues, animateColorValues = self._dataToValuesAttr()
		keyTimes = self._timesToKeyTimesAttr()
		
		existing = {}
		children = self._getAnimateChildren()
		if children:
			for anim in children:
				tag = anim.attrdict.get('atag')
				if tag == 'animateMotion':
					existing['pos'] = anim
				elif tag == 'animate':
					attributeName = MMAttrdefs.getattr(anim, 'attributeName')
					if attributeName == 'width':
						existing['width'] = anim
					elif attributeName == 'height':
						existing['height'] = anim
				elif tag == 'animateColor':
					existing['color'] = anim

		em = editmgr
		if not em.transaction():
			return 0
		
		anim = 	existing.get('pos')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateMotionValues)
		else:
			anim = self.root.context.newanimatenode('animateMotion')
			anim.targetnode = self.node
			self._updateNode(anim, keyTimes, animateMotionValues)
			em.addnode(self.node, 0, anim)

		anim = 	existing.get('width')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateWidthValues)
		else:
			anim = self.root.context.newanimatenode('animate')
			anim.targetnode = self.node
			self._updateNode(anim, keyTimes, animateWidthValues)
			em.addnode(self.node, 1, anim)

		anim = 	existing.get('height')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateHeightValues)
		else:
			anim = self.root.context.newanimatenode('animate')
			anim.targetnode = self.node
			self._updateNode(anim, keyTimes, animateHeightValues)
			em.addnode(self.node, 2, anim)

		anim = 	existing.get('color')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateColorValues)
		else:
			anim = self.root.context.newanimatenode('animate')
			anim.targetnode = self.node
			self._updateNode(anim, keyTimes, animateColorValues)
			em.addnode(self.node, 3, anim)
		
		em.commit()
		return 1

	
	def updateNode(self, node, times, values):
		node.attrdict['keyTimes'] = times
		node.attrdict['values'] = values

	def newNode(self, index, em, tag, times, values):
		newnode = self.root.context.newanimatenode(tag)
		newnode.targetnode = self.node
		em.addnode(self.node, index, newnode)

	#
	#  private
	#
	def _initDomValues(self):
		pass

	def _updateNode(self, node, times, values):
		node.attrdict['keyTimes'] = times
		node.attrdict['values'] = values

	def _getAnimateChildren(self):
		children = []
		for c in self.node.children:
			if c.GetType() == 'animate':
				children.append(c)
		return children

	def _dataToValuesAttr(self):
		animateMotionValues = [] 
		animateWidthValues = []
		animateHeightValues = [] 
		animateColorValues = []
		for rect, color in self.data:
			animateMotionValues.append(rect[:2])						
			animateWidthValues.append(rect[2])
			animateHeightValues.append(rect[3])
			animateColorValues.append(color)
		animateMotionValues = self._posListToStr(animateMotionValues)
		animateWidthValues = self._intListToStr(animateWidthValues)
		animateHeightValues = self._intListToStr(animateHeightValues)
		animateColorValues = self._colorListToStr(animateColorValues)
		return animateMotionValues, animateWidthValues, animateHeightValues, animateColorValues

	def _timesToKeyTimesAttr(self):
		return self._floatListToStr(self.times)

	def _intListToStr(self, sl):
		return ''

	def _floatListToStr(self, sl):
		return ''
		
	def _posListToStr(self, sl):
		return ''

	def _colorListToStr(self, sl):
		return ''

	def _strToIntList(self, str):
		return []

	def _strToFloatList(self, str):
		return []
		
	def _strToPosList(self, str):
		return []

	def _strToColorList(self, str):
		return []


