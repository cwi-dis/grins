# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from windowinterface import UNIT_PXL

from usercmd import *

import MMAttrdefs
import settings
import features

ALL_LAYOUTS = '(All Channels)'
	
###########################
# helper class to build tree from list

TYPE_ABSTRACT, TYPE_REGION, TYPE_MEDIA, TYPE_VIEWPORT = range(4)

class Node:
	def __init__(self, name, dict, ctx):
		self._isExclude = 0
		self._name = name
		self._defattrdict = dict
		self._parent = None
		self._children = []
		self._ctx = ctx
		self._viewport = None
		
		# graphic control (implementation: system dependant)
		self._graphicCtrl = None		

		# default attribute		
		self.importAttrdict()
		self._nodeType = TYPE_ABSTRACT

	def addNode(self, node):
		self._children.append(node)
		node._parent = self
		node._viewport = self._viewport

	# not completed yet. But for subregion positioning it's enough for now
	def removeNode(self, node):
		ind = 0
		for child in self._children:
			if child is node:
				# remove child as well			
				if node.isShowed():
					node.hide()
				del self._children[ind]
				break
			ind = ind+1

	def _do_init(self, parent):
		self._parent = parent
		parent._children.append(self)
		self._viewport = parent._viewport
			
	def isShowed(self):
		return self._graphicCtrl != None

	def getNodeType(self):
		return self._nodeType
	
	def getViewport(self):
		return self._viewport
	
	def importAttrdict(self):
		self._curattrdict = {}
		
		isExclude = self._defattrdict.get('isExclude')
		# todo: optimize
		if isExclude == None:
			parent = self.getParent()
			while parent != None:
				isExclude = parent._defattrdict.get('isExclude')
				if isExclude:
					break
				parent = parent.getParent()
		
			if parent == None:
				isExclude = 0
				
		self._isExclude = isExclude
			
	def getDocDict(self):
		return self._defattrdict

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
			self._graphicCtrl.select()

	def hide(self):
		if self._graphicCtrl != None:
			if self._parent != None:
				if self._parent._graphicCtrl != None:
					self._parent._graphicCtrl.removeRegion(self._graphicCtrl)
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
		showEditBackground = self._defattrdict.get('showEditBackground')
		if showEditBackground != None and showEditBackground == 1:
			return 1
		return 0		

	def isExclude(self):
		return 0
		
	def canShow(self):
		return not self._isExclude
	
class Region(Node):
	def __init__(self, name, dict, ctx):
		Node.__init__(self, name, dict, ctx)
		self._nodeType = TYPE_REGION
		
	def importAttrdict(self):
		Node.importAttrdict(self)

		if self._ctx.asOutLine:
			self._curattrdict['transparent'] = 1
		else:			
			editBackground = None
			if self.isShowEditBackground():
				editBackground = self._defattrdict.get('editBackground')
			
			if editBackground != None:				
					self._curattrdict['bgcolor'] = editBackground
					self._curattrdict['transparent'] = 0
			else:
				self._curattrdict['bgcolor'] = self._defattrdict.get('bgcolor')
				self._curattrdict['transparent'] = self._defattrdict.get('transparent')
		
		self._curattrdict['wingeom'] = self._defattrdict.get('base_winoff')
		self._curattrdict['z'] = self._defattrdict.get('z')
	
	def show(self):
		if self.canShow and self._parent._graphicCtrl != None:
			self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self._name)
			self._graphicCtrl.showName(self.getShowName())		
			self._graphicCtrl.addListener(self)

	def showAllNodes(self):
		if self.canShow():
			self.show()
			for child in self._children:
				child.showAllNodes()

	#
	# update of visualization attributes (not document)
	#

	def updateShowName(self,value):
		if self.canShow():
			self._graphicCtrl.showName(value)
		
	def updateAllShowNames(self, value):
		if self.canShow():
			self.updateShowName(value)
			for child in self._children:
				child.updateAllShowNames(value)

	def updateAllAsOutLines(self, value):
		if value:
			self._curattrdict['transparent'] = 1
		else:
			self._curattrdict['transparent'] = 0

		if self.canShow():
			self._graphicCtrl.setAttrdict(self._curattrdict)

		for child in self._children:
			child.updateAllAsOutLines(value)

	#
	# end update mothods
	#

	def onSelected(self):
		self._ctx.onPreviousSelectRegion(self)

	def onUnselected(self):
		pass
		
	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx.updateRegionGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.applyGeomOnRegion(self, geom)

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx.editProperties(self)
		else:
			self._ctx.selectBgColor(self)

	def isExclude(self):
		isExclude = self._defattrdict.get('isExclude')
		
		return isExclude

	def canShow(self):
		return Node.canShow(self) and self._ctx.isSelectedRegion(self.getName())
		
