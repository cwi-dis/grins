# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from windowinterface import UNIT_PXL

from usercmd import *

import MMAttrdefs
import settings
import features
import windowinterface

ALL_LAYOUTS = '(All Channels)'

debug = 0
debug2 = 0

from _LayoutView2 import treeVersion

###########################
# helper class to build tree from list

TYPE_ABSTRACT, TYPE_REGION, TYPE_MEDIA, TYPE_VIEWPORT = range(4)

class Node:
	def __init__(self, name, nodeRef, ctx):
		self._name = name
		self._nodeRef = nodeRef
		self._children = []
		self._ctx = ctx
		self._parent = None
		self._viewport = None
		
		# graphic control (implementation: system dependant)
		self._graphicCtrl = None		

		# default attribute		
		self.importAttrdict()
		self._nodeType = TYPE_ABSTRACT

		# avoid a recursive loop when selecting:
		# currently, on windows, a selecting operation generate a selected event !
		self._selecting = 0

		self._wantToShow = 0
		
	def _cleanup(self):
		if self.isShowed:
			self.hide()
		del self._ctx
		del self._viewport
		del self._parent
		
	def addNode(self, node):
		self._children.append(node)
		node._parent = self
		node._viewport = self._viewport

	def removeNode(self, node):
		node._cleanup()
		try:
			self._children.remove(node)
		except ValueError:
			pass

	def isShowed(self):
		return self._graphicCtrl != None

	def getNodeType(self):
		return self._nodeType
	
	def getViewport(self):
		return self._viewport
	
	def importAttrdict(self):
		self._curattrdict = {}
					
	def getNodeRef(self):
		return self._nodeRef

	def getSubNodeList(self):
		return self._children
		
	def getShowName(self):
		return self._ctx._context.showName		

	def getName(self):
		return self._name

	def getParent(self):
		return self._parent
	
	def applyOnAllNode(self, fnc, params):
		apply(fnc, params)
		for child in self._children:
			child.applyOnAllNode(fnc, params)

	def select(self):
		if debug: print 'Node.select : ',self.getName()
		if self.isShowed():
			if debug: print 'Node.select: graphic select'
			self._selecting = 1
			self._graphicCtrl.select()
			self._selecting = 0

	def onUnselected(self):
		if debug: print 'Node.Unselected : ',self.getName()
		self._ctx._context.onPreviousUnselect()

	def hide(self):
		if debug: print 'Node.hide: ',self.getName()
		if self._graphicCtrl != None:
			if self._parent != None:
				if self._parent._graphicCtrl != None:
					self._parent._graphicCtrl.removeRegion(self._graphicCtrl)
				self._graphicCtrl.removeListener(self)
			self._graphicCtrl = None
			self._ctx.previousCtrl.update()

	def hideAllNodes(self):
		self.hide()
		for child in self._children:
			child.hideAllNodes()

	def updateAttrdict(self):
		self.importAttrdict()
		if self.isShowed():
			self._graphicCtrl.setAttrdict(self._curattrdict)

	def updateAllAttrdict(self):
		if not self.isShowed():
			return
		self.updateAttrdict()
		for child in self._children:
			child.updateAllAttrdict()

	def getGeom(self):
		return self._curattrdict['wingeom']

	def isShowEditBackground(self):
		showEditBackground = self._nodeRef.GetAttrDef('showEditBackground',None)
		if showEditBackground != None and showEditBackground == 1:
			return 1
		return 0		

	def toShowedState(self):
		if debug: print 'Node.toShowState',self.getName()
		node = self
		nodeToShow = []
		while node != None:
			if not node._wantToShow:
				node._wantToShow = 1
				nodeToShow.append(node)
			node = node._parent
		nodeToShow.reverse()
		for node in nodeToShow:
			if node.getNodeType() != TYPE_VIEWPORT:
				if debug: print 'Node.toShowState show parent',node.getName()
				node.show()
		if debug: print 'Node.toShowState end'

	def toHiddenState(self):
		if debug: print 'Node.toHiddenState',self.getName()
		if not self._wantToShow:
			return
		self._wantToShow = 0
		for child in self._children:
			child.toHiddenState()	
		self.hide()
		
class Region(Node):
	def __init__(self, name, nodeRef, ctx):
		Node.__init__(self, name, nodeRef, ctx)
		self._nodeType = TYPE_REGION
		self._wantToShow = 0
		
	def importAttrdict(self):
		Node.importAttrdict(self)

		if self._ctx._context.asOutLine:
			self._curattrdict['transparent'] = 1
		else:			
			editBackground = None
			if self.isShowEditBackground():
				editBackground = self._nodeRef.GetAttrDef('editBackground',None)
			
			if editBackground != None:				
					self._curattrdict['bgcolor'] = editBackground
					self._curattrdict['transparent'] = 0
			else:
				self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
				self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)
		
		self._curattrdict['wingeom'] = self._nodeRef.getPxGeom()
		self._curattrdict['z'] = self._nodeRef.GetAttrDef('z', 0)
	
	def show(self):
		if debug: print 'Region.show : ',self.getName()
		if self._wantToShow and self._parent._graphicCtrl != None:
			self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self._name)
			self._graphicCtrl.showName(self.getShowName())		
			self._graphicCtrl.addListener(self)

	def showAllNodes(self):
		if self._wantToShow:
			self.show()
			for child in self._children:
				child.showAllNodes()

	#
	# update of visualization attributes (not document)
	#

	def updateShowName(self,value):
		if self.isShowed():
			self._graphicCtrl.showName(value)
		
	def updateAllShowNames(self, value):
		if self.isShowed():
			self.updateShowName(value)
			for child in self._children:
				child.updateAllShowNames(value)

	def updateAllAsOutLines(self, value):
		if value:
			self._curattrdict['transparent'] = 1
		else:
			self._curattrdict['transparent'] = 0

		if self.isShowed():
			self._graphicCtrl.setAttrdict(self._curattrdict)

		for child in self._children:
			child.updateAllAsOutLines(value)

	#
	# end update mothods
	#

	def onSelected(self):
		if not self._selecting:
			if debug: print 'Region.onSelected : ',self.getName()
			self._ctx._context.onPreviousSelectRegion(self)

	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx._context.updateRegionGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx._context.applyGeomOnRegion(self.getNodeRef(), geom)

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())
				
class MediaRegion(Region):
	def __init__(self, name, node, ctx):
		nodeRef = node
		Region.__init__(self, name, nodeRef, ctx)
		self._nodeType = TYPE_MEDIA

	def importAttrdict(self):
		Node.importAttrdict(self)
		self._curattrdict['bgcolor'] = MMAttrdefs.getattr(self._nodeRef, 'bgcolor')
		self._curattrdict['transparent'] = MMAttrdefs.getattr(self._nodeRef, 'transparent')
		
		# get wingeom according to the subregion positionning
		# note this step is not done during the parsing in order to maintains all constraint information
		# at some point we'll have to do the same thing for regions
		channel = self._nodeRef.GetChannel()
		wingeom = self._nodeRef.getPxGeom()

		# determinate the real fit attribute		
		scale = MMAttrdefs.getattr(self._nodeRef,'scale')
		if scale == 1:
			fit = 'hidden'
		elif scale == 0:
			fit = 'meet'
		elif scale == -1:
			fit = 'slice'
		else:
			fit = 'fill'
		self.fit = fit

		# ajust the internal geom for edition. If no constraint neither on right nor botton,
		# with fit==hidden: chg the internal region size.
		# it avoid a unexepected effet during the edition when you resize. don't change the semantic
		right =	self._nodeRef.GetRawAttrDef('right', None) 
		bottom = self._nodeRef.GetRawAttrDef('bottom', None) 
		width =	self._nodeRef.GetRawAttrDef('width', None) 
		height = self._nodeRef.GetRawAttrDef('height', None)
		regPoint = self._nodeRef.GetAttrDef('regPoint', None)
		regAlign = self._nodeRef.GetAttrDef('regAlign', None)
		self.media_width, self.media_height = self._nodeRef.GetDefaultMediaSize(wingeom[2], wingeom[3])
		# protect against getdefaultmediasize method which may return 0 !
		if self.media_width <= 0 or self.media_height <= 0:
			self.media_width, self.media_height = wingeom[2], wingeom[3]
		if regPoint == 'topLeft' and regAlign == 'topLeft':
			if fit == 'hidden':
				if right == None and width == None:
					x,y,w,h = wingeom
					wingeom = x,y,self.media_width,h
				if bottom == None and height == None:
					x,y,w,h = wingeom
					wingeom = x,y,w,self.media_height

		self._curattrdict['wingeom'] = wingeom
		self._curattrdict['z'] = 0

	def updateShowName(self,value):
		# no name showed
		pass

	def onSelected(self):
		if not self._selecting:
			if debug: print 'Media.onSelected : ',self.getName()
			self._ctx._context.onPreviousSelectMedia(self)

	def show(self):
		if debug: print 'Media.show : ',self.getName()
		if self._parent._graphicCtrl == None:
			return

		if self.isShowed():
			self.hide()
			
		self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self._name)
		self._graphicCtrl.showName(0)		
		self._graphicCtrl.addListener(self)
		
		# copy from old hierarchical view to determinate the image to showed
		node = self._nodeRef
		chtype = node.GetChannelType()
		

		f = None
		fit = 'fill'
		from cmif import findfile
		if chtype == 'image':
			fit = self.fit
			url = node.GetAttrDef('file', None)		
			if url != None:
				url = node.context.findurl(url)
				try:
					import MMurl
					f = MMurl.urlretrieve(url)[0]
				except IOError, arg:
					print "Cannot load image: %s"%arg
			else:
				print "Can't find image: %s"%url
		else:
			import os
			self.datadir = findfile('GRiNS-Icons')
			f = os.path.join(self.datadir, '%s.tiff' % chtype)
			
		if f is not None:
			self._graphicCtrl.setImage(f, fit)
		
	def onGeomChanging(self, geom):
		self._ctx._context.updateMediaGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx._context.applyGeomOnMedia(self.getNodeRef(), geom)

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
	
