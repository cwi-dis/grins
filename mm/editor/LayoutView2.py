__version__ = "$Id$"

from LayoutViewDialog2 import LayoutViewDialog2
from windowinterface import UNIT_PXL

from usercmd import *

import MMAttrdefs
import settings
import features
import windowinterface

from SMILCssResolver import SMILCssResolver

ALL_LAYOUTS = '(All Channels)'

debug = 0
debugAlign = 0
debug2 = 0
debugPreview = 0

COPY_PASTE_MEDIAS = 1
SHOW_ANIMATE_NODES = 0
USE_NEW_ANIMATECODE = 0

TYPE_UNKNOWN, TYPE_REGION, TYPE_MEDIA, TYPE_VIEWPORT, TYPE_ANIMATE = range(5)
CHILD_TYPE = (TYPE_ANIMATE,)

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

	def destroy(self):
		self.__channelTreeRef = None
		self.__mmnodeTreeRef = None
		self.__nodeList = None
		self.__rootList = None

	#
	# End experimental code to manage a default region
	#
		
	def _getMMNodeType(self, node):
		if node == None:
			return None
		from MMTypes import playabletypes
		if not node.type in playabletypes:
			return None
		chtype = node.GetChannelType()
		if chtype == None:
			return None
		if chtype == 'animate':
			return TYPE_ANIMATE
		return TYPE_MEDIA

	# check the media node references and update the internal structure
	def __checkMediaNodeList(self, nodeRef, position=0):
		if debug2: print 'treeHelper.__checkMediaNodeList : start ',nodeRef
		ctx = self._context.context
		type = self._getMMNodeType(nodeRef)
		
		if type == TYPE_MEDIA:
			parentRef = self.getParent(nodeRef, TYPE_MEDIA)
			if not parentRef is None:
				self.__checkNode(parentRef, nodeRef, position, TYPE_VIEWPORT, TYPE_REGION, TYPE_MEDIA)
		elif type == TYPE_ANIMATE:
			if not SHOW_ANIMATE_NODES:
				return
			parentRef = self.getParent(nodeRef, TYPE_ANIMATE)
			if not parentRef is None:
				parentType = self._getMMNodeType(parentRef)
				if parentType in (TYPE_MEDIA, TYPE_REGION):
					self.__checkNode(parentRef, nodeRef, position, TYPE_VIEWPORT, parentType, TYPE_ANIMATE)

		childPosition = 0			
		for child in nodeRef.GetChildren():
			self.__checkMediaNodeList(child, childPosition)
			childPosition = childPosition+1
						
		if debug2: print 'treeHelper.__checkMediaNodeList : end ',nodeRef

	# check the media node references and update the internal structure
	def _checkMediaNodeList(self):
		self.__checkMediaNodeList(self.__mmnodeTreeRef)

	# check the region/viewport node references and update the internal structure
	def __checkRegionNodeList(self, parentRef, nodeRef, position):
		if debug2: print 'treeHelper.__checkRegionNodeList : start ',nodeRef

		self.__checkNode(parentRef, nodeRef, position, TYPE_VIEWPORT, TYPE_REGION, TYPE_REGION)
		childPosition = 0
		for subreg in nodeRef.GetChildren():
			if subreg.GetType() == 'layout':
				self.__checkRegionNodeList(nodeRef, subreg, childPosition)
				childPosition = childPosition+1
			
		if debug2: print 'treeHelper.__checkRegionNodeList : end ',nodeRef

	# check the region/viewport node references and update the internal structure
	def _checkRegionNodeList(self):
		viewportRefList = self.__channelTreeRef.getviewports()
		position = 0
		for viewportRef in viewportRefList:
			self.__checkRegionNodeList(None, viewportRef, position)
			position = position+1

	def __checkNode(self, parentRef, nodeRef, orderRef, typeRoot, typeParent, typeChild):
		# if no default region to show, exclude it	
		if not self.hasDefaultRegion and typeChild == TYPE_REGION and nodeRef.isDefault():
			return

		tNode =  self.__nodeList.get(nodeRef)
		if parentRef is not None:
			# case for no root nodes (regions, medias, ...)
			tParentNode =  self.__nodeList.get(parentRef)
			if tParentNode == None:
				if debug2: print 'treeHelper.__checkNode : the parent doesn''t exist, create a new parent tree node'
				tParentNode = self.__nodeList[parentRef] = TreeNodeHelper(parentRef, typeParent)
			if tNode == None:
				if debug2: print 'treeHelper.__checkNode : it''s a node, create a new tree node'
				tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, typeChild)
				tParentNode.addChild(tNode)
			elif not tParentNode.hasChild(tNode):
				if debug2:
					print 'treeHelper.__checkNode : the parent has changed children:'
					for child in tNode.children.keys():
						print '* ',child.nodeRef
				oldNode = tNode
				tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, typeChild)
				tNode.children = oldNode.children
				tParentNode.addChild(tNode)
			else:
				tNode.checkMainUpdate()
				tNode.isUsed = 1
		elif tNode is None:
			# case for root node (viewport)
			tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, typeRoot)
			self.__rootList[nodeRef] = tNode
		else:
			# case for existing root node (viewport)
			tNode.checkMainUpdate()							
			tNode.isUsed = 1
		tNode.orderRef = orderRef
			
	# this method is called when a node has to be deleted
	def __onDelNode(self, parent, node, destroy=1):
		if debug: print 'treeHelper.__onDelNode : ',node.nodeRef
		if self.__nodeListToDel.has_key(node.nodeRef):
			if debug2: print 'treeHelper.__onDelNode : already deleted, return'
			return
		for child in node.children.keys():
			self.__onDelNode(node, child, 0)
		if parent == None:
			parentRef = None
		else:
			parentRef = parent.nodeRef
		self._context.onDelNodeRef(parentRef , node.nodeRef)
		if destroy:
			# extract from the parent only if it's the top node to delete
			# it allows to not affect the sub-nodes if this node has to be moved
			if parent is not None:
				del parent.children[node]
				siblingList = parent.children.keys()
			else:
				del self.__rootList[node.nodeRef]
				siblingList = self.__rootList.values()
				
			# update the current position
			position = node.currentPosition
			for sibling in siblingList:
				spos = sibling.currentPosition
				if spos >position:
					sibling.currentPosition = spos-1
	
		self.__nodeListToDel[node.nodeRef] = 1
		node.currentPosition = -1 # raz the current position
		
	# this method is called when a node has to be added	
	def __onNewNode(self, parent, node, position):
		if debug: print 'treeHelper.__onNewNode : ',node.nodeRef, 'child = ',node.children
		if parent != None:
			parentRef = parent.nodeRef
		else:
			parentRef = None
		node.currentPosition = position

		self._context.onNewNodeRef(parentRef, node.nodeRef)

		# get children in the right order
		children = node.children.keys()
		children.sort(self.__cmpNode)
					
		childPosition = 0
		for child in children:
			self.__onNewNode(node, child, childPosition)
			childPosition = childPosition+1
			
		# reset the flags for the next time
		node.isNew = 0
		node.isUsed = 0
		# if the node is marked to delete, we have to restore erase the mark
		if self.__nodeListToDel.has_key(node.nodeRef):
			del self.__nodeListToDel[node.nodeRef]

	# this method look for all mutations relative to the previous update		
	def __detectDelMutation(self, parent, node):
		if debug2: print 'treeHelper.__detectDelMutation : start ',node.nodeRef
		
		# detect the node to erase
		if not node.isNew and not node.isUsed:
			self.__onDelNode(parent, node)
		# detect the new nodes
		elif node.isNew:
			# not now
			pass
		else:
			# check in children
			for child in node.children.keys():
				self.__detectDelMutation(node, child)
		if debug2: print 'treeHelper.__detectDelMutation : end ',node.nodeRef

	# this method will be used by the sort method
	def __cmpNode(self, node1, node2):
		# this method is called a lot of times. It has to be optimized
		# first, try to sort by z-index
		if node1.z > node2.z:
			return 1
		elif node1.z < node2.z:
			return -1
		else:
			# otherwise, by document order for region, and alphabethique for other types
			if node1.type in (TYPE_REGION, TYPE_VIEWPORT) and node1.type == node2.type:
				if node1.orderRef > node2.orderRef:
					return 1
				elif node1.orderRef < node2.orderRef:
					return -1
			else:
				if node1.name > node2.name:
					return 1
				elif node1.name < node2.name:
					return -1
				
		return 0

	# this method look for all mutations relative to the previous update		
	def __detectNewMutation(self, parent, node, position):		
		if debug2: 
			if node is not None: print 'treeHelper.__detectNewMutation : start ',node.nodeRef

		# detect the new nodes		
		if node is not None and node.isNew:
			self.__onNewNode(parent, node, position)
		else:
			# get children in the right order
			if node is not None:
				children = node.children.keys()
			else:
				children = self.__rootList.values()
			children.sort(self.__cmpNode)
			
			# check if the node has to be rebuild entirely. A better way would be probably
			# to call the low level API for sorting. But it's very complex for now to interface Python and Windows API
			rebuild = 0
			position = 0
			endFlag = 0
			for child in children:
				if position != child.currentPosition:
					if child.currentPosition == -1:
						endFlag = 1
						continue
					rebuild = 1
					break
				elif endFlag:
					rebuild = 1
					break
				position = position+1
			if rebuild:
				if debug2:
					if node is not None: print 'treeHelper.__detectNewMutation : change children order of',node.nodeRef
					else: print 'treeHelper.__detectNewMutation : change root order'
				# first delete all children
				for child in children:
					if not child.isNew:
						self.__onDelNode(node, child, 0)
				# then, re-create them in the right order
				position = 0
				for child in children:
					self.__onNewNode(node, child, position)
					position = position+1
			else:
				# detect whether need to update the main attributes. basicly id and type
				if node is not None and node.isUpdated:
					self._context.onMainUpdate(node.nodeRef)
					node.isUpdated = 0
				# if no change, check children
				for child in children:
					self.__detectNewMutation(node, child, position)
			# reset the flags the the next time
			if node is not None:
				node.isUsed = 0
		if debug2: 
			if node is not None:
				print 'treeHelper.__detectNewMutation : end ',node.nodeRef
			
	# this method look for all mutations relative to the previous update		
	def _detectMutation(self):
		self.__nodeListToDel = {}
		for key, root in self.__rootList.items():
			self.__detectDelMutation(None, root)			
		self.__detectNewMutation(None, None, 0)
		for node in self.__nodeListToDel.keys():
			if self.__rootList.has_key(node):
				del self.__rootList[node]
			del self.__nodeList[node]

	#
	# public methods
	#

	# the method look for all mutations relative to the previous update, and call the appropriate handlers
	# in the right order for each basic operation
	def onTreeMutation(self):
		if debug: print 'treeHelper.onTreeMutation start'
		self.hasDefaultRegion = 0
		self._context.context.updateDefaultRegion()
		self._checkMediaNodeList()
		self._checkRegionNodeList()
		self._detectMutation()
		if debug: print 'treeHelper.onTreeMutation end'

	# return the list of the nodeRef children
	# the children are either some viewports, some regions or some medias
	def getChildren(self, nodeRef):
		list = []
		node = self.__nodeList.get(nodeRef)
		if node is not None:
			for child in node.children.keys():
				list.append(child.nodeRef)
		return list

	# return the media list of the regionRef children
	def getMediaChildren(self, regionRef):
		list = []
		node = self.__nodeList.get(regionRef)
		if node is not None:
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
		list = []
		for root in self.__rootList.keys():
			list.append(root)
		return list

	# return the type of the node
	# Note. This method works also if the node is already remove it from the reference document
	# and not yet from this structure
	def getNodeType(self, nodeRef):
		node = self.__nodeList.get(nodeRef)
		if node != None:
			return node.type

	# return the parent node reference in the layout view
	# Notes for regions: 
	# - that region may be differente that the defined region in the document
	# because of the default region
	# - don't move that method into mmnode, the behavior is specific to the layout view to edit purpose
	# the player has for instance another behavior
	def getParent(self, nodeRef, nodeType):
		if nodeType == TYPE_MEDIA:
			region = nodeRef.GetDefinedChannel()
			if region is None:
				# A association may be defined in the clipboard. In that case,
				# we don't show the media in the default region
				found = 0
				clipList = self._context.editmgr.getclip()
				for clipNode in clipList:
					if clipNode.getClassName() == 'RegionAssociation':
						if clipNode.getMediaNode() is nodeRef:
							found = 1
							break
				if found:
					# the node is in the clipboard. 
					return None
				else:
					# No region defined, return the default region
					self.hasDefaultRegion = 1
					return self._context.context.getDefaultRegion()
			else:
				# the region may be moved from the document to the clipboard. In that case,
				# we don't show the media in the default region
				if not region.isInDocument():
					return None
	
				return region
		elif nodeType == TYPE_REGION:
			return nodeRef.GetParent()
		elif nodeType == TYPE_ANIMATE:
			if hasattr(nodeRef, 'targetnode'):
				return nodeRef.targetnode

		# no layout parent			
		return None
							
	def delNode(self, nodeRef):
		if debug: print 'treeHelper.delNode ',nodeRef
		node = self.__nodeList.get(nodeRef)
		if node == None: return
		parentRef = nodeRef.GetParent()
		if parentRef == None:
			# it's a top layout
			parentNode = None
		else:
			parentNode = self.__nodeList.get(parentRef)
		self.__onDelNode(parentNode, node)
	
class TreeNodeHelper:
	def __init__(self, nodeRef, type):
		# this method is called a lot of times. It has to be optimized
		# read directly the attributes on the node: more efficient

		self.orderRef = 0		
		self.currentPosition = -1
		
		self.isNew = 1
		self.isUsed = 1
		self.isUpdated = 0
		self.nodeRef = nodeRef
		self.children = {}
		self.type = type
		attrdict = nodeRef.attrdict
		if type == TYPE_MEDIA:
			self.name = attrdict.get('name')
			self.mediatype = nodeRef.GetChannelType()
		elif type in (TYPE_VIEWPORT, TYPE_REGION):
			name = attrdict.get('regionName')
			if name == None:
				self.name = nodeRef.name
			else:
				self.name = name
		self.z = attrdict.get('z',0)
		self.previewShowOption = attrdict.get('previewShowOption')

	def hasChild(self, child):
		return self.children.has_key(child)
	
	def addChild(self, child):
		self.children[child] = 1

	def checkMainUpdate(self):
		# this method is called a lot of times. It has to be optimized
		# read directly the attributes on the node: more efficient
		nodeRef = self.nodeRef
		attrdict = nodeRef.attrdict
		if self.type == TYPE_MEDIA:
			name = attrdict.get('name')
			mediatype = nodeRef.GetChannelType()
			if name != self.name or mediatype != self.mediatype:
				self.isUpdated = 1
				self.name = name
				self.mediatype = mediatype
		elif self.type in (TYPE_VIEWPORT, TYPE_REGION):
			name = attrdict.get('regionName')
			if name == None:
				name = nodeRef.name
			if name != self.name:
				self.isUpdated = 1
				self.name = name
		self.z = attrdict.get('z',0)
		previewShowOption = attrdict.get('previewShowOption')
		if self.previewShowOption != previewShowOption:
			self.isUpdated = 1
			self.previewShowOption = previewShowOption
		
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
		self.currentSelectedNodeList = []
		self.previousSelectedNodeList = []
		self.currentFocus = None
		# allow to identify if the focus has been fixed by this view
		self.myfocus = None	# used to break recursion in setglobalfocus -> globalfocuschanged

		# when you swap to the pause state, the current region showed list is saved
		# it allows to restore the context when document is stopped
		# XXX may changed
		# self.stopSelectedRegionList = []
		# self.stopSelectedMediaList = []

		self.showName = 0
		self.showAllRegions = 1
		
		# define the valid command according to the node selected
		self.mkmediacommandlist()
		self.mkregioncommandlist()
		self.mkviewportcommandlist()
		self.mknositemcommandlist()
		self.mkmultisitemcommandlist()
		self.mkmultisiblingsitemcommandlist()
		
		# dictionary of widgets used in this view
		# basicly, this view is composed of 
		# - a tree widget which manage the standard tree control
		# - a previous widget which manage the previous area
		# - some light widgets (geom field, z-index field, buttons control, ...)
		self.widgetList = {}

		self.currentKeyTimeIndex = None
		self.timeValueChanged = 1
		self.isAKeyTime = 0
		self.currentTimeValue = None
		self.currentTargetAnimateNode = None
		self.currentAnimateNode = None
		
	def fixtitle(self):
		pass			# for now...
	
	def destroy(self):
		self.hide()
		LayoutViewDialog2.destroy(self)

	def mkviewportcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandViewportList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandViewportList = [
				]
		self.__appendCommonCommands(self.commandViewportList)

	def mkregioncommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandRegionList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