class MediaRegion(Region):
	def __init__(self, name, node, ctx):
		self.mmnode = node
		dict = node.attrdict
		Region.__init__(self, name, dict, ctx)
		self._nodeType = TYPE_MEDIA

	def importAttrdict(self):
		Node.importAttrdict(self)
		self._curattrdict['bgcolor'] = self._defattrdict.get('bgcolor')
		self._curattrdict['transparent'] = 1		
		
		# get wingeom according to the subregion positionning
		# note this step is not done during the parsing in order to maintains all constraint information
		# at some point we'll have to do the same thing for regions
		channel = self.mmnode.GetChannel()
		wingeom = self._ctx._getwingeom(channel, self.mmnode)

		self.ctype = self.mmnode.GetChannelType()

		# determinate the real fit attribute		
		scale = MMAttrdefs.getattr(self.mmnode,'scale')
		if scale == 1:
			fit = 'hidden'
		elif scale == 0:
			fit = 'meet'
		elif scale == -1:
			fit = 'slice'
		else:
			fit = 'fill'
		self.fit = fit

		if not settings.activeFullSmilCss:		
			# ajust the internal geom for edition. If no constraint neither on right nor botton,
			# with fit==hidden: chg the internal region size.
			# it avoid a unexepected effet during the edition when you resize. don't change the semantic
			right =	self.mmnode.GetAttrDef('right', None) 
			bottom = self.mmnode.GetAttrDef('bottom', None) 
			self.media_width, self.media_height = self.mmnode.GetDefaultMediaSize(wingeom[2], wingeom[3])
			if fit == 'hidden':
				if right == None:
					x,y,w,h = wingeom
					wingeom = x,y,self.media_width,h
				if bottom == None:
					x,y,w,h = wingeom
					wingeom = x,y,w,self.media_height
		else:
			# ajust the internal geom for edition. If no constraint neither on right nor botton,
			# with fit==hidden: chg the internal region size.
			# it avoid a unexepected effet during the edition when you resize. don't change the semantic
			right =	self.mmnode.GetRawAttrDef('right', None) 
			bottom = self.mmnode.GetRawAttrDef('bottom', None) 
			width =	self.mmnode.GetRawAttrDef('width', None) 
			height = self.mmnode.GetRawAttrDef('height', None)
			regPoint = self.mmnode.GetAttr('regPoint', None)
			regAlign = self.mmnode.GetAttr('regAlign', None)
			self.media_width, self.media_height = self.mmnode.GetDefaultMediaSize(wingeom[2], wingeom[3])
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
		self._ctx.onPreviousSelectMedia(self)

	def show(self):
		if not self.canShow():
			return

		if self._parent._graphicCtrl == None:
			return
						
		self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self._name)
		self._graphicCtrl.showName(0)		
		self._graphicCtrl.addListener(self)
		
		# copy from old hierarchical view to determinate the image to showed
		node = self.mmnode
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
		
	def onUnselected(self):
		pass
		
	def onGeomChanging(self, geom):
		self._ctx.updateMediaGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.applyGeomOnMedia(self, geom)

	def onProperties(self):
		# nothing for now
		pass

	def canShow(self):
		return Node.canShow(self) and self.getParent().canShow()
	
class Viewport(Node):
	def __init__(self, name, dict, ctx):
		self.currentX = 8
		self.currentY = 8
		
		Node.__init__(self, name, dict, ctx)
		self._nodeType = TYPE_VIEWPORT
		self._viewport = self

	def importAttrdict(self):
		Node.importAttrdict(self)

		editBackground = None
		if self.isShowEditBackground():
			editBackground = self._defattrdict.get('editBackground')
			
		if editBackground != None:				
				self._curattrdict['bgcolor'] = editBackground
				self._curattrdict['transparent'] = 0
		else:
			self._curattrdict['bgcolor'] = self._defattrdict.get('bgcolor')
			self._curattrdict['transparent'] = self._defattrdict.get('transparent')
		
		w,h=self._defattrdict.get('winsize')
		self._curattrdict['wingeom'] = (self.currentX,self.currentY,w,h)

	def getRegion(self, name):
		return self._regionList.get(name)
		
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
		self._ctx.onPreviousSelectViewport(self)

	def onUnselected(self):
		pass
		
	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx.updateViewportGeomOnDialogBox(geom[2:])

	def onGeomChanged(self, geom):
		# apply the new value
		self.currentX = geom[0]
		self.currentY = geom[1]
		self._ctx.applyGeomOnViewport(self, geom[2:])

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx.editProperties(self)
		else:
			self._ctx.selectBgColor(self)

###########################

class LayoutView2(LayoutViewDialog2):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		LayoutViewDialog2.__init__(self)

		# current state
		self.currentViewport = None
		
		self.currentNodeSelected = None
		self.currentExcludeRegionNameList = None
		
		self.currentExcludeRegionList = []

		self.lastViewportNameSelected = None
		self.currentRegionNameList = []
		self.currentRegionNameListSel = []
		self.lastRegionNameSelected = None
		self.currentMediaRegionList = []
		self.currentMediaRegionListSel = []
		self.lastMediaNameSelected = None
		self.currentFocus = None

		self.currentSelectedRegionList = None		

		self.currentNodeListShowed = []

		self.myfocus = None

		# incremental datas
		self._viewportsRegions = {}
		self._viewports = {}
		self._nameToRegionNode = {}
				
		# init state of different dialog controls
		self.showName = 1
		self.asOutLine = 0
		self.showBgcolor = 1

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
		self.treeMutation()
