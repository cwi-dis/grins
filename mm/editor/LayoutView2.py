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

# XXX we should use the same variable as the variable defined from component
DELTA_KEYTIME = 0.01

TYPE_UNKNOWN, TYPE_REGION, TYPE_MEDIA, TYPE_VIEWPORT, TYPE_ANIMATE, TYPE_ANCHOR = range(6)
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
		from MMTypes import mediatypes
		if features.SEPARATE_ANIMATE_NODE in features.feature_set:
			self.__mmnodetypes = mediatypes+['animpar', 'animate', 'anchor']
		else:
			self.__mmnodetypes = mediatypes+['anchor']
			
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
		if node.type not in self.__mmnodetypes:
			return None
		if node.type in ('animate', 'animpar'):
			if node.attrdict.get('internal'):
				return None
			return TYPE_ANIMATE
		if node.type == 'anchor':
			return TYPE_ANCHOR
		chtype = node.GetChannelType()
		if chtype == None:
			return None
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
			if features.SEPARATE_ANIMATE_NODE not in features.feature_set:
				return
			parentRef = self.getParent(nodeRef, TYPE_ANIMATE)
			if parentRef.getClassName() == 'MMNode' and parentRef.isAnimated():
				# light animation
				return
			if not parentRef is None:
				parentType = self._getMMNodeType(parentRef)
				if parentType in (TYPE_MEDIA, TYPE_REGION):
					self.__checkNode(parentRef, nodeRef, position, TYPE_VIEWPORT, parentType, TYPE_ANIMATE)
		elif type == TYPE_ANCHOR:
			parentRef = self.getParent(nodeRef, TYPE_ANCHOR)
			if not parentRef is None:
				self.__checkNode(parentRef, nodeRef, position, TYPE_VIEWPORT, TYPE_MEDIA, TYPE_ANCHOR)
		
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
			elif region.isDefault():
				self.hasDefaultRegion = 1
				return region
			else:
				# the region may be moved from the document to the clipboard. In that case,
				# we don't show the media in the default region
				if not region.isInDocument():
					return None
	
				return region
		elif nodeType == TYPE_REGION:
			return nodeRef.GetParent()
		elif nodeType == TYPE_ANIMATE:
			targetNode = None
			if hasattr(nodeRef, 'targetnode'):
				targetNode = nodeRef.targetnode
			if targetNode is None:
				targetNode = nodeRef.GetParent()
			return targetNode
		elif nodeType == TYPE_ANCHOR:
			return nodeRef.GetParent()

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
		else:
			self.name = attrdict.get('name')
			
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
		else:
			name = attrdict.get('name')
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
		self.mkdefaultregioncommandlist()
		self.mkviewportcommandlist()
		self.mknositemcommandlist()
		self.mkmultisitemcommandlist()
		self.mkmultisiblingsitemcommandlist()
		self.mkanchorcommandlist()
		
		# dictionary of widgets used in this view
		# basicly, this view is composed of 
		# - a tree widget which manage the standard tree control
		# - a previous widget which manage the previous area
		# - some light widgets (geom field, z-index field, buttons control, ...)
		self.widgetList = []

		self.timeValueChanged = 1
		
	def fixtitle(self):
		pass			# for now...
	
	def destroy(self):
		self.hide()
		LayoutViewDialog2.destroy(self)

	def mkviewportcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandViewportList = [
				NEW_REGION(callback = (self.onNewRegion, ())),
				]
		else:
			self.commandViewportList = [
				]
		self.__appendCommonCommands(self.commandViewportList)

	def mkregioncommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandRegionList = [
				NEW_REGION(callback = (self.onNewRegion, ())),
#				ENABLE_ANIMATION(callback = (self.onEnableAnimation, ())),
				]
		else:
			self.commandRegionList = [
				]
		self.__appendCommonCommands(self.commandRegionList)

	def mkdefaultregioncommandlist(self):
		self.commandDefaultRegionList = [
				]
		##self.__appendCommonCommands(self.commandRegionList)

	def mkanchorcommandlist(self):
		self.commandAnchorList = [
				]
		self.__appendCommonCommands(self.commandAnchorList)

	def mkmediacommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMediaList = [
				ENABLE_ANIMATION(callback = (self.onEnableAnimation, ())),
				CREATEANCHOR(callback = (self.onNewAnchor, ())),
				CREATEANCHOREXTENDED(callback = (self.onNewAnchor, (1,))),
				CREATEANCHOR_CONTEXT(callback = (self.onNewAnchor, (2,))),
				CREATEANCHOR_BROWSER(callback = (self.onNewAnchor, (3,))),
				]
		else:
			self.commandMediaList = []
		self.commandMediaList.append(CONTENT(callback = (self.onContent, ())))
		self.__appendCommonCommands(self.commandMediaList)
			
	def mknositemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandNoSItemList = [
				]
		else:
			self.commandNoSItemList = []
		self.__appendCommonCommands(self.commandNoSItemList)

	# available command when several items are selected
	def mkmultisitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSItemList = [
				]
		else:
			self.commandMultiSItemList = []		
		self.__appendCommonCommands(self.commandMultiSItemList)
		
	def mkmultisiblingsitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSiblingSItemList = [
				]
		else:
			self.commandMultiSiblingSItemList = []
		if features.ALIGNTOOL in features.feature_set:
			self.__appendAlignCommands(self.commandMultiSiblingSItemList)
		self.__appendCommonCommands(self.commandMultiSiblingSItemList)

	def __appendCommonCommands(self, commandlist):
		commandlist.append(ZOOMIN(callback = (self.onZoomIn, ())))
		commandlist.append(ZOOMOUT(callback = (self.onZoomOut, ())))
		commandlist.append(DRAG_REGION())
			
	def __appendAlignCommands(self, list):
		list.extend([
			ALIGN_LEFT(callback = (self.onAlignLeft, ())),
			ALIGN_CENTER(callback = (self.onAlignCenter, ())),
			ALIGN_RIGHT(callback = (self.onAlignRight, ())),
			ALIGN_TOP(callback = (self.onAlignTop, ())),
			ALIGN_MIDDLE(callback = (self.onAlignMiddle, ())),
			ALIGN_BOTTOM(callback = (self.onAlignBottom, ())),
			DISTRIBUTE_HORIZONTALLY(callback = (self.onDistributeHorizontally, ())),
			DISTRIBUTE_VERTICALLY(callback = (self.onDistributeVertically, ())),
			])
		
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
		for widget in self.widgetList:
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
		for widget in self.widgetList:
			widget.destroy()
		self.widgetList = []
		
		# hide the windows	
		LayoutViewDialog2.hide(self)

		# destroy the tree helper structure	
		self.treeHelper.destroy()

		# clear all variables state
		self.currentSelectedNodeList = []
		self.previousSelectedNodeList = []
		self.currentFocus = None
		self.myfocus = None

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
		
		self.previousWidget.appendNode(parentRef, nodeRef, nodeType)
		# update tree widget		
		self.treeWidget.appendNode(parentRef, nodeRef, nodeType)
		
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
		for widget in self.widgetList:
			widget.startMutation()
		self.treeHelper.onTreeMutation()
		# notify widgets that the document structure end to change
		for widget in self.widgetList:
			widget.endMutation()

	def commit(self, type):
		self.root = self.toplevel.root
		if type not in ('REGION_GEOM', 'MEDIA_GEOM'):
			self.treeMutation()
		
		# after a commit, the focus may have changed
		self.currentFocus = self.editmgr.getglobalfocus()
		self.previousWidget.mustBeUpdated()
		self.updateFocus(1)

	# make a list of nodes selected in this view
	def makeSelectedNodeList(self, selList):
		targetList = []
		for nodeRef in selList:
			if self.existRef(nodeRef):
				# keep only seleted nodes belong to this view
				targetList.append(nodeRef)
			elif nodeRef.getClassName() == 'MMNode' and nodeRef.type in ('animpar', 'animate'):
				parentRef = self.treeHelper.getParent(nodeRef, TYPE_ANIMATE)
				if parentRef is not None and self.getNodeType(parentRef) == TYPE_MEDIA and parentRef.getAnimateNode() is nodeRef:
					targetList.append(parentRef)
			
		self.currentSelectedNodeList = targetList
		
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
				elif (className == 'RegionAssociation' and selectedType == TYPE_REGION and COPY_PASTE_MEDIAS) or \
					 (className == 'MMNode' and node.type == 'anchor' and selectedType == TYPE_MEDIA):
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
			if not (self.getNodeType(selectedNode) == TYPE_REGION and selectedNode.isDefault()):
				commandlist.append(ATTRIBUTES(callback = (self.onEditProperties, ())))
				if self.getAnimateNode(selectedNode) is not None:
					commandlist.append(SHOW_ANIMATIONPATH(callback = (self.onShowAnimationPath, ())))
					checked = self.canShowAnimationPath(selectedNode)
					self.settoggle(SHOW_ANIMATIONPATH, checked)

		viewportNumber = len(self.getViewportRefList())							
		if len(self.currentSelectedNodeList) >= 1:
			active = 1
			for node in self.currentSelectedNodeList:
				nodeType = self.getNodeType(node)
				if (nodeType == TYPE_REGION and node.isDefault()) or \
					nodeType == TYPE_ANIMATE or \
					nodeType == TYPE_VIEWPORT and viewportNumber <=1:
					active = 0
					break
			if active:
				# no default region in the selected list
				commandlist.append(COPY(callback = (self.onCopy, ())))
				commandlist.append(CUT(callback = (self.onCut, ())))
				commandlist.append(DELETE(callback = (self.onDelNode, ())))

		if features.MULTIPLE_TOPLAYOUT in features.feature_set or  viewportNumber< 1:
			commandlist.append(NEW_TOPLAYOUT(callback = (self.onNewViewport, ())))
			commandlist.append(DRAG_TOPLAYOUT())
				
		self.setcommandlist(commandlist)

	def updateVisibility(self,listToUpdate, visible):
		self.previousWidget.updateVisibility(listToUpdate, visible)
		self.treeWidget.updateVisibility(listToUpdate, visible)
		
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

		# refresh first preview widget
		self.previousWidget.selectNodeList(localSelList, keepShowedNodes)
		# update widgets
		for widget in self.widgetList:
			if widget is not self.previousWidget:
				widget.selectNodeList(localSelList, keepShowedNodes)

		if len(localSelList) == 0:
			self.updateCommandList(self.commandNoSItemList)
		elif len(localSelList) == 1:
			if nodeType == TYPE_REGION:
				if localSelList[0].isDefault():
					self.updateCommandList(self.commandDefaultRegionList)
				else:
					self.updateCommandList(self.commandRegionList)
			elif nodeType == TYPE_VIEWPORT:
				self.updateCommandList(self.commandViewportList)
			elif nodeType == TYPE_ANCHOR:
				self.updateCommandList(self.commandAnchorList)
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
		if nodeType not in (TYPE_VIEWPORT, TYPE_REGION):
			return self.treeHelper.getParent(nodeRef, nodeType)
		else:
			region = self.__channelTreeRef.getparent(nodeRef)
			return region
		return None

	def getAnimateNode(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_ANIMATE:
			# the animate node is itself
			return nodeRef
		elif nodeType == TYPE_MEDIA:
			animateNode = nodeRef.getAnimateNode()
			if animateNode is not None:
				return animateNode
		return None
		
	# have to be called from inside a transaction	
	def insertKeyTime(self, nodeRef, tp, duplicateKey=None):
		index = -1
		animateNode = self.getAnimateNode(nodeRef)
		if animateNode is not None:
			index = animateNode._animateEditWrapper.insertKeyTime(self.editmgr, tp, duplicateKey)

		if index > 0:
			self.animateControlWidget.insertKey(tp)
			self.timeValueChanged = 1 # force layout to refresh
		return index
			
	# have to be called from inside a transaction	
	def removeKeyTime(self, nodeRef, index):
		animateNode = self.getAnimateNode(nodeRef)
		if animateNode is not None:
			if animateNode._animateEditWrapper.removeKeyTime(self.editmgr, index):
				self.animateControlWidget.removeKey(index)
		
	def getKeyForThisTime(self, list, time, round=0):
		# first, search for the same value
		for ind in range(len(list)):
			timeRef = list[ind]
			if time == timeRef:
				return ind

		if round:			
			for ind in range(len(list)):
				timeRef = list[ind]
				if time > timeRef-DELTA_KEYTIME and time < timeRef+DELTA_KEYTIME:
					return ind
		return None

	def getPxGeom(self, nodeRef):
		return self.previousWidget.getPxGeom(nodeRef)
		
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
			
		if nodeType in (TYPE_MEDIA, TYPE_ANIMATE, TYPE_ANCHOR):
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
		if name is None:
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
		import AttrEdit		
		nodeType = self.getNodeType(nodeRef)
		if nodeType in (TYPE_REGION, TYPE_VIEWPORT):
			# allow to choice attributes
			AttrEdit.showchannelattreditor(self.toplevel, nodeRef, initattr = 'cssbgcolor')
		elif nodeType == TYPE_MEDIA:
			# allow to choice attributes
			AttrEdit.showattreditor(self.toplevel, nodeRef, initattr = 'cssbgcolor')
		elif nodeType == TYPE_ANCHOR:
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
		# note: this widget has to be updated first, so keep it in the begining of the list
		self.previousWidget = PreviousWidget(self)
		widgetList.append(self.previousWidget)
		
		self.treeWidget = TreeWidget(self)
		widgetList.append(self.treeWidget)

		self.animateControlWidget = AnimateControlWidget(self)
		widgetList.append(self.animateControlWidget)

		self.geomFieldWidget = GeomFieldWidget(self)
		widgetList.append(self.geomFieldWidget)
		
		widgetList.append(ZFieldWidget(self))
		widgetList.append(FitWidget(self))

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

	def applyAnimatePathList(self, applyList):
		list = []
		for nodeRef, path in applyList:
			animateNode = self.getAnimateNode(nodeRef)
			if animateNode is not None:
				editWrapper = animateNode._animateEditWrapper
				timeList = editWrapper.getKeyTimeList()
				lenPath = len(timeList)
				if lenPath != len(path):
					print 'LayoutView2.applyAnimatePathList: invalid path len'
					return
				
				editmgr = self.editmgr
				if not editmgr.transaction():
					return
				for index in range(lenPath):
					time = timeList[index]
					left, top = path[index]
					for attrName, attrValue in (('left',left), ('top',top)):
						if editWrapper.isAnimatedAttribute(attrName):
							if not editWrapper.changeAttributeValue(editmgr, attrName, attrValue, time, self):
								# we can't edit the attribute at this time: cancel the transaction
								editmgr.rollback()
								return
				self.editmgr.commit()
			
	def applyGeomList(self, applyList):
		list = []		
		for nodeRef, geom in applyList:
			self.__makeAttrListToApplyFromGeom(nodeRef, geom, list)
		self.applyAttrList(list)

	def __makeNewGeomAttrValues(self, start, end, size, pxStart, pxSize, pxParentSize):
		nPxStart = nPxEnd = nPxSize = None
		if start is None:
			if end is None:
				nPxStart = pxStart
				nPxSize = pxSize
			else:
				if size is None:
					nPxStart = pxStart
					nPxEnd = pxParentSize-pxStart-pxSize
				else:
					nPxEnd = pxParentSize-pxStart-pxSize
					nPxSize = pxSize
		elif end is None or size is not None:
			nPxStart = pxStart
			nPxSize = pxSize
		else:
			nPxStart = pxStart
			nPxEnd = pxParentSize-pxStart-pxSize

		nStart = self.__fixUnit(start, nPxStart, pxParentSize)
		nEnd = self.__fixUnit(end, nPxEnd, pxParentSize)
		nSize = self.__fixUnit(size, nPxSize, pxParentSize)

		return nStart, nEnd, nSize

	def __fixUnit(self, oValue, nPxValue, pxParentSize):
		PIXELUNIT_DEFAULT = 1
		if nPxValue is None:
			return None	
		if (oValue is None and not PIXELUNIT_DEFAULT) or type(oValue) is type(1.0):
			if nPxValue > 0:
				val = float(nPxValue)+0.0001
			elif nPxValue < 0:
				val = float(nPxValue)-0.0001
			else:
				val = 0.0
			return val/pxParentSize
		return nPxValue
	
	def __makeAttrListToApplyFromGeom(self, nodeRef, geom, list):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			x,y,w,h = geom
			list.append((nodeRef, 'width', w))
			list.append((nodeRef, 'height', h))
		elif nodeType in (TYPE_REGION, TYPE_MEDIA):
			x,y,w,h = geom
			animateNode = self.getAnimateNode(nodeRef)
			editWrapper = None
			if animateNode is not None:
				editWrapper = animateNode._animateEditWrapper
				
			if editWrapper and editWrapper.isAnimatedAttribute('left'):
				oLeft = x
			else:
				oLeft = nodeRef.GetAttrDef('left', None)
			if editWrapper and editWrapper.isAnimatedAttribute('top'):
				oTop = y
			else:
				oTop = nodeRef.GetAttrDef('top', None)
			if editWrapper and editWrapper.isAnimatedAttribute('width'):
				oWidth = w
			else:
				oWidth = nodeRef.GetAttrDef('width', None)
			if editWrapper and editWrapper.isAnimatedAttribute('height'):
				oHeight = h
			else:
				oHeight = nodeRef.GetAttrDef('height', None)
					
			oRight = nodeRef.GetAttrDef('right', None)
			oBottom = nodeRef.GetAttrDef('bottom', None)
			parentNodeRef = self.getParentNodeRef(nodeRef)
			pgeom = self.getPxGeom(parentNodeRef)
			if self.getNodeType(parentNodeRef) == TYPE_VIEWPORT:
				pw, ph = pgeom
			else:
				px, py, pw, ph = pgeom
			nLeft, nRight, nWidth = self.__makeNewGeomAttrValues(oLeft, oRight, oWidth, x, w, pw)
			nTop, nBottom, nHeight = self.__makeNewGeomAttrValues(oTop, oBottom, oHeight, y, h, ph)
			list.append((nodeRef, 'left', nLeft))
			list.append((nodeRef, 'top', nTop))
			list.append((nodeRef, 'width', nWidth))
			list.append((nodeRef, 'height', nHeight))
			list.append((nodeRef, 'right', nRight))
			list.append((nodeRef, 'bottom', nBottom))
		elif nodeType == TYPE_ANIMATE:
			list.append((nodeRef, 'left', x))
			list.append((nodeRef, 'top', y))
			list.append((nodeRef, 'width', w))
			list.append((nodeRef, 'height', h))
			list.append((nodeRef, 'right', None))
			list.append((nodeRef, 'bottom', None))
		elif nodeType == TYPE_ANCHOR:
			x,y,w,h = geom
			parentRef = self.getParentNodeRef(nodeRef)
			if parentRef is None or self.getNodeType(parentRef) != TYPE_MEDIA:
				return
			pX, pY, pW, pH = self.previousWidget.getMediaPxGeom(parentRef)
			# remember whether it's specify in pixel or percent
			currentCoords = nodeRef.GetAttrDef('acoords', None)
			lInPixel=tInPixel=rInPixel=bInPixel = 1
			if currentCoords is not None and len(currentCoords) == 4:
				cL, cT, cR, cB = currentCoords
				if type(cL) == type(1.0): lInPixel = 0
				if type(cT) == type(1.0): tInPixel = 0
				if type(cR) == type(1.0): rInPixel = 0
				if type(cB) == type(1.0): bInPixel = 0
			l = x
			r = l+w
			t = y
			b = t+h
			if not lInPixel: l = float(l)/pW
			if not tInPixel: t = float(t)/pH
			if not rInPixel: r = float(r)/pW
			if not bInPixel: b = float(b)/pH
			coords = [l, t, r, b]
			list.append((nodeRef, 'acoords',coords))								
			list.append((nodeRef, 'ashape','rect'))								
			
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
		editmgr = self.editmgr
		if not editmgr.transaction():
			return
							
		for nodeRef, attrName, attrValue in nodeRefAndValueList:
			nodeType = self.getNodeType(nodeRef)
			animateNode = self.getAnimateNode(nodeRef)
			animated = 0
			if animateNode is not None:
				currentTimeValue = animateNode._currentTime
				editWrapper = animateNode._animateEditWrapper
				
				if editWrapper.isAnimatedAttribute(attrName):
					animated = 1
					if not editWrapper.changeAttributeValue(editmgr, attrName, attrValue, currentTimeValue, self):
						# we can't edit the attribute at this time: cancel the transaction
						editmgr.rollback()
						return
											
			if not animated or (currentTimeValue == 0 and nodeType != TYPE_ANIMATE):
				if nodeType in (TYPE_VIEWPORT, TYPE_REGION):					
					self.editmgr.setchannelattr(nodeRef.name, attrName, attrValue)
				elif nodeType in (TYPE_MEDIA, TYPE_ANCHOR):
					self.editmgr.setnodeattr(nodeRef, attrName, attrValue)
				
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
		l,t,w,h = self.getPxGeom(referenceNode)
		referenceValue = l

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeom(nodeRef)
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
		l,t,w,h = self.getPxGeom(referenceNode)
		referenceValue = int(l+w/2)
		
		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeom(nodeRef)
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
		l,t,w,h = self.getPxGeom(referenceNode)
		referenceValue = l+w

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeom(nodeRef)
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
		l,t,w,h = self.getPxGeom(referenceNode)
		referenceValue = t

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeom(nodeRef)
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
		l,t,w,h = self.getPxGeom(referenceNode)
		referenceValue = int(t+h/2)
		
		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeom(nodeRef)
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
		l,t,w,h = self.getPxGeom(referenceNode)
		referenceValue = t+h

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = self.getPxGeom(nodeRef)
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
			l,t,w,h = self.getPxGeom(node)
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
		l,t,w,h = self.getPxGeom(firstNodeRef)
		posRef = l+w
		for nodeRef in sortedList[1:]:
			l,t,w,h = self.getPxGeom(nodeRef)
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
			l,t,w,h = self.getPxGeom(node)
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
		l,t,w,h = self.getPxGeom(firstNodeRef)
		posRef = t+h
		for nodeRef in sortedList[1:]:
			l,t,w,h = self.getPxGeom(nodeRef)
			t = posRef+space
			posRef = t+h
			# make the new geom
			self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	# this method will be used by the sort method
	def __cmpNode(self, node1, node2):
		l1,t1,w1,h1 = self.getPxGeom(node1)
		l2,t2,w2,h2 = self.getPxGeom(node2)
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

	# enable disable light animations
	def onEnableAnimation(self):
		if len(self.currentSelectedNodeList) > 0:
			selectedNode = self.currentSelectedNodeList[0]
			nodeType = self.getNodeType(selectedNode)
			editmgr = self.editmgr
			if not editmgr.transaction():
				return
			if selectedNode.GetAttrDef('animated', None):
				# disable animation
				animateNode = self.getAnimateNode(selectedNode)
				editmgr.delnode(animateNode)
				editmgr.setnodeattr(selectedNode, 'animated', None)
			else:
				# enable animation
				animateNode = self.context.newnode('animpar')
				left, top, width, height = selectedNode.getPxGeom()
				bgcolor = selectedNode.GetInherAttrDef('bgcolor', (0,0,0))
				animateNode.SetAttr('animvals', [(0.0, {'top':top, 'left':left, 'width':width, 'height':height}),
														(1.0, {'top':top, 'left':left, 'width':width, 'height':height})])
				editmgr.addnode(selectedNode, -1, animateNode)
				editmgr.setnodeattr(selectedNode, 'animated', 1)
					
			editmgr.commit()

	def onShowAnimationPath(self):
		selectedNode = self.currentSelectedNodeList[0]
		nodeType = self.getNodeType(selectedNode)
		if nodeType not in (TYPE_MEDIA, TYPE_ANIMATE):
			return
		
		editmgr = self.editmgr
		if not editmgr.transaction():
			return
		if self.canShowAnimationPath(selectedNode):
			editmgr.setnodeattr(selectedNode, 'showAnimationPath', 0)
		else:
			editmgr.setnodeattr(selectedNode, 'showAnimationPath', 1)			
		editmgr.commit()

	# return the node where the preferences attributes are stored for animation nodes
	# according whether the animate node is include inside its targetnode or not (light animation)
	def getAnimationAttributesNode(self, nodeRef):
		# check whether the animate node is include inside the media node
		animateNode = self.getAnimateNode(nodeRef)
		if animateNode is None:
			return nodeRef
		if animateNode is nodeRef.getAnimateNode():
			return nodeRef
		else:
			return animateNode
		
	def canShowAnimationPath(self, nodeRef):
		# check whether the animate node is include inside the media node
		nRef = self.getAnimationAttributesNode(nodeRef)
		import MMAttrdefs
		return MMAttrdefs.getattr(nRef, 'showAnimationPath')

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
					nodeType = self.getNodeType(nodeRef)
					parent = self.getParentNodeRef(nodeRef)
					if parent != None:
						newFocus = [parent]
					if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
						self.editmgr.delchannel(nodeRef)
					elif nodeType == TYPE_ANCHOR:
						self.editmgr.delnode(nodeRef)						
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

	def onNewAnchor(self, extended = 0):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		if len(self.currentSelectedNodeList) == 1:
			self.newAnchor(self.currentSelectedNodeList[0], extended)

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
			elif nodeType == TYPE_ANCHOR:
				if isACopy:
					clipList.append(nodeRef.DeepCopy())
				else:
					clipList.append(nodeRef)
			elif nodeType in (TYPE_REGION, TYPE_VIEWPORT):
				if nodeRef.isDefault():
					# Should not happen.
					msg = "you cannot copy or cut the default region."
					windowinterface.showmessage(msg, mtype = 'error')
					return []
				if isACopy:
					clipList.append(nodeRef.DeepCopy())
				elif len(currentViewportList) == 1 and nodeRef is currentViewportList[0]:
					# Should not happen
					msg = "you cannot delete or cut the last viewport."
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
			elif className == 'MMNode' and node.type == 'anchor':
				pnode = self.getParentNodeRef(node)
				self.editmgr.delnode(node)
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

		selectedNode = None
		if len(self.currentSelectedNodeList) > 0:		
			selectedNode = self.currentSelectedNodeList[0]
			selectedNodeType = self.getNodeType(selectedNode)

		if selectedNode is None or (selectedNode.getClassName() in ('Viewport', 'Region') and selectedNode.isDefault()):
			# can't insert a node into the default region
			return
		
		if not self.editmgr.transaction():
			return

		nodeList = self.editmgr.getclipcopy()

		newFocus = []
		for node in nodeList:
			className = node.getClassName()

			if className == 'Region':
				self.editmgr.addchannel(selectedNode, -1, node)
				newFocus.append(node)
			elif className == 'RegionAssociation':
				if selectedNodeType == TYPE_REGION:
					mediaNode = node.getMediaNode()
					self.editmgr.setnodeattr(mediaNode, 'channel', selectedNode.name)					
					newFocus.append(mediaNode)
			elif className == 'MMNode' and node.type == 'anchor':
				self.editmgr.addnode(selectedNode, -1, node)
				newFocus.append(node)					
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
				windowinterface.showmessage("A top layout element with the same id already exists.", mtype = 'error')
				return
		self.applyNewViewport(name)
		self.setglobalfocus([self.nameToNodeRef(name)])
		self.updateFocus()

	def newAnchor(self, parentRef, extended = 0):
		# create the anchor
		anchor = self.toplevel.links.createanchor(parentRef, interesting = 1, extended = extended)
		if anchor is not None:
			self.setglobalfocus([anchor])
			self.updateFocus()
			if extended:
				import AttrEdit
				AttrEdit.showattreditor(self.toplevel, anchor, '.href')

	# check if moving a source node into a target node is valid
	def isValidMove(self, sourceNodeRef, targetNodeRef):
		if sourceNodeRef == None or targetNodeRef == None:
			return 0

		if sourceNodeRef.IsAncestorOf(targetNodeRef) or sourceNodeRef is targetNodeRef:
			return 0
				
		targetNodeType = self.getNodeType(targetNodeRef)
		# for now, accept only moving if the target node is viewport or region
		if targetNodeType not in (TYPE_VIEWPORT, TYPE_REGION, TYPE_MEDIA):
			return 0

		sourceNodeType = self.getNodeType(sourceNodeRef)
		# for now, moving a viewport is forbidden
		if sourceNodeType is None or sourceNodeType == TYPE_VIEWPORT:
			return 0

		if sourceNodeType == TYPE_MEDIA and targetNodeType != TYPE_REGION:
			return 0

		if targetNodeType == TYPE_REGION and targetNodeRef.isDefault():
			# you can't move anything into the default region
			return 0
		if sourceNodeType == TYPE_REGION and sourceNodeRef.isDefault():
			# you can't move the default region
			return 0

		if (targetNodeType == TYPE_MEDIA and sourceNodeType != TYPE_ANCHOR) or \
		   (sourceNodeType == TYPE_ANCHOR and targetNodeType != TYPE_MEDIA):
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
		elif sourceNodeType == TYPE_ANCHOR and targetNodeType == TYPE_MEDIA:
			if self.editmgr.transaction():
				self.editmgr.delnode(sourceNodeRef)
				self.editmgr.addnode(targetNodeRef, -1, sourceNodeRef)
				self.editmgr.commit()			
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
		if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
			return nodeRef.GetAttrDef('previewShowOption', 'always')
		else:
			return nodeRef.GetAttrDef('previewShowOption', 'onSelected')

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
				if optionValue == 'onSelected':
					list.append(nodeRef)
					# set value as well on all children recursivly
					children = self.getAllChildren(nodeRef)
					list = list+children
				elif optionValue == 'always':
					# set value as well on all parents
					parents = self.getAllParent(nodeRef)
					pvis = 1
					for pnode in parents:
						if not self.isAVisibleNode(pnode, self.getNodeType(pnode)):
							pvis = 0
							break
					# update only to visible if all parents are visible
					if pvis:
						list.append(nodeRef)
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
			else:
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

	def isShowed(self, nodeRef):
		return self.previousWidget.isShowed(nodeRef)
	
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
			elif nodeType == TYPE_ANCHOR:
				pass
			else:
				error = 5

		if error == 4:
			# show in priority that error
			windowinterface.showmessage("you cannot delete the last viewport.", mtype = 'error')
		elif error == 3:
			windowinterface.showmessage("You cannot delete media items in the Layout view.", mtype = 'error')
		elif error == 2:
			windowinterface.showmessage("You cannot delete the default region.", mtype = 'error')
		elif error == 1:
			ret = windowinterface.GetOKCancel("The item is not empty, deleting it will move the media items to a default region.", self.toplevel.window)
			if ret == 0:
				# ok
				error = 0

		return error == 0
			
	def onFastGeomUpdate(self, nodeRef, geom):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			self.geomFieldWidget.updateViewportGeom(geom)
		elif nodeType in (TYPE_REGION, TYPE_ANCHOR):
			self.geomFieldWidget.updateRegionGeom(geom)
		elif nodeType in (TYPE_MEDIA, TYPE_ANIMATE):
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

		isShowed = self._context.isShowed(nodeRef)
		if not self._context.isAVisibleNode(nodeRef, nodeType) or not isShowed:
			return 0, None

		return nodeType, nodeRef

	def hasVisibleAnimate(self, nodeRef):
		visibleAnimate = 0
		children = self._context.getChildren(nodeRef)
		for child in children:
			childType = self._context.getNodeType(child)
			if childType == TYPE_ANIMATE:
				if self._context.getVisibility(child, childType, 0):
					visibleAnimate = 1
		return visibleAnimate

	def onCheckCtrl(self, ctrlName, value):
		pass

	def getVisibleAnimatedAttrList(self, nodeRef, attrList):
		rList = []
		for attr in attrList:
			rList.append(0)
		children = self._context.getChildren(nodeRef)
		for child in children:
			childType = self._context.getNodeType(child)
			if childType == TYPE_ANIMATE:
				if self._context.getVisibility(child, childType, 0):
					if hasattr(child, '_animateEditWrapper'):
						editWrapper = child._animateEditWrapper
						for ind in range(len(attrList)):
							rList[ind] = rList[ind] | editWrapper.isAnimatedAttribute(attrList[ind])
		return rList
		
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
		elif nodeType == TYPE_ANIMATE:
			self.dialogCtrl.enable('RegionZ',0)
			nodeRef = self._context.getParentNodeRef(nodeRef, TYPE_ANIMATE)
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
		elif nodeType == TYPE_ANIMATE:
			self.__update(nodeRef, nodeType, readOnly=1)
		else:
			self.__unselect()

	# update the dialog box on unselection
	def __unselect(self):
		self.dialogCtrl.enable('Fit',0)
		self.dialogCtrl.setSelecterCtrl('Fit',-1)
		self.dialogCtrl.setLabel('FitLabel','Fit')

	# update the dialog box on valid selection
	def __update(self, nodeRef, nodeType, readOnly=0):
		if nodeType == TYPE_REGION:
			self.dialogCtrl.setLabel('FitLabel','Default fit')
			fit = nodeRef.GetAttrDef('fit', 'hidden')
			self.__currentShowedValues = self.showedValues
			index = self.fitValues.index(fit)
		elif nodeType in (TYPE_MEDIA, TYPE_ANIMATE):
			if nodeType == TYPE_ANIMATE:
				nodeRef = self._context.getParentNodeRef(nodeRef, TYPE_ANIMATE)
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
		if readOnly:
			self.dialogCtrl.enable('Fit',0)
		else:
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
		self._eLeft, self._eTop, self._eWidth, self._eHeight = 0, 0, 0, 0
				
		if nodeType == TYPE_VIEWPORT:
			self._eWidth, self._eHeight = 1, 1
			self.__updateSelection()
			self.__updateViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			self._eLeft, self._eTop, self._eWidth, self._eHeight = 1, 1, 1, 1
			self.__updateSelection()
			self.__updateRegion(nodeRef)			
		elif nodeType == TYPE_ANCHOR:
			shape = nodeRef.GetAttrDef('ashape', None)
			if shape in (None, 'rect'):
				self._eLeft, self._eTop, self._eWidth, self._eHeight = 1, 1, 1, 1				
				self.__updateRegion(nodeRef)			
			self.__updateSelection()
		elif nodeType == TYPE_MEDIA:
			aLeft, aTop, aWidth, aHeight = self.getVisibleAnimatedAttrList(nodeRef, ['left', 'top', 'width', 'height'])
			self._eLeft, self._eTop, self._eWidth, self._eHeight = not aLeft, not aTop, not aWidth, not aHeight
			self.__updateSelection()
			self.__updateMedia(nodeRef)
		elif nodeType == TYPE_ANIMATE:
			editWrapper = nodeRef._animateEditWrapper
			self._eLeft = editWrapper.isAnimatedAttribute('left')
			self._eTop = editWrapper.isAnimatedAttribute('top')
			self._eWidth = editWrapper.isAnimatedAttribute('width')
			self._eHeight = editWrapper.isAnimatedAttribute('height')
			self.__updateSelection()
			self.__updateMedia(nodeRef)
		else:
			self.__updateSelection()
			
	#
	#
	#
			
	def __updateSelection(self):
		if self._eLeft:
			self.dialogCtrl.enable('RegionX',1)
		else:
			self.dialogCtrl.enable('RegionX',0)
			self.dialogCtrl.setFieldCtrl('RegionX',"")
		if self._eTop:
			self.dialogCtrl.enable('RegionY',1)
		else:
			self.dialogCtrl.enable('RegionY',0)
			self.dialogCtrl.setFieldCtrl('RegionY',"")
		if self._eWidth:
			self.dialogCtrl.enable('RegionW',1)
		else:
			self.dialogCtrl.enable('RegionW',0)
			self.dialogCtrl.setFieldCtrl('RegionW',"")
		if self._eHeight:
			self.dialogCtrl.enable('RegionH',1)
		else:
			self.dialogCtrl.enable('RegionH',0)
			self.dialogCtrl.setFieldCtrl('RegionH',"")
		
	def __updateMediaGeom(self, geom):
		self.updateRegionGeom(geom)
			
	def __updateViewport(self, nodeRef):		
		w,h = nodeRef.getPxGeom()
		geom = 0,0,w,h
		self.updateViewportGeom(geom)				

	def updateViewportGeom(self, geom):
		# update the fields dialog box
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])
		
	def __updateRegion(self, nodeRef):
		geom = self._context.getPxGeom(nodeRef)
		self.updateRegionGeom(geom)
		
	def updateRegionGeom(self, geom):
		self.dialogCtrl.setFieldCtrl('RegionX',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionY',"%d"%geom[1])		
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])
		
	def __updateMedia(self, nodeRef):		
		geom = self._context.getPxGeom(nodeRef)
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
				elif nodeType in (TYPE_MEDIA, TYPE_ANIMATE, TYPE_ANCHOR):
					self.__onGeomOnRegionChanged(ctrlName, value)

	def __onGeomOnViewportChanged(self, ctrlName, value):
		if len(self._context.currentSelectedNodeList) > 0:
			nodeRef = self._context.currentSelectedNodeList[0]
			w,h = nodeRef.getPxGeom()
			if ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			if self.__checkSize(w, h):
				self._context.applyGeom(nodeRef, (0,0,w,h))

	def __onGeomOnRegionChanged(self, ctrlName, value):
		if len(self._context.currentSelectedNodeList) > 0:		
			nodeRef = self._context.currentSelectedNodeList[0]
			x,y,w,h = self._context.getPxGeom(nodeRef)
			if ctrlName == 'RegionX':
				x = value
			elif ctrlName == 'RegionY':
				y = value			
			elif ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			if self.__checkSize(w, h) and self.__checkPos(x, y):
				self._context.applyGeom(nodeRef, (x,y,w,h))

	def __checkSize(self, w, h):
		if w<1 or h<1 or w>20000 or h>20000:
			windowinterface.showmessage('Bad size', mtype = 'error')
			self._context.updateFocus()
			return 0
		return 1
	
	def __checkPos(self, x, y):
		if x>20000 or y>20000:
			windowinterface.showmessage('Bad position', mtype = 'error')
			self._context.updateFocus()
			return 0
		return 1
		
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
		
		if nodeType in (TYPE_MEDIA, TYPE_ANIMATE):
			if nodeType == TYPE_MEDIA:
				if nodeRef.isAnimated():
					# it's a light animation
					enabled = 1
					checked = 1
				else:
					# it's not a 'light' animation
					enabled = 1
					checked = 0
					children = self._context.getChildren(nodeRef)
					for child in children:
						if self._context.getNodeType(child) == TYPE_ANIMATE and not child.attrdict.get('internal'):
							# has some animate nodes
							checked = 1
							enabled = 0
							break
			else:
				# it's not a 'light' animation, read only
				enabled = 0
				checked = 1

			self.dialogCtrl.setCheckCtrl('AnimateEnable',checked)
			self.dialogCtrl.enable('AnimateEnable',enabled)				
			self._context.settoggle(ENABLE_ANIMATION, checked)
			self.__updateNode(nodeRef)
		else:
			self.dialogCtrl.enable('AnimateEnable',0)				
			self.dialogCtrl.setCheckCtrl('AnimateEnable',0)
			self._context.settoggle(ENABLE_ANIMATION, 0)
			self.__updateUnselected()
		
	#
	#
	#
				
	def __updateUnselected(self):
		self.isEnabled = 0
		self.sliderCtrl.setKeyTimes([0.0, 1.0])		
		self.sliderCtrl.setCursorPos(0)
		self.sliderCtrl.enable(0)
	
	def __updateViewport(self, nodeRef):
		self.__updateUnselected()
			
	def __updateNode(self, nodeRef):
		animateNode = self._context.getAnimateNode(nodeRef)
		if animateNode is None:
			self.__updateUnselected()
			return

		editWrapper = animateNode._animateEditWrapper
		keyTimeList = editWrapper.getKeyTimeList()
		self.sliderCtrl.setKeyTimes(keyTimeList)
		
		self.__selecting = 1
		timeValue = animateNode._currentTime
		keyTimeIndex = self._context.getKeyForThisTime(keyTimeList, timeValue, round=1)
		if keyTimeIndex is not None and keyTimeIndex >= 0:
			self.sliderCtrl.selectKeyTime(keyTimeIndex)
		else:
			self.sliderCtrl.selectKeyTime(-1)
		self.sliderCtrl.setCursorPos(timeValue)
		self.__selecting = 0
				
		self.isEnabled = 1
		self.sliderCtrl.enable(1)
		
	def insertKey(self, time):
		if self.isEnabled:
			self.sliderCtrl.insertKeyTime(time)

	def removeKey(self, index):
		if self.isEnabled:
			self.sliderCtrl.removeKeyTimeAtIndex(index)
			newIndex = index-1
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
			editmgr.commit()
			
	def onRemoveKey(self, index):
		if self.isEnabled:
			nodeType, nodeRef = self._selected
			editmgr = self._context.editmgr
			if not editmgr.transaction():
				return -1
			index = self._context.removeKeyTime(nodeRef, index)
			editmgr.commit()
					
	def onSelected(self, index):
		if self.isEnabled and not self.__selecting:
			nodeType, nodeRef = self._selected

			animateNode = self._context.getAnimateNode(nodeRef)
			timeList = self.sliderCtrl.getKeyTimes()
			time = timeList[index]
			
			animateNode._currentTime = time
			self.sliderCtrl.setCursorPos(time)
			self._context.updateFocus(1)

	def onCursorPosChanged(self, pos):
		if self.isEnabled:
			context = self._context
			nodeType, nodeRef = self._selected
			animateNode = self._context.getAnimateNode(nodeRef)
			editWrapper = animateNode._animateEditWrapper
			animateNode._currentTime = pos
			keyTimeList = editWrapper.getKeyTimeList()
			keyTimeIndex = self._context.getKeyForThisTime(keyTimeList, pos, round=1)
			if keyTimeIndex is not None and keyTimeIndex >= 0:
				self.sliderCtrl.selectKeyTime(keyTimeIndex)
			else:
				self.sliderCtrl.selectKeyTime(-1)
			previewWidget = self._context.previousWidget
			if previewWidget is not None:
				previewWidget.fastUpdate()
			context.onFastGeomUpdate(nodeRef, context.getPxGeom(nodeRef))

	def onKeyTimeChanged(self, index, time):
		if self.isEnabled:
			nodeType, nodeRef = self._selected
			editmgr = self._context.editmgr
			if not editmgr.transaction(editmgr):
				return

			animateNode = self._context.getAnimateNode(nodeRef)
			if animateNode is not None:
				animateNode._animateEditWrapper.changeKeyTime(editmgr, index, time)
				
			animateNode._currentTime = time
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
			elif nodeType == TYPE_ANCHOR:
				self.treeCtrl.setpopup(MenuTemplate.POPUP_REGIONTREE_ANCHOR)
			else:
				self.treeCtrl.setpopup(None)
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
		iconname = nodeRef.getIconName(wantmedia=1)
		name = self._context.getShowedName(nodeRef, nodeType)
		self.treeCtrl.updateNode(self.nodeRefToNodeTreeCtrlId[nodeRef], name, iconname, iconname)
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
			type = 'Media'
			objectId = nodeRef.GetUID()
		elif nodeType in (TYPE_VIEWPORT, TYPE_REGION):
			type = 'Region'
			objectId = nodeRef.name
		elif nodeType == TYPE_ANCHOR:
			type = 'NodeUID'
			objectId = nodeRef
		elif nodeType in (TYPE_ANIMATE):
			# not supported
			return
		self.treeCtrl.beginDrag(type, objectId)

	def __dragObjectIdToNodeRef(self, type, objectId):
		nodeRef = None
		if type == 'Media':
			# retrieve the reference of the source node
			try:
				nodeRef = self._context.context.mapuid(objectId)
			except:
				pass
		elif type == 'NodeUID':
			arg, uid = objectId
			nodeRef = self._context.context.mapuid(uid)		
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
		elif type in ('Region', 'Media', 'NodeUID'):
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
		elif type in ('Region', 'Media', 'NodeUID'):
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
		self.previousCtrl.destroy()

		self.previousCtrl = None
		for node in self._nodeRefToNodeTree.values():
			node._cleanup()
		self._nodeRefToNodeTree = {}

	def updateVisibility(self, nodeRefList, visible):
		for nodeRef in nodeRefList:
			nodeType = self._context.getNodeType(nodeRef)
			if visible:
				if nodeType == TYPE_REGION:
					self.__showRegion(nodeRef)
				elif nodeType == TYPE_MEDIA:
					self.__showMedia(nodeRef)
				elif nodeType == TYPE_ANIMATE:
					self.__showAnimate(nodeRef)
				elif nodeType == TYPE_ANCHOR:
					self.__showAnchor(nodeRef)
			else:
				if nodeType == TYPE_REGION:
					self.__hideRegion(nodeRef)
				elif nodeType == TYPE_MEDIA:
					self.__hideMedia(nodeRef)
				elif nodeType == TYPE_ANIMATE:
					self.__hideAnimate(nodeRef)
				elif nodeType == TYPE_ANCHOR:
					self.__hideAnchor(nodeRef)

	# update animation wrapper to be able to get interpolation values
	def updateAnimationWrapper(self, animateNode):
		import AnimationWrappers
		animateNode._animateEditWrapper = AnimationWrappers.makeAnimationWrapper(animateNode)
		if not hasattr(animateNode, '_currentTime'):
			animateNode._currentTime = 0
		animateNode._animateEditWrapper.updateAnimators()
		self.__mustBeUpdated = 1
		
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
			if node is None and self._context.getNodeType(nodeRef) == TYPE_ANIMATE:
				# for animate node, the shape is associated to the target node
				parentNodeRef = self._context.getParentNodeRef(nodeRef)
				if parentNodeRef is not None:
					node = self.getNode(parentNodeRef)
			if node is not None and node._graphicCtrl != None:
				shapeList.append(node._getSelectedObject())
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
			elif nodeType == TYPE_ANCHOR:
				self.previousCtrl.setpopup(MenuTemplate.POPUP_REGIONPREVIEW_ANCHOR)
		else:
			self.previousCtrl.setpopup(None)
				
		self.__selecting = 0

	#
	#
	#
	
	def updateRegionTree(self):
		self.__mustBeUpdated = 0
		if self.currentViewport is not None:
		# We assume here that no region has been added or supressed
			if debug: print 'LayoutView.updateRegionTree: update viewport',viewportNode.getName()
			self.currentViewport.updateAllAttrdict()

	def addRegion(self, parentRef, regionRef):
		if regionRef.isDefault():
			return None
		pNode = self.getNode(parentRef)
		regionNode = Region(regionRef, self)
		pNode.addNode(regionNode)
		self.__mustBeUpdated = 1
		return regionNode

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
		if not self._nodeRefToNodeTree.has_key(pNodeRef):
			# no parent: The parent node may be unvisible (sound, ...)
			return
			
		if nodeType == TYPE_REGION:
			node = self.addRegion(pNodeRef, nodeRef)
			self._nodeRefToNodeTree[nodeRef] = node
		
		visible = self._context.getVisibility(nodeRef, nodeType, selected=0)
		if visible:
			self.updateVisibility([nodeRef], visible)
			
	def removeNode(self, nodeRef, nodeType):		
		if nodeType == TYPE_VIEWPORT:
			self.removeViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			self.removeRegion(nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.__hideMedia(nodeRef)
		elif nodeType == TYPE_ANIMATE:
			self.__hideAnimate(nodeRef)
		elif nodeType == TYPE_ANCHOR:
			self.__hideAnchor(nodeRef)
				   
	# ensure that the viewport is in showing state
	def __showViewport(self, viewportRef):
		if self.currentViewport is None or viewportRef is not self.currentViewport.getNodeRef():
			if debug: print 'LayoutView.select: change viewport =',viewportRef
			self.displayViewport(viewportRef)
			self.__mustBeUpdated = 1
					
	# ensure that the region is in showing state
	def __showRegion(self, regionRef):
		if regionRef.isDefault():
			return

		regionNode = self.getNode(regionRef)
		if regionNode is None:
			# the region has not been created
			return
		
		if regionNode.isShowed():
			# already showed
			return
		
		if regionNode is not None:
			regionNode.toShowedState()									
		self.__mustBeUpdated = 1

	# ensure that the media is in a showing state
	def __showMedia(self, nodeRef):
		# update the animator if the animate node is include inside the media node		
		animateNode = nodeRef.getAnimateNode()
		if animateNode is not None:
			self.updateAnimationWrapper(animateNode)
			
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

	def __showAnchor(self, nodeRef):
		if self._nodeRefToNodeTree.has_key(nodeRef):
			# already showed, force to hide
			self.__hideAnchor(nodeRef)
		
		shape = nodeRef.GetAttrDef('ashape', None)
		if shape not in (None, 'rect'):
			# not supported shape
			return
		
		parentRef = self._context.getParentNodeRef(nodeRef)
		parentNode = self._nodeRefToNodeTree.get(parentRef)
		if parentNode is None:
			self.updateVisibility([parentRef], 1)

		self._nodeRefToNodeTree[nodeRef] = newNode = AnchorRegion(nodeRef, self)
		parentNode = self.getNode(parentRef)
		if parentNode is not None:
			parentNode.addNode(newNode)

		newNode.toShowedState()
			
		self.__mustBeUpdated = 1
	
	def __showAnimate(self, nodeRef):
		targetAnimateNodeRef = self._context.getParentNodeRef(nodeRef)
		targetAnimateNode = self._nodeRefToNodeTree.get(targetAnimateNodeRef)
	
		# force the target node to show if not
		if targetAnimateNode is None or not targetAnimateNode.isShowed():
			self.updateVisibility([targetAnimateNodeRef], 1)
			targetAnimateNode = self._nodeRefToNodeTree.get(targetAnimateNodeRef)
			if targetAnimateNode is None:
				print 'PreviewPane: can not show animate , no target'
				return
		
		self.updateAnimationWrapper(nodeRef)
		targetAnimateNode.setSeparatedAnimateNode(nodeRef)
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

		animateRef = mediaRef.getAnimateNode()
		if animateRef is not None:
			if hasattr(animateRef,'_animateEditWrapper'):
				del animateRef._animateEditWrapper
		
		self.__mustBeUpdated = 1

	def __hideAnimate(self, nodeRef):
		targetAnimateNodeRef = self._context.getParentNodeRef(nodeRef)
		targetAnimateNode = self._nodeRefToNodeTree.get(targetAnimateNodeRef)

		if hasattr(nodeRef,'_animateEditWrapper'):
			del nodeRef._animateEditWrapper
		if targetAnimateNode:
			targetAnimateNode.setSeparatedAnimateNode(None)
		self.__mustBeUpdated = 1

	def __hideAnchor(self, nodeRef):
		if not self._nodeRefToNodeTree.has_key(nodeRef):
			# already hidden
			return

		node = self.getNode(nodeRef)
		node.toHiddenState()
		parentNode = node.getParent()
		# remove from region tree
		if parentNode is not None:
			parentNode.removeNode(node)

		del self._nodeRefToNodeTree[nodeRef]
		self.__mustBeUpdated = 1
	
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
					animateNode = nodeTree.getSeparatedAnimateNode()
					if animateNode is None:
						list.append(nodeRef)
					else:
						list.append(animateNode)
					nodeRef._selectPath = 0
				elif nodeTree._path is obj:
					nodeRef._selectPath = 1
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
			if debugPreview: print 'can\'t show viewport ',viewportRef
			return
		self.currentViewport.updateNodes()
		self.previousCtrl.update()
		self.currentViewport.updateAllAttrdict()
		self.__mustBeUpdated = 1

	def onGeomChanging(self, objectList):
		# update only if one object is moving
		if len(objectList) != 1: return
		
		# xxx to optimize
		for nodeRef, nodeTree in self._nodeRefToNodeTree.items():
			animateNode = nodeTree.getSeparatedAnimateNode()
			if animateNode is not None:
				if self._context.isSelected(animateNode):
					nodeRef = animateNode			
			for obj in objectList:
				if nodeTree._graphicCtrl is obj:
					self._context.onFastGeomUpdate(nodeRef, nodeTree.getEditedGeom())
					break

	def onGeomChanged(self, objectList):		
		applyList = []
		animatePathList = []
		# xxx to optimize
		for nodeRef, nodeTree in self._nodeRefToNodeTree.items():
			animateNode = nodeTree.getSeparatedAnimateNode()
			if animateNode is not None:
				if self._context.isSelected(animateNode):
					nodeRef = animateNode
			for obj in objectList:
				if nodeTree._graphicCtrl is obj:
					applyList.append((nodeRef, nodeTree.getEditedGeom()))
					break
				elif nodeTree._path is obj:
					animatePathList.append((nodeRef, nodeTree.getEditedPathGeom()))

		if len(animatePathList) > 0:			
			self._context.applyAnimatePathList(animatePathList)
		self._context.applyGeomList(applyList)

	def mustBeUpdated(self):
		self.__mustBeUpdated = 1

	def fastUpdate(self):
		if self.currentViewport is not None:
			self.currentViewport.fastUpdateAllAttrdict()

	def getPxGeom(self, nodeRef):
		nodeType = self._context.getNodeType(nodeRef)
		if nodeType == TYPE_ANIMATE:
			parentRef = self._context.getParentNodeRef(nodeRef)
			node = self._nodeRefToNodeTree.get(parentRef)
		else:
			node = self._nodeRefToNodeTree.get(nodeRef)
		if node is None:
			print 'Preview: unenable to get wingeom ',nodeRef
			# return the dom value
			return nodeRef.getPxGeom()
		else:
			# return the current value (dom or current animate value according to an eventual visible animate node)
			return node.getWinGeom()

	# return the media geom (which is different from the sub-region geom)
	def getMediaPxGeom(self, nodeRef):
		node = self._nodeRefToNodeTree.get(nodeRef)
		if node is None:
			# failed. Shouldn't happen
			return (0, 0, 100, 100)
		# return the current value (dom or current animate value)
		return node.getMediaWinGeom()
		
	def isShowed(self, nodeRef):
		node = self._nodeRefToNodeTree.get(nodeRef)
		if node is None:
			return 0
		return node.isShowed()

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
		
		self._separatedAnimateNode = None

		# animation path support
		self._path = None

	def _cleanup(self):
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
		self.hideAllNodes()
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
		self._curattrdict['bgcolor'] = self._computedEditBackground
								
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
			self._graphicCtrl.removeListener(self)
			self._graphicCtrl.destroy()
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
		self.hideAllNodes()

	# get the geom for region and media which depends of whether we edit or not an animation.
	# if this node is being animated, we have to get an interpolated value.
	def getWinGeom(self):
		return self._cssResolver.getPxGeom(self._cssNode)

	# get the geom that has been edited and not applied yet in the document
	# note that for anchor this method is overided since there is a conversion to do
	def getEditedGeom(self):
		return self._graphicCtrl.getGeom()

	# get the geom that has been edited and not applied yet in the document
	# note that for anchor this method is overided since there is a conversion to do
	def getEditedPathGeom(self):
		if self._path is not None:
			return self._path.getGeom()
	
	def setSeparatedAnimateNode(self, animateNode):
		self._separatedAnimateNode = animateNode

	def getSeparatedAnimateNode(self):
		return self._separatedAnimateNode

	def _updateAnimateValues(self):
		animateNode = self._ctx._context.getAnimateNode(self._nodeRef)
		if animateNode is not None:
			if hasattr(animateNode, '_animateEditWrapper'):
				wingeom = animateNode._animateEditWrapper.getRectAt(animateNode._currentTime)
			else:
				print 'preview: unenable to get animate edit wrapper ',animateNode
				wingeom = animateNode.getPxGeom()
			x, y, w, h = wingeom
			# put the result into the local css resolver in order than all geom (children) are correctly updated
			updatedList = [('left', x), ('top', y), ('width', w), ('height', h), ('right', None), ('bottom', None)]
			self._cssResolver.setRawAttrs(self._cssNode, updatedList)

	def drawPath(self):
		context = self._ctx._context
		animateNode = context.getAnimateNode(self._nodeRef)

		if animateNode is None or self._parent is None:
			# not animated node
			return

		if not context.canShowAnimationPath(self._nodeRef):
			return
		
		parentShape = self._parent._graphicCtrl
		if parentShape is None or 0:
			return
		
		if hasattr(animateNode, '_animateEditWrapper'):
			animateEditWrapper = animateNode._animateEditWrapper
			keyTimeList = animateEditWrapper.getKeyTimeList()
		else:
			print 'preview: unenable to get animate edit wrapper ',animateNode
			return		

		pointList = []
		# get the media/region position
#		x, y, w, h = self._cssResolver.getPxAbsGeom(self._parent._cssNode)
		for keyTime in keyTimeList:
			aX, aY = animateEditWrapper.getPosAt(keyTime)
			pointList.append((aX, aY))
		if len(pointList) < 2:
			print 'preview: invalid path ',animateNode
			return
		self._path = parentShape.addPolyline(pointList, self._graphicCtrl)

	def removePath(self):
		if self._path is None:
			return
		
		self._path.destroy()

	def _getSelectedObject(self):
		if self._path:
			nodeRef = self._nodeRef
			if hasattr(nodeRef, '_selectPath') and nodeRef._selectPath:
				selObj = self._path
			else:
				selObj = self._graphicCtrl
		else:
			selObj = self._graphicCtrl
		return selObj

	def updateNodes(self):
		if self._wantToShow:
			if self.isShowed():
				self.hideAllNodes()
			self.show()
			for child in self._children:
				child.updateNodes()
		else:
			self.hideAllNodes()
					
class Region(Node):
	def __init__(self, nodeRef, ctx):
		Node.__init__(self, nodeRef, ctx)
		self._nodeType = TYPE_REGION
		self._wantToShow = 0

		self._cssNode = self._cssResolver.newRegion()
		
	def importAttrdict(self):
		Node.importAttrdict(self)

		self._cssNode.copyRawAttrs(self._nodeRef.getCssId())
		self._updateAnimateValues()
		
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
			self._updateAnimateValues()
			self._curattrdict['wingeom'] = self.getWinGeom()
			self._graphicCtrl.setAttrdict(self._curattrdict)

	def hide(self):
		if self.isShowed():
			parent = self._parent
			self._cssResolver.unlink(self._cssNode)			
			Node.hide(self)

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
		self._updateAnimateValues()
				
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

		node = self._nodeRef
		chtype = node.GetChannelType()
		if chtype == 'brush':
			# show just the brush color	(the bgcolor is overrided whatever its value)
			self._curattrdict['bgcolor'] = node.GetAttrDef('fgcolor', (0,0,0))
			self._curattrdict['transparent'] = 0

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

		if self._graphicCtrl:
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
		
		node = self._nodeRef
		
		# XXX copy from StructureWidgets to determinate the image to showed
		# XXX should be merged at some point
		mime = node.GetComputedMimeType()
		if mime == 'image/vnd.rn-realpix':
			chtype = 'RealPix'
		elif mime == 'text/vnd.rn-realtext':
			chtype = 'RealText'
		elif mime == 'video/vnd.rn-realvideo':
			chtype = 'RealVideo'
		elif mime in ('audio/vnd.rn-realaudio', 'audio/x-pn-realaudio', 'audio/x-realaudio'):
			chtype = 'RealAudio'
		else:
			chtype = node.GetChannelType()

		if chtype == 'brush':
			# special case for brush elements: no image to show and no scaling.
			self.drawPath()
			return
		
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
			
			# the algorithm to show the preview of the media depend of its type
			# for medias whose we can only show the icons (text, html, svg, ...), we show a matrix of icons to
			# keep the real size and ratio. Otherwise it's ugly
			if canBeScaled:
				self._graphicCtrl.setImage(f, fit, mediadisplayrect)
			else:
				self._graphicCtrl.drawbox(mediadisplayrect)
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
		self.drawPath()
		
	def fastUpdateAttrdict(self):
		chtype = self._nodeRef.GetChannelType()
		if chtype == 'image':
			self._updateAnimateValues()
			
			self._curattrdict = self._curattrdict.copy()
			self._updateAnimateValues()
			self._curattrdict['wingeom'] = self.getWinGeom()
			self._graphicCtrl.setAttrdict(self._curattrdict)
			mediadisplayrect  = self._cssResolver.getPxGeom(self._mediaCssNode)
			
			self._graphicCtrl.updateImage('fill', mediadisplayrect)
		else:
			# XXX for now, just recreat the media. Should be optimized
			if self._graphicCtrl is not None:
				isSelected = self._graphicCtrl.isSelected or (hasattr(self._nodeRef, '_selectPath') and self._nodeRef._selectPath)
			self.hide()
			self.show()
			if isSelected and self._graphicCtrl:	
				self._ctx.previousCtrl.appendSelection([self._getSelectedObject()])

	def hide(self):
		if self.isShowed():
			parent = self._parent
			self._cssResolver.unlink(self._mediaCssNode)			
			self._cssResolver.unlink(self._cssNode)
			Node.hide(self)
			self.removePath()

	def _cleanup(self):
		# XXX should allow the gc to destroy the media
		# XXX To check if really need it
		if self._mediaCssNode is not None:
			self._mediaCssNode.defaultSizeHandler = None
		Node._cleanup(self)
		
	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())

	def getMediaWinGeom(self):
		return self._cssResolver.getPxGeom(self._mediaCssNode)