class Viewport(Node):
	def __init__(self, name, nodeRef, ctx):
		self.currentX = 8
		self.currentY = 8
		
		Node.__init__(self, name, nodeRef, ctx)
		self._nodeType = TYPE_VIEWPORT
		self._viewport = self

	def importAttrdict(self):
		Node.importAttrdict(self)

		editBackground = None
		if self.isShowEditBackground():
			editBackground = self._nodeRef.GetAttrDef('editBackground',None)
			
		if not treeVersion:
			if editBackground != None:				
					self._curattrdict['bgcolor'] = editBackground
					self._curattrdict['transparent'] = 0
			else:
				self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
				self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)
		else:
			self._curattrdict['bgcolor'] = 200,200,200
			self._curattrdict['transparent'] = 0
		
		w,h=self._nodeRef.getPxGeom()
		self._curattrdict['wingeom'] = (self.currentX,self.currentY,w,h)

	def show(self):
		if debug: print 'Viewport.show : ',self.getName()
		self._graphicCtrl = self._ctx.previousCtrl.newViewport(self._curattrdict, self._name)
		self._graphicCtrl.addListener(self)
		
	def showAllNodes(self):
		if debug: print 'Viewport.showAllNodes : ',self.getName()
		self.show()
		for child in self._children:
			child.showAllNodes()
		self._ctx.previousCtrl.update()

	#
	# update of visualization attributes (not document)
	#
	
	def updateAllShowNames(self, value):
		for child in self._children:
			child.updateAllShowNames(value)

	def updateAllAsOutLines(self, value):
		for child in self._children:
			child.updateAllAsOutLines(value)
		# for now refresh all
		self.updateAllAttrdict()
#		self.showAllNodes()

	#
	# end update visualization mothods
	#

	def updateAllAttrdict(self):
		if not self.isShowed():
			return
		if debug: print 'LayoutView.updateAllAttrdict:',self.getName()
		Node.updateAllAttrdict(self)
		
		# for now refresh all
		if self.isShowed():
			self.showAllNodes()
		
	def onSelected(self):
		if not self._selecting:
			if debug: print 'Viewport.onSelected : ',self.getName()
			self._ctx._context.onPreviousSelectViewport(self)

	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx._context.updateViewportGeomOnDialogBox(geom[2:])

	def onGeomChanged(self, geom):
		# apply the new value
		self.currentX = geom[0]
		self.currentY = geom[1]
		self._ctx._context.applyGeomOnViewport(self.getNodeRef(), geom[2:])

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())

class PreviousWidget:
	def __init__(self, context):
		self._viewports = {}
		self._refToRegionNode = {}
		self._context = context

		# current state
		self.currentViewport = None		

		# deal with graphic selecter controls
		self.currentRegionRefListSel = []
		self.currentMediaRefListSel = []

		# media list currently showed whichever the node which are the focus
		self.currentMediaRefListM = []
		# media list currently showed which are removed when an external focus change
		self.currentMediaRefListT = []
		# media list (tuple of media node, parent node) which are showing
		self.currentMediaNodeListShowed = []

		# region list currently showed whichever the node which are the focus
		self.currentRegionRefListM = []
		# region list currently showed which are removed when an external focus change
		self.currentRegionRefListT = []
		# region list which are showing
		self.currentRegionNodeListShowed = []

	def init(self):
		self.previousCtrl = self._context.previousCtrl

	def updateRegionTree(self):
		if debug: print 'LayoutView.updateRegionTree begin'
		# We assume here that no region has been added or supressed
		viewportRefList = self._context.getViewportRefList()
		for viewportRef in viewportRefList:
			viewportNode = self.getViewportNode(viewportRef)
			if debug: print 'LayoutView.updateRegionTree: update viewport',viewportNode.getName()
			viewportNode.updateAllAttrdict()
		if debug: print 'LayoutView.updateRegionTree end'

	def addRegion(self, parentRef, regionRef):
		pNode = self.getNode(parentRef)
		self._refToRegionNode[regionRef] = regionNode = Region(regionRef.name, regionRef, self)
		pNode.addNode(regionNode)

		if self._context.showAllRegions:
			if regionRef not in self.currentRegionRefListM:
				self.currentRegionRefListM.append(regionRef)
			if regionRef in self.currentRegionRefListT:
				self.currentRegionRefListT.remove(regionRef)

	def addViewport(self, viewportRef):
		viewportNode = Viewport(viewportRef.name, viewportRef, self)
		self._viewports[viewportRef] = viewportNode

	def removeRegion(self, regionRef):
		self.removeRegionNode(regionRef)
		regionNode = self.getRegionNode(regionRef)
		parentNode = regionNode.getParent()
		parentNode.removeNode(regionNode)
		viewportRef = parentNode.getViewport().getNodeRef()

		if regionRef in self.currentRegionRefListM:
			self.currentRegionRefListM.remove(regionRef)
		if regionRef in self.currentRegionRefListT:
			self.currentRegionRefListT.remove(regionRef)
			
		del self._refToRegionNode[regionRef]
		
	def removeViewport(self, viewportRef):		
		del self._viewports[viewportRef]

	def selectRegion(self, regionRef):		
		appendList = []
		if regionRef not in self.currentRegionRefListT and regionRef not in self.currentRegionRefListM:
			appendList.append(regionRef)
			self.currentRegionRefListT.append(regionRef)

		# append and update region node list
		self.appendRegionNodeList(appendList)
		self.__select(regionRef)
			
	def selectViewport(self, viewportRef):
		self.__select(viewportRef)

	def selectUnknown(self, focusobject):
		self.__unselect()
									
	def selectMedia(self, mediaRef):
		appendList = []
		if mediaRef not in self.currentMediaRefListT and mediaRef not in self.currentMediaRefListM:
			appendList.append(mediaRef)
			self.currentMediaRefListT.append(mediaRef)

		# append and update media node list
		self.appendMediaNodeList(appendList)
		
		self.__select(mediaRef)

	def removeAllMediaNodeList(self):
		if len(self.currentMediaNodeListShowed) > 0:
			for mediaRegion, parentRegion in self.currentMediaNodeListShowed:
				# remove from region tree
				parentRegion.removeNode(mediaRegion)
		self.currentMediaNodeListShowed = []
		self.lastMediaRefSelected = None

	def removeMedia(self, mediaRef):
		if len(self.currentMediaNodeListShowed) > 0:
			i = 0
			mediaNode = self.getMediaNode(mediaRef)
			for mediaRegion, parentRegion in self.currentMediaNodeListShowed:
				if mediaRegion is mediaNode:
					parentRegion.removeNode(mediaRegion)
					if self.lastMediaRefSelected == mediaRegion.getNodeRef():					
						self.lastMediaRefSelected = None
					del self.currentMediaNodeListShowed[i]
					break
				i = i+1

	def removeRegionNode(self, regionRef):
		if regionRef in	self.currentRegionNodeListShowed:
			self.currentRegionNodeListShowed.remove(regionRef)
			regionNode = self.getRegionNode(regionRef)
			regionNode.toHiddenState()
							 
	def removeTempMediaNodeList(self):
		removeList = []
		ind = 0
		for mediaRegion, parentRegion in self.currentMediaNodeListShowed:
			if mediaRegion.getNodeRef() in self.currentMediaRefListT:
				removeList.append(ind)
				parentRegion.removeNode(mediaRegion)
			ind = ind+1
		removeList.reverse()
		for ind in removeList:
			del self.currentMediaNodeListShowed[ind]

		self.currentMediaRefListT = []

	def appendAllRegionNodeList(self):
		self.appendRegionNodeList(self.currentRegionRefListM)
	
	def appendRegionNodeList(self, nodeList):
		# change to show state each region node
		for nodeRef in nodeList:
			regionNode = self.getRegionNode(nodeRef)
			if regionNode != None:
				regionNode.toShowedState()
			self.currentRegionNodeListShowed.append(nodeRef)
									
	def appendMediaNodeList(self, nodeList):
		# create the media region nodes according to nodeList
		appendMediaRegionList = []
		for nodeRef in nodeList:
			channel = nodeRef.GetChannel()
			if channel == None: continue
			layoutChannel = channel.GetLayoutChannel()
			if layoutChannel == None: continue
			regionNode = self.getRegionNode(layoutChannel)
			if regionNode == None: continue
			name = nodeRef.attrdict.get("name")

			newRegionNode = MediaRegion(name, nodeRef, self)

			# add the new media region
			appendMediaRegionList.append((newRegionNode, regionNode))


		# add the list of new media regions
		for mediaRegion, parentRegion in appendMediaRegionList:
			self.currentMediaNodeListShowed.append((mediaRegion, parentRegion))
			parentRegion.addNode(mediaRegion)
			mediaRegion.importAttrdict()
			mediaRegion.show()

	def __unselect(self):
		# XXX for now re-show the viewport
		if self.currentViewport == None:
			# show the first viewport in the list		
			currentViewportList = self._context.getViewportRefList()
			viewportRef = currentViewportList[0]
		else:
			viewportRef = self.currentViewport.getNodeRef()
		self.displayViewport(viewportRef)
						
	def __select(self, nodeRef):
		if debug: print 'LayoutView.select: node ref =',nodeRef
		nodeType = self._context.getNodeType(nodeRef)

		if nodeType != None:			
			# display the right viewport
			viewportRef = self._context.getViewportRef(nodeRef)
			if self.currentViewport == None or viewportRef != self.currentViewport.getNodeRef():
				if debug: print 'LayoutView.select: change viewport =',viewportRef
				self.displayViewport(viewportRef)

			# select the node in layout area
			node = self.getNode(nodeRef)
			if node == None: return
			if debug: print 'LayoutView.select: node =',node
			node.toShowedState()
			node.select()

	def getRegionNode(self, regionRef):
		return self._refToRegionNode.get(regionRef)

	def getMediaNode(self, mediaRef):
		for mediaRegion, parentRegion in self.currentMediaNodeListShowed:
			nodeRef = mediaRegion.getNodeRef()
			if nodeRef is mediaRef:
				return mediaRegion
		return None

	def getViewportNode(self, viewportRef):
		return self._viewports.get(viewportRef)
		
	def getNode(self, nodeRef):
		node = self.getViewportNode(nodeRef)
		if node != None:
			return node
		
		node = self.getRegionNode(nodeRef)
		if node != None:
			return node

		node = self.getMediaNode(nodeRef)
		if node != None:
			return node

		return None			

	def displayViewport(self, viewportRef):
		if debug: print 'LayoutView.displayViewport: change viewport =',viewportRef
		if self.currentViewport != None:
			self.currentViewport.hide()
		self.currentViewport = self.getViewportNode(viewportRef)
		self.currentViewport.showAllNodes()
				