#		self.buildRegionTree(self.context)
		self.initDialogBox()		
		self.displayViewport(self._first)
		self.select(self.currentViewport)
		self.editmgr.registerfirst(self, 1, 1)

		# get the initial player state		
		type,node = self.editmgr.getplayerstate()
		if node != None:
			self.playerstatechanged(type, node)
			
		# get the initial focus		
		type,focus = self.editmgr.getglobalfocus()
		if focus != None:
			self.globalfocuschanged(type, focus)
		
	def hide(self):
		if not self.is_showing():
			return
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
		subregList = self.__channelTreeRef.getsubregions(parentId)
		for subreg in subregList:
			if subreg.get('subtype') != 'sound':
				orderedRegionList.append(subreg)
			self.__buildOrderedRegionList(orderedRegionList, subreg.name)
		
	# update the region tree
	def treeMutation(self):
		# make an ordered list of ref layout channel
		import MMNode
		channelTreeRef = self.__channelTreeRef = MMNode.MMChannelTree(self)
		viewportList = channelTreeRef.getviewports()
		viewportNameListRef = []
		for viewport in viewportList:
			viewportNameListRef.append(viewport.name)
		orderedRegionList = self.__orderedRegionList = []
		for viewportRef in viewportList:
			self.__buildOrderedRegionList(orderedRegionList, viewportRef.name)
		orderedRegionNameListRef = []
		for regionRef in orderedRegionList:
			orderedRegionNameListRef.append(regionRef.name)
				
		# make a list of new regions and viewports to append
		regionToAppendList = []
		viewportToAppendList = []

		for viewport in viewportList:
			viewportNode = self.getViewport(viewport.name)
			if viewportNode == None:
				viewportToAppendList.append(viewport)
				# temporarly
				self._first = viewport.name
				
		for region in orderedRegionList:
			regionNode = self.getRegion(region.name)
			parent = channelTreeRef.getparent(region.name)
			if regionNode == None:
				regionToAppendList.append((region, parent))

		# make a list of regions and viewports to remove
		regionToRemoveList = []
		viewportToRemoveList = []
		viewportNameList = self.getViewportNameList()
		for viewportId in viewportNameList:
			if viewportId not in viewportNameListRef:
				viewportToRemoveList.append(viewportId)
			regionNameList = self.getRegionNameList(viewportId)
			for regionId in regionNameList:
				if regionId not in orderedRegionNameListRef:
					regionToRemoveList.append(regionId)
		
		# call effective add/remove operations in the right order
		for regionId in regionToRemoveList:
			self.removeRegion(regionId)
		for viewportId in viewportToRemoveList:
			self.removeViewport(viewportId)
		for viewportRef in viewportToAppendList:
			self.addViewport(viewportRef)
		for regionRef, parentRef in regionToAppendList:
			self.addRegion(regionRef, parentRef)

		# update dialog box if needed
		if len(viewportToAppendList) > 0 or len(viewportToRemoveList) > 0:
			self.fillViewportListOnDialogBox()
		# the other properties will be refreshed with a selection
			
	def addRegion(self, regionRef, parentRef):
		# update data structure
		pNode = self.getNode(parentRef.name)
		self._nameToRegionNode[regionRef.name] = regionNode = Region(regionRef.name, regionRef, self)
		regionNode._do_init(pNode)
		viewport = self.__channelTreeRef.getviewport(parentRef)
		self._viewportsRegions[viewport.name].append(regionRef.name)

		# show node
		# note: the effective show will be done if the viewport is selected
		regionNode.show()
		
	def addViewport(self, viewportRef):
		# update data structure
		viewportNode = Viewport(viewportRef.name, viewportRef, self)
		self._viewports[viewportRef.name] = viewportNode
		self._viewportsRegions[viewportRef.name] = []
		# note: the viewport is not showed at this stage, but only when selected

	def removeRegion(self, regionId):
		# update UI
		regionNode = self.getRegion(regionId)
		regionNode.hide()
		parentNode = regionNode.getParent()
		parentNode.removeNode(regionNode)

		# update data struture
		viewportNode = regionNode.getViewport()
		del self._nameToRegionNode[regionId]
		list = self._viewportsRegions[viewportNode.getName()]
		ind = list.index(regionId)
		del list[ind]
		
	def removeViewport(self, viewportId):		
		del self._viewports[viewportId]
		del self._viewportsRegions[viewportId]
					 
	def commit(self, type):
		if type == 'REGION_TREE':
			self.treeMutation()
		else:
			# we have to update the tree
			# note: in this case, the tree structure hasn't changed
			self.updateRegionTree()

	def isValidMMNode(self, node):
		if node == None:
			return 0
		from MMTypes import leaftypes
		if not node.type in leaftypes:
			return 0
		if node.GetChannelType() == 'sound':
			return 0

		return 1

	def focusOnMMNode(self, focusobject):
		# remove media node from previous selection		
		self.removeAllFocusMediaNodeList()

		# make a append node list according to focusobject and the preferences
		appendList = []
		if self.isValidMMNode(focusobject):
			if not focusobject.attrdict.get('name') in self.currentNodeListShowed:
				appendList.append(focusobject)

		# append and update media node list
		self.appendMediaNodeList(appendList)
		self.updateFocus(focusobject)
		
	def updateFocus(self, object):
		# for now, select only one media (multiselection not supported yet)	
		if self.isValidMMNode(object):
			name = object.attrdict.get("name")
			for mediaRegion, parentRegion in self.currentMediaRegionList:
				if mediaRegion.getName() == name:
					if mediaRegion.getViewport() != self.currentViewport:
						self.displayViewport(mediaRegion.getViewport().getName())	
					self.select(mediaRegion)
					break
		else:
			if self.currentViewport != None:
				self.select(self.currentViewport)

	def showAllRegions(self):
		# remove all selected nodes
		self.removeAllMediaNodeList()

		self.currentNodeListShowed = []
		self.currentSelectedRegionList = None
		
		# re display all viewport
		self.displayViewport(self.currentViewport.getName())		

		# set the focus
		if self.currentFocus != None:
			self.focusOnMMNode(self.currentFocus)
		
	def showNodeList(self, nodeobject):
		# remove all selected nodes
		self.removeAllMediaNodeList()

		appendList = []
		selectedRegionList = []
		self.currentNodeListShowed = []
		for type, node in nodeobject:
			if type == 'MMChannel':
				selectedRegionList.append(node.name)
			elif type == 'MMNode':
				self.currentNodeListShowed.append(node.attrdict.get("name"))
				appendList.append(node)
		
		if len(selectedRegionList) > 0:
			self.currentSelectedRegionList = selectedRegionList
		else:
			self.currentSelectedRegionList = None

		# append the media node list
		self.appendMediaNodeList(appendList)
		
		# re display all viewport
		self.displayViewport(self.currentViewport.getName())

		# change the focus to the viewport
		self.myfocus = self.currentViewport
		self.editmgr.setglobalfocus('MMChannel',self.currentViewport)
		self.select(self.currentViewport)

	def isSelectedRegion(self, regionName):
		# by default all region selected
		if self.currentSelectedRegionList == None:
			return 1
		return regionName in self.currentSelectedRegionList
		
	def globalfocuschanged(self, focustype, focusobject):
		# skip the focus if already exist
		if self.currentFocus == focusobject:
			return
		if self.myfocus != None and focusobject == self.myfocus:
			self.myfocus = None
			return
		self.myfocus = None
		self.currentFocus = focusobject
		
		if focustype == 'MMNode':
			self.focusOnMMNode(focusobject)