class AnchorRegion(Region):
	def __init__(self, node, ctx):
		nodeRef = node
		Region.__init__(self, nodeRef, ctx)
		self._nodeType = TYPE_ANCHOR
		self._wantToShow = 1

	# the returned value is relative to the media (not to the sub-region)
	def getWinGeom(self):
		nodeRef = self._nodeRef
		parentGeom  = self._parent.getMediaWinGeom()
		pL, pT, pW, pH = parentGeom
		coords = nodeRef.attrdict.get('acoords')
		if coords is None or len(coords) != 4:
			return (0, 0, pW, pH)
		l, t, r, b = coords
		# convert percent values
		if type(l) == type(0.0):
			l = int(pW*l)
		if type(t) == type(0.0):
			t = int(pH*t)
		if type(r) == type(0.0):
			r = int(pW*r)
		if type(b) == type(0.0):
			b = int(pH*b)
		w = r-l
		h = b-t
		return (l, t, w, h)

	def importAttrdict(self):
		Node.importAttrdict(self)
				
		showMode = self._ctx._context.getShowEditBackgroundMode(self._nodeRef)
		self._curattrdict['transparent'] = 1

		parentGeom  = self._parent.getMediaWinGeom()
		wingeom = self.getWinGeom()
		# that value is relative to the media. To show it, it has to be relative to the media
		if wingeom is None or parentGeom is None:
			return
		x, y, w, h = wingeom
		pX, pY, pW, pH = parentGeom
			
		self._curattrdict['wingeom'] = (pX+x, pY+y, w, h)
		self._z = self._nodeRef.GetAttrDef('z', 0)
		self._curattrdict['z'] = self._z

	def updateShowName(self,value):
		# no name showed
		pass

	def show(self):
		if self._parent._graphicCtrl == None:
			print 'Anchor.show : no parent'
			return

		if self.isShowed():
			# hide this node and its sub-nodes
			self.hideAllNodes()
			
		parent = self._parent

		self.importAttrdict()

		if self._curattrdict.get('wingeom') is None:
			# it means we edit an shape we don't support yet (circle, poly, ...)
			return
		
		self._graphicCtrl = parent._graphicCtrl.addRegion(self._curattrdict, self.getName())
		self._graphicCtrl.showName(0)		
		self._graphicCtrl.setListener(self)

	def getEditedGeom(self):
		x, y, w, h = self._graphicCtrl.getGeom()

		# that value is relative to the sub-region. We have to return a value relative to the media
		parentGeom  = self._parent.getMediaWinGeom()
		if parentGeom is None:
			# failed. Shouldn't happen
			return (0, 0, 100, 100)
		pX, pY, pW, pH = parentGeom
		return (x-pX, y-pY, w, h)
		
	def fastUpdateAttrdict(self):
		# XXX for now, just recreat the anchor. Should be optimized
		if self._graphicCtrl is not None:
			isSelected = self._graphicCtrl.isSelected or (hasattr(self._nodeRef, '_selectPath') and self._nodeRef._selectPath)
		self.hide()
		self.show()
		if isSelected and self._graphicCtrl:
			self._ctx.previousCtrl.appendSelection([self._getSelectedObject()])
			
	def hide(self):
		if self.isShowed():
			Node.hide(self)
		
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

	def updateNodes(self):
		self.hideAllNodes()
		self.show()
		for child in self._children:
			child.updateNodes()

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
					windowinterface.showmessage('Cannot open trace image %s:\n %s' % (f, arg), mtype = 'error')

		self._graphicCtrl.setListener(self)
		
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
		if debug: print 'LayoutView.updateAllAttrdict:',self.getName()
		self.computeEditBackground()
		Node.updateAllAttrdict(self)
		# XXX if z-order has changed, recompute edit background, and re-import attrs
		# XXX not really clean !
		if self._mustUpdateEditBackground:
			self.updateAllAttrdict()
			return
		# for now refresh all
		self.updateNodes()

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())


		