###########################

#
# Helper to manage the tree needed for the layout view
# this class manage a tree of visible/audible nodes
# each node may be either:
# - a viewport node (MMChannel instance)
# - a region (MMChannel instance)
# - a media (MMNode) instance
#
# The main goals of this class are:
# - optimize the rendering (for the previous area and tree widget) when there is a tree mutation
# for example, if you delete one media, you don't need to rebuild all tree widget. The benefits are multiple:
# the visual effect will be much better. no unexpected scrolls, faster, ...
# - facilitate the region/media tree management, and in particular for the media nodes
# - facilitate some filter operations, and make much more robust the layout view

class TreeHelper:
	def __init__(self, context, channelTreeRef, mmnodeTreeRef):
		self._context = context
		self.__channelTreeRef = channelTreeRef
		self.__mmnodeTreeRef = mmnodeTreeRef
		self.__nodeList = {}
		self.__rootList = {}

	# return tree if node is a valid media nodes
	def _isValidMMNode(self, node):
		if node == None:
			return 0
		from MMTypes import leaftypes
		if not node.type in leaftypes:
			return 0
		import ChannelMap
		return ChannelMap.isvisiblechannel(node.GetChannelType())

	# check the media node references and update the internal structure
	def __checkMediaNodeList(self, nodeRef):
		if self._isValidMMNode(nodeRef):
			channel = nodeRef.GetChannel()
			if channel != None:
				region = channel.GetLayoutChannel()
				if region != None:
					parentRef = region
					tParentNode =  self.__nodeList.get(parentRef)
					if tParentNode == None:
						tParentNode = self.__nodeList[parentRef] = TreeNodeHelper(parentRef, TYPE_REGION)
					tNode =  self.__nodeList.get(nodeRef)
					if tNode == None:
						tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_MEDIA)
					if not tParentNode.hasChild(tNode):
						tNode.isNew = 1
						tParentNode.addChild(tNode)
					tNode.isUsed = 1
						
		for child in nodeRef.GetChildren():
			self.__checkMediaNodeList(child)

	# check the media node references and update the internal structure
	def _checkMediaNodeList(self):
		self.__checkMediaNodeList(self.__mmnodeTreeRef)

	# check the region/viewport node references and update the internal structure
	def __checkRegionNodeList(self, parentRef, nodeRef):
		if debug2: print 'treeHelper.__checkRegionNodeList : start ',nodeRef
		if parentRef != None:
			tParentNode =  self.__nodeList.get(parentRef)
			if tParentNode == None:
				tParentNode = self.__nodeList[parentRef] = TreeNodeHelper(parentRef, TYPE_REGION)
		tNode =  self.__nodeList.get(nodeRef)
		if tNode == None:
			if parentRef == None:
				tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_VIEWPORT)
			else:
				tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_REGION)
		if parentRef != None:
			if not tParentNode.hasChild(tNode):
				tNode.isNew = 1
				tParentNode.addChild(tNode)
		tNode.isUsed = 1
		
		# if viewport
		if parentRef == None:
			self.__rootList[nodeRef] = tNode
		for subreg in self.__channelTreeRef.getsubregions(nodeRef):
			self.__checkRegionNodeList(nodeRef, subreg)
		if debug2: print 'treeHelper.__checkRegionNodeList : end ',nodeRef

	# check the region/viewport node references and update the internal structure
	def _checkRegionNodeList(self):
		viewportRefList = self.__channelTreeRef.getviewports()
		for viewportRef in viewportRefList:
			self.__checkRegionNodeList(None, viewportRef)
		
	# this method is called when a node has to be deleted
	def __onDelNode(self, parent, node):
		if debug: print 'treeHelper.__onDelNode : ',node.nodeRef
		for child in node.children.keys():
			self.__onDelNode(node, child)
		if parent != None:
			del parent.children[node]
			parentRef = parent.nodeRef
		else:
			parentRef = None
			del self.__rootList[node.nodeRef]
		self._context.onDelNodeRef(parentRef, node.nodeRef)
		del self.__nodeList[node.nodeRef]

	# this method is called when a node has to be added	
	def __onNewNode(self, parent, node):
		if debug: print 'treeHelper.__onNewNode : ',node.nodeRef
		if parent != None:
			parentRef = parent.nodeRef
		else:
			parentRef = None		
		self._context.onNewNodeRef(parentRef, node.nodeRef)
		for child in node.children.keys():
			self.__onNewNode(node, child)
		# reset the flags for the next time
		node.isNew = 0
		node.isUsed = 0

	# this method look for all mutations relative to the previous update		
	def __detectMutation(self, parent, node):
		if debug2: print 'treeHelper.__detectMutation : start ',node.nodeRef
		# detect the node to erase
		if not node.isNew and not node.isUsed:
			self.__onDelNode(parent, node)
		# detect the new nodes
		elif node.isNew:
			self.__onNewNode(parent, node)
		else:
			# if no changment, check in children
			for child in node.children.keys():
				self.__detectMutation(node, child)
			# reset the flags the the next time
			node.isUsed = 0
		if debug2: print 'treeHelper.__detectMutation : end ',node.nodeRef
			
	# this method look for all mutations relative to the previous update		
	def _detectMutation(self):
		for key, root in self.__rootList.items():
			self.__detectMutation(None, root)

	#
	# public methods
	#

	# the method look for all mutations relative to the previous update, and call the appropriate handlers
	# in the right order for each basic operation
	def onTreeMutation(self):
		if debug: print 'treeHelper.onTreeMutation start'
		self._checkMediaNodeList()
		self._checkRegionNodeList()
		self._detectMutation()
		if debug: print 'treeHelper.onTreeMutation end'

	# return the list of the nodeRef children
	# the children are either some viewports, some regions or some medias
	def getChildren(self, nodeRef):
		list = []
		node = self.__nodeList.get(nodeRef)
		for child in node.children.keys():
			list.append(child.nodeRef)
		return list

	# return the media list of the regionRef children
	def getMediaChildren(self, regionRef):
		list = []
		node = self.__nodeList.get(regionRef)
		for child in node.children.keys():
			if self.getNodeType(child.nodeRef) == TYPE_MEDIA:
				list.append(child.nodeRef)
		return list

	# return the region list inside the viewport
	# This method is not optimized: it should disapear
	def getRegionList(self, viewportRef):
		list = []
		for nodeRef in self.__nodeList.keys():
			vp = self.__channelTreeRef.getviewport(nodeRef)
			if vp is viewportRef:
				list.append(nodeRef)
		return list
		
	# return true is the node ref exist and is valid
	def existRef(self, nodeRef):
		return self.__nodeList.has_key(nodeRef)

	# return the list of root node
	def getRootNodeList(self):
		return self.__channelTreeRef.getviewports()

	# return the type of the node
	# Note. This method works also if the node is already remove it from the reference document
	# and not yet from this structure
	def getNodeType(self, nodeRef):
		node = self.__nodeList.get(nodeRef)
		if node != None:
			return node.type			
		
