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
	
	def setRawAttrs(self, region, attrList):
		region.setRawAttrs(attrList)

	def copyRawAttrs(self, srcNode, destNode):
		destNode.copyRawAttrs(srcNode)
			
	def changeRawAttr(self, node, name, value):
		self.nodeGeomChangedList = []
		self.rawAttributesChangedList = []
		node.changeRawValue(name, value)
		self._updateListeners()

	def getRawAttr(self, node, name):
		return node.getRawAttr(name)

	def getAttr(self, node, name):
		return node.getAttr(name)
		
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
		node = RegionNode(self)

		return node

	def link(self, node, container):
		if container == None or node == None:
			# nothing to do
			return 
		node.link(container)

	def unlink(self, node):
		if node == None:
			return
		node.unlink()
		
	def newMedia(self):
		node = MediaNode(self)

		return node

	def removeRegion(self, region, container):
		container.removeRegion(region)

	def setGeomListener(self, node, listener):
		node.setGeomListener(listener)

	def setRawPosAttrListener(self, node, listener):
		node.setRawPosAttrListener(listener)

	def removeListener(self, node, listener):
		node.removeListener(listener)

	def getPxGeom(self, node):
		return node.getPxGeom()

	def getPxAbsGeom(self, node):
		return node.getPxAbsGeom()

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
	def __init__(self, context):
		self.children = []
		self.container = None
		self.context = context
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
		self.isRoot = 0

		# common attributes for media and region
		self.regAlign = None
		self.regPoint = None
		self.scale = None

	def copyRawAttrs(self, srcNode):
		self.regAlign = srcNode.regAlign
		self.regPoint = srcNode.regPoint
		self.scale = srcNode.scale

	def changeRawAttr(self, name, value):
		if name in ['left', 'width', 'right', 'top', 'height', 'bottom']:
			self.changeRawValues(name, value)
		elif name in ['regAlign', 'regPoint', 'scale']:
			self.changeAlignAttr(name, value)
			
	def link(self, container):
		# if already link, unlink before
		if self.container != None:
			print 'SMILCssResolver: Warning: node is already linked'
			self.unlink()
		self.container = container
		container.children.append(self)

	def unlink(self):
		self.isInit = 0
		try:
			index = self.container.children.index(self)
			del self.container.children[index]
		except:
			pass
		self.container = None
		
	def setRawPosAttrListener(self, listener):
		self.rawValuesListener = listener

	def setGeomListener(self, listener):
		self.pxValuesListener = listener

	def _toUnInitState(self):
		self.isInit = 0
		for child in self.children:
			if child.isInit:
				child._toUnInitState()
		
	def _toInitState(self):
		if self.isInit:
			# already in init state. do nothing
			return

		if self.container == None:
			raise 'SmilCssResolver: init failed, no root node'

		self.container._toInitState()		
		self._initialUpdate()
		self.isInit = 1
				
	def isInitState(self):
		return self.isInit

	def getPxGeom(self):
		self._toInitState()
		return self._getPxGeom()

	def getPxAbsGeom(self):
		self._toInitState()
		left, top, width, height = self._getPxGeom()
		pleft, ptop, pwidth, pheight = self.container.getPxAbsGeom()
		return pleft+left, ptop+top, width, height

	def _setRawAttr(self, name, value):
		if name == 'regPoint':
			self.regPoint = value
		elif name == 'regAlign':
			self.regAlign = value
		elif name == 'scale':
			self.scale = value

	def _getRawAttr(self, name):
		if name == 'regPoint':
			return self.regPoint
		elif name == 'regAlign':
			return self.regAlign
		elif name == 'scale':
			return self.scale

		return None

	def getAttr(self, name):
		self._toInitState()
		if name == 'regPoint':
			return self.getRegPoint()
		elif name == 'regAlign':
			return self.getRegAlign()
		elif name == 'scale':
			return self.getScale()

		return None
	
	def changeAlignAttr(self, name, value):
		self._toInitState()
		self.setAlignAttr(name, value)

		self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
		self._onGeomChanged()