#		elif focustype == 'MMChannel':
#			self.focusOnMMChannel(focusobject)

	def playerstatechanged(self, type, parameters):
		if type == 'paused':
			self.showNodeList(parameters)
		elif type == 'stopped':
			self.showAllRegions()
		
	def kill(self):
		self.destroy()

	#		
	# build one region tree by viewport
	# 
	def buildRegionTree(self, mmctx):
		self._channeldict = mmctx.channeldict
		self._viewportsRegions = {}
		self._viewports = {}
		id2parentid = {}
		for chan in mmctx.channels:
			if chan.get('type')=='layout':
				if chan.get('subtype') != 'sound':
					if chan.has_key('base_window'):
						# region
						id2parentid[chan.name] = chan['base_window']
					else:
						# no parent --> it's a viewport
						self._viewportsRegions[chan.name] = []
						self._viewports[chan.name] = Viewport(chan.name,chan, self)
						# temporarly
						self._first = chan.name

		nodes = self._viewports.copy()
		for id in id2parentid.keys():
			chan = mmctx.channeldict[id]
			nodes[id] = Region(id, chan, self)

		for id, parentid in id2parentid.items():
			idit = id
			while id2parentid.has_key(idit):
				idit = id2parentid[idit]
			viewportid = idit
			self._viewportsRegions[viewportid].append(id)
			nodes[id]._do_init(nodes[parentid])

		self._nameToRegionNode = {}
		for key, viewport in self._viewports.items():
			self.__initRegionList(viewport)
	
	def updateRegionTree(self):
		# We assume here that no region has been added or supressed
		viewportNameList = self.getViewportNameList()
		for viewportName in viewportNameList:
			viewport = self._viewports[viewportName]
			viewport.updateAllAttrdict()
		self.updateExcludeRegionOnDialogBox()
			
		if self.currentNodeSelected != None:
			self.select(self.currentNodeSelected)

#	def removeMediaFromPreviousFocus(self):
#		l = len(self.currentMediaRegionList)
#		if l > 1:
#			mediaRegion, parentRegion = self.currentMediaRegionList[0]
#			parentRegion.removeNode(mediaRegion)
#			del self.currentMediaRegionList[0]
#			if self.lastMediaNameSelected == mediaRegion.getName():
#				self.lastMediaNameSelected = None				
			
	def removeAllMediaNodeList(self):
		if len(self.currentMediaRegionList) > 0:
			for mediaRegion, parentRegion in self.currentMediaRegionList:
				# remove from region tree
				parentRegion.removeNode(mediaRegion)
		self.currentMediaRegionList = []
		self.lastMediaNameSelected = None

	def removeAllFocusMediaNodeList(self):
		removeList = []
		if len(self.currentMediaRegionList) > 0:
			i = 0
			for mediaRegion, parentRegion in self.currentMediaRegionList:
				if not mediaRegion.getName() in self.currentNodeListShowed:
					removeList.append(i)
					# remove from region tree
					parentRegion.removeNode(mediaRegion)
					if self.lastMediaNameSelected == mediaRegion.getName():					
						self.lastMediaNameSelected = None
				i = i+1

		removeList.reverse()				
		for num in removeList:
			del self.currentMediaRegionList[num]
									
	def appendMediaNodeList(self, nodeList):
		# create the media region nodes according to nodeList
		appendMediaRegionList = []
		for node in nodeList:
			channel = node.GetChannel()
			if channel == None: continue
			layoutChannel = channel.GetLayoutChannel()
			if layoutChannel == Node: continue
			layoutChannelName = layoutChannel.name
			regionNode = self.getRegion(layoutChannelName)
			if regionNode == None: continue
			newname = node.attrdict.get("name")

			newRegionNode = MediaRegion(newname, node, self)

			# add the new media region
			appendMediaRegionList.append((newRegionNode, regionNode))

		# add the list of new media regions
		for mediaRegion, parentRegion in appendMediaRegionList:
			self.currentMediaRegionList.append((mediaRegion, parentRegion))
			parentRegion.addNode(mediaRegion)
			mediaRegion.importAttrdict()
			mediaRegion.show()
						
	# extra pass to initialize map the region name list to the node object
	def __initRegionList(self, node, isRoot=1):
		if not isRoot:
			regionName = node._name
			self._nameToRegionNode[regionName] = node
		for child in node._children:
			self.__initRegionList(child,0)

	# general method for select a node
	# the rule is
	#    if the current node can't be displayed, go up into the hierarchy, and display the first found
	def select(self, node):
		sNode = node
		while sNode != None:
			if sNode.canShow():
				break
			sNode = sNode.getParent()

		if sNode != None:
			self.currentNodeSelected = sNode

			# select the node in layout area
			sNode.select()
			
			# update dialog box as well
			nodeType = sNode.getNodeType()
			if nodeType == TYPE_VIEWPORT:
				self.updateViewportOnDialogBox(sNode)
			elif nodeType == TYPE_REGION:
				self.updateRegionOnDialogBox(sNode)
			elif nodeType == TYPE_MEDIA:
				self.updateMediaOnDialogBox(sNode)

	def getViewportNameList(self):
		return self._viewportsRegions.keys()

	def getRegionNameList(self, vpname):
		return self._viewportsRegions[vpname]

	def getRegion(self, regionName):
		return self._nameToRegionNode.get(regionName)

	def getMedia(self, mediaName):
		for mediaRegion, parentRegion in self.currentMediaRegionList:
			mmnode = mediaRegion.mmnode
			if mmnode.attrdict.get('name') == mediaName:
				return mediaRegion
		return None

	def getViewport(self, vpName):
		return self._viewports.get(vpName)
		
	def getNode(self, id):
		node = self.getViewport(id)
		if node != None:
			return node
		
		node = self.getRegion(id)
		if node != None:
			return node

		node = self.getMedia(id)
		if node != None:
			return node

		return None			
		
	def displayViewport(self, name):
		if self.currentViewport != None:
			self.currentViewport.hide()
		self.currentViewport = self._viewports[name]
		self.currentViewport.showAllNodes()