class TreeNodeHelper:
	def __init__(self, nodeRef, type):
		self.isNew = 1
		self.isUsed = 1
		self.nodeRef = nodeRef
		self.children = {}
		self.type = type

	def hasChild(self, child):
		return self.children.has_key(child)
	
	def addChild(self, child):
		self.children[child] = 1

		
#
# Main layout view code
#

class LayoutView2(LayoutViewDialog2):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.GetContext()
		self.editmgr = self.context.editmgr

		# global variable which allow to acces the to tree region structure on the reference document		
		self.__channelTreeRef = None

		LayoutViewDialog2.__init__(self)

		# current state
		self.currentNodeRefSelected = None
		self.currentFocus = None
		self.currentFocusType = None
		# allow to identify if the focus has been fixed by this view
		self.myfocus = None

		# remember the last item selected		
		self.lastViewportRefSelected = None
		self.lastRegionRefSelected = None
		self.lastMediaRefSelected = None

		# when you swap to the pause state, the current region showed list is saved
		# it allows to restore the context when document is stopped
		# XXX may changed
		# self.stopSelectedRegionList = []
		# self.stopSelectedMediaList = []

		self.previousWidget = PreviousWidget(self)

		self.showName = 1
		if treeVersion:
			self.asOutLine = 0
		else:
			self.asOutLine = 1
		self.showAllRegions = 1
		
		# define the valid command according to the node selected
		self.mkmediacommandlist()
		self.mkregioncommandlist()
		self.mkviewportcommandlist()
		
	def fixtitle(self):
		pass			# for now...
	
	def get_geometry(self):
		pass
	
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		LayoutViewDialog2.destroy(self)

	def mkviewportcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandViewportList = [
				ATTRIBUTES(callback = (self.__editProperties, ())),
				NEW_REGION(callback = (self.__newRegion, ())),
				DELETE(callback = (self.__delNode, ())),
				]
		else:
			self.commandViewportList = [
				ATTRIBUTES(callback = (self.__selectBgColor, ())),
				]

	def mkregioncommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandRegionList = [
				ATTRIBUTES(callback = (self.__editProperties, ())),
				NEW_REGION(callback = (self.__newRegion, ())),
				DELETE(callback = (self.__delNode, ())),
				]
		else:
			self.commandRegionList = [
				ATTRIBUTES(callback = (self.__selectBgColor, ())),
				]

	def mkmediacommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMediaList = [
				ATTRIBUTES(callback = (self.__editProperties, ())),
				]
		else:
			self.commandMediaList = []
		
	def show(self):
		if self.is_showing():
			LayoutViewDialog2.show(self)
			return
		LayoutViewDialog2.show(self)
		
		# init the previous widget
		self.previousWidget.init()
		
		# init the tree control with the current datas
		if treeVersion:
			self.initTreeCtrl()

		self.__channelTreeRef = self.context.getchanneltree()

		################################################################################
		# IMPORTANT: call this method after calling the method context.getchanneltree()
		self.editmgr.register(self, 1, 1)
		################################################################################

		self.treeHelper = TreeHelper(self, self.__channelTreeRef, self.root)

		# all widget are maded from this step		
		self.treeMutation()

		# expand all region nodes by default
		if treeVersion:
			self.expandAllNodes(0)
		
		self.initDialogBox()
		
		# show the first viewport in the list		
		currentViewportList = self.getViewportRefList()
		viewport = currentViewportList[0]
		self.previousWidget.displayViewport(viewport)

		# show initial regions
		self.previousWidget.appendAllRegionNodeList()

		# XXX to implement
		# get the initial player state		
