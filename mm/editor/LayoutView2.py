# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from windowinterface import UNIT_PXL

from usercmd import *

import MMAttrdefs
import settings
import features
import windowinterface

ALL_LAYOUTS = '(All Channels)'
	
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
		return self._ctx.showName		

	def getName(self):
		return self._name

	def getParent(self):
		return self._parent
	
	def applyOnAllNode(self, fnc, params):
		apply(fnc, params)
		for child in self._children:
			child.applyOnAllNode(fnc, params)

	def select(self):
		if self.isShowed():
			self._selecting = 1
			self._graphicCtrl.select()
			self._selecting = 0

	def onUnselected(self):
		self._ctx.onPreviousUnselect()

	def hide(self):
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
		node = self
		nodeToShow = []
		while node != None:
			if not node._wantToShow:
				node._wantToShow = 1
				nodeToShow.append(node)
			node = node._parent
		nodeToShow.reverse()
		for node in nodeToShow:
			node.show()

	def toHiddenState(self):
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

		if self._ctx.asOutLine:
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
			self._ctx.onPreviousSelectRegion(self)

	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx.updateRegionGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.applyGeomOnRegion(self.getNodeRef(), geom)

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx.editProperties(self.getNodeRef())
		else:
			self._ctx.selectBgColor(self.getNodeRef())
				
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

		self.ctype = self._nodeRef.GetChannelType()

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
			self._ctx.onPreviousSelectMedia(self)

	def show(self):
		if self._parent._graphicCtrl == None:
			return

		if self.isShowed():
			self.hide()
			
		self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self._name)
		self._graphicCtrl.showName(0)		
		self._graphicCtrl.addListener(self)
		
		# copy from old hierarchical view to determinate the image to showed
		node = self._nodeRef
		ntype = node.GetType()
		
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')

		import os
		f = os.path.join(self.datadir, '%s.tiff' % self.ctype)
		url = node.GetAttrDef('file', None)		
		if self.ctype == 'image':
			fit = self.fit
			url = node.context.findurl(url)
			try:
				import MMurl
				f = MMurl.urlretrieve(url)[0]
			except IOError, arg:
				print "Cannot load image: %s"%arg
		else:
			fit = 'fill'
		if f is not None:
			self._graphicCtrl.setImage(f, fit)
		
	def onGeomChanging(self, geom):
		self._ctx.updateMediaGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.applyGeomOnMedia(self.getNodeRef(), geom)

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx.editProperties(self.getNodeRef())
	
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
			
		if editBackground != None:				
				self._curattrdict['bgcolor'] = editBackground
				self._curattrdict['transparent'] = 0
		else:
			self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
			self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)
		
		w,h=self._nodeRef.getPxGeom()
		self._curattrdict['wingeom'] = (self.currentX,self.currentY,w,h)

	def show(self):
		self._graphicCtrl = self._ctx.previousCtrl.newViewport(self._curattrdict, self._name)
		self._graphicCtrl.addListener(self)
		
	def showAllNodes(self):
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
		Node.updateAllAttrdict(self)
		
		# for now refresh all
		if self.isShowed():
			self.showAllNodes()
		
	def onSelected(self):
		if not self._selecting:
			self._ctx.onPreviousSelectViewport(self)

	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx.updateViewportGeomOnDialogBox(geom[2:])

	def onGeomChanged(self, geom):
		# apply the new value
		self.currentX = geom[0]
		self.currentY = geom[1]
		self._ctx.applyGeomOnViewport(self.getNodeRef(), geom[2:])

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx.editProperties(self.getNodeRef())
		else:
			self._ctx.selectBgColor(self.getNodeRef())