#		self.select(self.currentViewport)

	def selectBgColor(self, node):
		if node.getNodeType() != TYPE_MEDIA:
			dict = node.getDocDict()
			bgcolor = dict.get('bgcolor')
			transparent = dict.get('transparent')
		
			newbg = self.chooseBgColor(bgcolor)
			if newbg != None:
				if node.isShowEditBackground():
					list = []
					list.append(('editBackground',newbg))
					self.applyEditorPreference(node, list)
				else:
					self.applyBgColor(node, newbg, transparent)

	def editProperties(self, node):		
		if node.getNodeType() != TYPE_MEDIA:
			# allow to choise attributes
			import AttrEdit		
			AttrEdit.showchannelattreditor(self.toplevel,
						self.context.channeldict[node.getName()])

	def sendBack(self, region):
		dict = region.getDocDict()
		currentZ = dict.get('z')
		
		# get the list of sibling regions 
		regionList = region.getParent().getSubNodeList()

		# get the lower z-index
		# if the z index of selected region is already min:
		#   - don't change anything if it's the only region
		#	- change its value to a lower value to insure that it'll be all the time in back
		
		min = -1
		cntMin = 0
		for sibRegion in regionList:
			dict = sibRegion.getDocDict()
			z = dict.get('z')
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
			for sibRegion in regionList:
				dict = sibRegion.getDocDict()
				z = dict.get('z')
				if sibRegion == region:
					chList.append((region, min))
				else:
					chList.append((sibRegion, z+1))
				
		else:
			# we have just to fix the current z-index value to min-1
			chList.append((region, min-1))

		self.applyZOrderOnRegionList(chList)
		
	def bringFront(self, region):
		dict = region.getDocDict()
		currentZ = dict.get('z')
		
		# get the list of sibling regions 
		regionList = region.getParent().getSubNodeList()

		# get the max z-index
		# if the z index of selected region is already max:
		#   - don't change anything if it's the only region
		#	- change its value to a higher value to insure that it'll be all the time in front
		
		max = -1
		cntMax = 0
		for sibRegion in regionList:
			dict = sibRegion.getDocDict()
			z = dict.get('z')
			if z>max:
				max = z
				cntMax = 0
			elif z == max:
				cntMax = cntMax+1

		if currentZ == max and cntMax == 1:
			# don't change anything
			return

		self.applyZOrderOnRegion(region, max+1)
		
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
		
	def applyGeomOnViewport(self, viewport, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible at this time
		if self.editmgr.transaction('REGION_GEOM'):
			self.editmgr.setchannelattr(viewport.getName(), 'winsize', geom)
			self.editmgr.setchannelattr(viewport.getName(), 'units', UNIT_PXL)						
			self.editmgr.commit('REGION_GEOM')

	def applyGeomOnRegion(self, region, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible 
		if self.editmgr.transaction('REGION_GEOM'):
			self.editmgr.setchannelattr(region.getName(), 'base_winoff', geom)
			self.editmgr.setchannelattr(region.getName(), 'units', UNIT_PXL)			
			self.editmgr.commit('REGION_GEOM')

	def applyGeomOnMedia(self, media, value):
		attrdict = media.mmnode.attrdict
		if self.editmgr.transaction('MEDIA_GEOM'):
			fit = media.fit
			if fit =='hidden':
				scale = 1
			elif fit == 'meet':
				scale = 0
			elif fit == 'slice':
				scale = -1
			else:
				scale = -3
			
			x,y,w,h = value
			if not settings.activeFullSmilCss:
				self.editmgr.setnodeattr(media.mmnode, 'scale', scale)			
				self.editmgr.setnodeattr(media.mmnode, 'left', x)
				self.editmgr.setnodeattr(media.mmnode, 'top' , y)

				mw = media.media_width
				mh = media.media_height
				# parent region size
				parent = media.getParent()
				px, py, pw, ph = parent.getGeom()
				right = pw-(x+w)
				self.editmgr.setnodeattr(media.mmnode, 'right', right)
				bottom = ph-(y+h)
				self.editmgr.setnodeattr(media.mmnode, 'bottom' , bottom)
			else:
				self.editmgr.setnodeattr(media.mmnode, 'base_winoff', (x,y,w,h))
							
			# todo: some ajustements for take into account all fit values
			self.editmgr.commit('MEDIA_GEOM')
		
	def applyBgColor(self, node, bgcolor, transparent):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(node.getName(), 'bgcolor', bgcolor)
			self.editmgr.setchannelattr(node.getName(), 'transparent', transparent)
			self.editmgr.commit()

	def applyIsExclude(self, region, value):
		# test if possible 
		if self.editmgr.transaction():
			if value:
				self.editmgr.setchannelattr(region.getName(), 'isExclude', 1)
			else:
				self.editmgr.setchannelattr(region.getName(), 'isExclude', None)
			self.editmgr.commit()

	def applyZOrderOnRegion(self, region, value):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(region.getName(), 'z', value)
			self.editmgr.commit()

	def applyZOrderOnRegionList(self, list):
		# list is a list of tuple( region, z-index value)
		# test if possible 
		if self.editmgr.transaction():
			for region, z in list:
				self.editmgr.setchannelattr(region.getName(), 'z', z)
			self.editmgr.commit()

	def applyEditorPreference(self, node, attrList):
		if self.editmgr.transaction():
			if node.getNodeType() in (TYPE_REGION, TYPE_VIEWPORT):
				for name, value in attrList:
					self.editmgr.setchannelattr(node.getName(), name, value)
				self.editmgr.commit()

	def applyNewRegion(self, parentId, name):
		if self.editmgr.transaction():
			self.editmgr.addchannel(name, 0, 'layout')
			self.editmgr.setchannelattr(name, 'base_window', parentId)
			self.editmgr.setchannelattr(name, 'transparent', 1)
			self.editmgr.setchannelattr(name, 'center', 0)
			self.editmgr.setchannelattr(name, 'drawbox', 0)
			self.editmgr.setchannelattr(name, 'z', -1)
			self.editmgr.commit('REGION_TREE')

	def applyNewViewport(self, name):
		if self.editmgr.transaction():
			self.editmgr.addchannel(name, 0, 'layout')
			self.editmgr.setchannelattr(name, 'transparent', 0)
			self.editmgr.setchannelattr(name, 'center', 0)
			self.editmgr.setchannelattr(name, 'drawbox', 0)
			self.editmgr.setchannelattr(name, 'z', -1)
			self.editmgr.setchannelattr(name, 'winsize', (400, 400))
			self.editmgr.setchannelattr(name, 'units', UNIT_PXL)									
			self.editmgr.commit('REGION_TREE')

	def applyDelRegion(self, regionId):
		if self.editmgr.transaction():
			self.editmgr.delchannel(regionId)
			self.editmgr.commit('REGION_TREE')
			
	def applyDelViewport(self, viewportId):
		if self.editmgr.transaction():
			self.editmgr.delchannel(viewportId)
			self.editmgr.commit('REGION_TREE')
		
	def updateExcludeRegionOnDialogBox(self):
		# set exclude region name list
		excludeList = []
		ind = 0
		# disabled for now
		if 0:
			for regionName in self.currentRegionNameList:
				regionNode = self.getRegion(regionName)
				if regionNode != None:
					if regionNode.isExclude():
						if self.lastRegionNameSelected == regionName:
							self.lastRegionNameSelected = None
						self.dialogCtrl.setMultiSelecterCtrl('RegionList', ind, 1)
						excludeList.append(regionName)
					else:
						self.dialogCtrl.setMultiSelecterCtrl('RegionList', ind, 0)
				ind = ind+1
			
		self.currentExcludeRegionNameList = excludeList
		
	def updateViewportOnDialogBox(self, viewport):
		# update region list
		viewportName = viewport.getName()
		self.currentRegionNameList = self.getRegionNameList(viewportName)
		if self.lastViewportNameSelected != viewportName:
			self.lastRegionNameSelected = None
			self.lastViewportNameSelected = viewportName
			
		self.fillRegionListOnDialogBox()
		self.fillMediaListOnDialogBox()

		# disabled for now
		if 0:
			self.dialogCtrl.fillMultiSelCtrl('RegionList', self.currentRegionNameList)
			self.updateExcludeRegionOnDialogBox()
	
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
			
		# get the current geom value
		dict = viewport.getDocDict()
		geom = dict.get('winsize')		

		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = dict.get('showEditBackground')
		if showEditBackground == 1:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		# clear and disable not valid fields
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('RegionZ',0)

#		self.dialogCtrl.enable('BgColor', 1)
		
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		self.updateViewportGeomOnDialogBox(geom)
		
		# update the viewport selecter
		index = self.currentViewportList.index(viewport.getName())
		if index >= 0:
			self.dialogCtrl.setSelecterCtrl('ViewportSel',index)
		self.dialogCtrl.setCheckCtrl('ViewportCheck',1)
		self.dialogCtrl.setCheckCtrl('RegionCheck',0)
		self.dialogCtrl.setCheckCtrl('MediaCheck',0)

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
		
	def updateRegionOnDialogBox(self, region):
		self.fillRegionListOnDialogBox()
		self.fillMediaListOnDialogBox()

		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)

		self.lastRegionNameSelected = region.getName()
								
		# enable valid fields
		self.dialogCtrl.enable('SendBack',1)
		self.dialogCtrl.enable('BringFront',1)
		
		self.dialogCtrl.enable('RegionZ',1)

#		self.dialogCtrl.enable('BgColor', 1)

		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)

		dict = region.getDocDict()
		geom = dict.get('base_winoff')

		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = dict.get('showEditBackground')
		if showEditBackground == 1:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		z = dict.get('z', 0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)		
								  
		self.updateRegionGeomOnDialogBox(geom)

		# update the selecter
		if len(self.currentRegionNameListSel) > 0:
			index = self.currentRegionNameListSel.index(region.getName())
			if index >= 0:
				self.dialogCtrl.setSelecterCtrl('RegionSel',index)
		self.dialogCtrl.setCheckCtrl('ViewportCheck',0)
		self.dialogCtrl.setCheckCtrl('RegionCheck',1)
		self.dialogCtrl.setCheckCtrl('MediaCheck',0)

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

	def fillMediaListOnDialogBox(self):
		list = []
		self.currentMediaNameList = []
		for mediaRegion, parentRegion in self.currentMediaRegionList:
			mmnode = mediaRegion.mmnode
			name = mmnode.attrdict.get('name')
			if mediaRegion.getViewport() == self.currentViewport:
				if mediaRegion.canShow():
					list.append(name)
			self.currentMediaNameList.append(name)
			
		self.currentMediaNameListSel = list
			
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
		self.currentViewportList = self.getViewportNameList()
		self.dialogCtrl.fillSelecterCtrl('ViewportSel', self.currentViewportList)
		
	def fillRegionListOnDialogBox(self):
		list = []
		for regionName in self.currentRegionNameList:
			region = self.getRegion(regionName)
			if region != None:
				name = region.getName()
				if region.canShow():
					list.append(name)
						
		self.currentRegionNameListSel = list
		if len(list) > 0:
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
		
	def updateMediaOnDialogBox(self, media):
		mmnode = media.mmnode
		mediaName = mmnode.attrdict.get('name')
		self.lastMediaNameSelected = mediaName
		
		self.fillRegionListOnDialogBox()
		self.fillMediaListOnDialogBox()
			
		# update the media selecter
		if len(self.currentMediaNameListSel) > 0:
			index = self.currentMediaNameListSel.index(mediaName)
			if index >= 0:
				self.dialogCtrl.setSelecterCtrl('MediaSel',index)

		# update the region selecter
		region = media.getParent()
		regionName = region.getName()
		if self.currentRegionNameListSel != None:
			index = self.currentRegionNameListSel.index(regionName)
			if index >= 0:
				self.dialogCtrl.setSelecterCtrl('RegionSel',index)
		
		# get the current geom value: todo
		geom = media.getGeom()
		
		# clear and disable not valid fields
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('ShowRbg',0)
		self.dialogCtrl.setCheckCtrl('ShowRbg', 1)
		self.dialogCtrl.enable('RegionZ',0)

