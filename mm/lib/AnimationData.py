__version__ = "$Id$"

import string

import MMAttrdefs

from fmtfloat import fmtfloat, round

import tokenizer

import colors

# AnimationData pattern:
# <ref ...>  <--- AnimationData third argument (animparent)
#   <animateMotion values="x1, y1; x2, y2; x3, y3" keyTimes="0;0.3;1.0" dur="use_attr_edit"/>
#   <animate attributeName="width" values="w1;w2;w3" keyTimes="0;0.3;1.0" dur="use_attr_edit"/>
#   <animate attributeName="height" values="h1;h2;h3" keyTimes="0;0.3;1.0" dur="use_attr_edit"/>
#   <animateColor attributeName="backgroundColor" values="rgb1;rgb2;rgb3" keyTimes="0;0.3;1.0" dur="use_attr_edit"/>
# </ref>

# abstraction of animation target 
# represents MMNode and MMRegion targets 
# makes explicit what is needed by AnimationData
class AnimationTarget:
	def __init__(self, root, node, animparent):
		self._root = root
		self._mmobj = node
		self._animparent = animparent
		
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

	# return the animations targeting self.mmobj
	def getAnimations(self):
		children = []
		for c in self._animparent.GetChildren():
			if c.GetType() == 'animate':
				children.append(c)

		# experimental: 
		# append all nodes targeting this, not only self._animparent children
		self.__getSelfAnimations(self._root, children)

		return children

	# write animation nodes under
	# should be the same getAnimations got them
	def getAnimationsParent(self):
		return self._animparent

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

class AnimationData:
	KEY_TIMES_WRITE_PREC = 3
	KEY_TIMES_EPSILON = 0.0001

	def __init__(self, root, target, animparent):
		self._target = AnimationTarget(root, target, animparent) # animation target
		self._data = []   # a list of key frames (rect, color)
		self._times = []  # key times list
		self._domrect, self._domcolor = self._target.getDomValues()

		self._animateMotion = None
		self._animateWidth = None
		self._animateHeight = None
		self._animateColor = None

	#
	#  public
	#
	def isEmpty(self):
		return len(self._times) == 0

	def clear(self):
		self._times = []
		self._data = []
		
	# animation editor call
	# set key times and data explicitly
	def setTimesData(self, times, data):
		assert type(times) == type([]), 'illegal times argument'
		assert type(data) == type([]), 'illegal data argument'
		assert len(times) == len(data), 'illegal arguments'
		self._times = times
		self._data = data

	def insertTimeData(self, index, keytime, data):
		assert type(data) == type(()), 'illegal data argument'
		assert len(data) == 2, 'illegal data argument'
		assert type(keytime) == type(1.0) or type(keytime) == type(1), 'illegal keytime argument'
		assert keytime >=0 and keytime <= 1, 'illegal keytime argument'
		assert index >=0 and index <= len(self._times), 'illegal index argument'
		self._times.insert(index, float(keytime))
		self._data.insert(index, data)

	def eraseTimeData(self, index):
		if index >=0 and index < len(self._times):
			del self._times[index]
			del self._data[index]

	def updateTime(self, index, newtime):
		if index >=0 and index < len(self._times):
			self._times[index]= newtime

	def updateData(self, index, newdata):
		if index >=0 and index < len(self._data):
			self._data[index]= newdata
			
	# animation editor call
	def getTimes(self):
		return self._times # [:] force protocol

	# animation editor call
	def getData(self):
		return self._data # [:] force protocol

	def initData(self):
		entry = self._domrect, self._domcolor
		self._data = [entry, entry]
		self._times = [0.0, 1.0]

	# read animate nodes and set self data
	def readData(self):
		animations = self._target.getAnimations()
		if not animations:
			return

		str = MMAttrdefs.getattr(animations[0], 'keyTimes')
		if str:
			self._times = self._strToFloatList(str)
		else:
			self._times = [0.0, 1.0]
			
		animateMotionValues = [] 
		animateWidthValues = []
		animateHeightValues = [] 
		animateColorValues = []
		for anim in animations:
			tag = anim.attrdict.get('atag')
			str = MMAttrdefs.getattr(anim, 'values')
			if not str:
				str1 = MMAttrdefs.getattr(anim, 'from')
				str2 = MMAttrdefs.getattr(anim, 'to')
				if str1 and str2:
					str = str1 + ';' + str2
			if str:
				if tag == 'animateMotion':
					animateMotionValues = self._strToPosList(str)
				elif tag == 'animate':
					attributeName = MMAttrdefs.getattr(anim, 'attributeName')
					if attributeName == 'width':
						animateWidthValues = self._strToIntList(str)
					elif attributeName == 'height':
						animateHeightValues = self._strToIntList(str)
				elif tag == 'animateColor':
					animateColorValues = self._strToColorList(str)
		
		n = len(self._times)

		dompos = self._domrect[:2]
		while len(animateMotionValues)<n:
			animateMotionValues.append(dompos)
				
		domwidth = self._domrect[2]
		while len(animateWidthValues)<n:
			animateWidthValues.append(domwidth)

		domheight = self._domrect[3]
		while len(animateHeightValues)<n:
			animateHeightValues.append(domheight)

		while len(animateColorValues)<n:
			animateColorValues.append(self._domcolor)

		self._data = []
		for i in range(n):
			x, y = animateMotionValues[i]
			w = animateWidthValues[i]
			h = animateHeightValues[i]
			rect = x, y, w, h
			color = animateColorValues[i]
			self._data.append((rect, color))
		
	# create animate nodes from self data
	def applyData(self, editmgr, replace=0, defaultDuration=2):
		em = editmgr
