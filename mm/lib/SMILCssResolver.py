def convertToPx(value, containersize):
	if type(value) == type(0):
		return value
	elif type(value) == type(0.0):
		return int(value*containersize)
	else:
		return None

class SMILCssResolver:
	def __init__(self, documentContext):
		self.rootNode = None
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []
		self.documentContext = documentContext

	def newRootNode(self):
		node = RootNode(self)
		self.rootNode = node
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []

		return node

	def updateAll(self):
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []
		self.rootNode.updateAll()
		self._updateListeners()

	def getDocumentContext(self):
		return self.documentContext
	
	def setRootSize(self, node, width, height):
		node.setSize(width, height)

	def setRawAttrPos(self, region, left, width, right, top, height, bottom):
		region.setRawValues(left, width, right, top, height, bottom)

	def changeRawValue(self, node, name, value):
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []
		node.changeRawValue(name, value)
		self._updateListeners()

	def changePxValue(self, node, name, value):
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []
		node.changePxValue(name, value)
		self._updateListeners()

	def _updateListeners(self):
		for listener, geom in self.nodeGeomChangedList:
			listener(geom)
		for listener, attrname, value in self.rawAttributesChangedList:
			listener(attrname, value)

	def newRegion(self):
		node = RegionNode()

		return node

	def link(self, node, container):
		node.link(container)

	def unlink(self, node):
		node.unlink()
		
	def newMedia(self):
		node = MediaNode()

		return node

	def removeRegion(self, region, container):
		container.removeRegion(region)

	def setIntrinsicSize(self, media, width, height):
		media.setIntrinsicSize(width, height)

	def setAlignAttr(self, node, name, value):
		node.setAlignAttr(name, value)
		
	def changeAlignAttr(self, node, name, value):
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []		
		node.changeAlignAttr(name, value)
		self._updateListeners()
				
	def setGeomListener(self, node, listener):
		node.setGeomListener(listener)

	def setRawPosAttrListener(self, node, listener):
		node.setRawPosAttrListener(listener)

	def removeListener(self, node, listener):
		node.removeListener(listener)

	def getPxGeom(self, node):
		return node.getPxGeom()
	
	def _onPxValuesChanged(self, node, geom):
		if node.pxValuesListener != None:
			self.nodeGeomChangedList.append((node.pxValuesListener, geom))

	def _onRawValuesChanged(self, node, attrname, value):
		if node.rawValuesListener != None:
			self.rawAttributesChangedList.append((node.rawValuesListener, attrname, value))

# ###############################################################################
# Region hierarchy
# ###############################################################################

class Node:
	def __init__(self):
		self.children = []
		self.container = None
		self.context = None
		self.pxValuesListener = None
		self.rawValuesListener = None

		self.left = None
		self.width = None
		self.right = None
		self.top = None
		self.height = None
		self.bottom = None

		self.pxleft = None
		self.pxwidth = None
		self.pxtop = None
		self.pxheight = None

		self.pxValuesHasChanged = 0
		
		self.isInit = 0

	def link(self, container):
		self.container = container
		self.context = container.context		
		container.children.append(self)

		if container.isInit:			
			self._initialUpdate()
			self.isInit = 1

	def unlink(self):
		self.isInit = 0
		self.container = None
		try:
			index = self.container.index(self)
			del self.container[index]
		except:
			pass
		
	def setRawPosAttrListener(self, listener):
		self.rawValuesListener = listener

	def setGeomListener(self, listener):
		self.pxValuesListener = listener