#		type,node = self.editmgr.getplayerstate()
#		if node != None:
#			self.playerstatechanged(type, node)
			
		# get the initial focus		
		self.currentFocusType,self.currentFocus = self.editmgr.getglobalfocus()
		self.updateFocus()
		
	def hide(self):
		if not self.is_showing():
			return
		self.__channelTreeRef = None
		self.editmgr.unregister(self)
		LayoutViewDialog2.hide(self)

		# XXX to do: destroy all objects and to check that they are garbage collected
		
	def transaction(self, type):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def GetContext(self):
		return self.context
		
	def rebuildAll(self):
		self.treeMutation()
		self.previousWidget.updateRegionTree()		

	#
	# implementation of tree helper handler methods
	#
	
	def onNewNodeRef(self, parentRef, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			self.previousWidget.addViewport(nodeRef)			
			if treeVersion:
				self.appendViewportInTreeCtrl(nodeRef)
		elif nodeType == TYPE_REGION:
			self.previousWidget.addRegion(parentRef, nodeRef)
			if treeVersion:
				self.appendRegionInTreeCtrl(parentRef, nodeRef)
		elif nodeType == TYPE_MEDIA:
			if treeVersion:
				self.appendMediaInTreeCtrl(parentRef, nodeRef)
		
	def onDelNodeRef(self, parentRef, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			self.previousWidget.removeViewport(nodeRef)
			if treeVersion:
				self.removeNodeInTreeCtrl(nodeRef)
		elif nodeType == TYPE_REGION:
			self.previousWidget.removeRegion(nodeRef)
			if treeVersion:
				self.removeNodeInTreeCtrl(nodeRef)
		elif nodeType == TYPE_MEDIA:
			if treeVersion:
				self.removeNodeInTreeCtrl(nodeRef)

	#
	#
	#
	
	# update the region tree
	def treeMutation(self):
		if debug: print 'call treeHelper.treeMutation'
		self.treeHelper.onTreeMutation()

	def commit(self, type):
		if type in ('REGION_GEOM', 'MEDIA_GEOM'):
			self.previousWidget.updateRegionTree()
		elif type == 'REGION_TREE':
			self.treeMutation()
			self.previousWidget.updateRegionTree()
		else:
			self.rebuildAll()

		self.updateFocus()
				
	def isValidMMNode(self, node):
		if node == None:
			return 0
		from MMTypes import leaftypes
		if not node.type in leaftypes:
			return 0
		import ChannelMap
		return ChannelMap.isvisiblechannel(node.GetChannelType())

	def focusOnMMChannel(self, focusobject):		
		nodeType = self.getNodeType(focusobject)
		if nodeType == None:
			return

		# update previous area and command list
		if nodeType == TYPE_REGION:
			self.previousWidget.selectRegion(focusobject)			
			self.setcommandlist(self.commandRegionList)
		elif nodeType == TYPE_VIEWPORT:
			self.previousWidget.selectViewport(focusobject)			
			self.setcommandlist(self.commandViewportList)

		# update dialog box
		self.select(focusobject)
		
		# update tree widget
		if treeVersion:
			self.selectNodeInTreeCtrl(focusobject)
						
	def focusOnMMNode(self, focusobject):
		# update command list
		self.setcommandlist(self.commandMediaList)
		
		# update previous area
		self.previousWidget.selectMedia(focusobject)
			
		# update dialog box
		self.select(focusobject)
		
		# update tree widget
		if treeVersion:
			self.selectNodeInTreeCtrl(focusobject)

	def focusOnUnknown(self, focusobject):
		# update command list
		self.setcommandlist([])
		
		# update previous area
		self.previousWidget.selectUnknown(focusobject)

		# update dialog box
		self.unselect()

		# update tree widget
		if treeVersion:
			# XXX to do
			pass
							
		# XXX to implement
#	def toStopState(self):
#		# save current state
#		self.currentRegionRefListM = self.stopSelectedRegionList
#		self.currentMediaRefListM = self.stopSelectedMediaList

#		saveCurrentViewport = self.currentViewport
#		self.rebuildAll()
		
#		# append the media/region node list
#		self.appendRegionNodeList(self.currentRegionRefListM)
#		self.appendMediaNodeList(self.currentMediaRefListM)
		
#		# re display all viewport
#		self.displayViewport(saveCurrentViewport.getNodeRef())
#		self.updateFocus()
		
#	def toPauseState(self, nodeobject):
#		# save current state
#		self.stopSelectedRegionList = self.currentRegionRefListM
#		self.stopSelectedMediaList = self.currentMediaRefListM

#		self.currentMediaRefListM = []
#		self.currentRegionRefListM = []
#		saveCurrentViewport = self.currentViewport
#		self.rebuildAll()
		
#		for type, node in nodeobject:
#			if type == 'MMChannel':
#				self.currentRegionRefListM.append(node)
#			elif type == 'MMNode':
#				if self.isValidMMNode(node):
#					self.currentMediaRefListM.append(node)
		
#		# append the media/region node list
#		self.appendMediaNodeList(self.currentMediaRefListM)
#		self.appendRegionNodeList(self.currentRegionRefListM)
		
#		# re display all viewport
#		self.displayViewport(saveCurrentViewport.getNodeRef())
#		self.updateFocus()

	def updateFocus(self):
		if debug: print 'LayoutView.updateFocus:',self.currentFocusType,' focusobject=',self.currentFocus		
		# check is the focus is still valid
		# XXX this call should be exist. Normaly all view which are responsibled of delete a node
		# should change the global focus as well if it points on the deleted node
		if not self.isValidFocus():
			if debug: print 'LayoutView.updateFocus: no valid focus'
			self.focusOnUnknown(self.currentFocus)
			return
		
		if self.currentFocusType == 'MMNode':
			if debug: print 'LayoutView.updateFocus: focus on MMNode'
			self.focusOnMMNode(self.currentFocus)
		elif self.currentFocusType == 'MMChannel':
			if debug: print 'LayoutView.updateFocus: focus on MMChannel'
			self.focusOnMMChannel(self.currentFocus)
		else:
			if debug: print 'LayoutView.updateFocus: unknow focus type'
			self.focusOnUnknown(self.currentFocus)

	def isValidFocus(self):
		if self.currentFocusType == 'MMNode':
			return self.existRef(self.currentFocus)
		elif self.currentFocusType == 'MMChannel':
			name = self.currentFocus.name
			return self.context.getchannel(name) is not None
		else:
			# no focus, or unknown focus, doesn't change anything
			return 1
		
	def globalfocuschanged(self, focustype, focusobject):
		if debug: print 'LayoutView.globalfocuschanged focustype=',focustype,' focusobject=',focusobject
		self.currentFocus = focusobject
		self.currentFocusType = focustype
		if self.myfocus is not None and focusobject is self.myfocus:
			self.myfocus = None
			return
		self.myfocus = None

		# remove media node from previous selection		
		self.previousWidget.removeTempMediaNodeList()

		self.updateFocus()
		
	def setglobalfocus(self, focustype, focusobject):
		if debug: print 'LayoutView.globalfocuschanged focustype=',focustype,' focusobject=',focusobject
		self.myfocus = focusobject
		self.editmgr.setglobalfocus(focustype, focusobject)
		
	def playerstatechanged(self, type, parameters):
		pass
		# XXX to implement
#		if type == 'paused':
#			self.toPauseState(parameters)
#		elif type == 'stopped':
#			self.toStopState()
		
	def kill(self):
		self.destroy()
				
	# update the dialog box on unselection
	def unselect(self):
		self.updateUnselectedOnDialogBox()
						
	# update the dialog box on selection
	def select(self, nodeRef):
		if debug: print 'LayoutView.select: node ref =',nodeRef
		nodeType = self.getNodeType(nodeRef)

		if nodeType != None:
			self.currentNodeRefSelected = nodeRef
			
			self.fillViewportListOnDialogBox()
			viewportRef = self.getViewportRef(nodeRef)
			self.fillRegionListOnDialogBox(viewportRef)
			# update dialog box as well
			if nodeType == TYPE_VIEWPORT:
				self.fillMediaListOnDialogBox()
				self.updateViewportOnDialogBox(nodeRef)
				self.lastViewportRefSelected = nodeRef
				self.lastRegionRefSelected = None
				self.lastMediaRefSelected = None
			elif nodeType == TYPE_REGION:
				self.fillMediaListOnDialogBox(nodeRef)
				self.updateRegionOnDialogBox(nodeRef)
				self.lastRegionRefSelected = nodeRef
				self.lastMediaRefSelected = None
			elif nodeType == TYPE_MEDIA:
				self.fillMediaListOnDialogBox(self.getParentNodeRef(nodeRef, TYPE_MEDIA))
				self.updateMediaOnDialogBox(nodeRef)
				self.lastMediaRefSelected = nodeRef

	def getViewportRefList(self):
		return self.treeHelper.getRootNodeList()

	def getRegionRefList(self, viewportRef):
		return self.treeHelper.getRegionList(viewportRef)

	def getMediaChildren(self, regionRef):
		return self.treeHelper.getMediaChildren(regionRef)

	def getChildren(self, nodeRef):
		return self.treeHelper.getChildren(nodeRef)

	def existRef(self, nodeRef):
		return self.treeHelper.existRef(nodeRef)	
	
	def nameToNodeRef(self, name):
		return self.context.getchannel(name)

	def getNodeType(self, nodeRef):
		return self.treeHelper.getNodeType(nodeRef)

	# XXX to optimize, get info from tree helper
	def getViewportRef(self, nodeRef, nodeType = None):
		if nodeType == None:
			nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			region = self.getParentNodeRef(nodeRef, TYPE_MEDIA)
		else:
			region = nodeRef

		return self.__channelTreeRef.getviewport(region)
	
	# XXX to optimize, get info from tree helper
	# get the parent spatial node
	def getParentNodeRef(self, nodeRef, nodeType = None):
		if nodeType == None:
			nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			channel = nodeRef.GetChannel()
			if channel != None:
				region = channel.GetLayoutChannel()
				return region
			return None
		else:
			region = self.__channelTreeRef.getparent(nodeRef)
			return region
		return None
					
	def selectBgColor(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType != TYPE_MEDIA:
			# to do: for snap version, manage the inherit value
			bgcolor = nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
			transparent = nodeRef.GetInherAttrDef('transparent', 1)
		
			newbg = self.chooseBgColor(bgcolor)
			if newbg != None:
				if nodeRef.GetAttrDef('showEditBackground', 0):
					list = []
					list.append(('editBackground',newbg))
					self.applyEditorPreference(nodeRef, list)
				else:
					self.applyBgColor(nodeRef, newbg, transparent)

	def editProperties(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType in (TYPE_REGION, TYPE_VIEWPORT):
			# allow to choice attributes
			import AttrEdit		
			AttrEdit.showchannelattreditor(self.toplevel,
						self.context.channeldict[nodeRef.name])
		elif nodeType == TYPE_MEDIA:
			# allow to choice attributes
			import AttrEdit
			AttrEdit.showattreditor(self.toplevel, nodeRef)
			
	def sendBack(self, regionRef):
		currentZ = regionRef.GetAttrDef('z',0)

		# get the list of sibling regions
		parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
		regionRefList = self.getChildren(parentRef)

		# get the lower z-index
		# if the z index of selected region is already min:
		#   - don't change anything if it's the only region
		#	- change its value to a lower value to insure that it'll be all the time in back
		
		min = -1
		cntMin = 0
		for nodeRef in regionRefList:
			z = nodeRef.GetAttrDef('z', 0)
			if z<min or min == -1:
				min = z
				cntMin = 0
			elif z == min:
				cntMin = cntMin+1
				
		# make a list of region where the z index have to change
		chList = []
		if currentZ == min and cntMin == 1:
			# don't change anything
			return

		if min == 0:
			# we have to increment all z-index values
			for nodeRef in regionRefList:
				z = nodeRef.GetAttrDef('z', 0)
				if nodeRef is regionRef:
					chList.append((regionRef, min))
				else:
					chList.append((nodeRef, z+1))
				
		else:
			# we have just to fix the current z-index value to min-1
			chList.append((regionRef, min-1))

		self.applyZOrderOnRegionList(chList)
		
	def bringFront(self, regionRef):
		currentZ = regionRef.GetAttrDef('z', 0)
		
		# get the list of sibling regions
		parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
		regionRefList = self.getChildren(parentRef)

		# get the max z-index
		# if the z index of selected region is already max:
		#   - don't change anything if it's the only region
		#	- change its value to a higher value to insure that it'll be all the time in front
		
		max = -1
		cntMax = 0
		for nodeRef in regionRefList:
			z = nodeRef.GetAttrDef('z', 0)
			if z>max:
				max = z
				cntMax = 0
			elif z == max:
				cntMax = cntMax+1

		if currentZ == max and cntMax == 1:
			# don't change anything
			return

		self.applyZOrderOnRegion(regionRef, max+1)
		
	#
	# dialog box update methods
	#
	
	def initDialogBox(self):
		self.fillViewportListOnDialogBox()
		
		if not treeVersion:
			self.dialogCtrl.setCheckCtrl('ShowNames', self.showName)
			self.dialogCtrl.setCheckCtrl('AsOutLine', self.asOutLine)
			self.disableMediaListOnDialogBox()
			if features.CUSTOM_REGIONS in features.feature_set:
				self.dialogCtrl.enable('NewView',1)
				self.dialogCtrl.enable('ShowAllRegions',1)
				self.dialogCtrl.setCheckCtrl('ShowAllRegions', self.showAllRegions)
		
	def applyGeomOnViewport(self, viewportRef, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible at this time
		if self.editmgr.transaction('REGION_GEOM'):
			w,h =  geom
			self.editmgr.setchannelattr(viewportRef.name, 'width', geom[0])
			self.editmgr.setchannelattr(viewportRef.name, 'height', geom[1])
			self.editmgr.commit('REGION_GEOM')

	def applyGeomOnRegion(self, regionRef, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible 
		if self.editmgr.transaction('REGION_GEOM'):
			self.editmgr.setchannelattr(regionRef.name, 'base_winoff', geom)
			self.editmgr.setchannelattr(regionRef.name, 'units', UNIT_PXL)			
			self.editmgr.commit('REGION_GEOM')

	def applyGeomOnMedia(self, mediaRef, value):
		if self.editmgr.transaction('MEDIA_GEOM'):			
			x,y,w,h = value
			self.editmgr.setnodeattr(mediaRef, 'base_winoff', (x,y,w,h))
							
			# todo: some ajustements for take into account all fit values
			self.editmgr.commit('MEDIA_GEOM')
		
	def applyBgColor(self, nodeRef, bgcolor, transparent):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(nodeRef.name, 'bgcolor', bgcolor)
			self.editmgr.setchannelattr(nodeRef.name, 'transparent', transparent)
			self.editmgr.commit()

	def applyZOrderOnRegion(self, regionRef, value):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(regionRef.name, 'z', value)
			self.editmgr.commit()

	def applyZOrderOnMedia(self, mediaRef, value):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setnodeattr(mediaRef, 'z', value)
			self.editmgr.commit()

	def applyZOrderOnRegionList(self, list):
		# list is a list of tuple( region, z-index value)
		# test if possible 
		if self.editmgr.transaction():
			for regionRef, z in list:
				self.editmgr.setchannelattr(regionRef.name, 'z', z)
			self.editmgr.commit()

	def applyEditorPreference(self, nodeRef, attrList):
		if self.editmgr.transaction():
			nodeType = self.getNodeType(nodeRef)
			if nodeType in (TYPE_REGION, TYPE_VIEWPORT):
				for name, value in attrList:
					self.editmgr.setchannelattr(nodeRef.name, name, value)
			self.editmgr.commit()

	def applyNewRegion(self, parentRef, name):
		if self.editmgr.transaction():
			self.editmgr.addchannel(name, 0, 'layout')
			self.editmgr.setchannelattr(name, 'base_window', parentRef.name)
			self.editmgr.commit('REGION_TREE')

	def applyNewViewport(self, name):
		if self.editmgr.transaction():
			self.editmgr.addchannel(name, 0, 'layout')
			self.editmgr.setchannelattr(name, 'transparent', 0)
			self.editmgr.setchannelattr(name, 'showEditBackground', 1)
			self.editmgr.setchannelattr(name, 'width', 400)
			self.editmgr.setchannelattr(name, 'height', 400)
			self.editmgr.commit('REGION_TREE')

	def applyDelRegion(self, regionRef):
		if self.editmgr.transaction():
			self.editmgr.delchannel(regionRef.name)
			self.editmgr.commit('REGION_TREE')
			
	def applyDelViewport(self, viewportRef):
		if self.editmgr.transaction():
			self.editmgr.delchannel(viewportRef.name)
			self.editmgr.commit('REGION_TREE')

	def updateUnselectedOnDialogBox(self):
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.enable('RegionW',0)
		self.dialogCtrl.enable('RegionH',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		self.dialogCtrl.setFieldCtrl('RegionW',"")		
		self.dialogCtrl.setFieldCtrl('RegionH',"")
		
		if treeVersion: return
		# clear and disable not valid fields
#		self.dialogCtrl.setSelecterCtrl('ViewportSel',-1)
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('RegionZ',0)
		
		self.dialogCtrl.enable('RegionSel',0)
		self.dialogCtrl.enable('MediaSel',0)

		self.dialogCtrl.enable('HideRegion',0)
		self.dialogCtrl.enable('HideMedia',0)
		
		self.dialogCtrl.enable('RegionCheck', 0)
		self.dialogCtrl.enable('MediaCheck', 0)
		self.dialogCtrl.setCheckCtrl('ViewportCheck', 0)
		self.dialogCtrl.setCheckCtrl('RegionCheck', 0)
		self.dialogCtrl.setCheckCtrl('MediaCheck', 0)

		self.dialogCtrl.enable('ShowRbg',0)
		self.dialogCtrl.setCheckCtrl('ShowRbg', 0)

		# don't allow to remove or add new regions
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',0)
			self.dialogCtrl.enable('DelRegion',0)
	
	def updateViewportOnDialogBox(self, nodeRef):
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		
		geom = nodeRef.getPxGeom()
		self.updateViewportGeomOnDialogBox(geom)
				
		if treeVersion: return
		# update region list
		self.currentRegionRefListSel = self.getRegionRefList(nodeRef)
			
		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = nodeRef.GetAttrDef('showEditBackground', 0)
		if showEditBackground == 1:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		# clear and disable not valid fields
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		
		# update the viewport selecter
		index = self.currentViewportList.index(nodeRef)
		self.dialogCtrl.setSelecterCtrl('ViewportSel',index)
			
		self.dialogCtrl.setCheckCtrl('ViewportCheck',1)
		self.dialogCtrl.setCheckCtrl('RegionCheck',0)
		self.dialogCtrl.setCheckCtrl('MediaCheck',0)
		self.dialogCtrl.enable('HideRegion',0)
		self.dialogCtrl.enable('HideMedia',0)

		# allow to remove or add new regions
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',1)
			self.dialogCtrl.enable('DelRegion',1)

	def updateViewportGeomOnDialogBox(self, geom):
		# update the fields dialog box
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[1])
		
	def updateRegionOnDialogBox(self, nodeRef):
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)

		self.dialogCtrl.enable('RegionZ',1)
		
		z = nodeRef.GetAttrDef('z', 0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)		

		geom = nodeRef.getPxGeom()	
		self.updateRegionGeomOnDialogBox(geom)
		
		if treeVersion: return
		
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)

		# enable valid fields
		self.dialogCtrl.enable('SendBack',1)
		self.dialogCtrl.enable('BringFront',1)
		
		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = nodeRef.GetAttrDef('showEditBackground', 0)
		if showEditBackground == 1:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		# update the region selecter
		if len(self.currentRegionRefListSel) > 0:
			index = self.currentRegionRefListSel.index(nodeRef)
			self.dialogCtrl.setSelecterCtrl('RegionSel',index)
				
		# update the viewport selecter
		if len(self.currentViewportList) > 0:
			viewportRef = self.getViewportRef(nodeRef)
			index = self.currentViewportList.index(viewportRef)
			self.dialogCtrl.setSelecterCtrl('ViewportSel',index)

		self.dialogCtrl.setCheckCtrl('ViewportCheck',0)
		self.dialogCtrl.setCheckCtrl('RegionCheck',1)
		self.dialogCtrl.setCheckCtrl('MediaCheck',0)
		self.dialogCtrl.enable('HideRegion',0)
		self.dialogCtrl.enable('HideMedia',0)

		# allow to remove or add new regions
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',1)
			self.dialogCtrl.enable('DelRegion',1)

	def updateRegionGeomOnDialogBox(self, geom):
		self.dialogCtrl.setFieldCtrl('RegionX',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionY',"%d"%geom[1])		
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])

	def fillMediaListOnDialogBox(self, regionRef = None):
		if treeVersion: return
		if regionRef == None:
			self.currentMediaRefListSel = []
			list = []
		else:
			currentMediaList = self.getMediaChildren(regionRef)
			list = []
			for mediaRef in currentMediaList:
				list.append(mediaRef.attrdict.get('name'))
			self.currentMediaRefListSel = currentMediaList
		
		if len(list) > 0:
			self.dialogCtrl.fillSelecterCtrl('MediaSel', list)
			self.enableMediaListOnDialogBox()
		else:
			self.disableMediaListOnDialogBox()

	def disableMediaListOnDialogBox(self):
		if treeVersion: return
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)		
		self.dialogCtrl.enable('MediaSel',0)
		self.dialogCtrl.enable('MediaCheck', 0)

	def enableMediaListOnDialogBox(self):
		if treeVersion: return
		self.dialogCtrl.enable('MediaSel',1)
		self.dialogCtrl.enable('MediaCheck', 0)

	def fillViewportListOnDialogBox(self):
		if treeVersion: return
		self.currentViewportList = self.getViewportRefList()
		list = []
		for viewportRef in self.currentViewportList:
			list.append(viewportRef.name)
		self.dialogCtrl.fillSelecterCtrl('ViewportSel', list)
		
	def fillRegionListOnDialogBox(self, viewportRef):
		if treeVersion: return
		self.currentRegionRefListSel = self.getRegionRefList(viewportRef)
						
		if len(self.currentRegionRefListSel) > 0:
			list = []
			for regionRef in self.currentRegionRefListSel:
				list.append(regionRef.name)
			self.dialogCtrl.fillSelecterCtrl('RegionSel', list)
			self.enableRegionListOnDialogBox()
		else:
			self.disableRegionListOnDialogBox()

	def disableRegionListOnDialogBox(self):
		if treeVersion: return
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)		
		self.dialogCtrl.enable('RegionSel',0)
		self.dialogCtrl.enable('RegionCheck', 0)

	def enableRegionListOnDialogBox(self):
		if treeVersion: return
		self.dialogCtrl.enable('RegionSel',1)
		self.dialogCtrl.enable('RegionCheck', 0)
		
	def updateMediaOnDialogBox(self, nodeRef):
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)
		self.dialogCtrl.enable('RegionZ',1)

		z = nodeRef.GetAttrDef('z', 0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)		
		
		geom = nodeRef.getPxGeom()		
		self.updateMediaGeomOnDialogBox(geom)
		
		if treeVersion: return
		
		# update the media selecter
		if len(self.currentMediaRefListSel) > 0:
			index = self.currentMediaRefListSel.index(nodeRef)
			self.dialogCtrl.setSelecterCtrl('MediaSel',index)

		# update the region selecter
		regionRef = self.getParentNodeRef(nodeRef, TYPE_MEDIA)
		if self.currentRegionRefListSel != None:
			index = self.currentRegionRefListSel.index(regionRef)
			self.dialogCtrl.setSelecterCtrl('RegionSel',index)

		# update the viewport selecter
		if len(self.currentViewportList) > 0:
			index = self.currentViewportList.index(self.getViewportRef(nodeRef))
			self.dialogCtrl.setSelecterCtrl('ViewportSel',index)
		
		# clear and disable not valid fields
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('ShowRbg',0)
		self.dialogCtrl.setCheckCtrl('ShowRbg', 0)