#				ENABLE_ANIMATION(callback = (self.onEnableAnimation, ())),
				]
		else:
			self.commandRegionList = [
				]
		self.__appendCommonCommands(self.commandRegionList)

	def mkmediacommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMediaList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				ENABLE_ANIMATION(callback = (self.onEnableAnimation, ())),
				]
		else:
			self.commandMediaList = []
		self.commandMediaList.append(CONTENT(callback = (self.onContent, ())))
		self.__appendCommonCommands(self.commandMediaList)
			
	def mknositemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandNoSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandNoSItemList = []
		self.__appendCommonCommands(self.commandNoSItemList)

	# available command when several items are selected
	def mkmultisitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMultiSItemList = []		
		self.__appendCommonCommands(self.commandMultiSItemList)
		
	def mkmultisiblingsitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSiblingSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMultiSiblingSItemList = []
		self.__appendAlignCommands()
		self.__appendCommonCommands(self.commandMultiSiblingSItemList)

	def __appendCommonCommands(self, commandlist):
		commandlist.append(ZOOMIN(callback = (self.onZoomIn, ())))
		commandlist.append(ZOOMOUT(callback = (self.onZoomOut, ())))
		commandlist.append(DRAG_TOPLAYOUT())
		commandlist.append(DRAG_REGION())
			
	def __appendAlignCommands(self):
		self.commandMultiSiblingSItemList.append(ALIGN_LEFT(callback = (self.onAlignLeft, ())))
		self.commandMultiSiblingSItemList.append(ALIGN_CENTER(callback = (self.onAlignCenter, ())))
		self.commandMultiSiblingSItemList.append(ALIGN_RIGHT(callback = (self.onAlignRight, ())))
		self.commandMultiSiblingSItemList.append(ALIGN_TOP(callback = (self.onAlignTop, ())))
		self.commandMultiSiblingSItemList.append(ALIGN_MIDDLE(callback = (self.onAlignMiddle, ())))
		self.commandMultiSiblingSItemList.append(ALIGN_BOTTOM(callback = (self.onAlignBottom, ())))
		self.commandMultiSiblingSItemList.append(DISTRIBUTE_HORIZONTALLY(callback = (self.onDistributeHorizontally, ())))
		self.commandMultiSiblingSItemList.append(DISTRIBUTE_VERTICALLY(callback = (self.onDistributeVertically, ())))
		
	def show(self):
		if self.is_showing():
			LayoutViewDialog2.show(self)
			return
		LayoutViewDialog2.show(self)
		
		self.__channelTreeRef = self.context.getchanneltree()

		################################################################################
		# IMPORTANT: call this method after calling the method context.getchanneltree()
		self.editmgr.register(self, 1, 1)
		################################################################################

		self.initWidgets()
		
		self.treeHelper = TreeHelper(self, self.__channelTreeRef, self.root)

		# the tree and previous widgets are appended for this step
		self.treeMutation()

		# show the widgets
		for id, widget in self.widgetList.items():
			widget.show()
				
		# XXX to implement
		# get the initial player state		