class RegionNode(Node):
	def __init__(self):
		Node.__init__(self)
		self.regAlign = None
		self.regPoint = None
		self.scale = None

	def _initialUpdate(self):
		self.pxleft, self.pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, self.container.pxwidth)
		self.pxtop, self.pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, self.container.pxheight)
		self._onGeomChanged()

		for child in self.children:
			child._initialUpdate()

	def setRawValues(self, left, width, right, top, height, bottom):
		if width != None and width <= 0: width = 1
		if height != None and height <= 0: height = 1
		
		self.left = left
		self.width = width
		self.right = right
		self.top = top
		self.height = height
		self.bottom = bottom

	def _resolveCSS2Rule(self, beginValue, sizeValue, endValue, containersize):
		pxbegin = None
		pxsize = None
		if beginValue == None:
			if sizeValue == None:
				if endValue == None:
					pxbegin = 0
					pxsize = containersize
				else:
					pxsize = containersize-convertToPx(endValue, containersize)
					pxbegin = containersize-pxsize
			elif endValue == None:
				pxbegin = 0
				pxsize = convertToPx(sizeValue,containersize)
			else:
				pxsize = convertToPx(sizeValue, containersize)
				pxbegin = containersize-pxsize-convertToPx(endValue, containersize)                        
		elif sizeValue == None:
			if endValue == None:
				pxbegin = convertToPx(beginValue, containersize)
				pxsize = containersize-pxbegin
			else:
				pxbegin = convertToPx(beginValue, containersize)
				pxsize = containersize-pxbegin-convertToPx(endValue, containersize)
		elif endValue == None:
			pxbegin = convertToPx(beginValue, containersize)
			pxsize = convertToPx(sizeValue, containersize)
		else:
			pxbegin = convertToPx(beginValue, containersize)
			pxsize = convertToPx(sizeValue, containersize)

		return pxbegin, pxsize

	def _updatePxOnContainerWidthChanged(self):
		self.pxValuesHasChanged = 0
		
		containersize = self.container.pxwidth        
		pxleft, pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, containersize)

		if pxleft != self.pxleft:
			self.pxleft = pxleft
			self._onChangePxValue('left',pxleft)
		if pxwidth != self.pxwidth:
			self._onChangePxValue('width',pxwidth)
			self.pxwidth = pxwidth
			
			if self.pxValuesHasChanged:
				self._onGeomChanged()
				
			for child in self.children:
				child._updatePxOnContainerWidthChanged()
			# the commit is already done
			return

		if self.pxValuesHasChanged:
			self._onGeomChanged()

	def _updatePxOnContainerHeightChanged(self):
		self.pxValuesHasChanged = 0
		
		containersize = self.container.pxheight
		pxtop, pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, containersize)
		if pxtop != self.pxtop:
			self.pxtop = top
			self._onChangePxValue('top',pxtop)
		if pxheight != self.pxheight:
			self._onChangePxValue('height',pxheight)
			self.pxheight = height
			
			if self.pxValuesHasChanged:
				self._onGeomChanged()
				
			for child in self.children:
				child._updatePxOnContainerHeightChanged()
			# the commit is already done
			return

		if self.pxValuesHasChanged:
			self._onGeomChanged()

	# change an attribute value as spefified in the document
	# determinate new pixel values (left/width/top and height)
	# determinate recursively all changement needed in children as well
	# for each pixel value changed, the callback onChangePxValue is called
	def changeRawValue(self, name, value):
		self.pxValuesHasChanged = 0

		if name in ('left', 'width', 'right'):
			if name == 'left':
				self.left = value
			elif name == 'width':
				if value != None and value <= 0: value = 1
				self.width = value
			elif name == 'right':
				self.right = value

			pxleft, pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, self.container.pxwidth)
			if pxleft != self.pxleft:
				self._onChangePxValue('left',pxleft)
				self.pxleft = pxleft
			if pxwidth != self.pxwidth:
				self._onChangePxValue('width',pxwidth)
				self.pxwidth = pxwidth

				if self.pxValuesHasChanged:
					self._onGeomChanged()
				
				for child in self.children:
					child._updatePxOnContainerWidthChanged()
				# the commit is already done
				return
					
		elif name in ('top', 'height', 'bottom'):
			if name == 'top':
				self.top = value
			elif name == 'height':
				if value != None and value <= 0: value = 1
				self.height = value
			elif name == 'bottom':
				self.bottom = value

			pxtop, pxheight = self._resolveCSS2Rule(self, self.top, self.height, self.bottom, self.container.pxheight)
			if pxtop != self.pxtop:
				self._onChangePxValue('top',pxtop)
				self.pxtop = pxtop
			if pxheight != self.pxheight:
				self._onChangePxValue('height',pxheight)
				self.pxheight = pxheight
				
				if self.pxValuesHasChanged:
					self._onGeomChanged()

				for child in self.children:
					child._updatePxOnContainerHeightChanged()
				return

		if self.pxValuesHasChanged:
			self._onGeomChanged()

	def changeAlignAttr(self, name, value):
		if name == 'regPoint':
			self.regPoint = value
		elif name == 'regAlign':
			self.regAlign = value
		elif name == 'scale':
			self.scale = value

		# for now, in this case update all children			
		for child in self.children:
			child._updateRawOnContainerWidthChanged()

	def _updateRawOnContainerWidthChanged(self):
		if type(self.left) is type(0.0):
			self.left = float(self.pxleft/self.container.pxwidth)
			self._onChangeRawValue('left',self.left)
		elif type(self.width) is type(0.0):
			self.width = float(self.pxwidth/self.container.pxwidth)
			self._onChangeRawValue('width',self.width)
			for child in self.children:
				child._updateRawOnContainerWidthChanged()       
		elif type(self.right) is type(0.0):
			self.right = float((self.container.pxwidth-self.pxleft-self.pxwidth)/self.container.pxwidth)
			self._onChangeRawValue('right',self.right)

	def _updateRawOnContainerHeightChanged(self):
		if type(self.top) is type(0.0):
			self.top = float(self.pxtop/self.container.pxheight)
			self._onChangeRawValue('top',self.top)
		elif type(self.height) is type(0.0):
			self.height = float(self.pxheight/self.container.pxheight)
			self._onChangeRawValue('height',self.height)
			for child in self.children:
				child._updateRawOnContainerHeightChanged()
		elif type(self.bottom) is type(0.0):
			self.bottom = float((self.container.pxheight-self.pxtop-self.pxheight)/self.container.pxheight)
			self._onChangeRawValue('bottom',self.bottom)

	# change an pixel value only (left/width/top and height)
	# according to the changement modify the raw values in order to keep all constraint valid
	# for each raw value changed, the callback onChangeRawValue is called
	def changePxValue(self, name, value):
		self.pxValuesHasChanged = 0

		if name == 'left':
			if type(self.left) is type(0.0):
				self.left = float(value)/self.container.pxwidth
				self._onChangeRawValue('left',self.left)
			elif type(self.left) is type(0):
				self.left = value
				self._onChangeRawValue('left',self.left)
			elif type(self.right) is type(0.0):
				offset = value-self.pxleft
				self.right = float(self.right+offset)/self.container.pxwidth
				self._onChangeRawValue('right',self.right)
			elif type(self.right) is type(0):
				offset = value-self.pxleft
				self.right = self.right+offset
				self._onChangeRawValue('right',self.right)
			else:
				self.left = value
				self._onChangeRawValue('left',self.left)

			self._onChangePxValue('left',value)
		elif name == 'width':
			if type(self.width) is type(0.0):
				self.width = float(value)/self.container.pxwidth
				self._onChangeRawValue('width',self.width)
			elif type(self.width) is type(0):
				self.width = value
				self._onChangeRawValue('width',self.width)
			elif type(self.left) is not None and type(self.right) is not None:
				if type(self.right) is type(0.0):
					offset = value-self.pxwidth
					self.width = float(self.width+offset)/self.container.pxwidth
					self._onChangeRawValue('width',self.width)
				elif type(self.right) is type(0):
					offset = value-self.pxwidth
					self.width = self.width+offset
					self._onChangeRawValue('width',self.width)
			else:
				self.width = value
				self._onChangeRawValue('width',self.width)

			for child in self.children:
				child._updateRawOnContainerWidthChanged()
			self._onChangePxValue('width',value)

		elif name == 'top':
			if type(self.top) is type(0.0):
				self.top = float(value)/self.container.pxheight
				self._onChangeRawValue('top',self.top)
			elif type(self.top) is type(0):
				self.top = value
				self._onChangeRawValue('top',self.top)
			elif type(self.bottom) is type(0.0):
				offset = value-self.pxtop
				self.bottom = float(self.bottom+offset)/self.container.pxheight
				self._onChangeRawValue('bottom',self.bottom)
			elif type(self.bottom) is type(0):
				offset = value-self.pxtop
				self.bottom = self.bottom+offset
				self._onChangeRawValue('bottom',self.bottom)
			else:
				self.top = value
				self._onChangeRawValue('top',self.top)

			self._onChangePxValue('top',value)

		elif name == 'height':
			if type(self.height) is type(0.0):
				self.height = float(value)/self.container.pxheight
				self._onChangeRawValue('height',self.height)
			elif type(self.height) is type(0):
				self.height = value
				self._onChangeRawValue('height',self.height)
			elif type(self.top) is not None and type(self.bottom) is not None:
				if type(self.bottom) is type(0.0):
					offset = value-self.pxheight
					self.height = float(self.height+offset)/self.container.pxheight
					self._onChangeRawValue('height',self.height)
				elif type(self.bottom) is type(0):
					offset = value-self.pxheight
					self.height = self.height+offset
					self._onChangeRawValue('height',self.height)
			else:
				self.height = value
				self._onChangeRawValue('height',self.height)

			for child in self.children:
				child._updateRawOnContainerHeightChanged()
			self._onChangePxValue('height',height)

		if self.pxValuesHasChanged:
			self._onGeomChanged()

	def _onChangeRawValue(self, name, value):
		self.context._onRawValuesChanged(self, name, value)

	def _onChangePxValue(self, name, value):
		self.pxValuesHasChanged = 1

	def _onGeomChanged(self):
		self.context._onPxValuesChanged(self, self.getPxGeom())

	def getPxGeom(self):
		return (self.pxleft, self.pxtop, self.pxwidth, self.pxheight)
		
	def getScale(self):
		if self.scale != None:
			return self.scale
		else:
			# default value: hidden
			# todo: get value from mmattrdef
			return 1
		
	def getRegPoint(self):
		if self.regPoint != None:
			return self.regPoint
		else:
			# default value: topleft
			# todo: get value from mmattrdef
			return 'topLeft'
		
	def getRegAlign(self):
		if self.regAlign != None:
			return self.regAlign

		# if no regAlign defined here, the default come from regPoint
		return None
	