#		self.dialogCtrl.enable('BgColor', 0)
							   
		self.dialogCtrl.setCheckCtrl('ViewportCheck',0)
		self.dialogCtrl.setCheckCtrl('RegionCheck',0)
		self.dialogCtrl.setCheckCtrl('MediaCheck',1)
		self.dialogCtrl.enable('HideRegion',0)
		self.dialogCtrl.enable('HideMedia',0)

		# we can't add or remove regions from media object
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',0)
			self.dialogCtrl.enable('DelRegion',0)
				
	def updateMediaGeomOnDialogBox(self, geom):
		self.updateRegionGeomOnDialogBox(geom)
		
	#
	# internal methods
	#

	def __updateZOrder(self, value):
		if self.currentNodeRefSelected != None:
			nodeType = self.getNodeType(self.currentNodeRefSelected)
			if nodeType == TYPE_REGION:
				self.applyZOrderOnRegion(self.currentNodeRefSelected, value)
			elif nodeType == TYPE_MEDIA:
				self.applyZOrderOnMedia(self.currentNodeRefSelected, value)

	def __updateGeomOnViewport(self, ctrlName, value):
		if self.currentNodeRefSelected != None:
			nodeRef = self.currentNodeRefSelected
			w,h = nodeRef.getPxGeom()
			if ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			self.applyGeomOnViewport(nodeRef, (w,h))

	def __updateGeomOnRegion(self, ctrlName, value):
		if self.currentNodeRefSelected != None:		
			nodeRef = self.currentNodeRefSelected
			x,y,w,h = nodeRef.getPxGeom()
			if ctrlName == 'RegionX':
				x = value
			elif ctrlName == 'RegionY':
				y = value			
			elif ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value			
			self.applyGeomOnRegion(nodeRef, (x,y,w,h))

	def __updateGeomOnMedia(self, ctrlName, value):
		if self.currentNodeRefSelected != None:
			mediaNode = self.getMediaNode(self.currentNodeRefSelected)
			geom = mediaNode._curattrdict['wingeom']
			x,y,w,h = geom
			if ctrlName == 'RegionX':
				x = value
			elif ctrlName == 'RegionY':
				y = value			
			elif ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value			
			self.applyGeomOnMedia(self.currentNodeRefSelected, (x,y,w,h))
		
	def __updateGeom(self, ctrlName, value):
		if self.currentNodeRefSelected != None:
			nodeType = self.getNodeType(self.currentNodeRefSelected)
			if nodeType == TYPE_VIEWPORT:
				self.__updateGeomOnViewport(ctrlName, value)
			elif nodeType == TYPE_REGION:
				self.__updateGeomOnRegion(ctrlName, value)
			elif nodeType == TYPE_MEDIA:
				self.__updateGeomOnMedia(ctrlName, value)

	def __editProperties(self):
		if self.currentNodeRefSelected != None:
			self.editProperties(self.currentNodeRefSelected)
						
	def __selectBgColor(self):
		if self.currentNodeRefSelected != None:
			self.selectBgColor(self.currentNodeRefSelected)

	def __sendBack(self):
		if self.currentNodeRefSelected != None:
			self.sendBack(self.currentNodeRefSelected)

	def __bringFront(self):
		if self.currentNodeRefSelected != None:
			self.bringFront(self.currentNodeRefSelected)

	def __selectViewport(self, selectedName):
		nodeRef = None
		# search the viewport ref associated to the selected name
		viewportRefList = self.getViewportRefList()
		for ref in viewportRefList:
			if ref.name == selectedName:
				nodeRef = ref
				break
				
		if nodeRef != None:
