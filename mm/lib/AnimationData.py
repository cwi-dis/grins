__version__ = "$Id$"

import string

import MMAttrdefs

from fmtfloat import fmtfloat

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
		return children

	# write animation nodes under
	# should be the same getAnimations got them
	def getAnimationsParent(self):
		return self._animparent

	def _isRegion(self):
		return self._mmobj.getClassName() in ('Region', 'Viewport')



# AnimationData arguments:
# root: document root (MMNode)
# target: animation target element (MMNode or MMRegion)
# animparent: animations will be read and written under this node (MMNode)
# animparent can be target

class AnimationData:
	def __init__(self, root, target, animparent):
		self._target = AnimationTarget(root, target, animparent) # animation target
		self._data = []   # a list of key frames (rect, color)
		self._times = []  # key times list
		self._domrect, self._domcolor = self._target.getDomValues()

	#
	#  public
	#
	def isEmpty(self):
		return len(self._times)==0

	# animation editor call
	# set key times and data explicitly
	def setTimesData(self, times, data):
		assert len(times) == len(data), ''
		self._times = times
		self._data = data

	# animation editor call
	def getTimes(self):
		return self._times

	# animation editor call
	def getData(self):
		return self._data

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
		self._times = self._strToFloatList(str)

		animateMotionValues = [] 
		animateWidthValues = []
		animateHeightValues = [] 
		animateColorValues = []
		for anim in animations:
			tag = anim.attrdict.get('atag')
			str = MMAttrdefs.getattr(anim, 'values')
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

		for i in range(n):
			x, y = animateMotionValues[i]
			w = animateWidthValues[i]
			h = animateHeightValues[i]
			rect = x, y, w, h
			color = animateColorValues[i]
			self._data.append((rect, color))
		
	# create animate nodes from self data
	def applyData(self, editmgr):
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

		em = editmgr
		if not em.transaction():
			return 0

		anim = existing.get('pos')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateMotionValues)
		elif self._writeAnimateMotion:
			anim = context.newanimatenode('animateMotion')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateMotionValues, None, targname)
			em.addnode(parent, 0, anim)

		anim = existing.get('width')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateWidthValues)
		elif self._writeAnimateWidth:
			anim = context.newanimatenode('animate')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateWidthValues, 'width', targname)
			em.addnode(parent, 1, anim)

		anim = existing.get('height')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateHeightValues)
		elif self._writeAnimateHeight:
			anim = context.newanimatenode('animate')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateHeightValues, 'height', targname)
			em.addnode(parent, 2, anim)

		anim = existing.get('color')
		if anim is not None:
			self._updateNode(anim, keyTimes, animateColorValues)
		elif self._writeAnimateColor:
			anim = context.newanimatenode('animateColor')
			anim.targetnode = self._target.getTargetNode()
			self._updateNode(anim, keyTimes, animateColorValues, 'backgroundColor', targname)
			em.addnode(parent, 3, anim)
		
		em.commit()
		return 1

	#
	#  private
	#
	def _updateNode(self, node, times, values, attr = None, targname = None):
		if attr is not None:
			node.attrdict['attributeName'] = attr
		if targname is not None:
			node.attrdict['targetElement'] = targname
		node.attrdict['keyTimes'] = times
		node.attrdict['values'] = values
	
	def _setWriteFlagsOn(self):
		self._writeAnimateMotion = 1
		self._writeAnimateWidth = 1
		self._writeAnimateHeight = 1
		self._writeAnimateColor = 1

	def _dataToValuesAttr(self):
		animateMotionValues = [] 
		animateWidthValues = []
		animateHeightValues = [] 
		animateColorValues = []
		
		for rect, color in self._data:
			animateMotionValues.append(rect[:2])						
			animateWidthValues.append(rect[2])
			animateHeightValues.append(rect[3])
			animateColorValues.append(color)

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
		return self._floatListToStr(self._times)

	def _intListToStr(self, sl):
		str = ''
		for val in sl:
			str = str + '%d;' % val
		return str[:-1]

	def _floatListToStr(self, sl):
		str = ''
		for val in sl:
			str = str + '%s;' % fmtfloat(val)
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
		sl = string.split(str)
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