#		type,node = self.editmgr.getplayerstate()
#		if node != None:
#			self.playerstatechanged(type, node)
			
		# get the initial focus
		self.currentFocus = self.editmgr.getglobalfocus()
		self.updateFocus()
		
	def hide(self):
		if not self.is_showing():
			return
		self.__channelTreeRef = None
		self.editmgr.unregister(self)

		# XXX to do: destroy all objects and to check that they are garbage collected
		for id, widget in self.widgetList.items():
			widget.destroy()
		self.widgetList = {}
		
		# hide the windows	
		LayoutViewDialog2.hide(self)

		# destroy the tree helper structure	
		self.treeHelper.destroy()

		# clear all variables state
		self.currentSelectedNodeList = []
		self.previousSelectedNodeList = []
		self.currentFocus = None
		self.myfocus = None

		self.currentTargetAnimateNode = None		
		self.currentAnimateNode = None
		
	def transaction(self, type):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def GetContext(self):
		return self.context
		
	#
	# implementation of tree helper handler methods
	#
	
	def onNewNodeRef(self, parentRef, nodeRef):
		nodeType = self.getNodeType(nodeRef)

		# update tree widget		
		self.treeWidget.appendNode(parentRef, nodeRef, nodeType)
		self.previousWidget.appendNode(parentRef, nodeRef, nodeType)
		
	def onDelNodeRef(self, parentRef, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		
		# update tree widget		
		self.treeWidget.removeNode(nodeRef, nodeType)
		self.previousWidget.removeNode(nodeRef, nodeType)

	def onMainUpdate(self, nodeRef):
		self.treeWidget.updateNode(nodeRef)
	#
	#
	#
	
	# update the region tree
	def treeMutation(self):
		if debug: print 'call treeHelper.treeMutation'
		# notify widgets that the document structure start to change
		for id, widget in self.widgetList.items():
			widget.startMutation()
		self.treeHelper.onTreeMutation()
		# notify widgets that the document structure end to change
		for id, widget in self.widgetList.items():
			widget.endMutation()

	def commit(self, type):
		self.root = self.toplevel.root
		if type not in ('REGION_GEOM', 'MEDIA_GEOM'):
			self.treeMutation()

		# XXX very temporare to a allow demonstration
		if not USE_NEW_ANIMATECODE and self.currentTargetAnimateNode is not None:
			if self.existRef(self.currentTargetAnimateNode):
				# just update timing. Of course can't work in several cases (when layout view is closed, ...)
				animationData = self.currentTargetAnimateNode.getAnimationData()
				if animationData is not None:
					animationData.updateTimes()
		
		# after a commit, the focus may have changed
		self.currentFocus = self.editmgr.getglobalfocus()
		self.previousWidget.mustBeUpdated()
		self.updateFocus(1)

	# update animation wrapper to be able to get interpolation values
	def updateAnimationWrapper(self):
		animateNode = self.getAnimateNode()
		if animateNode is not None:
			import AnimationWrappers
			self.animationWrapper = AnimationWrappers.getAnimationWrapper(animateNode)
			self.animationWrapper.updateAnimators(animateNode)

	# make a list of nodes selected in this view
	def makeSelectedNodeList(self, selList):
		targetList = []
		for nodeRef in selList:
			if self.existRef(nodeRef):
				# keep only seleted nodes belong to this view
				targetList.append(nodeRef)

		self.currentSelectedNodeList = targetList
		
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

	def updateCommandList(self, basecommandlist):
		commandlist = basecommandlist[:]

		# determinate is paste is valid	depending on what is in the clipboard.	
		activePaste = 0
		nodeList = self.editmgr.getclip()
		for node in nodeList:
			className = node.getClassName()
			if className == 'Viewport':
				activePaste = 1
			elif len(self.currentSelectedNodeList) == 1: # only single selection
				selectedNode = self.currentSelectedNodeList[0]
				selectedType = self.getNodeType(selectedNode)
				if selectedType in (TYPE_VIEWPORT, TYPE_REGION) and className == 'Region':
					if selectedNode.isDefault():
						# no valid paste
						activePaste = 0
						break					
					activePaste = 1
				elif className == 'RegionAssociation' and selectedType == TYPE_REGION and COPY_PASTE_MEDIAS:
					activePaste = 1
				else:
					# no valid paste
					activePaste = 0
					break

		if activePaste:
			commandlist.append(PASTE(callback = (self.onPaste, ())))

		# some other commands to update
		if len(self.currentSelectedNodeList) == 1:
			selectedNode = self.currentSelectedNodeList[0]
			if not self.getNodeType(selectedNode) == TYPE_REGION or not selectedNode.isDefault():
				commandlist.append(ATTRIBUTES(callback = (self.onEditProperties, ())))
				commandlist.append(NEW_REGION(callback = (self.onNewRegion, ())))

		if len(self.currentSelectedNodeList) >= 1:
			active = 1
			for node in self.currentSelectedNodeList:
				if self.getNodeType(node) == TYPE_REGION and node.isDefault():
					active = 0
					break
			if active:
				# no default region in the selected list
				commandlist.append(COPY(callback = (self.onCopy, ())))
				commandlist.append(CUT(callback = (self.onCut, ())))
				commandlist.append(DELETE(callback = (self.onDelNode, ())))
				
		self.setcommandlist(commandlist)

	def updateVisibility(self,listToUpdate, visible):
		self.treeWidget.updateVisibility(listToUpdate, visible)
		self.previousWidget.updateVisibility(listToUpdate, visible)
		
	def updateFocus(self, keepShowedNodes=0):
		if debug: print 'LayoutView.updateFocus: focus on List'

		focusobject = self.currentFocus

		# determine if all the objects are siblings
		areSibling = 1
		previousObject = None
		nodeType = None
		for object in focusobject:
			if nodeType is None:
				nodeType = self.getNodeType(object)
			if areSibling and previousObject is not None and not self.areSibling(previousObject, object):
				areSibling = 0
			previousObject = object

		self.makeSelectedNodeList(focusobject)	
		localSelList = self.currentSelectedNodeList

		# animation support
		enabled = 0
		if len(localSelList) == 1:
			nodeRef = localSelList[0]
			nodeType = self.getNodeType(nodeRef)

			if USE_NEW_ANIMATECODE:
				self.currentAnimateNode = animateNode = self.findAnimateNode(nodeRef)
				if animateNode is not None:
					self.currentTargetAnimateNode = nodeRef
					enabled = 1
			else:
				animationData = None
				if nodeType == TYPE_MEDIA:
					animationData = nodeRef.computeAnimationData()
				else:
					# XXX 
					if hasattr(nodeRef,'_animparent'):
						animationData = nodeRef.computeAnimationData(nodeRef._animparent)
				if animationData is not None and not animationData.isEmpty():
					enabled = 1
					self.currentTargetAnimateNode = nodeRef
					
		if enabled:
			if USE_NEW_ANIMATECODE:
				self.updateAnimationWrapper()
			self.settoggle(ENABLE_ANIMATION, 1)
		else:
			self.currentTargetAnimateNode = None
			self.currentAnimateNode = None
			self.settoggle(ENABLE_ANIMATION, 0)

		if not enabled or self.currentFocus is None or len(self.currentFocus) != 1:
			self.setKeyTimeIndex(None, None)
		elif (self.previousSelectedNodeList is None or len(self.previousSelectedNodeList) != 1 or (not self.currentFocus[0] is self.previousSelectedNodeList[0])):
			self.setKeyTimeIndex(0, self.currentFocus[0])
				
		if self.timeValueChanged:
			self.previousWidget.mustBeUpdated()
			self.timeValueChanged = 0

		# update the visibility states according to the current and previous selection
		# XXX to optimize
		listToUpdate = []
		for nodeRef in self.previousSelectedNodeList:
			# force the state to 0
			list = self.getAllParent(nodeRef)
			list.append(nodeRef)
			for nodeRef in list:
				nodeType = self.getNodeType(nodeRef)
				visible = self.getVisibility(nodeRef, nodeType, selected=0)
				if not visible:				
					listToUpdate.append(nodeRef)
		self.updateVisibility(listToUpdate, 0)
		listToUpdate = []
		for nodeRef in localSelList:
			# force the state to 1
			list = self.getAllParent(nodeRef)
			list.append(nodeRef)
			for nodeRef in list:
				nodeType = self.getNodeType(nodeRef)
				visible = self.getVisibility(nodeRef, nodeType, selected=1)
				if visible:
					listToUpdate.append(nodeRef)
		self.updateVisibility(listToUpdate, 1)

		self.previousWidget.update()
		
		# update widgets
		for id, widget in self.widgetList.items():
			widget.selectNodeList(localSelList, keepShowedNodes)

		if len(localSelList) == 0:
			self.updateCommandList(self.commandNoSItemList)
		elif len(localSelList) == 1:
			if nodeType == TYPE_REGION:
				self.updateCommandList(self.commandRegionList)
			elif nodeType == TYPE_VIEWPORT:
				self.updateCommandList(self.commandViewportList)
			else:
				self.updateCommandList(self.commandMediaList)
		elif areSibling:
			self.updateCommandList(self.commandMultiSiblingSItemList)
		else:
			self.updateCommandList(self.commandMultiSItemList)

		# save the focus for the next time
		self.previousSelectedNodeList = []
		for nodeRef in self.currentSelectedNodeList:
			self.previousSelectedNodeList.append(nodeRef)
							
	def globalfocuschanged(self, focusobject):
		if debug: print 'LayoutView.globalfocuschanged focusobject=',focusobject
		self.currentFocus = focusobject
		if self.myfocus is None:
			self.updateFocus()
		self.myfocus = None

	def setglobalfocus(self, list):
		if debug: print 'LayoutView.setglobalfocus list=',list
		self.myfocus = list
		self.editmgr.setglobalfocus(list)
		self.currentSelectedNodeList = list
		
	def playerstatechanged(self, type, parameters):
		pass
		# XXX to implement
#		if type == 'paused':
#			self.toPauseState(parameters)
#		elif type == 'stopped':
#			self.toStopState()
		
	def kill(self):
		self.destroy()
				
	def getViewportRefList(self):
		return self.treeHelper.getRootNodeList()

	def getRegionRefList(self, viewportRef):
		return self.treeHelper.getRegionList(viewportRef)

	def getMediaChildren(self, regionRef):
		return self.treeHelper.getMediaChildren(regionRef)

	def getChildren(self, nodeRef):
		return self.treeHelper.getChildren(nodeRef)

	def getAllChildren(self, nodeRef):
		list = []
		return self.__getAllChildren(nodeRef, list)

	def getAllParent(self, nodeRef):
		list = []
		parent = self.getParentNodeRef(nodeRef)
		while parent is not None:
			list.append(parent)
			parent = self.getParentNodeRef(parent)
		return list
		
	def __getAllChildren(self, nodeRef, list):
		children = self.getChildren(nodeRef)
		for child in children:
			list.append(child)
			self.__getAllChildren(child, list)
		return list
		
	def existRef(self, nodeRef):
		return self.treeHelper.existRef(nodeRef)	
	
	def nameToNodeRef(self, name):
		return self.context.getchannel(name)

	def getNodeType(self, nodeRef):
		return self.treeHelper.getNodeType(nodeRef)

	def areSibling(self, nodeRef1, nodeRef2):
		parent1 = self.getParentNodeRef(nodeRef1)
		parent2 = self.getParentNodeRef(nodeRef2)
		# note exclude viewport
		return parent1 is not None and parent2 is not None and \
			   parent1 is parent2
		
	def getViewportRef(self, nodeRef, nodeType = None):
		if nodeType is None:
			nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			return nodeRef
		while nodeType != TYPE_REGION:
			nodeRef = self.treeHelper.getParent(nodeRef, nodeType)
			nodeType = self.getNodeType(nodeRef)
			if nodeType is None or nodeType == TYPE_UNKNOWN:
				break
		if nodeType == TYPE_REGION:
			return self.__channelTreeRef.getviewport(nodeRef)
		
		return None
	
	# XXX to optimize, get info from tree helper
	# get the parent spatial node
	def getParentNodeRef(self, nodeRef, nodeType = None):
		if nodeType == None:
			nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			return self.treeHelper.getParent(nodeRef, nodeType)
		else:
			region = self.__channelTreeRef.getparent(nodeRef)
			return region
		return None

	def setKeyTimeIndex(self, keyTimeIndex, nodeRef):
		self.isAKeyTime = 0
		if self.currentKeyTimeIndex != keyTimeIndex:
			self.timeValueChanged = 1
		self.currentKeyTimeIndex = keyTimeIndex
		if not nodeRef is None and not keyTimeIndex is None:
			if USE_NEW_ANIMATECODE:
				self.currentTimeValue = None # by default, indefinite
				animateNode = self.getAnimateNode()
				if animateNode is not None and animateNode.GetType() == 'animpar':
					animvals = animateNode.GetAttrDef('animvals', [])
					if len(animvals) > keyTimeIndex:
						self.currentTimeValue, vals = animvals[keyTimeIndex]
			else:
				animationData = nodeRef.getAnimationData()
				timeList = animationData.getTimes()
				self.currentTimeValue = timeList[keyTimeIndex]
			self.isAKeyTime = 1
		else:
			self.currentTimeValue = None

	def getKeyTimeIndex(self):
		return self.currentKeyTimeIndex
	
	def setCurrentTimeValue(self, currentTimeValue, nodeRef):
		if USE_NEW_ANIMATECODE:
			self.currentTimeValue = None # by default, indefinite
			animateNode = self.getAnimateNode()
			if animateNode is not None and animateNode.GetType() == 'animpar':
				animvals = animateNode.GetAttrDef('animvals', [])
				if self.currentTimeValue != currentTimeValue:
					self.timeValueChanged = 1
				self.currentTimeValue = currentTimeValue
				self.isAKeyTime = 0
				keyTimeIndex = self.getKeyForThisTime(animvals, currentTimeValue)
				if not keyTimeIndex is None:
					self.isAKeyTime = 1
				if self.currentKeyTimeIndex != keyTimeIndex:
					self.timeValueChanged = 1
				self.currentKeyTimeIndex = keyTimeIndex					
		else:
			animationData = nodeRef.getAnimationData()
			timeList = animationData.getTimes()
			if self.currentTimeValue != currentTimeValue:
				self.timeValueChanged = 1
			self.currentTimeValue = currentTimeValue
			self.isAKeyTime = 0
			keyTimeIndex = self.getKeyForThisTime(timeList, currentTimeValue)
			if not keyTimeIndex is None:
				self.isAKeyTime = 1
			if self.currentKeyTimeIndex != keyTimeIndex:
				self.timeValueChanged = 1
			self.currentKeyTimeIndex = keyTimeIndex

	def getCurrentTimeValue(self):
		return self.currentTimeValue

	def getTargetAnimateNode(self):
		return self.currentTargetAnimateNode

	def getAnimateNode(self):
		return self.currentAnimateNode

	def findAnimateNode(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		# XX for now, support only animpar type
		if nodeType == TYPE_MEDIA:
			children = nodeRef.GetChildren()
			for child in children:
				if child.type == 'animpar':
					return child
		return None
		
	# have to be called from inside a transaction	
	def insertKeyTime(self, nodeRef, tp, duplicateKey=None):
		index = 0
		if USE_NEW_ANIMATECODE:
			self.currentTimeValue = None # by default, indefinite
			animateNode = self.getAnimateNode()
			if animateNode is not None and animateNode.GetType() == 'animpar':
				animvals = animateNode.GetAttrDef('animvals', None)
				if animvals is not None:
					for time, vals in animvals:
						if time > tp:
							break
						index = index+1
					if index > 0 and index < len(animvals):
						# can only insert a key between the first and the end
						if duplicateKey is not None and duplicateKey >= 0:
							# duplicate a key value
							time, vals = animvals[duplicateKey]
							newvals = vals.copy()
						else:
							# interpolate values at this time
							left, top, width, height = self.animationWrapper.getRectAt(tp)
							bgcolor = self.animationWrapper.getColorAt(tp)
							newvals = {'left':left, 'top':top, 'width':width, 'height':height, 'bgcolor':bgcolor}
						animvals.insert(index, (tp, newvals))
						self.editmgr.setnodeattr(animateNode, 'animvals', animvals)
		else:			
			animationData = nodeRef.getAnimationData()
			timeList = animationData.getTimes()
			data = animationData.getData()
			index = 0
			for time in timeList:
				if time > tp:
					break
				index = index+1

			if index > 0 and index < len(timeList):
				# can only insert a key between the first and the end
				if duplicateKey is not None and duplicateKey >= 0:
					newData = (animationData.getRectAt(timeList[duplicateKey]), animationData.getColorAt(timeList[duplicateKey]))
				else:
					newData = (animationData.getRectAt(tp), animationData.getColorAt(tp))
				animationData.insertTimeData(index, tp, newData)

		if index > 0:
			self.setKeyTimeIndex(index, nodeRef) # XXX for new code, nodeRef should be removed
			self.animateControlWidget.insertKey(tp)
			self.timeValueChanged = 1 # force layout to refresh
			
	# have to be called from inside a transaction	
	def removeKeyTime(self, nodeRef, index):
		if USE_NEW_ANIMATECODE:
			animateNode = self.getAnimateNode()
			animvals = animateNode.GetAttrDef('animvals', [])
			if index > 0 and index < len(animvals)-1:
				# can only remove a key between the first and the end
				del animvals[index]
				self.editmgr.setnodeattr(animateNode, 'animvals', animvals)
				self.animateControlWidget.removeKey(index)
				self.setKeyTimeIndex(index-1, nodeRef)
		
	def getKeyForThisTime(self, list, time):
		if USE_NEW_ANIMATECODE:
			index = 0
			for timeRef, vals in list:
				if timeRef == time:
					return index
				index = index+1
			return None
		else:
			index = 0
			for timeRef in list:
				if timeRef == time:
					return index
				index = index+1
			return None
	
	def getPxGeomWithContextAnimation(self, nodeRef):
		time = self.currentTimeValue
		if USE_NEW_ANIMATECODE:
			if time is not None and nodeRef is self.getTargetAnimateNode():
				wingeom = self.animationWrapper.getRectAt(time)
			else:
				wingeom = nodeRef.getPxGeom()
		else:
			animationData = nodeRef.getAnimationData()
			if not time is None and animationData is not None:
				# XXX should move in another place
				wingeom = animationData.getRectAt(time)
			else:
				wingeom = nodeRef.getPxGeom()
			
		return wingeom
		
	# Test whether x is ancestor of node
	def IsAncestorOf(self, node, x):
		while x is not None:
			if node is x: return 1
			x = self.getParentNodeRef(x)
		return 0

	# return the name showed to the user according to the node 
	def getShowedName(self, nodeRef, nodeType=None):
		if nodeType == None:
			nodeType = self.getNodeType(nodeRef)
			
		if nodeType == TYPE_MEDIA:
			name = nodeRef.attrdict.get('name')
		elif nodeType == TYPE_REGION:
			# show first the region name
			# if the region name doesn't exist, the the id
			name = nodeRef.GetAttrDef('regionName',None)
			if name == None:
				name = nodeRef.name
			if nodeRef.isDefault():
				name = '# '+name
		elif nodeType == TYPE_VIEWPORT:
			name = nodeRef.name
		else:
			# unknown type
			name = ''
			
		return name
			
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
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
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
	
	def initWidgets(self):
		widgetList = self.widgetList
		self.previousWidget = widgetList['PreviousWidget'] = PreviousWidget(self)
		self.treeWidget = widgetList['TreeWidget'] = TreeWidget(self)
		self.geomFieldWidget = widgetList['GeomFieldWidget'] = GeomFieldWidget(self)
		widgetList['ZFieldWidget'] = ZFieldWidget(self)		
		widgetList['FitWidget'] = FitWidget(self)
		self.animateControlWidget = widgetList['AnimateControlWidget'] = AnimateControlWidget(self)

	def applyGeom(self, nodeRef, geom):
		# make a list of attr top apply according the geometry
		list = []
		transactionType = None
		nodeType = self.getNodeType(nodeRef)
		if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
			transactionType = 'REGION_GEOM'
		elif nodeType == TYPE_MEDIA:
			transactionType = 'MEDIA_GEOM'
		self.__makeAttrListToApplyFromGeom(nodeRef, geom, list)
		self.applyAttrList(list)		

	def applyGeomList(self, applyList):
		list = []		
		for nodeRef, geom in applyList:
			self.__makeAttrListToApplyFromGeom(nodeRef, geom, list)
		self.applyAttrList(list)

	def __makeAttrListToApplyFromGeom(self, nodeRef, geom, list):
		if self.getNodeType(nodeRef) == TYPE_VIEWPORT:
			x,y,w,h = geom
			list.append((nodeRef, 'width', w))
			list.append((nodeRef, 'height', h))
		else:
			x,y,w,h = geom
			list.append((nodeRef, 'left', x))
			list.append((nodeRef, 'top', y))
			list.append((nodeRef, 'width', w))
			list.append((nodeRef, 'height', h))
			list.append((nodeRef, 'right', None))
			list.append((nodeRef, 'bottom', None))
		
	def applyBgColor(self, nodeRef, bgcolor, transparent):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(nodeRef.name, 'bgcolor', bgcolor)
			self.editmgr.setchannelattr(nodeRef.name, 'transparent', transparent)
			self.editmgr.commit()

	def applyFit(self, nodeRef, value):
		# test if possible 
		if self.editmgr.transaction():
			nodeType = self.getNodeType(nodeRef)
			if nodeType == TYPE_MEDIA:
				self.editmgr.setnodeattr(nodeRef, 'fit', value)
			elif nodeType == TYPE_REGION:
				self.editmgr.setchannelattr(nodeRef.name, 'fit', value)
			
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

	def applyNewRegion(self, parentRef, id, regionName):
		if self.editmgr.transaction():
			channel = self.context.newchannel(id, -1, 'layout')
			self.editmgr.addchannel(parentRef, -1, channel)
			self.editmgr.setchannelattr(id, 'regionName', regionName)

			# set automaticly a the highest z-index amoung all sibling nodes
			# XXX should be probably changed/moved if we want also the same behavior when a node is copied, ...
			sibling = parentRef.GetChildren()
			max = None
			for nodeRef in sibling:
				z = nodeRef.GetAttrDef('z', 0)
				if max == None or z > max:
					max = z
			if max is not None:
				self.editmgr.setchannelattr(id, 'z', max+1)
								
			self.editmgr.commit('REGION_TREE')

	def applyNewViewport(self, name):
		if self.editmgr.transaction():
			channel = self.context.newviewport(name, -1, 'layout')
			self.editmgr.addchannel(None, -1, channel)
			self.editmgr.setchannelattr(name, 'transparent', 0)
			self.editmgr.setchannelattr(name, 'showEditBackground', 1)
			self.editmgr.setchannelattr(name, 'width', 400)
			self.editmgr.setchannelattr(name, 'height', 400)
			self.editmgr.commit('REGION_TREE')
		
	def __makeRegionListToDel(self, nodeRef, list):
		# remove the children before removing the node
		children = self.getChildren(nodeRef)
		for child in children:
			self.__makeRegionListToDel(child, list)
		nodeType = self.getNodeType(nodeRef)
		if nodeType in (TYPE_REGION, TYPE_VIEWPORT):
			list.append(nodeRef.name)

	def applyAttrList(self, nodeRefAndValueList):
		if not self.editmgr.transaction():
			return

		animationEnabled = self.currentTargetAnimateNode is not None
		
		if animationEnabled:
			if USE_NEW_ANIMATECODE:
				animateNode = self.getAnimateNode()
				animvals = animateNode.GetAttrDef('animvals', [])
				keyTimeIndex = self.getKeyTimeIndex()
				currentTimeValue = self.getCurrentTimeValue()
				if not currentTimeValue is None:
					if not self.isAKeyTime:
						self.insertKeyTime(animateNode, currentTimeValue)
						keyTimeIndex = self.getKeyTimeIndex()
			else:
				animatedType, animatedNode = self.animateControlWidget._selected
				animationData = animatedNode.getAnimationData()
				data = animationData.getData()
				timeList = animationData.getTimes()
				keyTimeIndex = self.getKeyTimeIndex()
				currentTimeValue = self.getCurrentTimeValue()
				if not currentTimeValue is None:
					if not self.isAKeyTime:
						self.insertKeyTime(animatedNode, currentTimeValue)
						keyTimeIndex = self.getKeyTimeIndex()
					
		for nodeRef, attrName, attrValue in nodeRefAndValueList:
			nodeType = self.getNodeType(nodeRef)
			animated = 0
			if USE_NEW_ANIMATECODE:
				if animationEnabled and nodeRef is self.getTargetAnimateNode() and attrName in ('left', 'top', 'width', 'height') and \
					not keyTimeIndex is None and keyTimeIndex >= 0:
						animated = 1
			else:
				if animationEnabled and nodeRef is animatedNode and attrName in ('left', 'top', 'width', 'height') and \
					not keyTimeIndex is None and keyTimeIndex >= 0:
						animated = 1
			if animated:
				if USE_NEW_ANIMATECODE:
					# animation value
					time, vals = animvals[keyTimeIndex]
					vals[attrName] = attrValue
					self.editmgr.setnodeattr(animateNode, 'animvals', animvals)
				else:
					# animation value
					(left, top, width, height), bgcolor = data[keyTimeIndex]
					if attrName == 'left':
						left = attrValue
					elif attrName == 'top':
						top = attrValue
					elif attrName == 'width':
						width = attrValue
					elif attrName == 'height':
						height = attrValue
					newdata = (left, top, width, height), bgcolor
					animationData.updateData(keyTimeIndex, newdata)

			if not animated or keyTimeIndex == 0:
				if nodeType in (TYPE_VIEWPORT, TYPE_REGION):					
					self.editmgr.setchannelattr(nodeRef.name, attrName, attrValue)
				elif nodeType == TYPE_MEDIA:
					self.editmgr.setnodeattr(nodeRef, attrName, attrValue)
				
		if animationEnabled and not USE_NEW_ANIMATECODE:
			nodeRef.applyAnimationData(self.editmgr)
				
		self.editmgr.commit()

	# apply some command which are automaticly applied when a control lost the focus
	# it avoids some recursives transactions and some crashes
	def flushChangement(self):
		# currently, some widget on dialog box generate the 'LOSTFOCUS' event too late. Thus, the new values are
		# applied too late For example, only when the dialog property box is open. So, it causes some crashes.
		# this code force to apply the new value before any new operation
		self.dialogCtrl.flushChangement()
		
	#
	# Alignment/Distribute commands
	#
	
	def onAlignLeft(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'align left : ',self.currentSelectedNodeList
		if len(self.currentSelectedNodeList) <= 1:
			return

		# get the node the most on the left
#		referenceValue = None
#		for node in self.currentSelectedNodeList:
#			l,t,w,h = node.getPxGeom()
#			if referenceValue == None or l < referenceValue:
#				referenceNode = node
#				referenceValue = l

		# the reference node is the last selected
		referenceNode = self.currentSelectedNodeList[-1]

		# determinate the reference value		
		l,t,w,h = self.getPxGeomWithContextAnimation(referenceNode)
		referenceValue = l

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
				l = referenceValue
				# make the new geom
				self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)
				
	def onAlignCenter(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'align center : ',self.currentSelectedNodeList
		if len(self.currentSelectedNodeList) <= 1:
			return

		# get the node the most on the left
#		referenceValue = None
#		for node in self.currentSelectedNodeList:
#			l,t,w,h = node.getPxGeom()
#			if referenceValue == None or l < referenceValue:
#				referenceNode = node
#				referenceValue = l

		# the reference node is the last selected
		referenceNode = self.currentSelectedNodeList[-1]

		# for the reference object, determinate the center
		l,t,w,h = self.getPxGeomWithContextAnimation(referenceNode)
		referenceValue = int(l+w/2)
		
		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
				center = int(l+w/2)
				diff = center-referenceValue
				l = l-diff
				# make the new geom
				self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	def onAlignRight(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'align right : ',self.currentSelectedNodeList
		if len(self.currentSelectedNodeList) <= 1:
			return

		# get the node the most on the left
#		referenceValue = None
#		for node in self.currentSelectedNodeList:
#			l,t,w,h = node.getPxGeom()
#			if referenceValue == None or l < referenceValue:
#				referenceNode = node
#				referenceValue = l

		# the reference node is the last selected
		referenceNode = self.currentSelectedNodeList[-1]

		# for the reference object, determinate the right border
		l,t,w,h = self.getPxGeomWithContextAnimation(referenceNode)
		referenceValue = l+w

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
				diff = l+w-referenceValue
				l = l-diff
				# make the new geom
				self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	def onAlignTop(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'align top : ',self.currentSelectedNodeList
		if len(self.currentSelectedNodeList) <= 1:
			return

		# get the node the most on the left
#		referenceValue = None
#		for node in self.currentSelectedNodeList:
#			l,t,w,h = node.getPxGeom()
#			if referenceValue == None or t < referenceValue:
#				referenceNode = node
#				referenceValue = t

		# the reference node is the last selected
		referenceNode = self.currentSelectedNodeList[-1]

		# determinate the reference value		
		l,t,w,h = self.getPxGeomWithContextAnimation(referenceNode)
		referenceValue = t

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
				t = referenceValue
				# make the new geom
				self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	def onAlignMiddle(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'align middle : ',self.currentSelectedNodeList
		if len(self.currentSelectedNodeList) <= 1:
			return

		# get the node the most on the left
#		referenceValue = None
#		for node in self.currentSelectedNodeList:
#			l,t,w,h = node.getPxGeom()
#			if referenceValue == None or l < referenceValue:
#				referenceNode = node
#				referenceValue = t

		# the reference node is the last selected
		referenceNode = self.currentSelectedNodeList[-1]

		# for the reference object, determinate the center
		l,t,w,h = self.getPxGeomWithContextAnimation(referenceNode)
		referenceValue = int(t+h/2)
		
		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
				center = int(t+h/2)
				diff = center-referenceValue
				t = t-diff
				# make the new geom
				self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	def onAlignBottom(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'align bottom : ',self.currentSelectedNodeList
		if len(self.currentSelectedNodeList) <= 1:
			return

		# get the node the most on the left
#		referenceValue = None
#		for node in self.currentSelectedNodeList:
#			l,t,w,h = node.getPxGeom()
#			if referenceValue == None or l < referenceValue:
#				referenceNode = node
#				referenceValue = t

		# the reference node is the last selected
		referenceNode = self.currentSelectedNodeList[-1]

		# for the reference object, determinate the right border
		l,t,w,h = self.getPxGeomWithContextAnimation(referenceNode)
		referenceValue = t+h

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
				diff = t+h-referenceValue
				t = t-diff
				# make the new geom
				self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	def onDistributeHorizontally(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'distribute horizontally : ',self.currentSelectedNodeList
		nodeNumber = len(self.currentSelectedNodeList)
		if nodeNumber <= 2:
			return

		# to determinate the space between min and the max value: referenceMinValue and referenceMaxValue
		# to determinate the somme of node sizes: som
		# sort the elements in the right order (XXX not optimized)
		referenceMinValue = None		
		referenceMaxValue = None
		som = 0
		sortedList = []
		for node in self.currentSelectedNodeList:
			l,t,w,h = self.getPxGeomWithContextAnimation(node)
			if referenceMinValue == None or l < referenceMinValue:
				referenceMinValue = l
			if referenceMaxValue == None or l+w > referenceMaxValue:
				referenceMaxValue = l+w
			som = som+w
			sortedList.append(node)
		self.__sortAttr = 'left'
		sortedList.sort(self.__cmpNode)

		# determinate the space between the different nodes
		space = (referenceMaxValue-referenceMinValue-som)/(nodeNumber-1)
		
		# make a list of node/attr to change
		list = []
		firstNodeRef = sortedList[0]
		l,t,w,h = self.getPxGeomWithContextAnimation(firstNodeRef)
		posRef = l+w
		for nodeRef in sortedList[1:]:
			l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
			l = posRef+space
			posRef = l+w
			# make the new geom
			self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	def onDistributeVertically(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if debugAlign: print 'distribute vertically : ',self.currentSelectedNodeList
		nodeNumber = len(self.currentSelectedNodeList)
		if nodeNumber <= 2:
			return

		# to determinate the space between min and the max value: referenceMinValue and referenceMaxValue
		# to determinate the somme of node sizes: som
		# sort the elements in the right order (XXX not optimized)
		referenceMinValue = None		
		referenceMaxValue = None
		som = 0
		sortedList = []
		for node in self.currentSelectedNodeList:
			l,t,w,h = self.getPxGeomWithContextAnimation(node)
			if referenceMinValue == None or t < referenceMinValue:
				referenceMinValue = t
			if referenceMaxValue == None or t+h > referenceMaxValue:
				referenceMaxValue = t+h
			som = som+h
			sortedList.append(node)
		self.__sortAttr = 'top'
		sortedList.sort(self.__cmpNode)

		# determinate the space between the different nodes
		space = (referenceMaxValue-referenceMinValue-som)/(nodeNumber-1)
		
		# make a list of node/attr to change
		list = []
		firstNodeRef = sortedList[0]
		l,t,w,h = self.getPxGeomWithContextAnimation(firstNodeRef)
		posRef = t+h
		for nodeRef in sortedList[1:]:
			l,t,w,h = self.getPxGeomWithContextAnimation(nodeRef)
			t = posRef+space
			posRef = t+h
			# make the new geom
			self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	# this method will be used by the sort method
	def __cmpNode(self, node1, node2):
		l1,t1,w1,h1 = self.getPxGeomWithContextAnimation(node1)
		l2,t2,w2,h2 = self.getPxGeomWithContextAnimation(node2)
		if self.__sortAttr == 'left':
			if l1 < l2:
				return -1
		elif self.__sortAttr == 'top':
			if t1 < t2:
				return -1
			
		return 1
			
	#
	#
	#

	def onZoomIn(self):
		self.zoomIn()
		
	def onZoomOut(self):
		self.zoomOut()

	def onContent(self):
		if len(self.currentSelectedNodeList) > 0:
			import NodeEdit
			NodeEdit.showeditor(self.currentSelectedNodeList[0])

	def onEnableAnimation(self):
		if len(self.currentSelectedNodeList) > 0:
			selectedNode = self.currentSelectedNodeList[0]
			nodeType = self.getNodeType(selectedNode)
			if USE_NEW_ANIMATECODE:
				animateNode = self.getAnimateNode()
				editmgr = self.editmgr
				if not editmgr.transaction():
					return
				if animateNode is not None:
					# disable animation
					editmgr.delnode(animateNode)
				else:
					# enable animation
					animateNode = self.context.newnode('animpar')
					left, top, width, height = selectedNode.getPxGeom()
					bgcolor = selectedNode.GetInherAttrDef('bgcolor', (0,0,0))
					animateNode.SetAttr('animvals', [(0.0, {'top':top, 'left':left, 'width':width, 'height':height, 'bgcolor':bgcolor}),
														(1.0, {'top':top, 'left':left, 'width':width, 'height':height, 'bgcolor':bgcolor})])
					editmgr.addnode(selectedNode, -1, animateNode)
					
				editmgr.commit()				
				return
			
			animationData = selectedNode.getAnimationData()
			if animationData is None:
				if nodeType == TYPE_MEDIA:
					animationData = selectedNode.computeAnimationData()
#				elif nodeType == TYPE_REGION:
#					animparent = None
#					import win32dialog
#					dlg = win32dialog.SelectElementDlg(self.toplevel.window, self.root, None, filter='node')
#					if dlg.show():
#						animparent = dlg.getmmobject()
#						self.updateFocus(1)
#						return
#					else:
#						# do not create animation
#						self.updateFocus(1)
#						return
#					# XXX save parent
#					selectedNode._animparent = animparent
#					
#					animationData = selectedNode.computeAnimationData(animparent)

			if not self.editmgr.transaction():
				return
					
			if animationData.isEmpty():
				geom = selectedNode.getPxGeom()
				bgcolor = selectedNode.GetInherAttrDef('bgcolor', (0,0,0))
				item1 = geom, bgcolor
				item2 = geom, bgcolor
				# enable animation: just initialize the first and the last value with the current value
				animationData.setTimesData([0.0, 1.0], [item1, item2])
				self.setKeyTimeIndex(0, selectedNode)
			else:
				# disable animation: just remove all datas
				animationData.clear()
				self.setKeyTimeIndex(None, selectedNode)
			selectedNode.applyAnimationData(self.editmgr)
			self.updateFocus(1)
			self.editmgr.commit()

	def onEditProperties(self):
		if len(self.currentSelectedNodeList) > 0:
			self.editProperties(self.currentSelectedNodeList[0])

	def onLayoutProperties(self):
		if len(self.currentSelectedNodeList) > 0:
			self.editProperties(self.currentSelectedNodeList[0])

	def onAnchors(self):
		if len(self.currentSelectedNodeList) > 0:
			self.editProperties(self.currentSelectedNodeList[0])
							
	def onSelectBgColor(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if len(self.currentSelectedNodeList) > 0:
			self.selectBgColor(self.currentSelectedNodeList[0])

	def onSendBack(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if len(self.currentSelectedNodeList) > 0:
			self.sendBack(self.currentSelectedNodeList[0])

	def onBringFront(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if len(self.currentSelectedNodeList) > 0:
			self.bringFront(self.currentSelectedNodeList[0])

	def onShowEditBackground(self, value):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if len(self.currentSelectedNodeList) > 0:
			nodeRef = self.currentSelectedNodeList
			nodeType = self.getNodeType(self.currentSelectedNodeList[0])
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

	def onDelNode(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()

		if not self.editmgr.transaction():
			return
		
		nodeListToDel = self.makeListWithoutRelationShip(self.currentSelectedNodeList)
		newFocus = []
		if len(nodeListToDel) > 0:
			if self.canDel(nodeListToDel):
				for nodeRef in nodeListToDel:
					parent = self.getParentNodeRef(nodeRef)
					if parent != None:
						newFocus = [parent]
					self.editmgr.delchannel(nodeRef)
					self.editmgr.clearRefs(nodeRef)
		self.setglobalfocus(newFocus)
		self.editmgr.commit()
		
	def onNewRegion(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if len(self.currentSelectedNodeList) > 0:
			self.newRegion(self.currentSelectedNodeList[0])

	def onNewViewport(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		self.newViewport()

	# make a list of node that are not relationship
	def makeListWithoutRelationShip(self, nodeList):
		retNodeList = []
		# make a list of node that are not relationship
		for i in nodeList:
			for j in nodeList:
				if j is not i and self.IsAncestorOf(j,i):
					break
			else:
				retNodeList.append(i)
		return retNodeList
				
	# make a list of objects to copy into the clipboard:
	def makeClipboardList(self, isACopy = 1):		
		# make a list of node that are not relationship
		nodeRefList= self.makeListWithoutRelationShip(self.currentSelectedNodeList)
		
		clipList = []
		currentViewportList = self.getViewportRefList()
		# make a list compatible with the clipboard
		for nodeRef in nodeRefList:
			nodeType = self.getNodeType(nodeRef)
			if nodeType == TYPE_MEDIA:
				if isACopy:
					clipList.append(nodeRef.DeepCopy())
				else:
					import MMNode
					node = MMNode.MMRegionAssociation(nodeRef)
					clipList.append(node)
			elif nodeType in (TYPE_REGION, TYPE_VIEWPORT):
				if nodeRef.isDefault():
					msg = "you can't copy or cut the default region"
					windowinterface.showmessage(msg, mtype = 'error')
					return []
				if isACopy:
					clipList.append(nodeRef.DeepCopy())
				elif len(currentViewportList) == 1 and nodeRef is currentViewportList[0]:
					msg = "you can't delete or cut the last viewport"
					windowinterface.showmessage(msg, mtype = 'error')
					return []
				else:
					clipList.append(nodeRef)
		
		return clipList

	def onCopy(self):		
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()

		nodeList = self.makeClipboardList(1)
		if len(nodeList) == 0 or not self.editmgr.transaction():
			return
		
		self.editmgr.setclip(nodeList)
		
		self.editmgr.commit()
		
	def onCut(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()

		nodeList = self.makeClipboardList(0)
		
		if len(nodeList) == 0 or not self.editmgr.transaction():
			return
		
		pnode = None
		for node in nodeList:
			className = node.getClassName()
			if className == 'RegionAssociation':
				mediaNode = node.getMediaNode()
				pnode = self.getParentNodeRef(mediaNode)
				self.editmgr.setnodeattr(mediaNode, 'channel', None)
			elif className in ('Region', 'Viewport'):
				pnode = self.getParentNodeRef(node)
				self.editmgr.delchannel(node)
		if pnode:
			self.setglobalfocus([pnode])
		else:
			self.setglobalfocus([])

		self.editmgr.setclip(nodeList)

		self.editmgr.commit()
				
	def	onPaste(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashes
		self.flushChangement()

		selectedNodeType = None
		if len(self.currentSelectedNodeList) > 0:		
			selectedNode = self.currentSelectedNodeList[0]
			selectedNodeType = self.getNodeType(selectedNode)

		if selectedNode.isDefault():
			# can't insert a node into the default region
			return
		
		if not self.editmgr.transaction():
			return

		nodeList = self.editmgr.getclipcopy()

		newFocus = []
		for node in nodeList:
			className = node.getClassName()

			if className == 'Region':
				if selectedNodeType in (TYPE_REGION, TYPE_VIEWPORT):
					self.editmgr.addchannel(selectedNode, -1, node)
				newFocus.append(node)
			elif className == 'RegionAssociation':
				if selectedNodeType == TYPE_REGION:
					mediaNode = node.getMediaNode()
					self.editmgr.setnodeattr(mediaNode, 'channel', selectedNode.name)					
					newFocus.append(mediaNode)
			elif className == 'Viewport':
				self.editmgr.addchannel(None, -1, node)
				newFocus.append(node)
			
		# update the focus
		self.setglobalfocus(newFocus)
		self.editmgr.commit()

	def newRegion(self, parentRef):
		if parentRef.isDefault():
			# can't insert a node into the default region
			return
		
		# choice a default name which doesn't exist		
		channeldict = self.context.channeldict
		baseName = 'region'
		i = 1
		# XXX to change
		id = baseName + `i`
		while channeldict.has_key(id):
			i = i+1
			id = baseName + `i`
			
#		self.__parentRef = parentRef
#		self.askname(id, 'Name for region', self.__regionNamedCallback)

		self.applyNewRegion(parentRef, id, None)
		self.setglobalfocus([self.nameToNodeRef(id)])
		self.updateFocus()

#		self.editProperties(self.context.getchannel(id))

#	def __regionNamedCallback(self, name):
#		id = name
#		channeldict = self.context.channeldict
#		i = 0
#		while channeldict.has_key(id):
#			i = i+1
#			id = name + `i`
#		if name == id:
#			name = None
#		self.applyNewRegion(self.__parentRef, id, name)
#		self.setglobalfocus([self.nameToNodeRef(id)])
#		self.updateFocus()

	def newViewport(self):
		# choice a default name which doesn't exist		
		channeldict = self.context.channeldict
		baseName = 'TopLayout'
		i = 1
		name = baseName + `i`
		while channeldict.has_key(name):
			i = i+1
			name = baseName + `i`
			
#		self.askname(name, 'Name for TopLayout', self.__viewportNamedCallback)

		self.applyNewViewport(name)
		self.setglobalfocus([self.nameToNodeRef(name)])
		self.updateFocus()

#		self.editProperties(self.context.getchannel(name))

	def __viewportNamedCallback(self, name):
		# check if the viewport already exist
		for viewportRef in self.getViewportRefList():
			if viewportRef.name == name:
				windowinterface.showmessage("A top layout element with the same id already exists", mtype = 'error')
				return
		self.applyNewViewport(name)
		self.setglobalfocus([self.nameToNodeRef(name)])
		self.updateFocus()

	# check if moving a source node into a target node is valid
	def isValidMove(self, sourceNodeRef, targetNodeRef):
		if sourceNodeRef == None or targetNodeRef == None:
			return 0

		if sourceNodeRef.IsAncestorOf(targetNodeRef) or sourceNodeRef is targetNodeRef:
			return 0
				
		targetNodeType = self.getNodeType(targetNodeRef)
		# for now, accept only moving if the target node is viewport or region
		if targetNodeType not in (TYPE_VIEWPORT, TYPE_REGION):
			return 0

		sourceNodeType = self.getNodeType(sourceNodeRef)
		# for now, moving a viewport is forbidden
		if sourceNodeType == TYPE_VIEWPORT:
			return 0

		if sourceNodeType == TYPE_MEDIA and targetNodeType != TYPE_REGION:
			return 0

		if targetNodeType == TYPE_REGION and targetNodeRef.isDefault():
			# you can't move anything into the default region
			return 0
		if sourceNodeType == TYPE_REGION and sourceNodeRef.isDefault():
			# you can't move the default region
			return 0
		
		return 1

	# move the source node into a target node
	def moveNode(self, sourceNodeRef, targetNodeRef):
		if not self.isValidMove(sourceNodeRef, targetNodeRef):
			return None
		
		sourceNodeType = self.getNodeType(sourceNodeRef)
		targetNodeType = self.getNodeType(targetNodeRef)
		
		if sourceNodeType == TYPE_MEDIA and targetNodeType == TYPE_REGION:
			if self.editmgr.transaction():
				self.editmgr.setnodeattr(sourceNodeRef, 'channel', targetNodeRef.name)
				self.editmgr.commit('REGION_TREE')
		elif targetNodeType in (TYPE_REGION, TYPE_VIEWPORT):
			if self.editmgr.transaction():
				self.editmgr.delchannel(sourceNodeRef)
				self.editmgr.addchannel(targetNodeRef, -1, sourceNodeRef)
#				self.editmgr.setchannelattr(sourceNodeRef.name, 'base_window', targetNodeRef.name)
				self.editmgr.commit('REGION_TREE')

		return 'move'

	def getShowEditBackgroundMode(self, nodeRef):
		return nodeRef.GetInherAttrDef('showEditBgMode', 'normal')
	
	def getPreviewOption(self, nodeRef, nodeType):
		# the default value is node type dependent
		if nodeType == TYPE_MEDIA:
			return nodeRef.GetAttrDef('previewShowOption', 'onSelected')
		elif nodeType in (TYPE_VIEWPORT, TYPE_REGION):
			return nodeRef.GetAttrDef('previewShowOption', 'always')

	def isSelected(self, nodeRef):
		for n in self.currentSelectedNodeList:
			if n is nodeRef:
				return 1
		return 0

	def isAVisibleNode(self, nodeRef, nodeType):
		if nodeType == TYPE_REGION:
			if nodeRef.isDefault():
				return 0
			type = nodeRef.GetAttrDef('chsubtype', None)
			if type != None:
				# if the region is typed, we show only the region if visible
				import ChannelMap
				if not ChannelMap.isvisiblechannel(type):
					return  0
		elif nodeType == TYPE_MEDIA:
			type = nodeRef.GetChannelType()
			import ChannelMap
			if not ChannelMap.isvisiblechannel(type):
				return  0
			parentNodeRef =  self.getParentNodeRef(nodeRef)
			if parentNodeRef is None or parentNodeRef.isDefault():
				return 0
			
		return 1
			
	def getVisibility(self, nodeRef, nodeType, selected):		
		optionValue = self.getPreviewOption(nodeRef, nodeType)
		if (optionValue == 'always' or (optionValue == 'onSelected' and selected)) and \
			self.isAVisibleNode(nodeRef, nodeType):
			return 1
		else:
			return 0
		
	def setPreviewShowOptions(self, nodeRefList, optionValue):
		editmgr = self.editmgr
		if not editmgr.transaction():
			return
		list = []
		for nodeRef in nodeRefList:
			nodeType = self.getNodeType(nodeRef)
			if self.isAVisibleNode(nodeRef, nodeType):
				list.append(nodeRef)
				if optionValue == 'onSelected':
					# set value as well on all children recursivly
					children = self.getAllChildren(nodeRef)
					list = list+children
				elif optionValue == 'always':
					# set value as well on all parents
					parents = self.getAllParent(nodeRef)
					list = list+parents

		# update the visibility
		if optionValue == 'onSelected':
			status = 0
		else:
			status = 1
		self.updateVisibility(list, status)
		
		for nodeRef in list:
			nodeType = self.getNodeType(nodeRef)
			# the default value is node type dependent
			if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
				if optionValue == 'onSelected':
					value = 'onSelected'
				else:
					value = None
				editmgr.setchannelattr(nodeRef.name, 'previewShowOption', value)
			elif nodeType == TYPE_MEDIA:
				if optionValue == 'always':
					value = 'always'
				else:
					value = None		
				editmgr.setnodeattr(nodeRef, 'previewShowOption', value)

			if optionValue == 'onSelected':
				# if the item is selected, unselected it for consistence purpose
				for nodeRefSel in self.currentSelectedNodeList:
						if nodeRef is nodeRefSel:
							self.editmgr.delglobalfocus([nodeRef])
				
		self.previousWidget.mustBeUpdated()
		editmgr.commit()

	# checking if the region/viewport node contains any sub-region or media
	def isEmpty(self, nodeRef):
		# checking if has sub-region
		children = self.treeHelper.getChildren(nodeRef)
		if children != None:
			return len(children) == 0
		return 1

	# checking if the region/viewport or sub-regions contain any media
	def doesContainMedias(self, nodeRef):
		if self.getNodeType(nodeRef) == TYPE_MEDIA:
			return 1
		children = self.getChildren(nodeRef)
		for child in children:
			if self.doesContainMedias(child):
				return 1

		return 0

	def canDel(self, nodeListToDel):
		currentViewportList = self.getViewportRefList()
		viewportToDel = []
		error = 0
		for nodeRef in nodeListToDel:
			nodeType = self.getNodeType(nodeRef)
			if nodeType == TYPE_VIEWPORT:
				viewportToDel.append(nodeRef)
				if len(currentViewportList) == len(viewportToDel):
					error = 4
					break
			if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
				if nodeRef.isDefault():
					if error < 2:
						error = 2
				if self.doesContainMedias(nodeRef):
					if error < 1:
						error = 1
			elif nodeType == TYPE_MEDIA:
				if error < 3:
					error = 3

		if error == 4:
			# show in priority that error
			windowinterface.showmessage("you can't delete the last viewport", mtype = 'error')
		elif error == 3:
			windowinterface.showmessage("You can't remove any media from the Layout view.\n Use Cut/Paste or Drag/Drop to move a media.", mtype = 'error')
		elif error == 2:
			windowinterface.showmessage("You can't remove the default region", mtype = 'error')
		elif error == 1:
			ret = windowinterface.GetOKCancel("At least one item that you want to remove contains some medias. Do you want to continue ?", self.toplevel.window)
			if ret == 0:
				# ok
				error = 0

		return error == 0
			
	def onFastGeomUpdate(self, nodeRef, geom):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			self.geomFieldWidget.updateViewportGeom(geom)
		elif nodeType == TYPE_REGION:
			self.geomFieldWidget.updateRegionGeom(geom)
		elif nodeType == TYPE_MEDIA:
			self.geomFieldWidget.updateMediaGeom(geom)

	# called from any widget belong to this view
	def onSelectChanged(self, nodeRefList, keepShowedNodes=1):
		# XXX in the case, if the focus is change from the tree widget, the focus in the control field is not updated.
		# So we have to force any apply.
		self.flushChangement()
		
		self.setglobalfocus(nodeRefList)

		self.updateFocus(keepShowedNodes)

	# called from any widget belong to this view
	# selected update nodes handler method
	# state = 1 means: add into selected list
	# state = 0 means: remove from selected list
	def onSelectUpdated(self, nodeRefList, state, keepShowedNodes=1):
		# XXX in the case, if the focus is change from the tree widget, the focus in the control field is not updated.
		# So we have to force any apply.
		self.flushChangement()

		if state:
			self.editmgr.addglobalfocus(nodeRefList)
		else:
			self.editmgr.delglobalfocus(nodeRefList)
		self.currentFocus = self.editmgr.getglobalfocus()
		self.makeSelectedNodeList(self.currentFocus)
		self.updateFocus(keepShowedNodes)
					
#
# common class for all widgets
#

class Widget:
	def __init__(self, context):
		self._context = context

	#
	# overrided methods
	#
	
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		pass

	def onSelecterChanged(self, ctrlName, value):
		pass

	def show(self):
		pass

	def destroy(self):
		pass

	def startMutation(self):
		pass

	def endMutation(self):
		pass
	
#
# common class for light widget
#
		
class LightWidget(Widget):
	def __init__(self, context):
		Widget.__init__(self, context)
		self._context = context
		self.dialogCtrl = context.dialogCtrl

	def getSingleSelection(self, nodeRefList):
		if len(nodeRefList) != 1:
			# if no node selected or several nodes are selected in the same time, disable the fields
			return 0, None
		nodeRef = nodeRefList[0]
		nodeType = self._context.getNodeType(nodeRef)

		if not self._context.isAVisibleNode(nodeRef, nodeType):
			return 0, None
			
		return nodeType, nodeRef

	def onCheckCtrl(self, ctrlName, value):
		pass
		
#
# z field widget management
#

class ZFieldWidget(LightWidget):
	#
	# inherited methods
	#
	
	def show(self):
		self.dialogCtrl.setListener('RegionZ', self)

	def destroy(self):
		self.dialogCtrl.removeListener('RegionZ')
		
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		nodeType, nodeRef = self.getSingleSelection(nodeRefList)
		
		if nodeType == TYPE_VIEWPORT:
			self.dialogCtrl.enable('RegionZ',0)
			self.dialogCtrl.setFieldCtrl('RegionZ',"")
		elif nodeType == TYPE_REGION:
			self.dialogCtrl.enable('RegionZ',1)		
			z = nodeRef.GetAttrDef('z', 0)
			self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)		
		elif nodeType == TYPE_MEDIA:
			self.dialogCtrl.enable('RegionZ',1)
			z = nodeRef.GetAttrDef('z', 0)
			self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)
		else:
			self.__unselect()

	# update the dialog box on unselection
	def __unselect(self):
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"")

	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onFieldCtrl(self, ctrlName, value):
		if ctrlName == 'RegionZ':
			try:
				value = int(value)
			except:
				value = 0
			self.__onZOrderChanged(value)

	def __onZOrderChanged(self, value):
		if len(self._context.currentSelectedNodeList)  > 0:
			nodeRef = self._context.currentSelectedNodeList[0]
			nodeType = self._context.getNodeType(nodeRef)
			if nodeType == TYPE_REGION:
				self._context.applyZOrderOnRegion(nodeRef, value)
			elif nodeType == TYPE_MEDIA:
				self._context.applyZOrderOnMedia(nodeRef, value)

#
# z field widget management
#

class FitWidget(LightWidget):
	#
	# inherited methods
	#

	showedValues = ['show whole media', 'actual size', 'fill whole region', 'scroll media if necessary', 'show whole media in whole region']
	fitValues = ['meet', 'hidden', 'slice', 'scroll', 'fill']
	
	def show(self):
		self.dialogCtrl.setListener('Fit', self)
		self.dialogCtrl.fillSelecterCtrl('Fit', self.showedValues)
		self._selected = None

	def destroy(self):
		self.dialogCtrl.removeListener('Fit')
		
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		nodeType, nodeRef = self.getSingleSelection(nodeRefList)
		self._selected = (nodeType, nodeRef)

		if nodeType == TYPE_VIEWPORT:
			self.__unselect()
		elif nodeType == TYPE_REGION:
			self.__update(nodeRef, nodeType)
		elif nodeType == TYPE_MEDIA:
			self.__update(nodeRef, nodeType)
		else:
			self.__unselect()

	# update the dialog box on unselection
	def __unselect(self):
		self.dialogCtrl.enable('Fit',0)
		self.dialogCtrl.setSelecterCtrl('Fit',-1)
		self.dialogCtrl.setLabel('FitLabel','Fit')

	# update the dialog box on valid selection
	def __update(self, nodeRef, nodeType):
		if nodeType == TYPE_REGION:
			self.dialogCtrl.setLabel('FitLabel','Default fit')
			fit = nodeRef.GetAttrDef('fit', 'hidden')
			self.__currentShowedValues = self.showedValues
			index = self.fitValues.index(fit)
		elif nodeType == TYPE_MEDIA:
			self.dialogCtrl.setLabel('FitLabel','Fit')
			fit = nodeRef.GetAttrDef('fit', None)
			region = self._context.getParentNodeRef(nodeRef)
			defaultFit = region.GetAttrDef('fit', 'hidden')
			defaultIndex = self.fitValues.index(defaultFit)
			if fit is None:
				index = 0
			else:
				index = self.fitValues.index(fit)+1
			self.__currentShowedValues = ['default ['+self.showedValues[defaultIndex]+']']+self.showedValues
			
		self.dialogCtrl.fillSelecterCtrl('Fit', self.__currentShowedValues)		
		self.dialogCtrl.setSelecterCtrl('Fit',index)
		self.dialogCtrl.enable('Fit',1)
		
	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onSelecterChanged(self, ctrlName, value):
		nodeType, nodeRef = self._selected
		if nodeType == TYPE_MEDIA:
			if value == 0:
				fit = None
			else:
				fit = self.fitValues[value-1]
		else:
			fit = self.fitValues[value]
			
		self._context.applyFit(nodeRef, fit)
		
#
# geom field widget management
#
		
class GeomFieldWidget(LightWidget):	
	#
	# inherited methods
	#

	def show(self):
		self.dialogCtrl.setListener('RegionX', self)
		self.dialogCtrl.setListener('RegionY', self)
		self.dialogCtrl.setListener('RegionW', self)
		self.dialogCtrl.setListener('RegionH', self)

	def destroy(self):
		self.dialogCtrl.removeListener('RegionX')
		self.dialogCtrl.removeListener('RegionY')
		self.dialogCtrl.removeListener('RegionW')
		self.dialogCtrl.removeListener('RegionH')
	
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		nodeType, nodeRef = self.getSingleSelection(nodeRefList)
				
		if nodeType == TYPE_VIEWPORT:
			self.__updateViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			self.__updateRegion(nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.__updateMedia(nodeRef)
		else:
			self.__unselect()
			
	#
	#
	#
			
	def __unselect(self):
		self.__updateUnselected()						
	
	def __updateMediaGeom(self, geom):
		self.updateRegionGeom(geom)

	def __updateUnselected(self):
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.enable('RegionW',0)
		self.dialogCtrl.enable('RegionH',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
		self.dialogCtrl.setFieldCtrl('RegionW',"")		
		self.dialogCtrl.setFieldCtrl('RegionH',"")
			
	def __updateViewport(self, nodeRef):
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
		
		w,h = nodeRef.getPxGeom()
		geom = 0,0,w,h
		self.updateViewportGeom(geom)				

	def updateViewportGeom(self, geom):
		# update the fields dialog box
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])
		
	def __updateRegion(self, nodeRef):
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)

		geom = self._context.getPxGeomWithContextAnimation(nodeRef)
		self.updateRegionGeom(geom)
		
	def updateRegionGeom(self, geom):
		self.dialogCtrl.setFieldCtrl('RegionX',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionY',"%d"%geom[1])		
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])
		
	def __updateMedia(self, nodeRef):
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionW',1)
		self.dialogCtrl.enable('RegionH',1)
		
		geom = self._context.getPxGeomWithContextAnimation(nodeRef)
		self.updateMediaGeom(geom)
						
	def updateMediaGeom(self, geom):
		self.updateRegionGeom(geom)
				
	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onFieldCtrl(self, ctrlName, value):
		if ctrlName in ('RegionX','RegionY','RegionW','RegionH'):
			try:
				value = int(value)
			except:
				value = None

			selectedNode = self._context.currentSelectedNodeList[0]
			if selectedNode != None:
				nodeType = self._context.getNodeType(selectedNode)
				if nodeType == TYPE_VIEWPORT:
					self.__onGeomOnViewportChanged(ctrlName, value)
				elif nodeType == TYPE_REGION:
					self.__onGeomOnRegionChanged(ctrlName, value)
				elif nodeType == TYPE_MEDIA:
					self.__onGeomOnMediaChanged(ctrlName, value)

	def __onGeomOnViewportChanged(self, ctrlName, value):
		if len(self._context.currentSelectedNodeList) > 0:
			nodeRef = self._context.currentSelectedNodeList[0]
			w,h = nodeRef.getPxGeom()
			if ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			self._context.applyGeom(nodeRef, (0,0,w,h))

	def __onGeomOnRegionChanged(self, ctrlName, value):
		if len(self._context.currentSelectedNodeList) > 0:		
			nodeRef = self._context.currentSelectedNodeList[0]
			x,y,w,h = self._context.getPxGeomWithContextAnimation(nodeRef)
			if ctrlName == 'RegionX':
				x = value
			elif ctrlName == 'RegionY':
				y = value			
			elif ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value			
			self._context.applyGeom(nodeRef, (x,y,w,h))

	def __onGeomOnMediaChanged(self, ctrlName, value):
		if len(self._context.currentSelectedNodeList) > 0:
			nodeRef = self._context.currentSelectedNodeList[0]
			x,y,w,h = self._context.getPxGeomWithContextAnimation(nodeRef)
			if ctrlName == 'RegionX':
				x = value
			elif ctrlName == 'RegionY':
				y = value			
			elif ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			self._context.applyGeom(nodeRef, (x,y,w,h))

class AnimateControlWidget(LightWidget):		
	#
	# inherited methods
	#

	def show(self):
		self._selected = (0, None)
		self.isEnabled = 0
		self.__selecting = 0
		self.__enabling = 0
		self.sliderCtrl = self._context.keyTimeSliderCtrl
		self.sliderCtrl.enable(self.isEnabled)
		self.sliderCtrl.setListener(self)

		self.dialogCtrl.setListener('AnimateEnable', self)

	def destroy(self):
		self.sliderCtrl.removeListener()
		self.dialogCtrl.removeListener('AnimateEnable')
	
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		nodeType, nodeRef = self.getSingleSelection(nodeRefList)
		self._selected = (nodeType, nodeRef)
		
		if nodeType == TYPE_MEDIA:
			self.dialogCtrl.enable('AnimateEnable',1)
			self.__updateNode(nodeRef)
		else:
			self.dialogCtrl.enable('AnimateEnable',0)
			self.__updateUnselected()
		
	#
	#
	#
				
	def __updateUnselected(self):
		self.isEnabled = 0
		self.sliderCtrl.setKeyTimes([0.0, 1.0])		
		self.sliderCtrl.setCursorPos(0)
		self.sliderCtrl.enable(0)
		self.dialogCtrl.setCheckCtrl('AnimateEnable',0)
	
	def __updateViewport(self, nodeRef):
		self.__updateUnselected()
			
	def __updateNode(self, nodeRef):
		if USE_NEW_ANIMATECODE:
			animateNode = self._context.getAnimateNode()
			if animateNode is None or animateNode.GetType() != 'animpar':
				self.__updateUnselected()
				return

			if animateNode.GetType() == 'animpar':
				animvals = animateNode.GetAttrDef('animvals', [])
				keyTimeList = []
				for time, vals in animvals:
					keyTimeList.append(time)
			else:
				# no key time
				keyTimeList = None
		else:
			animationData = nodeRef.getAnimationData()
			if animationData is None or animationData.isEmpty():
				self.__updateUnselected()
				return
			times = animationData.getTimes()
			keyTimeList = []
			for time in times:
				keyTimeList.append(time)
			
		self.sliderCtrl.setKeyTimes(keyTimeList)
		timeIndex = self._context.getKeyTimeIndex()
		timeValue = self._context.getCurrentTimeValue()
		self.__selecting = 1
		self.sliderCtrl.selectKeyTime(timeIndex)
		if not timeIndex is None and timeIndex >= 0:
			list = self.sliderCtrl.getKeyTimes()
			self.sliderCtrl.setCursorPos(list[timeIndex])
		elif not timeValue is None:
			self.sliderCtrl.selectKeyTime(timeValue)			
		self.__selecting = 0
	
		self.isEnabled = 1
		self.sliderCtrl.enable(1)
		self.dialogCtrl.setCheckCtrl('AnimateEnable',1)
		
	def insertKey(self, time):
		if self.isEnabled:
			self.sliderCtrl.insertKeyTime(time)

	def removeKey(self, index):
		if self.isEnabled:
			self.sliderCtrl.removeKeyTimeAtIndex(index)
			newIndex = self._context.getKeyTimeIndex()
			list = self.sliderCtrl.getKeyTimes()
			self.sliderCtrl.setCursorPos(list[newIndex])
			self.sliderCtrl.selectKeyTime(newIndex)
		
	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onInsertKey(self, tp, duplicateKey=None):
		if self.isEnabled:
			nodeType, nodeRef = self._selected
			editmgr = self._context.editmgr
			if not editmgr.transaction():
				return -1
			self._context.insertKeyTime(nodeRef, tp, duplicateKey)
			if not USE_NEW_ANIMATECODE:
				nodeRef.applyAnimationData(editmgr)
			editmgr.commit()
			
	def onRemoveKey(self, index):
		if self.isEnabled:
			if USE_NEW_ANIMATECODE:
				nodeType, nodeRef = self._selected
				editmgr = self._context.editmgr
				if not editmgr.transaction():
					return -1
				index = self._context.removeKeyTime(nodeRef, index)
				editmgr.commit()
			else:
				nodeType, nodeRef = self._selected
				animationData = nodeRef.getAnimationData()
				timeList = animationData.getTimes()
				if index > 0 and index < len(timeList)-1:
					# can only remove a key between the first and the end
					data = animationData.getData()
					if index < len(timeList):
						editmgr = self._context.editmgr
						if not editmgr.transaction():
							return
						animationData.eraseTimeData(index)
						self.sliderCtrl.removeKeyTimeAtIndex(index)
						self._context.setKeyTimeIndex(index-1, nodeRef)
						list = self.sliderCtrl.getKeyTimes()
						self.sliderCtrl.setCursorPos(list[index-1])
						self.sliderCtrl.selectKeyTime(index-1)
						nodeRef.applyAnimationData(editmgr)
						editmgr.commit()			
					
	def onSelected(self, index):
		if self.isEnabled and not self.__selecting:
			nodeType, nodeRef = self._selected
			self._context.setKeyTimeIndex(index, nodeRef)
			list = self.sliderCtrl.getKeyTimes()
			self.sliderCtrl.setCursorPos(list[index])
			self._context.updateFocus(1)

	def onCursorPosChanged(self, pos):
		if self.isEnabled:
			nodeType, nodeRef = self._selected
			self._context.setCurrentTimeValue(pos, nodeRef)
			if USE_NEW_ANIMATECODE:
				animateNode = self._context.getAnimateNode()
				animvals = animateNode.GetAttrDef('animvals', [])
				keyTimeIndex = self._context.getKeyForThisTime(animvals, pos)
			else:
				animationData = nodeRef.getAnimationData()
				timeList = animationData.getTimes()
				keyTimeIndex = self._context.getKeyForThisTime(timeList, pos)
			if keyTimeIndex is not None and keyTimeIndex >= 0:
				self.sliderCtrl.selectKeyTime(keyTimeIndex)
			else:
				self.sliderCtrl.selectKeyTime(-1)
			previewWidget = self._context.previousWidget
			if previewWidget is not None:
				previewWidget.fastUpdate()
			context = self._context
			context.onFastGeomUpdate(nodeRef, context.getPxGeomWithContextAnimation(nodeRef))

	def onKeyTimeChanged(self, index, time):
		if self.isEnabled:
			nodeType, nodeRef = self._selected
			editmgr = self._context.editmgr
			if not editmgr.transaction(editmgr):
				return

			if USE_NEW_ANIMATECODE:
				animateNode = self._context.getAnimateNode()
				animvals = animateNode.GetAttrDef('animvals', [])
				oldtime, vals = animvals[index]
				animvals[index] = (time, vals)
				editmgr.setnodeattr(animateNode, 'animvals', animvals)
			else:
				animationData = nodeRef.getAnimationData()
				animationData.updateTime(index, time)
				nodeRef.applyAnimationData(editmgr)
				
			self._context.setCurrentTimeValue(time, nodeRef)
			editmgr.commit()

	def onKeyTimeChanging(self, time):
		if self.isEnabled:
			self.sliderCtrl.setCursorPos(time)
			
					
	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onCheckCtrl(self, ctrlName, value):
		if self.__enabling or ctrlName != 'AnimateEnable': return
		self.__enabling = 1
		self._context.onEnableAnimation()
		self.__enabling = 0

#
# tree widget management
#

class TreeWidget(Widget):
	def __init__(self, context):
		self.nodeRefToNodeTreeCtrlId = {}
		self.nodeTreeCtrlIdToNodeRef = {}
		self._context = context
		self.treeCtrl = context.treeCtrl
	#
	# inherited methods
	#

	def show(self):
		self.treeCtrl.setListener(self)

	def destroy(self):
		self.treeCtrl.removeListener()
		self.treeCtrl.destroy()
			
	#		
	# tree mutation operations
	#

	# currently, the expand operation can be done only at the end of the mutation (windows api issue)
	# so, we register in this method the node to expand according to the GRiNS property
	# expand stored in the node. The expand operation will be done at the end of the tree mutation
	# note: in the current tree widget implementation all new nodes are by default collapsed
	def startMutation(self):
		self.__nodeRefListToExpand = []

	def endMutation(self):
		expandMediaNode = 0
		# do expand operations
		for nodeRef in self.__nodeRefListToExpand:
			if nodeRef.collapsed == 0:
				expand = 1
			elif nodeRef.collapsed == 1:
				expand = 0
			else:
				# default behavior: expand node only if contains region inside
				hasNotOnlyMedia = 0
				nodeType = self._context.getNodeType(nodeRef)
				children = self._context.getChildren(nodeRef)
				if not expandMediaNode and children != None:
					# expand only this node if there is a region inside
					for child in children:
						if not self._context.getNodeType(child) == TYPE_MEDIA:
							hasNotOnlyMedia = 1
	
				if not (hasNotOnlyMedia or expandMediaNode):
					expand = 0
					nodeRef.collapsed = 1
				else:
					expand = 1
					nodeRef.collapsed = 0

			if expand:				
				self.treeCtrl.expand(self.nodeRefToNodeTreeCtrlId[nodeRef])
		# clear the list		
		self.__nodeRefListToExpand = []

	def _appendItem(self, pNodeRef, nodeRef, tp):
		iconname = nodeRef.getIconName(wantmedia=1)
		name = self._context.getShowedName(nodeRef, tp)
		if pNodeRef is None:
			idx = 0
		else:
			idx = self.nodeRefToNodeTreeCtrlId[pNodeRef]
		ret = self.treeCtrl.insertNode(idx, name, iconname, iconname)
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef
		
	def appendNode(self, pNodeRef, nodeRef, nodeType):
		self._appendItem(pNodeRef, nodeRef, nodeType)
		
		if not nodeType in CHILD_TYPE:
			# save the new node for expand. The expand operation can't be done here
			self.__nodeRefListToExpand.append(nodeRef)

		if nodeType in (TYPE_VIEWPORT, TYPE_REGION, TYPE_MEDIA):
			visible = self._context.getVisibility(nodeRef, nodeType, selected=0)
			self.updateVisibility([nodeRef], visible)
					
	def removeNode(self, nodeRef, nodeType):
		nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
		if nodeTreeCtrlId != None:
			self.treeCtrl.removeNode(nodeTreeCtrlId)
			del self.nodeRefToNodeTreeCtrlId[nodeRef]
			del self.nodeTreeCtrlIdToNodeRef[nodeTreeCtrlId]
				

	#
	#
	#
	
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		list = []
		for nodeRef in nodeRefList:
			nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
			if nodeTreeCtrlId != None:
				list.append(nodeTreeCtrlId)
		self.treeCtrl.selectNodeList(list)

		# update popup menu according to the last item selected
		if len(nodeRefList) == 1:
			lastNodeRef = nodeRefList[-1]
			nodeType = self._context.getNodeType(lastNodeRef)
			import MenuTemplate
			if nodeType == TYPE_VIEWPORT:
				self.treeCtrl.setpopup(MenuTemplate.POPUP_REGIONTREE_TOPLAYOUT)
			elif nodeType == TYPE_REGION:
				self.treeCtrl.setpopup(MenuTemplate.POPUP_REGIONTREE_REGION)
			elif nodeType == TYPE_MEDIA:
				self.treeCtrl.setpopup(MenuTemplate.POPUP_REGIONTREE_MEDIA)
		else:
			self.treeCtrl.setpopup(None)

	#
	#
	#

	def __unselect(self):
		# todo
		pass
	
	def updateNode(self, nodeRef):
		nodeType = self._context.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			type = nodeRef.GetChannelType()
			name = self._context.getShowedName(nodeRef, TYPE_MEDIA)
		elif nodeType == TYPE_REGION:
			type = 'region'
			name = self._context.getShowedName(nodeRef, TYPE_REGION)
		else:
			type = 'viewport'
			name = self._context.getShowedName(nodeRef, TYPE_VIEWPORT)
		if name == None:
			name=''
		self.treeCtrl.updateNode(self.nodeRefToNodeTreeCtrlId[nodeRef], name, type, type)
		selected = self._context.isSelected(nodeRef)
		visible = self._context.getVisibility(nodeRef, nodeType, selected=selected)
		self.updateVisibility([nodeRef], visible)
		
	# selected node handler method
	def onSelectChanged(self, nodeTreeCtrlIdList):
		nodeRefList = []
		for nodeTreeCtrlId in nodeTreeCtrlIdList:
			nodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
			nodeRefList.append(nodeRef)
		# update the selection
		self._context.onSelectChanged(nodeRefList, 0)

	# selected update node handler method
	# state = 1 means: add into selected list
	# state = 0 means: remove from selected list
	def onSelectUpdated(self, nodeTreeCtrlIdList, state):
		nodeRefList = []
		for nodeTreeCtrlId in nodeTreeCtrlIdList:
			nodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
			nodeRefList.append(nodeRef)
		# update the selection
		self._context.onSelectUpdated(nodeRefList, state)

	# the image state (check box) has changed
	# state = 0 means: check box unselected
	# state = 1 means: check box selected
	def onStateActivated(self, nodeTreeCtrlId, state):
		nodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		if nodeRef:
			if state == 'hidden' or state == 'showed':
				self._context.setPreviewShowOptions([nodeRef], 'always')
			elif state == 'locked':
				self._context.setPreviewShowOptions([nodeRef], 'onSelected')

	def updateVisibility(self, nodeRefList, visible):
		for nodeRef in nodeRefList:
			nodeTreeCtrlIdList = []
			nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
			if nodeTreeCtrlId != None:
				nodeTreeCtrlIdList.append(nodeTreeCtrlId)
			nodeType = self._context.getNodeType(nodeRef)
			previewOption = self._context.getPreviewOption(nodeRef, nodeType)
			if visible and previewOption == 'always':
				self.treeCtrl.setStateNodeList(nodeTreeCtrlIdList, 'locked')
			elif visible:
				self.treeCtrl.setStateNodeList(nodeTreeCtrlIdList, 'showed')
			else:
				self.treeCtrl.setStateNodeList(nodeTreeCtrlIdList, 'hidden')
							  			
	def onExpanded(self, nodeTreeCtrlId, isExpanded):
		nodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		if nodeRef:
			nodeType = self._context.getNodeType(nodeRef)
			if nodeType != TYPE_MEDIA:
				# XXX for now store information without commit or other mechanism
				if not isExpanded:
					nodeRef.collapsed = 1
				else:
					nodeRef.collapsed = 0
		
	def expandNodes(self, nodeRef, expandMediaNode):
		hasNotOnlyMedia = 0
		nodeType = self._context.getNodeType(nodeRef)
		children = self._context.getChildren(nodeRef)
		if not expandMediaNode and children != None:
			# expand only this node if there is a region inside
			for child in children:
				if self._context.getNodeType(child) != TYPE_MEDIA:
					hasNotOnlyMedia = 1
		if nodeType != TYPE_MEDIA and (hasNotOnlyMedia or expandMediaNode):
			self.treeCtrl.expand(self.nodeRefToNodeTreeCtrlId[nodeRef])
			for child in children:
				if self._context.getNodeType(child) != TYPE_MEDIA:
					self.expandNodes(child, expandMediaNode)
		
	# expand all region nodes
	# by default, don't make visible the media nodes
	def expandAllNodes(self, expandMediaNode):
		rootNodeList = self._context.treeHelper.getRootNodeList()
		for node in rootNodeList:
			self.expandNodes(node, expandMediaNode)

	#
	# drag and drop support
	#
	
	def onBeginDrag(self, nodeTreeCtrlId):
		# the object id allows to idenfify any object (known by any view) 
		nodeRef= self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		nodeType = self._context.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			# XXX define type in another module
			type = 'Media'
			objectId = nodeRef.GetUID()
		elif nodeType in (TYPE_VIEWPORT, TYPE_REGION):
			# XXX define type in another module
			type = 'Region'
			# XXX the GetUID seems bugged, so we use directly the region Id as global id for now
			objectId = nodeRef.name
		elif nodeType == TYPE_ANIMATE:
			type = 'Animate'
			objectId = nodeRef.GetUID()
		self.treeCtrl.beginDrag(type, objectId)

	def __dragObjectIdToNodeRef(self, type, objectId):
		nodeRef = None
		if type == 'Media': 
			# retrieve the reference of the source node
			try:
				nodeRef = self._context.context.mapuid(objectId)
			except:
				pass
						
		elif type == 'Region':
			# retrieve the reference of the source node
			nodeRef = self._context.context.getchannel(objectId)
		return nodeRef			
		
	def onDragOver(self, nodeTreeCtrlId, type, objectId):
		targetNodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		if type == 'Tool':
			if objectId == DRAG_TOPLAYOUT:
				# Viewports can only be dragged to "nowhere"
				if targetNodeRef == None:
					return 'copy'
			elif objectId == DRAG_REGION:
				# Regions can be dragged to viewports or regions
				if targetNodeRef and \
						targetNodeRef.getClassName() != 'MMNode':
					return 'copy'
			# Otherwise we can't drop it here.
			return None
		elif type in ('Region', 'Media'):
			sourceNodeRef = self.__dragObjectIdToNodeRef(type, objectId)
			if self._context.isValidMove(sourceNodeRef, targetNodeRef):
				return 'move'
		return None

	def onDrop(self, nodeTreeCtrlId, type, objectId):
		targetNodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		if type == 'Tool':
			if objectId == DRAG_TOPLAYOUT:
				# Viewports can only be dragged to "nowhere"
				if targetNodeRef == None:
					self._context.flushChangement() # XXXX Is this needed?
					self._context.newViewport()
					return 'copy'
			elif objectId == DRAG_REGION:
				# Regions can be dragged to viewports or regions
				if targetNodeRef and \
						targetNodeRef.getClassName() != 'MMNode':
					self._context.flushChangement() # XXXX Is this needed?
					self._context.newRegion(targetNodeRef)
					return 'copy'
			# Otherwise we can't drop it here.
			return None
		elif type in ('Region', 'Media'):
			sourceNodeRef = self.__dragObjectIdToNodeRef(type, objectId)
			return self._context.moveNode(sourceNodeRef, targetNodeRef)
						   
class PreviousWidget(Widget):
	def __init__(self, context):
		self._viewports = {}
		self._nodeRefToNodeTree = {}
		self._context = context

		# current state
		self.currentViewport = None		

		self.previousCtrl = self._context.previousCtrl

		# to prevent against indefite loop
		self.__selecting = 0
		
		self.__mustBeUpdated = 1
		self._cssResolver =  SMILCssResolver(self._context.context)

	#
	# inherited methods
	#
	
	def show(self):
		# show the first viewport in the list		
		currentViewportList = self._context.getViewportRefList()
		viewport = currentViewportList[0]
		self.displayViewport(viewport)
		self.previousCtrl.setListener(self)

	def destroy(self):
		self.previousCtrl.removeListener()
		if self.currentViewport != None:
			self.currentViewport.hideAllNodes()
			self.currentViewport = None

		self.previousCtrl = None

	def updateVisibility(self, nodeRefList, visible):
		for nodeRef in nodeRefList:
			nodeType = self._context.getNodeType(nodeRef)
			if visible:
				if nodeType == TYPE_REGION:
					self.__showRegion(nodeRef)
				elif nodeType == TYPE_MEDIA:
					self.__showMedia(nodeRef)
			else:
				if nodeType == TYPE_REGION:
					self.__hideRegion(nodeRef)
				elif nodeType == TYPE_MEDIA:
					self.__hideMedia(nodeRef)

	def update(self):
		if self.__mustBeUpdated:
			self.updateRegionTree()
			self.__mustBeUpdated = 0
					   
	def selectNodeList(self, nodeRefList, keepShowedNodes):
		# to prevent against indefite loop
		self.__selecting = 1

		# show the right selected nodes if need
		listToShow = []
		for nodeRef in nodeRefList:			
			nodeType = self._context.getNodeType(nodeRef)
			visible = self._context.getVisibility(nodeRef, nodeType, selected=1)
			if visible:
				listToShow.append(nodeRef)
		self.updateVisibility(listToShow, 1)
				
		# determinate the right viewport to show
		viewport = None
		if len(nodeRefList) > 0:
			# get the last selected valid object
			indList = range(len(nodeRefList))
			indList.reverse()
			for ind in indList:
				n = nodeRefList[ind]
				viewport = self._context.getViewportRef(n)
				if viewport is not None:
					break
		if viewport is not None:
			self.__showViewport(viewport)

		self.update()

		# select the list of shapes
		shapeList = []
		for nodeRef in nodeRefList:
			node = self.getNode(nodeRef)
			if node != None and node._graphicCtrl != None:
				shapeList.append(node._graphicCtrl)
		self.previousCtrl.selectNodeList(shapeList)
	
		# update popup menu according to the last item selected
		if len(nodeRefList) == 1:
			lastNodeRef = nodeRefList[-1]
			nodeType = self._context.getNodeType(lastNodeRef)
			import MenuTemplate
			if nodeType == TYPE_VIEWPORT:
				self.previousCtrl.setpopup(MenuTemplate.POPUP_REGIONPREVIEW_TOPLAYOUT)
			elif nodeType == TYPE_REGION:
				self.previousCtrl.setpopup(MenuTemplate.POPUP_REGIONPREVIEW_REGION)
			elif nodeType == TYPE_MEDIA:
				self.previousCtrl.setpopup(MenuTemplate.POPUP_REGIONPREVIEW_MEDIA)
		else:
			self.previousCtrl.setpopup(None)
				
		self.__selecting = 0

	#
	#
	#
	
	def updateRegionTree(self):
		if debug: print 'LayoutView.updateRegionTree begin'
		self.__mustBeUpdated = 0
			
		# We assume here that no region has been added or supressed
		viewportRefList = self._context.getViewportRefList()
		for viewportRef in viewportRefList:
			viewportNode = self.getNode(viewportRef)
			if viewportNode is not None:
				if debug: print 'LayoutView.updateRegionTree: update viewport',viewportNode.getName()
				viewportNode.updateAllAttrdict()
		if debug: print 'LayoutView.updateRegionTree end'

	def addRegion(self, parentRef, regionRef):
		if regionRef.isDefault():
			return None
		pNode = self.getNode(parentRef)
		regionNode = Region(regionRef, self)
		pNode.addNode(regionNode)
		self.__mustBeUpdated = 1
		return regionNode
#		visible = self._context.getVisibility(regionRef, TYPE_REGION, selected=0)
#		if visible:
#			self.__showRegion(regionRef)

	def addViewport(self, viewportRef):
		viewportNode = Viewport(viewportRef, self)
		self.__mustBeUpdated = 1
		return viewportNode

	def removeRegion(self, regionRef):
		if regionRef.isDefault():
			return

		if not self._nodeRefToNodeTree.has_key(regionRef):
			return
					
		regionNode = self.getNode(regionRef)			
		parentNode = regionNode.getParent()
		parentNode.removeNode(regionNode)
		del self._nodeRefToNodeTree[regionRef]
		self.__mustBeUpdated = 1
		
	def removeViewport(self, viewportRef):
		if not self._nodeRefToNodeTree.has_key(viewportRef):
			return

		if self.currentViewport is not None and viewportRef is self.currentViewport.getNodeRef():
			# show the first viewport in the list		
			currentViewportList = self._context.getViewportRefList()
			if len(currentViewportList) > 0:
				newViewportRef = currentViewportList[0]
				self.displayViewport(newViewportRef)
			else:
				self.currentViewport.hideAllNodes()
				self.currentViewport = None
		del self._nodeRefToNodeTree[viewportRef]
		self.__mustBeUpdated = 1
						
	def appendNode(self, pNodeRef, nodeRef, nodeType):
		if not self._context.isAVisibleNode(nodeRef, nodeType):
			return
		
		if nodeType == TYPE_VIEWPORT:
			node = self.addViewport(nodeRef)
			if node is not None:
				self._nodeRefToNodeTree[nodeRef] = node
				self.displayViewport(nodeRef)
			return
		elif nodeType == TYPE_REGION:
			node = self.addRegion(pNodeRef, nodeRef)
			self._nodeRefToNodeTree[nodeRef] = node
		elif nodeType == TYPE_MEDIA:
			pass
		
		visible = self._context.getVisibility(nodeRef, nodeType, selected=0)
		if visible:
			self.updateVisibility([nodeRef], visible)
			
	def removeNode(self, nodeRef, nodeType):
		if not self._context.isAVisibleNode(nodeRef, nodeType):
			return
		
		if nodeType == TYPE_VIEWPORT:
			self.removeViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			self.removeRegion(nodeRef)
		elif nodeType == TYPE_MEDIA:
			pass
				   
	# ensure that the viewport is in showing state
	def __showViewport(self, viewportRef):
		if self.currentViewport == None or viewportRef != self.currentViewport.getNodeRef():
			if debug: print 'LayoutView.select: change viewport =',viewportRef
			self.displayViewport(viewportRef)
			self.__mustBeUpdated = 1
					
	# ensure that the region is in showing state
	def __showRegion(self, regionRef):
		if regionRef.isDefault():
			return

		regionNode = self.getNode(regionRef)
		if regionNode.isShowed():
			# already showed
			return
		
		if regionNode is not None:
			regionNode.toShowedState()									
		self.__mustBeUpdated = 1

	# ensure that the media is in a showing state
	def __showMedia(self, nodeRef):
		if self._nodeRefToNodeTree.has_key(nodeRef):
			# already showed
			return
		
		self._nodeRefToNodeTree[nodeRef] = newNode = MediaRegion(nodeRef, self)
		parentRef = self._context.getParentNodeRef(nodeRef)
		parentNode = self.getNode(parentRef)
		if parentNode is not None:
			parentNode.addNode(newNode)

		newNode.toShowedState()
		self.__mustBeUpdated = 1

	def __hideRegion(self, regionRef):
		regionNode = self.getNode(regionRef)
		if regionNode is not None:
			regionNode.toHiddenState()									
		self.__mustBeUpdated = 1

	def __hideMedia(self, mediaRef):
		if not self._nodeRefToNodeTree.has_key(mediaRef):
			# already hidden
			return
		
		node = self.getNode(mediaRef)
		node.toHiddenState()
		parentNode = node.getParent()
		# remove from region tree
		if parentNode != None:
			parentNode.removeNode(node)
		del self._nodeRefToNodeTree[mediaRef]
		self.__mustBeUpdated = 1
									
#	def removeRegionNode(self, regionRef):
#		if regionRef in	self.currentRegionNodeListShowed:
#			self.currentRegionNodeListShowed.remove(regionRef)
#			regionNode = self.getNode(regionRef)
#			regionNode.toHiddenState()
#			self.__mustBeUpdated = 1
							 
	def onSelectChanged(self, objectList):
		# prevent against infinite loop
		if self.__selecting:
			return

		list = self.__getNodeRefSelectedList(objectList)
		if debugPreview: print 'PreviewWidget.onSelectChanged ',list
		self._context.onSelectChanged(list)

	# selected update nodes handler method
	# state = 1 means: add into selected list
	# state = 0 means: remove from selected list
	def onSelectUpdated(self, objectList, state):
		# prevent against infinite loop
		if self.__selecting:
			return

		list = self.__getNodeRefSelectedList(objectList)
		if debugPreview: print 'PreviewWidget.onSelectUpdated ',list
		self._context.onSelectUpdated(list, state)

	def __getNodeRefSelectedList(self, objectList):
		# build the list of the reference nodes selected
		list = []
		# xxx to optimize
		for nodeRef, nodeTree in self._nodeRefToNodeTree.items():
			for obj in objectList:
				if nodeTree._graphicCtrl is obj:
					list.append(nodeRef)

		return list
	
	def getNode(self, nodeRef):
		node = self._nodeRefToNodeTree.get(nodeRef)
		return node

	def displayViewport(self, viewportRef):
		if debug: print 'LayoutView.displayViewport: change viewport =',viewportRef
		if self.currentViewport != None:
			self.currentViewport.hideAllNodes()
		self.currentViewport = self.getNode(viewportRef)
		if self.currentViewport == None:
			# shouldn't pass here
			if debugPreview: print 'can''t show viewport ',viewportRef
			return
		self.currentViewport.showAllNodes()
		self.currentViewport.updateAllAttrdict()
		self.__mustBeUpdated = 1

	def onGeomChanging(self, objectList):
		# update only if one object is moving
		if len(objectList) != 1: return
		
		# xxx to optimize
		for  nodeRef, nodeTree in self._nodeRefToNodeTree.items():
			for obj in objectList:
				if nodeTree._graphicCtrl is obj:
					self._context.onFastGeomUpdate(nodeRef, obj.getGeom())
					break

	def onGeomChanged(self, objectList):		
		applyList = []
		# xxx to optimize
		for  nodeRef, nodeTree in self._nodeRefToNodeTree.items():
			for obj in objectList:
				if nodeTree._graphicCtrl is obj:
					applyList.append((nodeRef, obj.getGeom()))
					break

		self._context.applyGeomList(applyList)

	def mustBeUpdated(self):
		self.__mustBeUpdated = 1

	def fastUpdate(self):
		if self.currentViewport is not None:
			self.currentViewport.fastUpdateAllAttrdict()
		
class Node:
	def __init__(self, nodeRef, ctx):
		self._nodeRef = nodeRef
		self._children = []
		self._ctx = ctx
		self._parent = None
		self._viewport = None

		self._cssResolver = ctx._cssResolver
		self._cssNode = None
		
		# graphic control (implementation: system dependant)
		self._graphicCtrl = None		

		self._computedEditBackground = (200, 200, 200)
		self._z = self._nodeRef.GetAttrDef('z', 0)

		# default attribute		
		self._nodeType = TYPE_UNKNOWN

		# avoid a recursive loop when selecting:
		# currently, on windows, a selecting operation generate a selected event !
		self._selecting = 0

		self._wantToShow = 0
		self._mustUpdateEditBackground = 1
		self._curattrdict = {}
		
	def _cleanup(self):
		if self.isShowed:
			self.hide()
		self._ctx = None
		self._viewport = None
		self._parent = None
		
	def addNode(self, node):
		self._children.append(node)
		node._parent = self
		node._viewport = self._viewport
		if self._viewport is not None and node._nodeType in (TYPE_REGION, TYPE_VIEWPORT):
			self._viewport._mustUpdateEditBackground = 1

	def removeNode(self, node):
		if self._viewport is not None and node._nodeType in (TYPE_REGION, TYPE_VIEWPORT):
			self._viewport._mustUpdateEditBackground = 1
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
		return self._ctx._context.getShowedName(self._nodeRef)
	
	def getParent(self):
		return self._parent
	
	def applyOnAllNode(self, fnc, params):
		apply(fnc, params)
		for child in self._children:
			child.applyOnAllNode(fnc, params)

	def hide(self):
		if debug: print 'Node.hide: ',self.getName()
		if self._graphicCtrl != None:
			if self._parent != None:
				self._graphicCtrl.removeListener(self)
				if self._parent._graphicCtrl != None:
					self._parent._graphicCtrl.removeRegion(self._graphicCtrl)
			self._graphicCtrl = None
			self._ctx.previousCtrl.update()

	def hideAllNodes(self):
		for child in self._children:
			child.hideAllNodes()
		self.hide()

	def updateAttrdict(self):
		self.importAttrdict()
		if self.isShowed():
			self._graphicCtrl.setAttrdict(self._curattrdict)

	def fastUpdateAttrdict(self):
		# by default, do nothing.
		pass

	def updateAllAttrdict(self):
		if not self.isShowed():
			return
		self.updateAttrdict()
		for child in self._children:
			child.updateAllAttrdict()

	# this method has to be executed pretty quicky
	# It is used for animation preview and dynamic update (update during editing operation)
	def fastUpdateAllAttrdict(self):
		self.fastUpdateAttrdict()
		for child in self._children:
			child.fastUpdateAllAttrdict()		

	def getGeom(self):
		return self._curattrdict['wingeom']

	def __cmpZ(self, node1, node2):
		if node1._z > node2._z:
			return 1
		else:
			return -1
		
	def __computeLightFactor(self, factor=0, maxFactor=0):
		self._lightFactor = factor
		children = self._children
		children.sort(self.__cmpZ)
		currentZ = 0
		nextFactor = factor
		ind = 0
		for child in children:
			cz = child._z
			if cz != currentZ:
				factor = nextFactor
			currentZ = cz
			
			context = self._ctx._context
			nodeType = context.getNodeType(child._nodeRef)
			if nodeType not in (TYPE_VIEWPORT, TYPE_REGION):
				continue
			visible = context.getVisibility(child._nodeRef, nodeType, selected=1)
			if not visible:
				continue
			if child._nodeRef.GetAttrDef('editBackground',None) is not None:
				child._computeLightFactor()
				nextFactor = factor+1
			else:
				nextFactor, mFactor = child.__computeLightFactor(factor+1, maxFactor)
				if mFactor > maxFactor:
					maxFactor = mFactor
			ind = ind+1
		factor = factor+1
		if factor > maxFactor:
			maxFactor = factor
		return factor, maxFactor
			
	def _computeLightFactor(self):
		dummy, maxFactor = self.__computeLightFactor()
		self._maxFactor = maxFactor

	def __computeEditBackground(self, maxFactor, baseColor):
		factor = self._lightFactor
		# experimental algorithm to determinate the computed color
		r, g, b = baseColor
		if maxFactor < 5:
			colorNumber = 5
		else:
			colorNumber = maxFactor
		m = min(r, g, b)
		c = float(m)/colorNumber
		s = int(c*factor)
		self._computedEditBackground = r-s, g-s, b-s
		children = self._children
		for child in children:
			context = self._ctx._context
			nodeType = context.getNodeType(child._nodeRef)
			if nodeType not in (TYPE_VIEWPORT, TYPE_REGION):
				continue
			visible = context.getVisibility(child._nodeRef, nodeType, selected=1)
			if not visible:
				continue
			if child._nodeRef.GetAttrDef('editBackground',None) is not None:
				child._computeEditBackground()
			else:
				child.__computeEditBackground(maxFactor, baseColor)
		
	def _computeEditBackground(self):
		baseColor = self._nodeRef.GetAttrDef('editBackground',(200, 200, 200))
		self.__computeEditBackground(self._maxFactor, baseColor)

	def computeEditBackground(self):
		if self._mustUpdateEditBackground:
			self._computeLightFactor()
			self._computeEditBackground()
			self._mustUpdateEditBackground = 0
		
#	def isShowEditBackground(self):
#		showEditBackground = self._nodeRef.GetAttrDef('showEditBackground',None)
#		if showEditBackground != None and showEditBackground == 1:
#			return 1
#		return 0		

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

	# get the geom for region and media which depends of whether we edit or not an animation.
	# if this node is being animated, we have to get an interpolated value, and put the result into
	# the local css resolver in order than all geom children are correctly updated
	def getWinGeom(self):
		context = self._ctx._context
		targetAnimateNode = context.getTargetAnimateNode()
		if targetAnimateNode is self._nodeRef:
			wingeom = x, y, w, h = context.getPxGeomWithContextAnimation(self._nodeRef)
			updatedList = [('left', x), ('top', y), ('width', w), ('height', h), ('right', None), ('bottom', None)]
			self._cssResolver.setRawAttrs(self._cssNode, updatedList)
		else:
			wingeom = self._cssResolver.getPxGeom(self._cssNode)
		return wingeom

class Region(Node):
	def __init__(self, nodeRef, ctx):
		Node.__init__(self, nodeRef, ctx)
		self._nodeType = TYPE_REGION
		self._wantToShow = 0

		self._cssNode = self._cssResolver.newRegion()
		
	def importAttrdict(self):
		Node.importAttrdict(self)

		self._cssNode.copyRawAttrs(self._nodeRef.getCssId())
			
		z = self._nodeRef.GetAttrDef('z', 0)
		if z != self._z:
			self._z = z
			self._viewport._mustUpdateEditBackground = 1
		self._curattrdict['z'] = self._z

		showMode = self._ctx._context.getShowEditBackgroundMode(self._nodeRef)
		if showMode == 'editBackground':
			self._curattrdict['bgcolor'] = self._computedEditBackground
			self._curattrdict['transparent'] = 0
		elif showMode == 'outline':
			self._curattrdict['transparent'] = 1
		else:								
			self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
			self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)

		self._curattrdict['wingeom'] = wingeom = self.getWinGeom()
	
	def show(self):
		if debug: print 'Region.show : ',self.getName()

		if self.isShowed():
			# hide this node and its sub-nodes
			self.hideAllNodes()

		if self._wantToShow and self._parent._graphicCtrl != None:
			parent = self._parent
			self._cssResolver.link(self._cssNode, parent._cssNode)

			self.importAttrdict()
			self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self.getName())
			self._graphicCtrl.showName(self.getShowName())		
			self._graphicCtrl.setListener(self)

	def fastUpdateAttrdict(self):
		if self._graphicCtrl is not None:
			# XXX do a copy to force the low level to update
			self._curattrdict = self._curattrdict.copy()
			self._curattrdict['wingeom'] = self.getWinGeom()
			self._graphicCtrl.setAttrdict(self._curattrdict)

	def hide(self):
		if self.isShowed():
			parent = self._parent
			self._cssResolver.unlink(self._cssNode)			
			Node.hide(self)

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

	#
	# end update mothods
	#

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())
				
class MediaRegion(Region):
	def __init__(self, node, ctx):
		nodeRef = node
		Region.__init__(self, nodeRef, ctx)
		self._nodeType = TYPE_MEDIA
		self._wantToShow = 1

		self._cssNode = self._cssResolver.newRegion()
		self._mediaCssNode = self._cssResolver.newMedia(self._nodeRef.GetDefaultMediaSize)

	def importAttrdict(self):
		Node.importAttrdict(self)

		self._cssNode.copyRawAttrs(self._nodeRef.getSubRegCssId())
		self._mediaCssNode.copyRawAttrs(self._nodeRef.getMediaCssId())
				
		showMode = self._ctx._context.getShowEditBackgroundMode(self._nodeRef)
		if showMode == 'editBackground':
			self._curattrdict['transparent'] = 1			
		elif showMode == 'outline':
			self._curattrdict['transparent'] = 1
		else:								
			self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
			self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)

		# get wingeom according to the subregion positionning
		# note this step is not done during the parsing in order to maintains all constraint information
		# at some point we'll have to do the same thing for regions		
		channel = self._nodeRef.GetChannel()

		wingeom = self.getWinGeom()
			
		# determinate the real fit attribute		
		self.fit = fit = self._nodeRef.getCssAttr('fit','hidden')

		# ajust the internal geom for edition. If no constraint neither on right nor botton,
		# with fit==hidden: chg the internal region size.
		# it avoid a unexepected effet during the edition when you resize. don't change the semantic
#		right =	self._nodeRef.GetRawAttrDef('right', None) 
#		bottom = self._nodeRef.GetRawAttrDef('bottom', None) 
#		width =	self._nodeRef.GetRawAttrDef('width', None) 
#		height = self._nodeRef.GetRawAttrDef('height', None)
#		regPoint = self._nodeRef.GetAttrDef('regPoint', None)
#		regAlign = self._nodeRef.GetAttrDef('regAlign', None)
#		self.media_width, self.media_height = self._nodeRef.GetDefaultMediaSize(wingeom[2], wingeom[3])
#		# protect against getdefaultmediasize method which may return 0 !
#		if self.media_width <= 0 or self.media_height <= 0:
#			self.media_width, self.media_height = wingeom[2], wingeom[3]
#		if regPoint == 'topLeft' and regAlign == 'topLeft':
#			if fit == 'hidden':
#				if right == None and width == None:
#					x,y,w,h = wingeom
#					wingeom = x,y,self.media_width,h
#				if bottom == None and height == None:
#					x,y,w,h = wingeom
#					wingeom = x,y,w,self.media_height

		self._curattrdict['wingeom'] = wingeom
		self._z = self._nodeRef.GetAttrDef('z', 0)
		self._curattrdict['z'] = self._z

	def updateShowName(self,value):
		# no name showed
		pass

	def show(self):
		if debug: print 'Media.show : ',self.getName()
		if self._parent._graphicCtrl == None:
			return

		if self.isShowed():
			# hide this node and its sub-nodes
			self.hideAllNodes()


		parent = self._parent

		# for sub reg
		self._cssResolver.link(self._cssNode, parent._cssNode)
		# for media
		self._cssResolver.link(self._mediaCssNode, self._cssNode)

		self.importAttrdict()
		
		self._graphicCtrl = parent._graphicCtrl.addRegion(self._curattrdict, self.getName())
		self._graphicCtrl.showName(0)		
		self._graphicCtrl.setListener(self)
		
		# copy from old hierarchical view to determinate the image to showed
		node = self._nodeRef
		chtype = node.GetChannelType()
		
		canBeScaled = 1
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
			canBeScaled = 0

		if f is not None:
			mediadisplayrect  = self._cssResolver.getPxGeom(self._mediaCssNode)
			self._graphicCtrl.drawbox(mediadisplayrect)
			
			# the algorithm to show the preview of the media depend of its type
			# for medias whose we can only show the icons (text, html, svg, ...), we show a matrix of icons to
			# keep the real size and ratio. Otherwise it's ugly
			if canBeScaled:
				self._graphicCtrl.setImage(f, fit, mediadisplayrect)
			else:
				left, top, width ,height = mediadisplayrect
				import Sizes, MMurl
				url = MMurl.guessurl(f)
				# real the icon size
				iconWidth, iconHeight = Sizes.GetSize(url, 'image', 'tiff')
				if iconWidth == 0 or iconHeight == 0:
					print 'LayoutView.Preview.Media.show: invalid icon :',url
					return
				iconRatio = float(iconWidth)/iconHeight

				# min space 1 between each icon: used if the area is small
				spaceMinBetweenIcon1 = 40
				# min space 2 between each icon: used if the area is large
				spaceMinBetweenIcon2 = 100
				# derterminate if the first value is too small : important for optimization
				# show too many icons may be very slow
				limitOfMin2 = 3

				fit = 'hidden'				
				if height < iconHeight:
					fit = 'fill'
					iconWidth = int(iconRatio*height)
					iconHeight = height
				if width < iconWidth:
					fit = 'fill'
					iconHeight = int(width/iconRatio)
					iconWidth = width
					
				#
				# Vertical loop
				#
				spaceYBetweenIcon = 0
				iconYNumber = 1
				if height > 2*iconHeight+10:
					# figure out out the icon number in y axes
					heightLeft = height - 2*iconHeight
					iconYNumber = int(heightLeft-spaceMinBetweenIcon1)/int(iconHeight+spaceMinBetweenIcon1)
					if iconYNumber < 0:
						spaceYBetweenIcon = heightLeft
						iconYNumber = 2
					else:
						if iconYNumber > limitOfMin2:
							# too many icon, use the second specified space
							iconYNumber = int(heightLeft-spaceMinBetweenIcon2)/int(iconHeight+spaceMinBetweenIcon2)
						# figure out the real space
						spaceYBetweenIcon = float(heightLeft-iconHeight*iconYNumber)/(iconYNumber+1)
						iconYNumber = iconYNumber+2
					offsetY = top
				else:
					offsetY = top+(height-iconHeight)/2

				for indY in range(iconYNumber):
					#
					# Horizontal loop
					#
					spaceXBetweenIcon = 0
					iconXNumber = 1
					if width > 2*iconWidth+10:
						# figure out out the icon number in x axes
						widthLeft = width - 2*iconWidth
						iconXNumber = int(widthLeft-spaceMinBetweenIcon1)/int(iconWidth+spaceMinBetweenIcon1)
						if iconXNumber < 0:
							spaceXBetweenIcon = widthLeft
							iconXNumber = 2
						else:
							if iconXNumber > limitOfMin2:
								# too many icon, use the second specified space
								iconXNumber = int(widthLeft-spaceMinBetweenIcon2)/int(iconWidth+spaceMinBetweenIcon2)
							# figure out the real space
							spaceXBetweenIcon = float(widthLeft-iconWidth*iconXNumber)/(iconXNumber+1)
							iconXNumber = iconXNumber+2					
						offsetX = left
					else:
						offsetX = left+(width-iconWidth)/2

					xShift = iconWidth+spaceXBetweenIcon
					yShift = iconHeight+spaceYBetweenIcon
					# draw icons
					for indX in range(iconXNumber):
						self._graphicCtrl.setImage(f, fit, (offsetX+xShift*indX, \
															offsetY+yShift*indY, iconWidth, iconHeight))

	def fastUpdateAttrdict(self):
		# XXX for now, just recreat the media. Should be optimized
		if self._graphicCtrl is not None:
			isSelected = self._graphicCtrl.isSelected
		self.hide()
		self.show()
		if isSelected and self._graphicCtrl:
			self._ctx.previousCtrl.appendSelection([self._graphicCtrl])
			
	def hide(self):
		if self.isShowed():
			parent = self._parent
			self._cssResolver.unlink(self._mediaCssNode)			
			self._cssResolver.unlink(self._cssNode)			
			Node.hide(self)

	def _cleanup(self):
		# XXX should allow the gc to destroy the media
		# XXX To check if really need it
		self._mediaCssNode.defaultSizeHandler = None
		Node._cleanup(self)
		
	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
	
class Viewport(Node):
	def __init__(self, nodeRef, ctx):
		self.currentX = 8
		self.currentY = 8
		
		Node.__init__(self, nodeRef, ctx)
		self._nodeType = TYPE_VIEWPORT
		self._viewport = self

		self._cssNode = self._cssResolver.newRootNode()
		
	def importAttrdict(self):
		Node.importAttrdict(self)

		self._cssNode.copyRawAttrs(self._nodeRef.getCssId())
			
#		if editBackground != None:				
#				self._curattrdict['bgcolor'] = editBackground
#				self._curattrdict['transparent'] = 0
#		else:
#			self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
#			self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)
		self._curattrdict['bgcolor'] = 220,220,220
		self._curattrdict['transparent'] = 0
		
		w,h=self._nodeRef.getPxGeom()
		self._curattrdict['wingeom'] = (self.currentX,self.currentY,w,h)

	def show(self):
		if debug: print 'Viewport.show : ',self.getName()
		self.importAttrdict()
		self._graphicCtrl = self._ctx.previousCtrl.newViewport(self._curattrdict, self.getName())

		# show a the trace image if specified		
		traceImage = self._nodeRef.GetAttrDef('traceImage', '')
		if traceImage != '':
			import MMurl
			f = self._ctx._context.context.findurl(traceImage)
			if not f:
				# no file specified. do nothing
				pass
			else:
				try:
					f = MMurl.urlretrieve(f)[0]
					self._graphicCtrl.setImage(f,fit='fill')
				except IOError, arg:
					if type(arg) is type(self):
						arg = arg.strerror
					windowinterface.showmessage('Cannot resolve the trace image URL "%s": %s' % (f, arg), mtype = 'error')

		self._graphicCtrl.setListener(self)
		
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

	#
	# end update visualization mothods
	#

	def updateAllAttrdict(self):
		if not self.isShowed():
			return
		if debug: print 'LayoutView.updateAllAttrdict:',self.getName()
		self.computeEditBackground()
		Node.updateAllAttrdict(self)
		# XXX if z-order has changed, recompute edit background, and re-import attrs
		# XXX not really clean !
		if self._mustUpdateEditBackground:
			self.updateAllAttrdict()
			return
		# for now refresh all
		if self.isShowed():
			self.showAllNodes()

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())


		