#			self.displayViewport(nodeRef)
			self.setglobalfocus('MMChannel',nodeRef)
			self.updateFocus()
			
	def __selectRegion(self, selectedName):
		nodeRef = None
		# search the region ref associated to the selected name
		for ref in self.currentRegionRefListSel:
			if ref.name == selectedName:
				nodeRef = ref
				break
			
		if nodeRef != None:
#			if nodeRef not in self.currentRegionRefListM and nodeRef not in self.currentRegionRefListT:
#				# add the region
#				self.appendRegionNodeList([nodeRef])
#				self.currentRegionRefListM.append(nodeRef)
#			elif nodeRef not in self.currentRegionRefListM:
#				# transfert to the main list
#				self.currentRegionRefListM.append(nodeRef)
#				self.currentRegionRefListT.remove(nodeRef)

			self.setglobalfocus('MMChannel',nodeRef)
			self.updateFocus()
			
	def __selectMedia(self, selectedName):
		nodeRef = None
		# get the node ref associated to the selected item
		for ref in self.currentMediaRefListSel:
			if ref.attrdict.get('name') == selectedName:
				nodeRef = ref
				break
			
#		if not self.isValidMMNode(nodeRef):
#			return
		
		if nodeRef != None:
#			if nodeRef not in self.currentMediaRefListM and nodeRef not in self.currentMediaRefListT:
#				# add the media
#				self.appendMediaNodeList([nodeRef])
#				self.currentMediaRefListM.append(nodeRef)
#			elif nodeRef not in self.currentMediaRefListM:
#				# transfert to the main list
#				self.currentMediaRefListM.append(nodeRef)
#				self.currentMediaRefListT.remove(nodeRef)

			self.setglobalfocus('MMNode',nodeRef)
			self.updateFocus()

	def __showEditBackground(self, value):
		if self.currentNodeRefSelected != None:
			nodeRef = self.currentNodeRefSelected
			nodeType = self.getNodeType(self.currentNodeRefSelected)
			if nodeType in (TYPE_REGION, TYPE_VIEWPORT):
				list = []
				if not value:
					if not nodeRef.has_key('showEditBackground'):
						list.append(('showEditBackground',1))
					if not nodeRef.has_key('editBackground'):	
						list.append(('editBackground',nodeRef.GetAttrDef('bgcolor')))
				else:
					if nodeRef.has_key('showEditBackground'):
						list.append(('showEditBackground',None))
				self.applyEditorPreference(nodeRef, list)

	def newRegion(self, parentRef):
		# choice a default name which doesn't exist		
		channeldict = self.context.channeldict
		baseName = 'region'
		i = 1
		name = baseName + `i`
		while channeldict.has_key(name):
			i = i+1
			name = baseName + `i`
			
		self.__parentRef = parentRef
		self.askname(name, 'Name for region', self.__regionNamedCallback)

	def __regionNamedCallback(self, name):
		self.applyNewRegion(self.__parentRef, name)
		self.setglobalfocus('MMChannel', self.nameToNodeRef(name))
		self.updateFocus()

	def newViewport(self):
		# choice a default name which doesn't exist		
		channeldict = self.context.channeldict
		baseName = 'viewport'
		i = 1
		name = baseName + `i`
		while channeldict.has_key(name):
			i = i+1
			name = baseName + `i`
			
		self.askname(name, 'Name for viewport', self.__viewportNamedCallback)

	def __viewportNamedCallback(self, name):
		self.applyNewViewport(name)
		self.setglobalfocus('MMChannel', self.nameToNodeRef(name))
		self.updateFocus()

	def __newRegion(self):
		if self.currentNodeRefSelected != None:
			self.newRegion(self.currentNodeRefSelected)

	def __newViewport(self):
		self.newViewport()

	def delRegion(self, regionRef):
		# for now, we can only erase an empty viewport
#		if not self.isEmpty(regionRef):
#			msg = "you have to delete before the sub regions and associated medias"
#			windowinterface.showmessage(msg, mtype = 'error')
#			return
		
		parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
		self.setglobalfocus('MMChannel',parentRef)
		self.applyDelRegion(regionRef)

	# checking if the region/viewport node contains any sub-region or media
	def isEmpty(self, nodeRef):
		# checking if has sub-region
		children = self.treeHelper.getChildren(nodeRef)
		if children != None:
			return len(children) == 0
		return 1

	def delViewport(self, nodeRef):
		# for now, we have to keep at least one viewport
		currentViewportList = self.getViewportRefList()
		if len(currentViewportList) <= 1:
			msg = "you can't delete the last viewport"
			windowinterface.showmessage(msg, mtype = 'error')
			return

		# for now, we can only erase an empty viewport