#		self.dialogCtrl.enable('BgColor', 0)
							   
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		self.updateMediaGeomOnDialogBox(geom)

		# update the selecter
		if self.currentRegionNameList != None:
			index = self.currentRegionNameList.index(region.getName())
			if index >= 0:
				self.dialogCtrl.setSelecterCtrl('RegionSel',index)
		self.dialogCtrl.setCheckCtrl('ViewportCheck',0)
		self.dialogCtrl.setCheckCtrl('RegionCheck',0)
		self.dialogCtrl.setCheckCtrl('MediaCheck',1)

		# we can't add or remove regions from media object
		if features.CUSTOM_REGIONS in features.feature_set:
			self.dialogCtrl.enable('NewRegion',0)
			self.dialogCtrl.enable('DelRegion',0)

		commandList = []	
		self.setcommands(commandList, '')
				
	def updateMediaGeomOnDialogBox(self, geom):
		self.updateRegionGeomOnDialogBox(geom)

	def excludeRegionList(self, regionListIndex):
		# looking for the element which has changed
		regionName = None
		for index in regionListIndex:
			item = self.currentRegionNameList[index]
			try:
				self.currentExcludeRegionNameList.index(item)
			except:
				# select
				value = 1
				regionName = item
				break

		if regionName == None:
			# not found yet
			for item in self.currentExcludeRegionNameList:
				ind = self.currentRegionNameList.index(item)
				try:
					regionListIndex.index(ind)
				except:
					# unselect
					value = 0
					regionName = item
					break

		# if found
		if regionName != None:
			region = self.getRegion(regionName)
			if region != None:
				self.applyIsExclude(region, value)
		
	#
	# internal methods
	#

	def __updateZOrder(self, value):
		self.applyZOrderOnRegion(self.currentNodeSelected, value)

	def __updateGeomOnViewport(self, ctrlName, value):
		dict = self.currentNodeSelected.getDocDict()
		w,h = dict.get('winsize')
		if ctrlName == 'RegionW':
			w = value
		elif ctrlName == 'RegionH':
			h = value
		self.applyGeomOnViewport(self.currentNodeSelected, (w,h))

	def __updateGeomOnRegion(self, ctrlName, value):
		dict = self.currentNodeSelected.getDocDict()
		x,y,w,h = dict.get('base_winoff')
		if ctrlName == 'RegionX':
			x = value
		elif ctrlName == 'RegionY':
			y = value			
		elif ctrlName == 'RegionW':
			w = value
		elif ctrlName == 'RegionH':
			h = value			
		self.applyGeomOnRegion(self.currentNodeSelected, (x,y,w,h))

	def __updateGeomOnMedia(self, ctrlName, value):
		geom = self.currentNodeSelected._curattrdict['wingeom']
		x,y,w,h = geom
		if ctrlName == 'RegionX':
			x = value
		elif ctrlName == 'RegionY':
			y = value			
		elif ctrlName == 'RegionW':
			w = value
		elif ctrlName == 'RegionH':
			h = value			
		self.applyGeomOnMedia(self.currentNodeSelected, (x,y,w,h))
		
	def __updateGeom(self, ctrlName, value):
		if self.currentNodeSelected != None:
			if self.currentNodeSelected.getNodeType() == TYPE_VIEWPORT:
				self.__updateGeomOnViewport(ctrlName, value)
			elif self.currentNodeSelected.getNodeType() == TYPE_REGION:
				self.__updateGeomOnRegion(ctrlName, value)
			elif self.currentNodeSelected.getNodeType() == TYPE_MEDIA:
				self.__updateGeomOnMedia(ctrlName, value)

	def __editProperties(self):
		if self.currentNodeSelected != None:
			self.editProperties(self.currentNodeSelected)
						
	def __selectBgColor(self):
		if self.currentNodeSelected != None:
			self.selectBgColor(self.currentNodeSelected)

	def __sendBack(self):
		if self.currentNodeSelected != None:
			self.sendBack(self.currentNodeSelected)

	def __bringFront(self):
		if self.currentNodeSelected != None:
			self.bringFront(self.currentNodeSelected)

	def __selectViewport(self, name=None):
		if name == None:
			keys = self._viewports.keys()
			viewport = self._viewports[keys[0]]
		else:
			viewport = self._viewports.get(name)
			
		if viewport != None:
			self.displayViewport(viewport.getName())
			self.select(viewport)

	def __selectRegion(self, name=None):
		if name == None:
			if self.lastRegionNameSelected != None:
				name = self.lastRegionNameSelected
			elif len(self.currentRegionNameList) > 0:
				name = self.currentRegionNameList[0]
			
		region = self.getRegion(name)
		if region != None:
			self.select(region)
			self.lastRegionNameSelected = name

	def __selectMedia(self, name=None):
		if name == None:
			if self.lastMediaNameSelected != None:
				name = self.lastMediaNameSelected
			elif len(self.currentMediaNameList) > 0:
				name = self.currentMediaNameList[0]
				
		media = self.getMedia(name)
		if media != None:
			self.select(media)
			self.lastMediaNameSelected = name

	def __showEditBackground(self, value):
		node = self.currentNodeSelected
		if node.getNodeType() in (TYPE_REGION, TYPE_VIEWPORT):
			list = []
			if not value:
				dict = node.getDocDict()
				if not dict.has_key('showEditBackground'):
					list.append(('showEditBackground',1))
				if not dict.has_key('editBackground'):	
					list.append(('editBackground',dict.get('bgcolor')))
			else:
				dict = node.getDocDict()
				if dict.has_key('showEditBackground'):
					list.append(('showEditBackground',None))
			self.applyEditorPreference(node, list)

	def newRegion(self, parentId):
		# choice a default name which doesn't exist		
		channeldict = self.context.channeldict
		baseName = 'region'
		i = 1
		name = baseName + `i`
		while channeldict.has_key(name):
			i = i+1
			name = baseName + `i`
			
		self.__parentId = parentId
		self.askname(name, 'Name for region', self.__regionNamedCallback)

	def __regionNamedCallback(self, name):
		self.applyNewRegion(self.__parentId, name)
		self.select(self.getNode(name))

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
		self.displayViewport(name)
		self.select(self.getNode(name))

	def __newRegion(self):
		if self.currentNodeSelected != None:
			self.newRegion(self.currentNodeSelected.getName())

	def __newViewport(self):
		self.newViewport()

	def delRegion(self, regionNode):
		parentNode = regionNode.getParent()
		self.applyDelRegion(regionNode.getName())
		# select parent node
		self.select(parentNode)

	def delViewport(self, viewportNode):
		self.applyDelViewport(viewportNode.getName())
		# choice another viewport to show (this first in the list)
		viewportName = self.currentViewportList[0]
		self.displayViewport(viewportName)
		self.select(self.getNode(viewportName))
		
	def __delNode(self):
		if self.currentNodeSelected != None:
			nodeSelected = self.currentNodeSelected
			if nodeSelected.getNodeType() == TYPE_VIEWPORT:
				self.delViewport(nodeSelected)
			elif nodeSelected.getNodeType() == TYPE_REGION:
				self.delRegion(nodeSelected)
	
	#
	# interface implementation of 'previous tree node' 
	#
	
	def onPreviousSelectViewport(self, viewport):
		self.currentNodeSelected = viewport	
		self.updateViewportOnDialogBox(viewport)
		
	def onPreviousSelectRegion(self, region):
		self.currentNodeSelected = region												
		self.updateRegionOnDialogBox(region)
		
	def onPreviousSelectMedia(self, media):
		self.currentNodeSelected = media				
		self.updateMediaOnDialogBox(media)
		self.myfocus = media.mmnode
		self.editmgr.setglobalfocus('MMNode',media.mmnode)

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
		if ctrlName == 'RegionList':
			self.excludeRegionList(itemList)
			
	def onCheckCtrl(self, ctrlName, value):
		if ctrlName == 'ShowNames':
			self.showName = value
			if self.currentViewport != None:
				self.currentViewport.updateAllShowNames(self.showName)
		elif ctrlName == 'AsOutLine':
			self.asOutLine = value
			if self.currentViewport != None:
				self.currentViewport.updateAllAsOutLines(self.asOutLine)
			self.updateRegionTree()				
		elif ctrlName == 'ShowRbg':
			self.__showEditBackground(value)			
		elif ctrlName == 'ViewportCheck':
			self.__selectViewport()
		elif ctrlName == 'RegionCheck':
			self.__selectRegion()
		elif ctrlName == 'MediaCheck':
			self.__selectMedia()

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

