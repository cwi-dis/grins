__version__ = "$Id$"


# AnimationData pattern:
# <animateMotion targetElement="xxx" values="x1, y1; x2, y2; x3, y3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
# <animate targetElement="xxx" attributeName="width" values="w1, w2, w3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
# <animate targetElement="xxx"  attributeName="height" values="h1, h2, h3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>
# <animateColor targetElement="xxx" attributeName="backgroundColor" values="rgb1, rgb2, rgb3" keyTimes="0, 0.3, 1.0" dur="use_attr_edit"/>

class AnimationData:
	def __init__(self, node):
		self.node = node # animation target
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
		pass

	# create animate nodes from self data
	def applyData(self, editmgr):
		pass

	#
	#  private
	#
	def _initDomValues(self):
		pass

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
		return ''
		
	def _strToPosList(self, str):
		return ''

	def _strToColorList(self, str):
		return ''