#		if not self.isEmpty(nodeRef):
#			msg = "you have to delete before the sub regions and associated medias"
#			windowinterface.showmessage(msg, mtype = 'error')
#			return
		
		# change the focus
		# choice another viewport to show (this first in the list)
		currentViewportList = self.getViewportRefList()
		for viewportRef in currentViewportList:
			if viewportRef != nodeRef:
				self.setglobalfocus('MMChannel', viewportRef)
				break
		
		self.applyDelViewport(nodeRef)
		
	def __delNode(self):
		if self.currentNodeRefSelected != None:
			nodeType = self.getNodeType(self.currentNodeRefSelected)
			if nodeType == TYPE_VIEWPORT:
				self.delViewport(self.currentNodeRefSelected)
			elif nodeType == TYPE_REGION:
				self.delRegion(self.currentNodeRefSelected)

	def __hideRegion(self):
		if self.currentNodeRefSelected != None:
			regionRef = self.currentNodeRefSelected
			self.removeRegionNode(regionRef)
			if regionRef in self.currentRegionRefListM:
				self.currentRegionRefListM.remove(regionRef)
			if regionRef in self.currentRegionRefListT:
				self.currentRegionRefListT.remove(regionRef)

			# redisplay viewport
			self.displayViewport(self.currentViewport.getNodeRef())

			# update focus
			parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
			self.setglobalfocus('MMChannel', parentRef)
			self.updateFocus()

	def __showAllRegions(self):
		self.showAllRegions = 1
		self.currentRegionRefListM = []
		self.currentRegionRefListT = []
		# focus on viewport
		self.rebuildAll()
		self.updateFocus()

	def __hideAllRegions(self):
		self.showAllRegions = 0
		self.currentRegionRefListM = []
		self.currentRegionRefListT = []
		# focus on viewport
		self.rebuildAll()
		
		self.updateFocus()
			
	def __hideMedia(self):
		if self.currentNodeRefSelected != None:
			mediaRef = self.currentNodeRefSelected
			self.removeMedia(mediaRef)
			if mediaRef in self.currentMediaRefListM:
				self.currentMediaRefListM.remove(mediaRef)
			if mediaRef in self.currentMediaRefListT:
				self.currentMediaRefListT.remove(mediaRef)

			# update focus
			parentRef = self.getParentNodeRef(mediaRef, TYPE_MEDIA)
			self.setglobalfocus('MMChannel', parentRef)
			self.updateFocus()
		
	#
	# interface implementation of 'previous tree node' 
	#
	
	def onPreviousSelectViewport(self, viewportNode):
		nodeRef = viewportNode.getNodeRef()
		self.currentNodeRefSelected = nodeRef
		self.fillRegionListOnDialogBox(nodeRef)
		self.fillMediaListOnDialogBox()
		self.updateViewportOnDialogBox(nodeRef)
		self.setglobalfocus('MMChannel',nodeRef)
		self.lastViewportRefSelected = nodeRef
		self.lastRegionRefSelected = None
		self.lastMediaRefSelected = None
		if treeVersion:
			self.selectNodeInTreeCtrl(nodeRef)
			
	def onPreviousSelectRegion(self, regionNode):
		nodeRef = regionNode.getNodeRef()
		self.currentNodeRefSelected  = nodeRef
		self.fillRegionListOnDialogBox(self.getViewportRef(nodeRef))
		self.fillMediaListOnDialogBox(nodeRef)
		self.updateRegionOnDialogBox(nodeRef)
		self.setglobalfocus('MMChannel',nodeRef)
		self.lastRegionRefSelected = nodeRef
		self.lastMediaRefSelected = None
		if treeVersion:
			self.selectNodeInTreeCtrl(nodeRef)
				
	def onPreviousSelectMedia(self, mediaNode):
		nodeRef = mediaNode.getNodeRef()
		self.currentNodeRefSelected  = nodeRef
		self.fillRegionListOnDialogBox(self.getViewportRef(nodeRef))
		self.fillMediaListOnDialogBox(self.getParentNodeRef(nodeRef, TYPE_MEDIA))
		self.updateMediaOnDialogBox(nodeRef)
		self.setglobalfocus('MMNode',nodeRef)
		self.lastMediaRefSelected = nodeRef
		if treeVersion:
			self.selectNodeInTreeCtrl(nodeRef)

	def onPreviousUnselect(self):
		self.setglobalfocus(None,None)
		self.updateFocus()

	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onSelecterCtrl(self, ctrlName, value):
		if ctrlName == 'ViewportSel':
			self.__selectViewport(value)	
		elif ctrlName == 'RegionSel':
			self.__selectRegion(value)	
		elif ctrlName == 'MediaSel':
			self.__selectMedia(value)	

	def onMultiSelCtrl(self, ctrlName, itemList):
		pass
	
	def onCheckCtrl(self, ctrlName, value):
		if ctrlName == 'ShowNames':
			self.showName = value
			self.updateFocus()
		elif ctrlName == 'AsOutLine':
			self.asOutLine = value
			self.updateFocus()
		elif ctrlName == 'ShowRbg':
			self.__showEditBackground(value)			
		elif ctrlName == 'ShowAllRegions':
			if value:
				self.__showAllRegions()
			else:
				self.__hideAllRegions()
				
	def onFieldCtrl(self, ctrlName, value):
		if ctrlName in ('RegionX','RegionY','RegionW','RegionH'):
			try:
				value = int(value)
				self.__updateGeom(ctrlName, value)
			except:
				value = None
		elif ctrlName == 'RegionZ':
			try:
				value = int(value)
			except:
				value = 0
			self.__updateZOrder(value)

	def onButtonClickCtrl(self, ctrlName):
#		if ctrlName == 'BgColor':
#			self.__selectBgColor()
#		elif ctrlName == 'Properties':
#			self.__editProperties()			
		if ctrlName == 'SendBack':
			self.__sendBack()
		elif ctrlName == 'BringFront':
			self.__bringFront()
		elif ctrlName == 'NewRegion':
			self.__newRegion()
		elif ctrlName == 'NewView':
			self.__newViewport()
		elif ctrlName == 'DelRegion':
			self.__delNode()

	#
	# tree ctrl management 
	#

	def appendMediaInTreeCtrl(self, pNodeRef, nodeRef):
		mediaType = nodeRef.GetChannelType()
		name = nodeRef.attrdict.get('name')
		if name == None:
			name=''
		ret = self.treeCtrl.insertNode(self.nodeRefToNodeTreeCtrlId[pNodeRef], name, mediaType, mediaType)
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef

	def appendViewportInTreeCtrl(self, nodeRef):
		ret = self.treeCtrl.insertNode(0, nodeRef.name, 'viewport', 'viewport')
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef
			
	def appendRegionInTreeCtrl(self, pNodeRef, nodeRef):
		ret = self.treeCtrl.insertNode(self.nodeRefToNodeTreeCtrlId[pNodeRef], nodeRef.name, 'region', 'region')
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef
		
	def removeNodeInTreeCtrl(self, nodeRef):
		nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
		if nodeTreeCtrlId != None:
			self.treeCtrl.removeNode(nodeTreeCtrlId)
			del self.nodeRefToNodeTreeCtrlId[nodeRef]
			del self.nodeTreeCtrlIdToNodeRef[nodeTreeCtrlId]
		
	def initTreeCtrl(self):
		self.treeCtrl.setHandler(self)
		
		self.nodeRefToNodeTreeCtrlId = {}
		self.nodeTreeCtrlIdToNodeRef = {}

	# selected node handler method
	def onSelectTreeNodeCtrl(self, nodeTreeCtrlId):
		nodeRefSelected = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		if nodeRefSelected == None:
			return
		
		# update focus
		nodeType = self.getNodeType(nodeRefSelected)
		if nodeType == None:
			return
		if nodeType == TYPE_REGION or nodeType == TYPE_VIEWPORT:
			self.setglobalfocus('MMChannel', nodeRefSelected)
		elif nodeType == TYPE_MEDIA:
			self.setglobalfocus('MMNode', nodeRefSelected)
		self.updateFocus()

	# select a node in the tree control
	def selectNodeInTreeCtrl(self, nodeRef):
		nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
		if nodeTreeCtrlId != None:
			self.treeCtrl.selectNode(nodeTreeCtrlId)

	def expandNodes(self, nodeRef, expandMediaNode):
		hasNotOnlyMedia = 0
		nodeType = self.getNodeType(nodeRef)
		children = self.getChildren(nodeRef)
		if not expandMediaNode and children != None:
			# expand only this node if there is a region inside
			for child in children:
				if self.getNodeType(child) != TYPE_MEDIA:
					hasNotOnlyMedia = 1
		if nodeType != TYPE_MEDIA and (hasNotOnlyMedia or expandMediaNode):
			self.treeCtrl.expand(self.nodeRefToNodeTreeCtrlId[nodeRef])
			for child in children:
				if self.getNodeType(child) != TYPE_MEDIA:
					self.expandNodes(child, expandMediaNode)
		
	# expand all region nodes
	# by default, don't make visible the media nodes
	def expandAllNodes(self, expandMediaNode):
		viewportRefList = self.__channelTreeRef.getviewports()
		rootNodeList = self.treeHelper.getRootNodeList()
		for node in rootNodeList:
			self.expandNodes(node, expandMediaNode)
				
		