# ################################################################################################
# for now, copied from channel
# to do: when all mix constraints will be managed fully, we'll can (move / suppress) this code
# ################################################################################################

	def _getParentChannel(self, channel):
		# actualy the layout channel is directly the parent channel
		cname = channel.attrdict.get('base_window')
		if not cname:
			return None
		return self.context.channeldict.get(cname)

	# get the parent window geometry in pixel
	def _getWingeomInPixel(self, layoutchannel):
		parentChannel = self._getParentChannel(layoutchannel)
		
		if parentChannel == None:
			# top window
			size = layoutchannel._attrdict.get('winsize', (50, 50))
			w,h = size
			return 0,0,w,h
		
		units = layoutchannel.attrdict['units']
		import windowinterface
		if units == windowinterface.UNIT_PXL:
			# The size in smil source is specified in pixel, we don't need to 
			# convert it and return directly it
			return layoutchannel.attrdict['base_winoff']
		if layoutchannel._wingeomInPixel != None:
			# The size is expressed in pourcent in smil source document, but
			# the size in pixel is already pre-calculate.
			return layoutchannel._wingeomInPixel

		# The size is expressed in pourcent in smil source document, we don't determinate 
		# yet its size in pixel. For this, we need to know the parent size in pixel
		
		parentChannel = self._getParentChannel(layoutchannel)
		parentGeomInPixel = parentChannel._getWingeomInPixel()
		
		x,y,w,h = layoutchannel._attrdict['base_winoff']
		px,py,pw,ph = parentGeomInPixel
		
		# we save the current size in pixel for the next request
		layoutchannel._wingeomInPixel = x*pw, y*ph, w*pw, h*ph
		
		return layoutchannel._wingeomInPixel

	# get the sub channel geom according to sub-regions
	# return in pixel value
	def _getwingeom(self, channel, node):
		if settings.activeFullSmilCss:
			regGeom = node.getPxGeom()
			return regGeom
		subreg_left = node.GetAttrDef('left', 0)
		subreg_right = node.GetAttrDef('right', 0)
		subreg_top = node.GetAttrDef('top', 0)
		subreg_bottom = node.GetAttrDef('bottom', 0)

		layoutchannel = self._getParentChannel(channel)
		reg_left, reg_top, reg_width, reg_height = self._getWingeomInPixel(layoutchannel)

		# translate in pixel
		if type(subreg_left) == type(0.0):
			subreg_left = int(reg_width*subreg_left)
		if type(subreg_top) == type(0.0):
			subreg_top = int(reg_height*subreg_top)
		if type(subreg_right) == type(0.0):
			subreg_right = int(reg_width*subreg_right)
		if type(subreg_bottom) == type(0.0):
			subreg_bottom = int(reg_height*subreg_bottom)

		# determinate subregion height and width
		subreg_height = reg_height-subreg_top-subreg_bottom
		subreg_width = reg_width-subreg_left-subreg_right
		# print 'sub region height =',subreg_height
		# print 'sub region width = ',subreg_width

		# allow only no null or negative value
		if subreg_height <= 0:
			subreg_height = 1
		if subreg_width <= 0:
			subreg_width = 1

		node.__subreg_height = subreg_height
		node.__subreg_width = subreg_width
		node.__subreg_top = subreg_top
		node.__subreg_left = subreg_left

		# print subreg_left, subreg_top, subreg_width, subreg_height
		return subreg_left, subreg_top, subreg_width, subreg_height