class RegionNode(Node):
	def __init__(self, context):
		Node.__init__(self, context)

	def _initialUpdate(self):
		self.pxleft, self.pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, self.container.pxwidth)
		if self.pxwidth <= 0: self.pxwidth = 1
		self.pxtop, self.pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, self.container.pxheight)
		if self.pxheight <= 0: self.pxheight = 1
		self._onGeomChanged()

	def setRawAttrs(self, attrList):
		for name, value in attrList:
			if name == 'left':
				self.left = value
			elif name == 'top':
				self.top = value
			elif name == 'width':
				if value != None and value <= 0: value = 1
				self.width = value
			elif name == 'height':
				if value != None and value <= 0: value = 1
				self.height = value
			elif name == 'right':
				self.right = value
			elif name =='bottom':
				self.bottom = value
			else:
				Node._setRawAttr(self, name, value)
		
		self._toUnInitState()

	def getRawAttr(self, name):
		if name == 'left':
			return self.left 
		elif name == 'top':
			return self.top
		elif name == 'width':
			return self.width 
		elif name == 'height':
			return self.height
		elif name == 'right':
			return self.right
		elif name =='bottom':
			return self.bottom
		else:
			return Node._getRawAttr(self, name)

	def copyRawAttrs(self, srcNode):
		Node.copyRawAttrs(self,srcNode)
		self.left = srcNode.left
		self.width = srcNode.width
		self.right = srcNode.right
		self.top = srcNode.top
		self.height = srcNode.height
		self.bottom = srcNode.bottom

		self._toUnInitState()		

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
		self._toInitState()
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
		self._toInitState()
		self.pxValuesHasChanged = 0
		
		containersize = self.container.pxheight
		pxtop, pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, containersize)
		if pxtop != self.pxtop:
			self.pxtop = pxtop
			self._onChangePxValue('top',pxtop)
		if pxheight != self.pxheight:
			self._onChangePxValue('height',pxheight)
			self.pxheight = pxheight
			
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
	def changeRawValues(self, name, value):
		self._toInitState()
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
				if pxwidth <= 0: pxwidth = 1
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

			pxtop, pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, self.container.pxheight)
			if pxtop != self.pxtop:
				self._onChangePxValue('top',pxtop)
				self.pxtop = pxtop
			if pxheight != self.pxheight:
				self._onChangePxValue('height',pxheight)
				if pxheight <= 0: pxheight = 1
				self.pxheight = pxheight
				
				if self.pxValuesHasChanged:
					self._onGeomChanged()

				for child in self.children:
					child._updatePxOnContainerHeightChanged()
				return

		if self.pxValuesHasChanged:
			self._onGeomChanged()

	def changeAlignAttr(self, name, value):
		self._toInitState()
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
		self._toInitState()
		if type(self.left) is type(0.0):
			self.left = float(self.pxleft)/self.container.pxwidth
			self._onChangeRawValue('left',self.left)
		elif type(self.width) is type(0.0):
			self.width = float(self.pxwidth)/self.container.pxwidth
			self._onChangeRawValue('width',self.width)
			for child in self.children:
				child._updateRawOnContainerWidthChanged()       
		elif type(self.right) is type(0.0):
			self.right = float(self.container.pxwidth-self.pxleft-self.pxwidth)/self.container.pxwidth
			self._onChangeRawValue('right',self.right)

	def _updateRawOnContainerHeightChanged(self):
		self._toInitState()
		if type(self.top) is type(0.0):
			self.top = float(self.pxtop)/self.container.pxheight
			self._onChangeRawValue('top',self.top)
		elif type(self.height) is type(0.0):
			self.height = float(self.pxheight)/self.container.pxheight
			self._onChangeRawValue('height',self.height)
			for child in self.children:
				child._updateRawOnContainerHeightChanged()
		elif type(self.bottom) is type(0.0):
			self.bottom = float(self.container.pxheight-self.pxtop-self.pxheight)/self.container.pxheight
			self._onChangeRawValue('bottom',self.bottom)

	# change an pixel value only (left/width/top and height)
	# according to the changement modify the raw values in order to keep all constraint valid
	# for each raw value changed, the callback onChangeRawValue is called
	def changePxValue(self, name, value):
		self._toInitState()
		self.pxValuesHasChanged = 0

		if name == 'left':
			if type(self.left) is type(0.0):
				self.left = float(value)/self.container.pxwidth
				self._onChangeRawValue('left',self.left)
				self.pxleft = value
			elif type(self.left) is type(0):
				self.left = value
				self._onChangeRawValue('left',self.left)
				self.pxleft = value
			elif type(self.right) is type(0.0):
				offset = value-self.pxleft
				self.right = float(self.right+offset)/self.container.pxwidth
				self._onChangeRawValue('right',self.right)
				self.pxleft = value
			elif type(self.right) is type(0):
				offset = value-self.pxleft
				self.right = self.right+offset
				self._onChangeRawValue('right',self.right)
				self.pxleft = value
			else:
				self.left = value
				self._onChangeRawValue('left',self.left)
				self.pxleft = value

		elif name == 'width':
			if type(self.width) is type(0.0):
				self.width = float(value)/self.container.pxwidth
				self._onChangeRawValue('width',self.width)
				if value <= 0: value = 1
				self.pxwidth = value
			elif type(self.width) is type(0):
				self.width = value
				self._onChangeRawValue('width',self.width)
				if value <= 0: value = 1
				self.pxwidth = value
			elif type(self.left) != type(None) and type(self.right) != type(None):
				if type(self.right) is type(0.0):
					offset = value-self.pxwidth
					self.right = float(self.right-offset)/self.container.pxwidth
					self._onChangeRawValue('right',self.right)
					if value <= 0: value = 1
					self.pxwidth = value
				elif type(self.right) is type(0):
					offset = value-self.pxwidth
					self.right = self.width-offset
					self._onChangeRawValue('right',self.right)
					if value <= 0: value = 1
					self.pxwidth = value
			else:
				self.width = value
				self._onChangeRawValue('width',self.width)
				if value <= 0: value = 1
				self.pxwidth = value

			for child in self.children:
				child._updateRawOnContainerWidthChanged()

		elif name == 'top':
			if type(self.top) is type(0.0):
				self.top = float(value)/self.container.pxheight
				self._onChangeRawValue('top',self.top)
				self.pxtop = value
			elif type(self.top) is type(0):
				self.top = value
				self._onChangeRawValue('top',self.top)
				self.pxtop = value
			elif type(self.bottom) is type(0.0):
				offset = value-self.pxtop
				self.bottom = float(self.bottom+offset)/self.container.pxheight
				self._onChangeRawValue('bottom',self.bottom)
				self.pxtop = value
			elif type(self.bottom) is type(0):
				offset = value-self.pxtop
				self.bottom = self.bottom+offset
				self._onChangeRawValue('bottom',self.bottom)
				self.pxtop = value
			else:
				self.top = value
				self._onChangeRawValue('top',self.top)
				self.pxtop = value

		elif name == 'height':
			if type(self.height) is type(0.0):
				self.height = float(value)/self.container.pxheight
				self._onChangeRawValue('height',self.height)
				if value <= 0: value = 1
				self.pxheight = value
			elif type(self.height) is type(0):
				self.height = value
				self._onChangeRawValue('height',self.height)
				if value <= 0: value = 1
				self.pxheight = value
			elif type(self.top) != type(None) and type(self.bottom) != type(None):
				if type(self.bottom) is type(0.0):
					offset = value-self.pxheight
					self.bottom = float(self.bottom-offset)/self.container.pxheight
					self._onChangeRawValue('bottom',self.bottom)
					if value <= 0: value = 1
					self.pxheight = value
				elif type(self.bottom) is type(0):
					offset = value-self.pxheight
					self.bottom = self.bottom-offset
					self._onChangeRawValue('bottom',self.bottom)
					if value <= 0: value = 1
					self.pxheight = value
			else:
				self.height = value
				self._onChangeRawValue('height',self.height)
				if value <= 0: value = 1
				self.pxheight = value

			for child in self.children:
				child._updateRawOnContainerHeightChanged()

		if self.pxValuesHasChanged:
			self._onGeomChanged()

	def _onChangeRawValue(self, name, value):
		self.context._onRawValuesChanged(self, name, value)

	def _onChangePxValue(self, name, value):
		self.pxValuesHasChanged = 1

	def _onGeomChanged(self):
		self.context._onPxValuesChanged(self, self._getPxGeom())

	def _getPxGeom(self):
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

	def _minsize(self, start, extent, end, minsize):
		# Determine minimum size for parent window given that it
		# has to contain a subwindow with the given start/extent/end
		# values.  Start and extent can be integers or floats.  The
		# type determines whether they are interpreted as pixel values
		# or as fractions of the top-level window.
		# end is only used if extent is None.
		if start == 0:
			# make sure this is a pixel value
			start = 0