#		if not em.transaction():
#			return 0

		if replace:
			animations = self._target.getAnimations()
			for animation in animations:
				em.delnode(animation)

		animateMotionValues, animateWidthValues,\
		animateHeightValues, animateColorValues = self._dataToValuesAttr()
		keyTimes = self._timesToKeyTimesAttr()
		
		existing = {}
		animations = self._target.getAnimations()
		if animations:
			for anim in animations:
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
		
		parent = self._target.getAnimationsParent()
		targname = None
		if parent != self._target.getMMObj():
			targname = self._target.getUID()
		context = self._target.getContext()

		# update/insert animation nodes starting at this index
		nodeIndex = 0 
		
		anim = existing.get('pos')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateMotionValues)
		elif self._writeAnimateMotion:
			anim = context.newanimatenode('animateMotion')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateMotionValues, None, targname, dur = defaultDuration)
			em.addnode(parent, nodeIndex, anim)
			nodeIndex = nodeIndex + 1

		anim = existing.get('width')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateWidthValues)
		elif self._writeAnimateWidth:
			anim = context.newanimatenode('animate')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateWidthValues, 'width', targname, dur = defaultDuration)
			em.addnode(parent, nodeIndex, anim)
			nodeIndex = nodeIndex + 1

		anim = existing.get('height')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateHeightValues)
		elif self._writeAnimateHeight:
			anim = context.newanimatenode('animate')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateHeightValues, 'height', targname, dur = defaultDuration)
			em.addnode(parent, nodeIndex, anim)
			nodeIndex = nodeIndex + 1

		anim = existing.get('color')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateColorValues)
		elif self._writeAnimateColor:
			anim = context.newanimatenode('animateColor')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateColorValues, 'backgroundColor', targname, dur = defaultDuration)
			em.addnode(parent, nodeIndex, anim)
			nodeIndex = nodeIndex + 1
		