###########################

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
		self.currentViewport = None		
		self.currentNodeRefSelected = None
		self.currentFocus = None
		self.currentFocusType = None

		# deal with graphic selecter controls
		self.currentRegionRefListSel = []
		self.currentMediaRefListSel = []

		# remember the last item selected		
		self.lastViewportRefSelected = None
		self.lastRegionRefSelected = None
		self.lastMediaRefSelected = None

		# when you swap to the pause state, the current region showed list is saved
		# it allows to restore the context when document is stopped
		# XXX may changed
		self.stopSelectedRegionList = []
		self.stopSelectedMediaList = []

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

		# allow to identify if the focus has been fixed by this view
		self.myfocus = None

		# datas which are the image of the reference document
		# this datas are updated after each edit operation
		self._viewportsRegions = {}
		self._viewports = {}
		self._refToRegionNode = {}
				
		# init state of different dialog controls
		self.showName = 1
		self.asOutLine = 0
		self.showBgcolor = 1
		self.showAllRegions = 1

	def fixtitle(self):
		pass			# for now...
	
	def get_geometry(self):
		pass
	
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		LayoutViewDialog2.destroy(self)

	def show(self):
		if self.is_showing():
			LayoutViewDialog2.show(self)
			return
		LayoutViewDialog2.show(self)
		self.__channelTreeRef = self.context.getchanneltree()
		self.__makeMediaRefList()
		self.treeMutation()
		self.initDialogBox()

		# show the first viewport in the list		
		currentViewportList = self.getViewportRefList()
		viewport = currentViewportList[0]
		self.displayViewport(viewport)

		# show initial regions
		self.appendRegionNodeList(self.currentRegionRefListM)

		self.editmgr.register(self, 1, 1)

		# get the initial player state		
		type,node = self.editmgr.getplayerstate()
		if node != None:
			self.playerstatechanged(type, node)
			
		self.updateFocus()
		# get the initial focus		
		self.currentFocusType,self.currentFocus = self.editmgr.getglobalfocus()
		self.updateFocus()
		
	def hide(self):
		if not self.is_showing():
			return
		self.__channelTreeRef = None
		self.editmgr.unregister(self)
		LayoutViewDialog2.hide(self)

	def transaction(self, type):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def GetContext(self):
		return self.context

	# recursive method to build an ordered region list (any child is store after its parent)
	# the pure sound region are excluded
	def __buildOrderedRegionList(self, orderedRegionList, parentId):
		for subreg in self.__channelTreeRef.getsubregions(parentId):
			if subreg.GetAttrDef('chsubtype',None) != 'sound':
				orderedRegionList.append(subreg)
			self.__buildOrderedRegionList(orderedRegionList, subreg.name)

	# synchonize media lists with the reference document
	def __synchronizeCurrentMediaRefList(self):
		# main list
		deleteList = []
		for mediaRef in self.currentMediaRefListM:
			if not self.existMediaRef(mediaRef):
				deleteList.append(mediaRef)
		for mediaRef in deleteList:
			self.currentMediaRefListM.remove(mediaRef)

		# temporare list
		deleteList = []
		for mediaRef in self.currentMediaRefListT:
			if not self.existMediaRef(mediaRef):
				deleteList.append(mediaRef)
		for mediaRef in deleteList:
			self.currentMediaRefListT.remove(mediaRef)
		
	def rebuildAll(self):
		# incremental datas
		self._viewportsRegions = {}
		self._viewports = {}
		self._refToRegionNode = {}

		# force viewport to redisplay
		self.currentViewport = None
		
		# clear media list which are showing		
		self.currentMediaNodeListShowed = []

		# clear region list which are showing		
		self.currentRegionNodeListShowed = []

		# rebuild the node ref list		
		self.__makeMediaRefList()
		
		self.treeMutation()

		self.initDialogBox()

		# supress medias ids which doesn't exist anymore
		self.__synchronizeCurrentMediaRefList()
		
		# show current medias and regions selected
		self.appendMediaNodeList(self.currentMediaRefListM)
		self.appendMediaNodeList(self.currentMediaRefListT)
		self.appendRegionNodeList(self.currentRegionRefListM)
		self.appendRegionNodeList(self.currentRegionRefListT)
		
	# update the region tree
	def treeMutation(self):
		# make an ordered list of ref layout channel
		viewportRefList = self.__channelTreeRef.getviewports()
		orderedRegionRefList = self.__orderedRegionRefList = []
		for viewportRef in viewportRefList:
			self.__buildOrderedRegionList(orderedRegionRefList, viewportRef.name)
				
		# make a list of new regions and viewports to append
		regionToAppendList = []
		viewportToAppendList = []

		for viewportRef in viewportRefList:
			viewportNode = self.getViewportNode(viewportRef)
			if viewportNode == None:
				viewportToAppendList.append(viewportRef)
				
		for regionRef in orderedRegionRefList:
			regionNode = self.getRegionNode(regionRef)
			parentRef = self.__channelTreeRef.getparent(regionRef.name)
			if regionNode == None:
				regionToAppendList.append((regionRef, parentRef))

		# make a list of viewports, regions to remove
		regionToRemoveList = []
		viewportToRemoveList = []
		oldViewportRefList = self._viewportsRegions.keys()
		for viewportRef in oldViewportRefList:
			if viewportRef not in viewportRefList:
				viewportToRemoveList.append(viewportRef)
			oldRegionRefList = self._viewportsRegions[viewportRef]
			for regionRef in oldRegionRefList:
				if regionRef not in orderedRegionRefList:
					regionToRemoveList.append(regionRef)
		
		# call effective add/remove operations in the right order
		for regionRef in regionToRemoveList:
			self.removeRegion(regionRef)
		for viewportRef in viewportToRemoveList:
			self.removeViewport(viewportRef)
		for viewportRef in viewportToAppendList:
			self.addViewport(viewportRef)
		for regionRef, parentRef in regionToAppendList:
			self.addRegion(regionRef, parentRef)

	def addRegion(self, regionRef, parentRef):
		pNode = self.getNode(parentRef)
		self._refToRegionNode[regionRef] = regionNode = Region(regionRef.name, regionRef, self)
		pNode.addNode(regionNode)
		viewport = self.__channelTreeRef.getviewport(parentRef)
		self._viewportsRegions[viewport].append(regionRef)

		if self.showAllRegions:
			if regionRef not in self.currentRegionRefListM:
				self.currentRegionRefListM.append(regionRef)
			if regionRef in self.currentRegionRefListT:
				self.currentRegionRefListT.remove(regionRef)

	def addViewport(self, viewportRef):
		viewportNode = Viewport(viewportRef.name, viewportRef, self)
		self._viewports[viewportRef] = viewportNode
		self._viewportsRegions[viewportRef] = []
		# note: the viewport is not showed at this stage, but only when selected

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
		list = self._viewportsRegions[viewportRef]
		list.remove(regionRef)
		
	def removeViewport(self, viewportRef):		
		del self._viewports[viewportRef]
		del self._viewportsRegions[viewportRef]

	def commit(self, type):
		if type in ('REGION_GEOM', 'MEDIA_GEOM'):
			self.updateRegionTree()
		elif type == 'REGION_TREE':
			self.treeMutation()
			self.updateRegionTree()
		else:
			# by default rebuild all
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
		if nodeType == TYPE_REGION:
			appendList = []
			if focusobject not in self.currentRegionRefListT and focusobject not in self.currentRegionRefListM:
				appendList.append(focusobject)
				self.currentRegionRefListT.append(focusobject)

			# append and update region node list
			self.appendRegionNodeList(appendList)
				
		self.select(focusobject)
				
	def focusOnMMNode(self, focusobject):
		# make a append node list according to focusobject and the preferences
		if self.isValidMMNode(focusobject):
			appendList = []
			if focusobject not in self.currentMediaRefListT and focusobject not in self.currentMediaRefListM:
				appendList.append(focusobject)
				self.currentMediaRefListT.append(focusobject)

			# append and update media node list
			self.appendMediaNodeList(appendList)

			# selection
			self.select(focusobject)
		
	def toStopState(self):
		# save current state
		self.currentRegionRefListM = self.stopSelectedRegionList
		self.currentMediaRefListM = self.stopSelectedMediaList

		saveCurrentViewport = self.currentViewport
		self.rebuildAll()
		
		# append the media/region node list
		self.appendRegionNodeList(self.currentRegionRefListM)
		self.appendMediaNodeList(self.currentMediaRefListM)
		
		# re display all viewport
		self.displayViewport(saveCurrentViewport.getNodeRef())
		self.updateFocus()
		
	def toPauseState(self, nodeobject):
		# save current state
		self.stopSelectedRegionList = self.currentRegionRefListM
		self.stopSelectedMediaList = self.currentMediaRefListM

		self.currentMediaRefListM = []
		self.currentRegionRefListM = []
		saveCurrentViewport = self.currentViewport
		self.rebuildAll()
		
		for type, node in nodeobject:
			if type == 'MMChannel':
				self.currentRegionRefListM.append(node)
			elif type == 'MMNode':
				if self.isValidMMNode(node):
					self.currentMediaRefListM.append(node)
		
		# append the media/region node list
		self.appendMediaNodeList(self.currentMediaRefListM)
		self.appendRegionNodeList(self.currentRegionRefListM)
		
		# re display all viewport
		self.displayViewport(saveCurrentViewport.getNodeRef())
		self.updateFocus()

	def updateFocus(self):		
		# check is the focus is still valid
		# XXX this call should be exist. Normaly all view which are responsibled of delete a node
		# should change the global focus as well if it points on the deleted node
		if not self.isValidFocus():
			self.unselect()
			return
		
		if self.currentFocusType == 'MMNode':
			self.focusOnMMNode(self.currentFocus)
		elif self.currentFocusType == 'MMChannel':
			self.focusOnMMChannel(self.currentFocus)
		else:
			self.unselect()

	def unselect(self):
		# XXX for now re-show the viewport
		if self.currentViewport == None:
			# show the first viewport in the list		
			currentViewportList = self.getViewportRefList()
			viewportRef = currentViewportList[0]
		else:
			viewportRef = self.currentViewport.getNodeRef()
		self.displayViewport(viewportRef)

		# update dialog box		
		self.updateUnselectedOnDialogBox()

	def isValidFocus(self):
		if self.currentFocusType == 'MMNode':
			return self.existMediaRef(self.currentFocus)
		elif self.currentFocusType == 'MMChannel':
			name = self.currentFocus.name
			return self.context.getchannel(name) is not None
		else:
			# no focus, or unknown focus, doesn't change anything
			return 1
		
	def globalfocuschanged(self, focustype, focusobject):
		self.currentFocus = focusobject
		self.currentFocusType = focustype
		if self.myfocus is not None and focusobject is self.myfocus:
			self.myfocus = None
			return
		self.myfocus = None

		# remove media node from previous selection		
		self.removeTempMediaNodeList()

		self.updateFocus()
		
	def setglobalfocus(self, focustype, focusobject):
		self.myfocus = focusobject
		self.editmgr.setglobalfocus(focustype, focusobject)
		
	def playerstatechanged(self, type, parameters):
		if type == 'paused':
			self.toPauseState(parameters)
		elif type == 'stopped':
			self.toStopState()
		
	def kill(self):
		self.destroy()
	
	def updateRegionTree(self):
		# We assume here that no region has been added or supressed
		viewportRefList = self.getViewportRefList()
		for viewportRef in viewportRefList:
			viewportNode = self.getViewportNode(viewportRef)
			viewportNode.updateAllAttrdict()
			
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
						
	# general method to select a node
	def select(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)

		if nodeType != None:
			self.currentNodeRefSelected = nodeRef
			
			# display the right viewport
			viewportRef = self.getViewportRef(nodeRef)
			if self.currentViewport == None or viewportRef != self.currentViewport.getNodeRef():
				self.displayViewport(viewportRef)

			# select the node in layout area
			node = self.getNode(nodeRef)
			node.toShowedState()
			node.select()

			self.fillViewportListOnDialogBox()
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
		return self._viewportsRegions.keys()

	def getRegionRefList(self, viewportRef):
		return self._viewportsRegions[viewportRef]

	def getMediaRefList(self, regionRef):
		list = []
		# checking if has a associated media
		for node in self.__mediaRefList:
			channel = node.GetChannel()
			if channel != None:
				layoutChannel = channel.GetLayoutChannel()
				if layoutChannel is regionRef:
					list.append(node)

		return list			
		
	def getRegionNode(self, regionRef):
		return self._refToRegionNode.get(regionRef)

	def getMediaNode(self, mediaRef):
		for mediaRegion, parentRegion in self.currentMediaNodeListShowed:
			nodeRef = mediaRegion.getNodeRef()
			if nodeRef is mediaRef:
				return mediaRegion
		return None

	def nameToNodeRef(self, name):
		return self.context.getchannel(name)

	# these two method allow to optimize the media ref search
	# to looking for a media node reference in the document
	# currently, we have to course the tree structure to know if the media is still there
	# if you check if the UID still exist, it doesn't work because, if the media is removed from
	# the document but may still exist in mapuid. In addition, we have to know here only the media nodes
	# linked to a valid region
	def __makeNodeRefList(self, node):
		if self.isValidMMNode(node):
			channel = node.GetChannel()
			if channel != None:
				region = channel.GetLayoutChannel()
				if region != None:
					# XXX should check as well that the region exist
					self.__mediaRefList.append(node)
		for child in node.GetChildren():
			self.__makeNodeRefList(child)

	def __makeMediaRefList(self):
		self.__mediaRefList = []
		self.__makeNodeRefList(self.root)

	def existMediaRef(self, nodeRef):
		return nodeRef in self.__mediaRefList
			
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

	def getNodeType(self, nodeRef):
		# XXX to do: find the node type directly from the document
		if nodeRef != None:
			node = self.getNode(nodeRef)
			if node == None:
				return None
			return node.getNodeType()
		return None

	def getViewportRef(self, nodeRef, nodeType = None):
		if nodeType == None:
			nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			region = self.getParentNodeRef(nodeRef, TYPE_MEDIA)
		else:
			region = nodeRef

		return self.__channelTreeRef.getviewport(region)
	
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

	# get the children spatial node
	def getSubNodeRefList(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			# XXX not implemented
			return []
		else:
			sublist = self.__channelTreeRef.getsubchannels(nodeRef)
			retList = []
			for chan in sublist:
				# keep only the regions
				if chan.get('type') == 'layout':
					retList.append(chan)
			return retList
					
	def displayViewport(self, viewportRef):
		if self.currentViewport != None:
			self.currentViewport.hide()
		self.currentViewport = self.getViewportNode(viewportRef)
		self.currentViewport.showAllNodes()

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
		node = self.getNode(nodeRef)
		if node != None:
			nodeType = node.getNodeType()
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
		regionRefList = self.getSubNodeRefList(parentRef)

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
		regionRefList = self.getSubNodeRefList(parentRef)

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
		# clear and disable not valid fields
#		self.dialogCtrl.setSelecterCtrl('ViewportSel',-1)
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('RegionZ',0)
		
		self.dialogCtrl.enable('RegionSel',0)
		self.dialogCtrl.enable('MediaSel',0)
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

		commandList = []	
		self.setcommands(commandList, '')
		
	def updateViewportOnDialogBox(self, nodeRef):
		# update region list
		self.currentRegionRefListSel = self.getRegionRefList(nodeRef)
			
		# get the current geom value
		geom = nodeRef.getPxGeom()

		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = nodeRef.GetAttrDef('showEditBackground', 0)
		if showEditBackground == 1:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)
		
		# clear and disable not valid fields
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		self.updateViewportGeomOnDialogBox(geom)
		
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

		commandList = self.mkcommandlist()	
		self.setcommands(commandList, '')

	def mkcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			commandList = [
				ATTRIBUTES(callback = (self.__editProperties, ())),
				]
		else:
			commandList = [
				ATTRIBUTES(callback = (self.__selectBgColor, ())),
				]

		return commandList			
		
	def updateViewportGeomOnDialogBox(self, geom):
		# update the fields dialog box
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[1])
		
	def updateRegionOnDialogBox(self, nodeRef):
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)

		# enable valid fields
		self.dialogCtrl.enable('SendBack',1)
		self.dialogCtrl.enable('BringFront',1)
		
		self.dialogCtrl.enable('RegionZ',1)

		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)

		geom = nodeRef.getPxGeom()

		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = nodeRef.GetAttrDef('showEditBackground', 0)
		if showEditBackground == 1:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		z = nodeRef.GetAttrDef('z', 0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)		
								  
		self.updateRegionGeomOnDialogBox(geom)

		# update the region selecter
		if len(self.currentRegionRefListSel) > 0:
			index = self.currentRegionRefListSel.index(nodeRef)
			self.dialogCtrl.setSelecterCtrl('RegionSel',index)
				
		# update the viewport selecter
		if len(self.currentViewportList) > 0:
			regionNode = self.getRegionNode(nodeRef)
			index = self.currentViewportList.index(regionNode.getViewport().getNodeRef())
			self.dialogCtrl.setSelecterCtrl('ViewportSel',index)

		self.dialogCtrl.setCheckCtrl('ViewportCheck',0)
		self.dialogCtrl.setCheckCtrl('RegionCheck',1)
		self.dialogCtrl.setCheckCtrl('MediaCheck',0)
		self.dialogCtrl.enable('HideRegion',1)
		self.dialogCtrl.enable('HideMedia',0)

		# allow to remove or add new regions
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',1)
			self.dialogCtrl.enable('DelRegion',1)

		commandList = self.mkcommandlist()	
		self.setcommands(commandList, '')

	def updateRegionGeomOnDialogBox(self, geom):
		self.dialogCtrl.setFieldCtrl('RegionX',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionY',"%d"%geom[1])		
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])

	def fillMediaListOnDialogBox(self, regionRef = None):
		if regionRef == None:
			self.currentMediaRefListSel = []
			list = []
		else:
			currentMediaList = self.getMediaRefList(regionRef)
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
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)		
		self.dialogCtrl.enable('MediaSel',0)
		self.dialogCtrl.enable('MediaCheck', 0)

	def enableMediaListOnDialogBox(self):
		self.dialogCtrl.enable('MediaSel',1)
		self.dialogCtrl.enable('MediaCheck', 1)

	def fillViewportListOnDialogBox(self):
		self.currentViewportList = self.getViewportRefList()
		list = []
		for viewportRef in self.currentViewportList:
			list.append(viewportRef.name)
		self.dialogCtrl.fillSelecterCtrl('ViewportSel', list)
		
	def fillRegionListOnDialogBox(self, viewportRef):
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
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)		
		self.dialogCtrl.enable('RegionSel',0)
		self.dialogCtrl.enable('RegionCheck', 0)

	def enableRegionListOnDialogBox(self):
		self.dialogCtrl.enable('RegionSel',1)
		self.dialogCtrl.enable('RegionCheck', 1)
		
	def updateMediaOnDialogBox(self, nodeRef):
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
		
		# get the current geom value: todo
		geom = nodeRef.getPxGeom()
		
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)

		# clear and disable not valid fields
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('ShowRbg',0)
		self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		self.dialogCtrl.enable('RegionZ',0)