##	if extent is None and (type(start) is type(end) or start == 0):
##		extent = end - start
##		end = None
		if type(start) is type(0):
			# start is pixel value
			if type(extent) is type(0.0):
				# extent is fraction
				if extent == 0 or (extent == 1 and start > 0):
					raise error, 'region with impossible size'
				if extent == 1:
					return minsize
				size = int(start / (1 - extent) + 0.5)
				if minsize > 0 and extent > 0:
					size = max(size, int(minsize/extent + 0.5))
				return size
			elif type(extent) is type(0):
				# extent is pixel value
				if extent == 0:
					extent = minsize
				return start + extent
			elif type(end) is type(0.0):
				# no extent, end is fraction
				return int((start + minsize) / (1 - end) + 0.5)
			elif type(end) is type(0):
				# no extent, end is pixel value
				# warning end is relative to the parent end egde
				return start + minsize + end
			else:
				# no extent and no end
				return start + minsize
		elif type(start) is type(0.0):
			# start is fraction
			if start == 1:
				raise error, 'region with impossible size'
			if type(extent) is type(0):
				# extent is pixel value
				if extent == 0:
					extent = minsize
				return int(extent / (1 - start) + 0.5)
			elif type(extent) is type(0.0):
				# extent is fraction
				if minsize > 0 and extent > 0:
					return int(minsize / extent + 0.5)
				return 0
			elif type(end) is type(0):
				# no extent, end is pixel value
				return int ((minsize + end) / (1 - start) + 0.5)
			elif type(end) is type(0.0):
				# no extent, end is fraction
				return int(minsize / (1 - start - end) + 0.5)
			else:
				# no extent and no end
				return int(minsize / (1 - start) + 0.5)
		elif type(end) is type(0):
			# no start, end is pixel value
			# warning end is relative to the parent end egde
			return end + minsize
		elif type(end) is type(0.0):
			# no start, end is fraction
			if end <= 0:
				return minsize
			if type(extent) is type(0):
				# extent is pixel value
				if extent == 0:
					extent = minsize
				return int(extent / end + 0.5)
			elif type(extent) is type(0.0):
				# extent is fraction
				return int(minsize / end + 0.5)
		elif type(extent) is type(0):
			return extent
		elif type(extent) is type(0.0) and extent > 0:
			return int(minsize / extent + 0.5)
		return minsize

	def guessSize(self):
		minWidth = 100
		minHeight = 100
		for child in self.children:
			widthChild, heightChild = child.guessSize()
			width = self._minsize(self.left, self.width,
					self.right,widthChild)
			if width > minWidth:
				minWidth = width
			height = self._minsize(self.top, self.height,
					self.bottom, heightChild)
			if height > minHeight:
				minHeight = height
		
		return minWidth, minHeight
			