#		em.commit()
		return 1

	def createAnimators(self):
		if self.isEmpty(): 
			return

		import svgpath
		import Animators
		
		animateMotionValues, animateWidthValues,\
		animateHeightValues, animateColorValues = self._dataToValues()
		
		dur = 1.0
		times = self._times

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
	
	def getDomRect(self):
		return self._domrect

	def getColorAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateColor is not None:
			return self._animateColor.getValue(keyTime)
		return self._domcolor

	def getPosAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateMotion is not None:
			z = self._animateMotion.getValue(keyTime)
			return self._animateMotion.convert(z)
		return self._domrect[:2]

	def getWidthAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateWidth is not None:
			return round(self._animateWidth.getValue(keyTime))
		return self._domrect[2]

	def getHeightAt(self, keyTime):
		keyTime = self._clampKeyTime(keyTime)
		if self._animateHeight is not None:
			return round(self._animateHeight.getValue(keyTime))
		return self._domrect[3]

	#
	#  private
	#
	def _updateNode(self, node, times, values, attr = None, targname = None, dur = None):
		if attr is not None:
			node.attrdict['attributeName'] = attr
		if targname is not None:
			node.attrdict['targetElement'] = targname
		if times is not None:
			node.attrdict['keyTimes'] = times
		node.attrdict['values'] = values
		if dur is not None:
			node.attrdict['duration'] = dur
		node.attrdict['fill'] = 'freeze'
	
	def _clampKeyTime(self, keyTime):
		if keyTime<0.0:
			keyTime = 0.0
		elif keyTime>=1.0:
			keyTime = 1.0 - AnimationData.KEY_TIMES_EPSILON
		return keyTime

	def _setWriteFlagsOn(self):
		self._writeAnimateMotion = 1
		self._writeAnimateWidth = 1
		self._writeAnimateHeight = 1
		self._writeAnimateColor = 1

	def _dataToValues(self):
		animateMotionValues = [] 
		animateWidthValues = []
		animateHeightValues = [] 
		animateColorValues = []
		
		for rect, color in self._data:
			animateMotionValues.append(rect[:2])						
			animateWidthValues.append(rect[2])
			animateHeightValues.append(rect[3])
			animateColorValues.append(color)
		return animateMotionValues, animateWidthValues, animateHeightValues, animateColorValues

	def _dataToValuesAttr(self):
		animateMotionValues, animateWidthValues,\
		animateHeightValues, animateColorValues = self._dataToValues()

		self._setWriteFlagsOn()

		if self._domrect:
			self._writeAnimateMotion = 0
			for v in animateMotionValues:
				if v != self._domrect[:2]:
					self._writeAnimateMotion = 1
					break

			self._writeAnimateWidth = 0
			for v in animateWidthValues:
				if v != self._domrect[2]:
					self._writeAnimateWidth = 1
					break

			self._writeAnimateHeight = 0
			for v in animateHeightValues:
				if v != self._domrect[3]:
					self._writeAnimateHeight = 1
					break

		if self._domcolor:
			self._writeAnimateColor = 0
			for v in animateColorValues:
				if v != self._domcolor:
					self._writeAnimateColor = 1
					break
			
		animateMotionValues = self._posListToStr(animateMotionValues)
		animateWidthValues = self._intListToStr(animateWidthValues)
		animateHeightValues = self._intListToStr(animateHeightValues)
		animateColorValues = self._colorListToStr(animateColorValues)
		return animateMotionValues, animateWidthValues, animateHeightValues, animateColorValues

	def _timesToKeyTimesAttr(self):
		if len(self._times) > 2:
			return self._floatListToStr(self._times, prec = AnimationData.KEY_TIMES_WRITE_PREC)
		return None

	def _intListToStr(self, sl):
		str = ''
		for val in sl:
			str = str + '%d;' % val
		return str[:-1]

	def _floatListToStr(self, sl, prec = -1):
		str = ''
		for val in sl:
			str = str + '%s;' % fmtfloat(val, prec = prec)
		return str[:-1]
		
	def _posListToStr(self, sl):
		str = ''
		for point in sl:
			str = str + '%d %d;' % point
		return str[:-1]

	def _colorListToStr(self, sl):
		str = ''
		for rgb in sl:
			if colors.rcolors.has_key(rgb):
				s = colors.rcolors[rgb]
			else:
				s = '#%02x%02x%02x' % rgb
			str = str + s + ';'
		return str[:-1]

	def _strToIntList(self, str):
		sl = string.split(str,';')
		vl = []
		for s in sl:
			if s: 
				vl.append(string.atoi(s))
		return vl	

	def _strToFloatList(self, str):
		sl = string.split(str,';')
		vl = []
		for s in sl:
			if s: 
				vl.append(string.atof(s))
		return vl	
		
	def _strToPosList(self, str):
		sl = string.split(str,';')
		vl = []
		for s in sl:
			if s: 
				pair = self._getNumPair(s)
				if pair:
					vl.append(pair)
		return vl	

	def _getNumPair(self, str):
		if not str: return None
		str = string.strip(str)
		sl = tokenizer.splitlist(str, delims=' ,')
		if len(sl)==2:
			x, y = sl
			return string.atoi(x), string.atoi(y)
		return None

	def _strToColorList(self, str):
		vl = []
		try:
			vl = map(convert_color, string.split(str,';'))
		except ValueError:
			pass
		return vl


############################
# should go normally to parse utilities
# copy/paste form SMILTreeRead

def convert_color(val):
	from colors import colors
	from SMILTreeRead import color
	import SystemColors
	val = val.lower()
	if colors.has_key(val):
		return colors[val]
	if val in ('transparent', 'inherit'):
		return val
	if SystemColors.colors.has_key(val):
		return SystemColors.colors[val]
	res = color.match(val)
	if res is None:
		self.syntax_error('bad color specification')
		return None
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