#		self.dialogCtrl.enable('BgColor', 0)
							   
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		self.updateMediaGeomOnDialogBox(geom)

		self.dialogCtrl.setCheckCtrl('ViewportCheck',0)
		self.dialogCtrl.setCheckCtrl('RegionCheck',0)
		self.dialogCtrl.setCheckCtrl('MediaCheck',1)
		self.dialogCtrl.enable('HideRegion',0)
		self.dialogCtrl.enable('HideMedia',1)

		# we can't add or remove regions from media object
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',0)
			self.dialogCtrl.enable('DelRegion',0)

		commandList = self.mkcommandlist()	
		self.setcommands(commandList, '')
				
	def updateMediaGeomOnDialogBox(self, geom):
		self.updateRegionGeomOnDialogBox(geom)
		
	#
	# internal methods
	#

	def __updateZOrder(self, value):
		if self.currentNodeRefSelected != None:
			self.applyZOrderOnRegion(self.currentNodeRefSelected, value)

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

	def __selectViewport(self, selectedName=None):
		nodeRef = None
		if selectedName == None:
			if self.lastViewportRefSelected != None:
				nodeRef = self.lastViewportRefSelected
			else:
				viewportRefList = self.getViewportRefList()
				nodeRef = viewportRefList[0]
		else:
			# search the viewport ref associated to the selected name
			viewportRefList = self.getViewportRefList()
			for ref in viewportRefList:
				if ref.name == selectedName:
					nodeRef = ref
					break
				
		self.displayViewport(nodeRef)
		self.setglobalfocus('MMChannel',nodeRef)
		self.updateFocus()
			
	def __selectRegion(self, selectedName=None):
		nodeRef = None
		if selectedName == None:
			if self.lastRegionRefSelected != None:
				nodeRef = self.lastRegionRefSelected
			elif len(self.currentRegionRefListSel) > 0:
				nodeRef = self.currentRegionRefListSel[0]
		else:
			# search the region ref associated to the selected name
			for ref in self.currentRegionRefListSel:
				if ref.name == selectedName:
					nodeRef = ref
					break
			
		if nodeRef != None:
			if nodeRef not in self.currentRegionRefListM and nodeRef not in self.currentRegionRefListT:
				# add the region
				self.appendRegionNodeList([nodeRef])
				self.currentRegionRefListM.append(nodeRef)
			elif nodeRef not in self.currentRegionRefListM:
				# transfert to the main list
				self.currentRegionRefListM.append(nodeRef)
				self.currentRegionRefListT.remove(nodeRef)

			self.setglobalfocus('MMChannel',nodeRef)
			self.updateFocus()
			
	def __selectMedia(self, selectedName=None):
		nodeRef = None
		if selectedName == None:
			if self.lastMediaRefSelected != None:
				nodeRef = self.lastMediaRefSelected
			elif len(self.currentMediaRefListSel) > 0:
				nodeRef = self.currentMediaRefListSel[0]
		else:
			# get the node ref associated to the selected item
			for ref in self.currentMediaRefListSel:
				if ref.attrdict.get('name') == selectedName:
					nodeRef = ref
					break
			
		if not self.isValidMMNode(nodeRef):
			return
		
		if nodeRef != None:
			if nodeRef not in self.currentMediaRefListM and nodeRef not in self.currentMediaRefListT:
				# add the media
				self.appendMediaNodeList([nodeRef])
				self.currentMediaRefListM.append(nodeRef)
			elif nodeRef not in self.currentMediaRefListM:
				# transfert to the main list
				self.currentMediaRefListM.append(nodeRef)
				self.currentMediaRefListT.remove(nodeRef)

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
		if not self.isEmpty(regionRef):
			msg = "you have to delete before the sub regions and associated medias"
			windowinterface.showmessage(msg, mtype = 'error')
			return
		
		parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
		self.setglobalfocus('MMChannel',parentRef)
		self.applyDelRegion(regionRef)

	# checking if the region/viewport node contains any sub-region or media
	def isEmpty(self, nodeRef):
		# checking if has sub-region
		if self.__channelTreeRef.getsubregions(nodeRef.name):
			return 0

		# checking if has a associated media
		for n in self.__mediaRefList:
			channel = n.GetChannel()
			if channel != None:
				layoutChannel = channel.GetLayoutChannel()
				if layoutChannel is nodeRef:
					return 0

		return 1			

	def delViewport(self, nodeRef):
		# for now, we have to keep at least one viewport
		currentViewportList = self.getViewportRefList()
		if len(currentViewportList) <= 1:
			msg = "you can't delete the last viewport"
			windowinterface.showmessage(msg, mtype = 'error')
			return

		# for now, we can only erase an empty viewport
		if not self.isEmpty(nodeRef):
			msg = "you have to delete before the sub regions and associated medias"
			windowinterface.showmessage(msg, mtype = 'error')
			return
		
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
		saveCurrentViewport = self.currentViewport
		# focus on viewport
		self.rebuildAll()
		
		# redisplay viewport
		viewportRef = saveCurrentViewport.getNodeRef()
		self.displayViewport(viewportRef)
		self.updateFocus()

	def __hideAllRegions(self):
		self.showAllRegions = 0
		self.currentRegionRefListM = []
		self.currentRegionRefListT = []
		saveCurrentViewport = self.currentViewport
		# focus on viewport
		self.rebuildAll()
		
		# redisplay viewport
		viewportRef = saveCurrentViewport.getNodeRef()
		self.displayViewport(viewportRef)
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
		
	def onPreviousSelectRegion(self, regionNode):
		nodeRef = regionNode.getNodeRef()
		self.currentNodeRefSelected  = nodeRef
		self.fillRegionListOnDialogBox(self.getViewportRef(nodeRef))
		self.fillMediaListOnDialogBox(nodeRef)
		self.updateRegionOnDialogBox(nodeRef)
		self.setglobalfocus('MMChannel',nodeRef)
		self.lastRegionRefSelected = nodeRef
		self.lastMediaRefSelected = None
				
	def onPreviousSelectMedia(self, mediaNode):
		nodeRef = mediaNode.getNodeRef()
		self.currentNodeRefSelected  = nodeRef
		self.fillRegionListOnDialogBox(self.getViewportRef(nodeRef))
		self.fillMediaListOnDialogBox(self.getParentNodeRef(nodeRef, TYPE_MEDIA))
		self.updateMediaOnDialogBox(nodeRef)
		self.setglobalfocus('MMNode',nodeRef)
		self.lastMediaRefSelected = nodeRef

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
			if self.currentViewport != None:
				self.currentViewport.updateAllShowNames(self.showName)
			self.updateFocus()
		elif ctrlName == 'AsOutLine':
			self.asOutLine = value
			if self.currentViewport != None:
				self.currentViewport.updateAllAsOutLines(self.asOutLine)
			self.updateRegionTree()
			self.updateFocus()
		elif ctrlName == 'ShowRbg':
			self.__showEditBackground(value)			
		elif ctrlName == 'ViewportCheck':
			self.__selectViewport()
		elif ctrlName == 'RegionCheck':
			self.__selectRegion()
		elif ctrlName == 'MediaCheck':
			self.__selectMedia()
		elif ctrlName == 'ShowAllRegions':
			if value:
				self.__showAllRegions()
			else:
				self.__hideAllRegions()
				
	def onFieldCtrl(self, ctrlName, value):
		if ctrlName in ('RegionX','RegionY','RegionW','RegionH'):
			value = int(value)
			self.__updateGeom(ctrlName, value)
		elif ctrlName == 'RegionZ':
			value = int(value)
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
		elif ctrlName == 'HideRegion':
			self.__hideRegion()
		elif ctrlName == 'HideMedia':
			self.__hideMedia()