class RootNode(RegionNode):
	def __init__(self, context):
		Node.__init__(self, context)

	def copyRawAttrs(self, srcNode):
		self.pxwidth = srcNode.pxwidth
		self.pxheight = srcNode.pxheight
		
		self._toUnInitState()		

	def setRawAttrs(self, attrList):
		for name, value in attrList:
			if name == 'width':
				self.pxwidth = value
			elif name == 'height':
				self.pxheight = value

		self._toUnInitState()

	def getRawAttr(self, name):
		if name == 'width':
			return self.pxwidth
		elif name == 'height':
			return self.pxheight

		return None		

	def updateAll(self):
		self._onGeomChanged()
		for child in self.children:
			child._initialUpdate()
			
	def _onGeomChanged(self):
		self.context._onPxValuesChanged(self, self._getPxGeom())

	def _getPxGeom(self):
		return (self.pxwidth, self.pxheight)

	def getPxAbsGeom(self):
		self._toInitState()
		return 0, 0, self.pxwidth, self.pxheight
		
	def _toInitState(self):
		if self.pxwidth == None or self.pxheight == None:
			self.pxwidth, self.pxheight = self.guessSize()
		self.isInit = 1
		
class MediaNode(Node):
	def __init__(self, context):
		Node.__init__(self, context)
		self.alignHandler = None
		self.intrinsicWidth = None
		self.intrinsicHeight = None

	def copyRawAttrs(self, srcNode):
		Node.copyRawAttrs(self,srcNode)
		self.intrinsicWidth = srcNode.intrinsicWidth
		self.intrinsicHeight = srcNode.intrinsicHeight

		self._toUnInitState()		

	def _initialUpdate(self):
		self.pxleft, self.pxtop, self.pxwidth, self.pxheight = self._getMediaSpaceArea()
		if self.pxwidth <= 0: self.pxwidth = 1
		if self.pxheight <= 0: self.pxheight = 1
		self._onGeomChanged()

	# return the tuple x,y alignment in pourcent value
	# alignOveride is an optional overide id
	def _getxyAlign(self, alignOveride=None):
		alignId = None
		if alignOveride == None:
			alignId = self.getregalign()
		else:
			alignId = alignOveride
			
		from RegpointDefs import alignDef
		xy = alignDef.get(alignId)
		if xy == None:		
			# impossible value, avoid a crash if bug
			xy = (0.0, 0.0)
		return xy

	def guessSize(self):
		# if no intrinsic size, return a default value
		if self.intrinsicHeight == None or self.intrinsicWidth == None:
			return 100,100
		
		regPoint = self.getRegPoint()		
		regPointObject = self.context.getDocumentContext().GetRegPoint(regPoint)
		regAlign = self._getRegAlign(regPointObject)
		
		# convert regalignid to pourcent value
		regAlignX, regAlignY = self._getxyAlign(regAlign)

		# convert value to pixel, relative to the media
		regAlignW1 = int (regAlignX * self.intrinsicWidth + 0.5)
		regAlignW2 = int ((1-regAlignX) * self.intrinsicWidth + 0.5)

		regAlignH1 = int (regAlignY * self.intrinsicHeight + 0.5)
		regAlignH2 = int ((1-regAlignY) * self.intrinsicHeight + 0.5)

		width = self._minsizeRp(regPointObject['left'],
					 regPointObject['right'],
					 regAlignW1, regAlignW2, self.intrinsicWidth)

		height = self._minsizeRp(regPointObject['top'],
					regPointObject['bottom'],
					regAlignH1, regAlignH2, self.intrinsicHeight)

		return width, height
	
	# Determine the minimum size for the container  the regpoint/regalign
	# wR1 is the size from container left edge to regpoint.
	# wR2 is the size from regpoint to container right edge)
	# wR1 and wR2 are in pourcent (float) or pixel (integer). You can't have the both in the same time
	# wM1 is the size from media left edge to alignPoint
	# wM2 is the size from alignpoint to media right edge
	# wM1 and wM2 are pixel only (integer). You have to specify the both in the same time
	def _minsizeRp(self, wR1, wR2, wM1, wM2, minsize):

		# for now. Avoid to have in some case some to big values
		MAX_REGION_SIZE = 5000

		if wR1 is not None and wR2 is not None:
			# conflict regpoint attribute
			return minsize

		if wM1 is None or wM2 is None:
			# bad parameters
			raise minsize

		# first constraint
		newsize = minsize
		if type(wR1) is type (0.0):
			if wR1 == 1.0:
				raise error, 'regpoint with impossible alignment'
			wN = int (wM2 / (1-wR1) + 0.5)
			if wN > newsize:
				newsize = wN
		elif type(wR1) is type (0):
			wN = wR1 + wM2
			if wN > newsize:
				newsize = wN
		elif type(wR2) is type (0.0):
			if wR2 == 0.0:
				# the media will stay invisible whichever the value
				# we keep the same size
				pass
			else:
				wN = int(wM2 / wR2 + 0.5)
				# test if the size is acceptable
				if wN > MAX_REGION_SIZE:
					wN = MAX_REGION_SIZE
				if wN > newsize:
					newsize = wN
		elif type(wR2) is type (0):
			# keep the same size
			pass
		else:
			# no constraint
			pass

		# second constraint
		if type(wR2) is type (0.0):
			if wR2 == 1.0:
				raise error, 'regpoint with impossible alignment'
			wN = int(wM1 / (1.0-wR2) + 0.5)
			if wN > newsize:
				newsize = wN
		elif type(wR2) is type (0):
			# don't change anything
			pass
		elif type(wR1) is type (0.0):
			if wR1 == 0.0:
				# the media will stay invisible whichever the value
				# we keep the same size
				pass
			else:
				wN = int(wM1 / wR1 + 0.5)
				# test if the size is acceptable
				if wN > MAX_REGION_SIZE:
					wN = MAX_REGION_SIZE
				if wN > newsize:
					newsize = wN
		elif type(wR1) is type (0):
			wN = wR1 + wM1
			if wN > newsize:
				newsize = wN
		else:
			# no constraint
			pass

		return newsize

	def setRawAttrs(self, attrList):
		for name, value in attrList:
			if name == 'width':
				self.intrinsicWidth = value
			elif name == 'height':
				self.intrinsicHeight = value
			else:
				Node._setRawAttr(self, name, value)

		self._toUnInitState()

	def getRawAttr(self, name):
		if name == 'width':
			return self.intrinsicWidth
		elif name == 'height':
			return self.intrinsicHeight
		else:
			return Node._getRawAttr(self, name)

	def _updateOnContainerHeightChanged(self):
		self._toInitState()
		self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
		self._onGeomChanged()
		
	def _updateOnContainerWidthChanged(self):
		self._toInitState()
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
		regalign = self._getRegAlign(regPointObject)

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
				area_height = int(area_width/media_ratio+0.5)
			else:
				area_width = int(area_height*media_ratio+0.5)

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

		# avoid crashes
		if area_width <= 0: area_width = 1
		if area_height <= 0: area_height = 1
		
		return area_left, area_top, area_width, area_height

	def getScale(self):
		if self.scale != None:
			return self.scale
		else:
			region = self.__getRegion()
			if region != None:
				return region.getScale()
			
	def __getRegion(self):
		subreg = self.container
		if self.container != None:
			return subreg.container

		return None
	
	def getRegPoint(self):
		if self.regPoint != None:
			return self.regPoint
		else:
			region = self.__getRegion()
			if region != None:
				return region.getRegPoint()

		# we shouldn't pass here
		return 'topLeft'			

	def getRegAlign(self):
		regPoint = self.getRegPoint()
		regPointObject = self.context.getDocumentContext().GetRegPoint(regPoint)
		return self._getRegAlign(regPointObject)
		
	def _getRegAlign(self, regPointObject):
		if self.regAlign != None:
			return self.regAlign
		else:
			# default value
			regAlign = 'topLeft'
			region = self.__getRegion()
			if region != None:
				regAlign = region.getRegAlign()
				if regAlign == None:
					regAlign = regPointObject.getregalign()
				
		return regAlign

	def _onChangePxValue(self, name, value):
		self.pxValuesHasChanged = 1

	def _onGeomChanged(self):
		self.context._onPxValuesChanged(self, self._getPxGeom())

	def _getPxGeom(self):
		return (self.pxleft, self.pxtop, self.pxwidth, self.pxheight)
		