class RootNode(RegionNode):
	def __init__(self, context):
		Node.__init__(self)
		self.context = context

	def setSize(self, width, height):
		if type(width) is not type(0):
			return 
		if type(height) is not type(0):
			return 

		self.pxwidth = width
		self.pxheight = height
		# we assume that this node is init as soon as we know its size
		self.isInit = 1

	def updateAll(self):
		if self.isInit:
			self._onGeomChanged()
			for child in self.children:
				child._initialUpdate()
			
	def _onGeomChanged(self):
		self.context._onPxValuesChanged(self, self.getPxGeom())

	def getPxGeom(self):
		return (self.pxwidth, self.pxheight)

class MediaNode(Node):
	def __init__(self):
		Node.__init__(self)
		self.alignHandler = None
		self.regAlign = None
		self.regPoint = None
		self.scale = None
		self.intrinsicWidth = None
		self.intrinsicHeight = None

	def _initialUpdate(self):
		self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
		self._onGeomChanged()

	def setIntrinsicSize(self, width, height):
		# avoid crashes
		if width <= 0: width = 1
		if height <= 0: height = 1
		self.intrinsicWidth = width
		self.intrinsicHeight = height

	def setAlignAttr(self, name, value):
		if name == 'regPoint':
			self.regPoint = value
		elif name == 'regAlign':
			self.regAlign = value
		elif name == 'scale':
			self.scale = value
		
	def changeAlignAttr(self, name, value):
		self.setAlignAttr(name, value)

		self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
		self._onGeomChanged()

	def _updateOnContainerHeightChanged(self):
		self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
		self._onGeomChanged()
		
	def _updateOnContainerWidthChanged(self):
		self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
		self._onGeomChanged()
	
	def _updatePxOnContainerHeightChanged(self):
		self._updateOnContainerHeightChanged()

	def _updateRawOnContainerHeightChanged(self):
		self._updateOnContainerHeightChanged()

	def _updatePxOnContainerWidthChanged(self):
		self._updateOnContainerWidthChanged()

	def _updateRawOnContainerWidthChanged(self):
		self._updateOnContainerWidthChanged()
			
	# get the space display area of media according to registration points /alignement and fit attribute
	# return pixel values
	def _getMediaSpaceArea(self):

		# if no intrinsic size, the size area is the entire region		
		if self.intrinsicHeight == None or self.intrinsicWidth == None:
			return self.container.pxleft, self.container.pxwidth, self.container.pxtop, self.container.pxheight
		
		# get fit attribute
		scale = self.getScale()

		# get regpoint
		# for now, regpoint come from directly MMContext.
		# It's not a problem as long as regpoint element is not animable
		regPoint = self.getRegPoint()
		regPointObject = self.context.getDocumentContext().GetRegPoint(regPoint)
		
		regpoint_x = regPointObject.getx(self.container.pxwidth)
		regpoint_y = regPointObject.gety(self.container.pxheight)

		# get regalign
		regalign = self.getRegAlign(regPointObject)

		# this algorithm depends of fit attribute
		if scale == 1:  #hidden
			area_height = self.intrinsicHeight
			area_width = self.intrinsicWidth

		elif scale == 0: # meet
			if regalign in ('topLeft', 'topMid', 'topRight'):
				area_height = self.container.pxheight-regpoint_y
			if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
				area_width = self.container.pxwidth-regpoint_x
			if regalign in ('topMid', 'center', 'bottomMid'):
				area_width = self.container.pxwidth-regpoint_x
				if regpoint_x < area_width:
					area_width = regpoint_x
				area_width = area_width*2
			if regalign in ('topRight', 'midRight', 'bottomRight'):
				area_width = regpoint_x
			if regalign in ('midLeft', 'midRight', 'center'):
				area_height = self.container.pxheight-regpoint_y
				if regpoint_y < area_height:
					area_height = regpoint_y
				area_height = area_height*2
			if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
				area_height = regpoint_y

			media_ratio = float(self.intrinsicWidth)/float(self.intrinsicHeight)
			# print 'ratio=',media_ratio
			if area_height*media_ratio > area_width:
				area_height = area_width/media_ratio
			else:
				area_width = area_height*media_ratio

		elif scale == -1: # slice
			if regalign in ('topLeft', 'topMid', 'topRight'):
				area_height = self.container.pxheight-regpoint_y
			if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
				area_width = self.container.pxwidth-regpoint_x
			if regalign in ('topMid', 'center', 'bottomMid'):
				area_width = self.container.pxwidth-regpoint_x
				if regpoint_x > area_width:
					area_width = regpoint_x
				area_width = area_width*2
			if regalign in ('topRight', 'midRight', 'bottomRight'):
				area_width = regpoint_x
			if regalign in ('midLeft', 'midRight', 'center'):
				area_height = self.container.pxheight-regpoint_y
				if regpoint_y > area_height:
					area_height = regpoint_y
				area_height = area_height*2
			if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
				area_height = regpoint_y
				
			media_ratio = float(self.intrinsicWidth)/float(self.intrinsicHeight)
			# print 'ratio=',media_ratio
			if area_height*media_ratio < area_width:
				area_height = area_width/media_ratio
			else:
				area_width = area_height*media_ratio

		elif scale == -3: # fill
			if regalign in ('topLeft', 'topMid', 'topRight'):
				area_height = self.container.pxheight-regpoint_y
			if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
				area_width = self.container.pxwidth-regpoint_x
			if regalign in ('topMid', 'center', 'bottomMid'):
				area_width = self.container.pxwidth-regpoint_x
				area_width = area_width*2
			if regalign in ('topRight', 'midRight', 'bottomRight'):
				area_width = regpoint_x
			if regalign in ('midLeft', 'midRight', 'center'):
				area_height = self.container.pxheight-regpoint_y
				area_height = area_height*2
			if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
				area_height = regpoint_y

		if regalign in ('topLeft', 'topMid', 'topRight'):
			area_top = regpoint_y
		if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
			area_left = regpoint_x
		if regalign in ('topMid', 'center', 'bottomMid'):
			area_left = regpoint_x-(area_width/2)
		if regalign in ('topRight', 'midRight', 'bottomRight'):
			area_left = regpoint_x-area_width
		if regalign in ('midLeft', 'midRight', 'center'):
			area_top = regpoint_y-(area_height/2)
		if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
			area_top = regpoint_y-area_height

		#
		# end of positioning algorithm

		# print 'area geom = ',area_left, area_top, area_width, area_height

		return area_left, area_top, area_width, area_height

	def getScale(self):
		if self.scale != None:
			return self.scale
		else:
			return self.container.getScale()

	def getRegPoint(self):
		if self.regPoint != None:
			return self.regPoint
		else:
			return self.container.getRegPoint()
		
	def getRegAlign(self, regPointObject):
		if self.regAlign != None:
			return self.regAlign
		else:
			regAlign = self.container.getRegAlign()
			if regAlign == None:
				regAlign = regPointObject.getRegAlign()
				
			return regAlign

	def _onChangePxValue(self, name, value):
		self.pxValuesHasChanged = 1

	def _onGeomChanged(self):
		self.context._onPxValuesChanged(self, self.getPxGeom())

	def getPxGeom(self):
		return (self.pxleft, self.pxtop, self.pxwidth, self.pxheight)

