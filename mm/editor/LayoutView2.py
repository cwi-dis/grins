from LayoutViewDialog2 import LayoutViewDialog2
from windowinterface import UNIT_PXL

from usercmd import *

import MMAttrdefs
import settings
import features
import windowinterface

ALL_LAYOUTS = '(All Channels)'

debug = 0
debugAlign = 0
debug2 = 0
debugPreview = 0

COPY_PASTE_MEDIAS = 1

TYPE_ABSTRACT, TYPE_REGION, TYPE_MEDIA, TYPE_VIEWPORT = range(4)

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
		self.__initDefaultRegion()

	def destroy(self):
		self.__channelTreeRef = None
		self.__mmnodeTreeRef = None
		self.__nodeList = None
		self.__rootList = None

	#
	# Experimental code to manage a default region
	#
	
	def __initDefaultRegion(self):
		self.__defaultRegion = None
		self.__defaultViewport = None

	def __getDefaultViewport(self):
		viewportRefList = self.__channelTreeRef.getviewports()
		self.__defaultViewport = viewportRefList[0]
		return self.__defaultViewport
	
	def __getDefaultRegion(self):
		if self.__defaultRegion == None:
			defaultViewport = self.__getDefaultViewport()
			self.__defaultRegion = FakeMMChannel('Unreferenced medias')
			self.__defaultRegion.setParent(defaultViewport)
		return self.__defaultRegion

	def _checkDefaultViewport(self):
		if self.__defaultRegion != None:
			self.__checkRegionNodeList(self.__defaultViewport, self.__defaultRegion, 1)

	#
	# End experimental code to manage a default region
	#
		
	# return tree if node is a valid media nodes
	def _isValidMMNode(self, node):
		if node == None:
			return 0
		from MMTypes import leaftypes
		if not node.type in leaftypes:
			return 0
		chtype = node.GetChannelType()
		if chtype == None or chtype == 'animate':
			return 0
		return 1

	# check the media node references and update the internal structure
	def __checkMediaNodeList(self, nodeRef):
		if debug2: print 'treeHelper.__checkMediaNodeList : start ',nodeRef
		if self._isValidMMNode(nodeRef):
			region = nodeRef.GetChannel()
			if region == None:
				pass
				# the region doesn't exist, return the default region
#				parentRef = self.__getDefaultRegion()
			else:
				parentRef = region

			if region != None:				
				tParentNode =  self.__nodeList.get(parentRef)
				if tParentNode == None:
					tParentNode = self.__nodeList[parentRef] = TreeNodeHelper(parentRef, TYPE_REGION)
				tNode =  self.__nodeList.get(nodeRef)
				if tNode == None or not tParentNode.hasChild(tNode):
					tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_MEDIA)
					tParentNode.addChild(tNode)
				else:
					tNode.checkMainUpdate()
					tNode.isUsed = 1
						
		for child in nodeRef.GetChildren():
			self.__checkMediaNodeList(child)
		if debug2: print 'treeHelper.__checkMediaNodeList : end ',nodeRef

	# check the media node references and update the internal structure
	def _checkMediaNodeList(self):
		self.__checkMediaNodeList(self.__mmnodeTreeRef)

	# check the region/viewport node references and update the internal structure
	def __checkRegionNodeList(self, parentRef, nodeRef, isFakePart = 0):
		if debug2: print 'treeHelper.__checkRegionNodeList : start ',nodeRef
		tNode =  self.__nodeList.get(nodeRef)
		if parentRef != None:
			# case for regions
			tParentNode =  self.__nodeList.get(parentRef)
			if tParentNode == None:
				if debug2: print 'treeHelper.__checkMediaNodeList : the parent doesn''t exist, create a new parent tree node'
				tParentNode = self.__nodeList[parentRef] = TreeNodeHelper(parentRef, TYPE_REGION)
			if tNode == None:
				if debug2: print 'treeHelper.__checkMediaNodeList : it''s a new region, create a new tree node'
				tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_REGION)
				tParentNode.addChild(tNode)
			elif not tParentNode.hasChild(tNode):
				if debug2: print 'treeHelper.__checkMediaNodeList : the parent has changed children=',tNode.children
				oldNode = tNode
				tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_REGION)
				tNode.children = oldNode.children
				tParentNode.addChild(tNode)
			else:
				tNode.checkMainUpdate()
				tNode.isUsed = 1
		elif tNode == None:
			# case for new viewport 
			tNode = self.__nodeList[nodeRef] = TreeNodeHelper(nodeRef, TYPE_VIEWPORT)
			self.__rootList[nodeRef] = tNode
		else:
			# case for existing viewport
			tNode.checkMainUpdate()							
			tNode.isUsed = 1
		
		if not isFakePart:
			for subreg in self.__channelTreeRef.getsubregions(nodeRef):
				self.__checkRegionNodeList(nodeRef, subreg)
						
		if debug2: print 'treeHelper.__checkRegionNodeList : end ',nodeRef

	# check the region/viewport node references and update the internal structure
	def _checkRegionNodeList(self):
		viewportRefList = self.__channelTreeRef.getviewports()
		for viewportRef in viewportRefList:
			self.__checkRegionNodeList(None, viewportRef)
		
	# this method is called when a node has to be deleted
	def __onDelNode(self, parent, node, top=1):
		if debug: print 'treeHelper.__onDelNode : ',node.nodeRef
		for child in node.children.keys():
			self.__onDelNode(node, child, 0)
		if parent != None:
			if top:
				# extract from the parent only if it's the top node to delete
				# it allows to not affect the sub-nodes if this node has to be moved
				del parent.children[node]
			parentRef = parent.nodeRef
		else:
			parentRef = None
			del self.__rootList[node.nodeRef]
		self._context.onDelNodeRef(parentRef, node.nodeRef)
		# we can't delete now the node because the node may have moved
		self.__nodeListToDel.append(node.nodeRef)

	# this method is called when a node has to be added	
	def __onNewNode(self, parent, node):
		if debug: print 'treeHelper.__onNewNode : ',node.nodeRef, 'child = ',node.children
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
		# if the node is marked to delete, we have to restore erase the mark
		# note don't use remove. more efficient
		for ind in range(len(self.__nodeListToDel)):
			if self.__nodeListToDel[ind] is node.nodeRef:
				del self.__nodeListToDel[ind]
				break

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

	# this method look for all mutations relative to the previous update		
	def __detectNewMutation(self, parent, node):
		if debug2: print 'treeHelper.__detectNewMutation : start ',node.nodeRef
		# detect the new nodes
		if node.isNew:
			self.__onNewNode(parent, node)
		else:
			# detect if need to update the main attributes. basicly id and type
			if node.isUpdated:
				self._context.onMainUpdate(node.nodeRef)
				node.isUpdated = 0
			# if no changment, check in children
			for child in node.children.keys():
				self.__detectNewMutation(node, child)
			# reset the flags the the next time
			node.isUsed = 0
		if debug2: print 'treeHelper.__detectNewMutation : end ',node.nodeRef
			
	# this method look for all mutations relative to the previous update		
	def _detectMutation(self):
		self.__nodeListToDel = []
		for key, root in self.__rootList.items():
			self.__detectDelMutation(None, root)
		for key, root in self.__rootList.items():
			self.__detectNewMutation(None, root)
		for node in self.__nodeListToDel:
			del self.__nodeList[node]

	#
	# public methods
	#

	# the method look for all mutations relative to the previous update, and call the appropriate handlers
	# in the right order for each basic operation
	def onTreeMutation(self):
		if debug: print 'treeHelper.onTreeMutation start'
		self.__initDefaultRegion()
		self._checkMediaNodeList()
		self._checkRegionNodeList()
#		self._checkDefaultViewport()
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

#
# Experimental code to manage a default region
#
	
class FakeMMChannel:
	def __init__(self, name):
		self._parent = None
		self.attrdict = {}
		self.name = name
		self.collapsed = 0

	def GetAttrDef(self, attr, default=None):
		return default
		
	def getClassName(self):
		return 'FakeMMChannel'
	
	def GetParent(self):
		return self._parent

	def setParent(self, parent):
		self._parent = parent

	#
	# End experimental code to manage a default region
	#
	
class TreeNodeHelper:
	def __init__(self, nodeRef, type):
		# this method is called a lot of times. It has to be optimized
		# read directly the attributes on the node: more efficient
		self.isNew = 1
		self.isUsed = 1
		self.isUpdated = 0
		self.nodeRef = nodeRef
		self.children = {}
		self.type = type
		if type == TYPE_MEDIA:
			self.name = nodeRef.attrdict.get('name')
			self.mediatype = nodeRef.GetChannelType()
		else:
			name = nodeRef.attrdict.get('regionName')
			if name == None:
				self.name = nodeRef.name

	def hasChild(self, child):
		return self.children.has_key(child)
	
	def addChild(self, child):
		self.children[child] = 1

	def checkMainUpdate(self):
		# this method is called a lot of times. It has to be optimized
		# read directly the attributes on the node: more efficient
		nodeRef = self.nodeRef
		if self.type == TYPE_MEDIA:
			name = nodeRef.attrdict.get('name')
			mediatype = nodeRef.GetChannelType()
			if name != self.name or mediatype != self.mediatype:
				self.isUpdated = 1
				self.name = name
				self.mediatype = mediatype
		else:
			name = nodeRef.attrdict.get('regionName')
			if name == None:
				name = nodeRef.name
			if name != self.name:
				self.isUpdated = 1
				self.name = name
		
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
		self.currentFocus = None
		# allow to identify if the focus has been fixed by this view
		self.myfocus = None	# used to break recursion in setglobalfocus -> globalfocuschanged
		self.commitAlreadyUpdated = 0

		# when you swap to the pause state, the current region showed list is saved
		# it allows to restore the context when document is stopped
		# XXX may changed
		# self.stopSelectedRegionList = []
		# self.stopSelectedMediaList = []

		self.showName = 1
		self.asOutLine = 0
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
				ATTRIBUTES(callback = (self.onEditProperties, ())),
				NEW_REGION(callback = (self.onNewRegion, ())),
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				DELETE(callback = (self.onDelNode, ())),
				COPY(callback = (self.onCopy, ())),
				CUT(callback = (self.onCut, ())),
				ATTRIBUTES_LAYOUT(callback = (self.onLayoutProperties, ())),
				]
		else:
			self.commandViewportList = [
				ATTRIBUTES(callback = (self.onSelectBgColor, ())),
				]
		self.__appendZoomCommands(self.commandViewportList)

	def mkregioncommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandRegionList = [
				ATTRIBUTES(callback = (self.onEditProperties, ())),
				NEW_REGION(callback = (self.onNewRegion, ())),
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				DELETE(callback = (self.onDelNode, ())),
				COPY(callback = (self.onCopy, ())),
				CUT(callback = (self.onCut, ())),
				ATTRIBUTES_LAYOUT(callback = (self.onLayoutProperties, ())),
				]
		else:
			self.commandRegionList = [
				ATTRIBUTES(callback = (self.onSelectBgColor, ())),
				]
		self.__appendZoomCommands(self.commandRegionList)

	def mkmediacommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMediaList = [
				ATTRIBUTES(callback = (self.onEditProperties, ())),
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				ATTRIBUTES_ANCHORS(callback = (self.onAnchors, ())),
				ATTRIBUTES_LAYOUT(callback = (self.onLayoutProperties, ())),
				]
			if COPY_PASTE_MEDIAS:
				self.commandMediaList.append(COPY(callback = (self.onCopy, ())))
				self.commandMediaList.append(CUT(callback = (self.onCut, ())))
		else:
			self.commandMediaList = []
		self.commandMediaList.append(CONTENT(callback = (self.onContent, ())))
		self.__appendZoomCommands(self.commandMediaList)
			
	def mknositemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandNoSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandNoSItemList = []
		self.__appendZoomCommands(self.commandNoSItemList)

	# available command when several items are selected
	def mkmultisitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMultiSItemList = []		
		self.__appendZoomCommands(self.commandMultiSItemList)
		
	def mkmultisiblingsitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSiblingSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMultiSiblingSItemList = []
		self.__appendAlignCommands()
		self.__appendZoomCommands(self.commandMultiSiblingSItemList)

	def __appendZoomCommands(self, commandlist):
		commandlist.append(CANVAS_ZOOM_IN(callback = (self.onZoomIn, ())))
		commandlist.append(CANVAS_ZOOM_OUT(callback = (self.onZoomOut, ())))
			
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
		self.currentFocus = None
		self.myfocus = None
		self.commitAlreadyUpdated = 0
		
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
			if nodeRef.getClassName() != 'FakeMMChannel':
				self.previousWidget.addViewport(nodeRef)			
			self.treeWidget.appendViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			if nodeRef.getClassName() != 'FakeMMChannel':
				self.previousWidget.addRegion(parentRef, nodeRef)
			self.treeWidget.appendRegion(parentRef, nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.treeWidget.appendMedia(parentRef, nodeRef)
		
	def onDelNodeRef(self, parentRef, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			if nodeRef.getClassName() != 'FakeMMChannel':
				self.previousWidget.removeViewport(nodeRef)
			self.treeWidget.removeNode(nodeRef)
		elif nodeType == TYPE_REGION:
			if nodeRef.getClassName() != 'FakeMMChannel':
				self.previousWidget.removeRegion(nodeRef)
			self.treeWidget.removeNode(nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.treeWidget.removeNode(nodeRef)
			self.previousWidget.removeMedia(nodeRef)

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
		if self.commitAlreadyUpdated:
			self.commitAlreadyUpdated = 0
			return
		if type in ('REGION_GEOM', 'MEDIA_GEOM'):
			self.previousWidget.updateRegionTree()
		elif type == 'REGION_TREE':
			self.treeMutation()
			self.previousWidget.updateRegionTree()
		else:
			self.rebuildAll()

		# after a commit, the focus may have changed
		self.currentFocus = self.editmgr.getglobalfocus()
		self.updateFocus(1)
				
	def isValidMMNode(self, node):
		return self.treeHelper._isValidMMNode(node)

	def focusOnList(self, focusobject, keepShowedNodes=0):
		# update command list

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

		self.currentSelectedNodeList = focusobject

		# update widgets
		for id, widget in self.widgetList.items():
			widget.selectNodeList(focusobject, keepShowedNodes)

		if len(focusobject) == 0:
			self.updateCommandList(self.commandNoSItemList)
		elif len(focusobject) == 1:
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

		# determinate is paste is valid		
		activePaste = 0
		t, n = self.editmgr.getclip()
		if t == 'viewport' and n is not None:
			activePaste = 1
		elif len(self.currentSelectedNodeList) == 1: # only simple selection
			selectedNode = self.currentSelectedNodeList[0]
			selectedType = self.getNodeType(selectedNode)
			# Enable "paste" commands depending on what is in the clipboard.
			if selectedType in (TYPE_VIEWPORT, TYPE_REGION) and \
				t in ('region', 'viewport') and n is not None:
				activePaste = 1
			elif t == 'media' and selectedType == TYPE_REGION and COPY_PASTE_MEDIAS:
				# check that the media is valid and still in the 'body' part
				if self.existRef(selectedNode):
					activePaste = 1

		if activePaste:
			commandlist.append(PASTE(callback = (self.onPaste, ())))

		self.setcommandlist(commandlist)
		
	def updateFocus(self, keepShowedNodes=0):
		if debug: print 'LayoutView.updateFocus: focus on List'
		self.focusOnList(self.currentFocus, keepShowedNodes)

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
		className = nodeRef.getClassName()
		if className == 'MMNode':
			region = nodeRef.GetChannel()
		else:
			region = nodeRef

		if region != None:
			return self.__channelTreeRef.getviewport(region)
		
		return None
	
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
			self.editmgr.addchannel(id, 0, 'layout')
			self.editmgr.setchannelattr(id, 'base_window', parentRef.name)
			self.editmgr.setchannelattr(id, 'regionName', regionName)
			self.editmgr.commit('REGION_TREE')

	def applyNewViewport(self, name):
		if self.editmgr.transaction():
			self.editmgr.addchannel(name, 0, 'layout')
			self.editmgr.setchannelattr(name, 'transparent', 0)
			self.editmgr.setchannelattr(name, 'showEditBackground', 1)
			self.editmgr.setchannelattr(name, 'width', 400)
			self.editmgr.setchannelattr(name, 'height', 400)
			self.editmgr.commit('REGION_TREE')

	def __recurDelNode(self, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		# if the node is a media, we just remove the link with the region
		if nodeType == TYPE_MEDIA:
			# we do nothing.
			# XXX we can't remove the region link, because a media may be associated to more than one channel
			# XXX (region name). need to think about
			pass
		elif nodeType in (TYPE_VIEWPORT, TYPE_REGION):
			# remove the children before to remove the node
			children = self.getChildren(nodeRef)
			for child in children:
				self.__recurDelNode(child)

#			self.treeHelper.delNode(nodeRef)
			if nodeRef.getClassName() != 'FakeMMChannel':
				self.editmgr.delchannel(nodeRef.name)
			
	def applyDelRegion(self, regionRef):
		if self.editmgr.transaction():
			# update directly (more efficient. No need to compare all nodes)
			self.__recurDelNode(regionRef)
#			self.commitAlreadyUpdated = 1 
			self.editmgr.commit('REGION_TREE')
			
	def applyDelViewport(self, viewportRef):
		if self.editmgr.transaction():
			# update directly (more efficient. No need to compare all nodes)
			self.__recurDelNode(viewportRef)
#			self.commitAlreadyUpdated = 1 
			self.editmgr.commit('REGION_TREE')

	def applyAttrList(self, nodeRefAndValueList):
		if self.editmgr.transaction():
			for nodeRef, attrName, attrValue in nodeRefAndValueList:
				nodeType = self.getNodeType(nodeRef)
				if nodeType in (TYPE_VIEWPORT, TYPE_REGION):					
					self.editmgr.setchannelattr(nodeRef.name, attrName, attrValue)
				elif nodeType == TYPE_MEDIA:
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
		l,t,w,h = referenceNode.getPxGeom()
		referenceValue = l

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = nodeRef.getPxGeom()
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
		l,t,w,h = referenceNode.getPxGeom()
		referenceValue = int(l+w/2)
		
		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = nodeRef.getPxGeom()
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
		l,t,w,h = referenceNode.getPxGeom()
		referenceValue = l+w

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = nodeRef.getPxGeom()
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
		l,t,w,h = referenceNode.getPxGeom()
		referenceValue = t

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = nodeRef.getPxGeom()
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
		l,t,w,h = referenceNode.getPxGeom()
		referenceValue = int(t+h/2)
		
		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = nodeRef.getPxGeom()
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
		l,t,w,h = referenceNode.getPxGeom()
		referenceValue = t+h

		# make a list of node/attr to change
		list = []
		for nodeRef in self.currentSelectedNodeList:
			if not nodeRef is referenceNode:
				l,t,w,h = nodeRef.getPxGeom()
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
			l,t,w,h = node.getPxGeom()
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
		l,t,w,h = firstNodeRef.getPxGeom()
		posRef = l+w
		for nodeRef in sortedList[1:]:
			l,t,w,h = nodeRef.getPxGeom()
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
			l,t,w,h = node.getPxGeom()
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
		l,t,w,h = firstNodeRef.getPxGeom()
		posRef = t+h
		for nodeRef in sortedList[1:]:
			l,t,w,h = nodeRef.getPxGeom()
			t = posRef+space
			posRef = t+h
			# make the new geom
			self.__makeAttrListToApplyFromGeom(nodeRef, (l,t,w,h), list)
		self.applyAttrList(list)

	# this method will be used by the sort method
	def __cmpNode(self, node1, node2):
		l1,t1,w1,h1 = node1.getPxGeom()
		l2,t2,w2,h2 = node2.getPxGeom()
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
		if self.currentSelectedNodeList != None:
			import NodeEdit
			NodeEdit.showeditor(self.currentSelectedNodeList[0])
		
	def onEditProperties(self):
		if self.currentSelectedNodeList != None:
			self.editProperties(self.currentSelectedNodeList[0])

	def onLayoutProperties(self):
		if self.currentSelectedNodeList != None:
			self.editProperties(self.currentSelectedNodeList[0])

	def onAnchors(self):
		if self.currentSelectedNodeList != None:
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
		
		if len(self.currentSelectedNodeList) > 0:
			nodeType = self.getNodeType(self.currentSelectedNodeList[0])
			if nodeType == TYPE_VIEWPORT:
				self.delViewport(self.currentSelectedNodeList[0])
			elif nodeType == TYPE_REGION:
				self.delRegion(self.currentSelectedNodeList[0])

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

	def onCopy(self):
		self.__cleanClipboard()
		
		# for now, support only single selection
		if len(self.currentSelectedNodeList) == 1:
			selectedNode = self.currentSelectedNodeList[0]
			self.__copyIntoClipboard(selectedNode)
			# XXX just useful to update command list
			self.updateFocus()

	def onCut(self):
		self.__cleanClipboard()
		
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashs
		self.flushChangement()
		
		# for now, support only simple selection
		if len(self.currentSelectedNodeList) == 1:
			selectedNode = self.currentSelectedNodeList[0]
			self.__copyIntoClipboard(selectedNode)
			
			# call del region without check if there is some medias inside
			nodeType = self.getNodeType(selectedNode)
			if nodeType == TYPE_REGION:
				self.delRegion(selectedNode, 0)
			elif nodeType == TYPE_VIEWPORT:
				self.delViewport(selectedNode, 0)
			elif nodeType == TYPE_MEDIA:
				if COPY_PASTE_MEDIAS and self.editmgr.transaction():
					parentRef = self.getParentNodeRef(selectedNode, TYPE_MEDIA)
					self.setglobalfocus([parentRef])
					self.updateFocus()
					self.editmgr.setnodeattr(selectedNode, 'channel', None)
					self.editmgr.commit()
				
	def	onPaste(self):
		# apply some command which are automaticly applied when a control lost the focus
		# it avoids some recursives transactions and some crashes
		self.flushChangement()

		# for now, support only simple selection
		if len(self.currentSelectedNodeList) == 1:
			selectedNode = self.currentSelectedNodeList[0]
			type, node = self.editmgr.getclip()
			# XXXX Note by Jack: we may have to call getclipcopy() here in some cases
			# to make sure we don't get multiple references to the same MMChannel object
			# or something.
			cNode = None
			if self.editmgr.transaction():
				if type == 'region':
					cNode = node.CopyIntoContext(self.context, selectedNode)
				elif type == 'viewport':
					cNode = node.CopyIntoContext(self.context, None)
				elif type == 'media' and COPY_PASTE_MEDIAS:
					doPaste = 0
					if self.existRef(node):
						ret = windowinterface.GetOKCancel("Do you really want to move the media to the selected region ?", self.toplevel.window)
						if ret == 0:
							# ok
							doPaste = 1
					else:
						doPaste = 1
					if doPaste and self.getNodeType(selectedNode) == TYPE_REGION:
						cNode = node
						self.editmgr.setnodeattr(node, 'channel', selectedNode.name)
				self.editmgr.commit()
				if cNode != None:
					self.setglobalfocus([cNode])
				self.updateFocus()

	def __copyIntoClipboard(self, selectedNode):
		if self.getNodeType(selectedNode) == TYPE_REGION:
			exportedNode = selectedNode.deepExport()
			self.editmgr.setclip('region', exportedNode)
		elif self.getNodeType(selectedNode) == TYPE_VIEWPORT:
			exportedNode = selectedNode.deepExport()
			self.editmgr.setclip('viewport', exportedNode)
		elif self.getNodeType(selectedNode) == TYPE_MEDIA:
			# XXX special case, put for now just the node itself
			self.editmgr.setclip('media', selectedNode)
				
	def __cleanClipboard(self):
		# XXX to do something
		pass

	def newRegion(self, parentRef):
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
		baseName = 'viewport'
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

	def delRegion(self, regionRef, check=1):
		# if this region or any sub region contain a media, show a warning message, and ask confirmation
		if check and self.doesContainMedias(regionRef):
			ret = windowinterface.GetOKCancel("The region that you want to remove contains some medias. Do you want to continue ?", self.toplevel.window)
			if ret != 0:
				# cancel
				return
			
		parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
		self.setglobalfocus([parentRef])
		self.updateFocus()
		self.applyDelRegion(regionRef)


	# check if moving a source node into a target node is valid
	def isValidMove(self, sourceNodeRef, targetNodeRef):
		if sourceNodeRef == None or targetNodeRef == None:
			return 0

		if targetNodeRef.getClassName() == 'FakeMMChannel':
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
		
		return 1

	# move the source node into a target node
	def moveNode(self, sourceNodeRef, targetNodeRef):
		if not self.isValidMove(sourceNodeRef, targetNodeRef):
			return 0
		
		sourceNodeType = self.getNodeType(sourceNodeRef)
		targetNodeType = self.getNodeType(targetNodeRef)
		
		if sourceNodeType == TYPE_MEDIA and targetNodeType == TYPE_REGION:
			if self.editmgr.transaction():
				self.editmgr.setnodeattr(sourceNodeRef, 'channel', targetNodeRef.name)
				self.editmgr.commit('REGION_TREE')
		elif targetNodeType in (TYPE_REGION, TYPE_VIEWPORT):
			if self.editmgr.transaction():
				self.editmgr.setchannelattr(sourceNodeRef.name, 'base_window', targetNodeRef.name)
				self.editmgr.commit('REGION_TREE')

		return 1
	
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
	
	def delViewport(self, nodeRef, check=1):
		# for now, we have to keep at least one viewport
		currentViewportList = self.getViewportRefList()
		if len(currentViewportList) <= 1:
			msg = "you can't delete or cut the last viewport"
			windowinterface.showmessage(msg, mtype = 'error')
			return

		# if this region or any sub region contain a media, show a warning message, and ask confirmation
		if check and self.doesContainMedias(nodeRef):
			ret = windowinterface.GetOKCancel("The topLayout element that you want to remove contains some medias. Do you want to continue ?", self.toplevel.window)
			if ret != 0:
				# cancel
				return
		
		# change the focus
		# choice another viewport to show (this first in the list)
		currentViewportList = self.getViewportRefList()
		for viewportRef in currentViewportList:
			if viewportRef != nodeRef:
				self.setglobalfocus([viewportRef])
				self.updateFocus()
				break
		
		self.applyDelViewport(nodeRef)

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
		self.dialogCtrl = context.dialogCtrl

#
# z field widget management
#

class ZFieldWidget(LightWidget):
	def __init__(self, context):
		LightWidget.__init__(self, context)

	#
	# inherited methods
	#
	
	def show(self):
		self.dialogCtrl.setListener('RegionZ', self)

	def destroy(self):
		self.dialogCtrl.removeListener('RegionZ')
		
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		if len(nodeRefList) != 1:
			# if no node selected or several nodes are selected in the same time, disable the fields
			self.__unselect()
			return
		nodeRef = nodeRefList[0]
		
		nodeType = self._context.getNodeType(nodeRef)
		if nodeRef.getClassName() == 'FakeMMChannel' or (nodeType == TYPE_MEDIA and not nodeRef.GetChannel()):
			self.__unselect()
			return
		
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
# geom field widget management
#
		
class GeomFieldWidget(LightWidget):
	def __init__(self, context):
		LightWidget.__init__(self, context)
	
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
		self.dialogCtrl.removeListener('RegionZ')
	
	def selectNodeList(self, nodeRefList, keepShowedNodes=0):
		# if no node selected or several nodes are selected in the same time, disable the fields
		if len(nodeRefList) != 1:
			self.__unselect()
			return
		nodeRef = nodeRefList[0]
		
		nodeType = self._context.getNodeType(nodeRef)
		
		if nodeRef.getClassName() == 'FakeMMChannel' or (nodeType == TYPE_MEDIA and not nodeRef.GetChannel()):
			self.__unselect()
			return
		
		if nodeType == TYPE_VIEWPORT:
			self.__updateViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			self.__updateRegion(nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.__updateMedia(nodeRef)
			
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

		geom = nodeRef.getPxGeom()	
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
		
		geom = nodeRef.getPxGeom()		
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
			x,y,w,h = nodeRef.getPxGeom()
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
			x,y,w,h = nodeRef.getPxGeom()
			if ctrlName == 'RegionX':
				x = value
			elif ctrlName == 'RegionY':
				y = value			
			elif ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			self._context.applyGeom(nodeRef, (x,y,w,h))

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
						if self._context.getNodeType(child) != TYPE_MEDIA:
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

	def appendMedia(self, pNodeRef, nodeRef):
		mediaType = nodeRef.GetChannelType()
		name = self._context.getShowedName(nodeRef, TYPE_MEDIA)
		ret = self.treeCtrl.insertNode(self.nodeRefToNodeTreeCtrlId[pNodeRef], name, mediaType, mediaType)
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef

	def appendViewport(self, nodeRef):
		name = self._context.getShowedName(nodeRef, TYPE_VIEWPORT)
		ret = self.treeCtrl.insertNode(0, name, 'viewport', 'viewport')
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef

		# save the new node for expand. The expand operation can't be done here
		self.__nodeRefListToExpand.append(nodeRef)
			
	def appendRegion(self, pNodeRef, nodeRef):
		name = self._context.getShowedName(nodeRef, TYPE_REGION)
		ret = self.treeCtrl.insertNode(self.nodeRefToNodeTreeCtrlId[pNodeRef], name, 'region', 'region')
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef

		# save the new node for expand. The expand operation can't be done here
		self.__nodeRefListToExpand.append(nodeRef)

	def removeNode(self, nodeRef):
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
		self.treeCtrl.beginDrag(type, objectId)

	def __dragObjectIdToNodeRef(self, type, objectId):
		nodeRef = None
		if type == 'Media': 
			# retrieve the reference of the source node
			try:
				nodeRef = self._context.context.mapuid(objectId)
			except:
				nodeRef = None
						
		elif type == 'Region':
			# retrieve the reference of the source node
			nodeRef = self._context.context.getchannel(objectId)

		return nodeRef			
		
	def onDragOver(self, nodeTreeCtrlId, type, objectId):
		targetNodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		sourceNodeRef = self.__dragObjectIdToNodeRef(type, objectId)
		if self._context.isValidMove(sourceNodeRef, targetNodeRef):
			# XXX should change
			return LayoutViewDialog2.DROPEFFECT_MOVE
		else:
			# XXX should change
			return LayoutViewDialog2.DROPEFFECT_NONE

	def onDrop(self, nodeTreeCtrlId, type, objectId):
		targetNodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
		sourceNodeRef = self.__dragObjectIdToNodeRef(type, objectId)
		return self._context.moveNode(sourceNodeRef, targetNodeRef)
						   
class PreviousWidget(Widget):
	def __init__(self, context):
		self._viewports = {}
		self._nodeRefToNodeTree = {}
		self._context = context

		# current state
		self.currentViewport = None		

		# media list currently showed whichever the node which are the focus
		self.currentMediaRefListM = []

		# region list currently showed whichever the node which are the focus
		self.currentRegionRefListM = []
		# region list which are showing
		self.currentRegionNodeListShowed = []

		self.previousCtrl = self._context.previousCtrl

		# to prevent against indefite loop
		self.__selecting = 0

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

		self.currentMediaRefListM = None
		self.currentRegionRefListM = None
		self.currentRegionNodeListShowed = None
		self.previousCtrl = None

	def selectNodeList(self, nodeRefList, keepShowedNodes):
		# to prevent against indefite loop
		self.__selecting = 1

		if not keepShowedNodes:
			# remove previous medias which are not selected anymore
			mediaToRemove = []
			for nodeRef in self.currentMediaRefListM:
				if not nodeRef in nodeRefList:
					mediaToRemove.append(nodeRef)
			for nodeRef in mediaToRemove:
				self.removeMedia(nodeRef)

		for nodeRef in nodeRefList:			
			nodeType = self._context.getNodeType(nodeRef)
			if nodeRef.getClassName() == 'FakeMMChannel' or (nodeType == TYPE_MEDIA and not nodeRef.GetChannel()):
				continue
			if nodeType == TYPE_VIEWPORT:
				viewport = nodeRef
			elif nodeType == TYPE_REGION:
				self.__showRegion(nodeRef)
			elif nodeType == TYPE_MEDIA:
				self.__showMedia(nodeRef)
		# determinate the right viewport to show
		viewport = None
		if len(nodeRefList) > 0:
			# get the last selected valid object
			indList = range(len(nodeRefList))
			indList.reverse()
			for ind in indList:
				n = nodeRefList[ind]
				if (n.getClassName() == 'MMNode' and self._context.isValidMMNode(n)) or n.getClassName() == 'MMChannel':
					if nodeType != TYPE_MEDIA or nodeRef.GetChannel():
						viewport = self._context.getViewportRef(n)
						break
		if viewport != None:
			self.__showViewport(viewport)

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
		# We assume here that no region has been added or supressed
		viewportRefList = self._context.getViewportRefList()
		for viewportRef in viewportRefList:
			if viewportRef.getClassName() == 'FakeMMChannel':
				continue
			viewportNode = self.getNode(viewportRef)
			if debug: print 'LayoutView.updateRegionTree: update viewport',viewportNode.getName()
			viewportNode.updateAllAttrdict()
		if debug: print 'LayoutView.updateRegionTree end'

	def addRegion(self, parentRef, regionRef):
		pNode = self.getNode(parentRef)
		self._nodeRefToNodeTree[regionRef] = regionNode = Region(regionRef, self)
		pNode.addNode(regionNode)

		if self._context.showAllRegions:
			self.__showRegion(regionRef)

	def addViewport(self, viewportRef):
		viewportNode = Viewport(viewportRef, self)
		self._nodeRefToNodeTree[viewportRef] = viewportNode

	def removeRegion(self, regionRef):
		self.removeRegionNode(regionRef)
		regionNode = self.getNode(regionRef)
		parentNode = regionNode.getParent()
		parentNode.removeNode(regionNode)
		viewportRef = parentNode.getViewport().getNodeRef()

		if regionRef in self.currentRegionRefListM:
			self.currentRegionRefListM.remove(regionRef)
			
		del self._nodeRefToNodeTree[regionRef]
		
	def removeViewport(self, viewportRef):		
		del self._nodeRefToNodeTree[viewportRef]
		if viewportRef is self.currentViewport.getNodeRef():
			# show the first viewport in the list		
			currentViewportList = self._context.getViewportRefList()
			viewportRef = currentViewportList[0]
			self.displayViewport(viewportRef)
									
	# ensure that the viewport is in showing state
	def __showViewport(self, viewportRef):
		if self.currentViewport == None or viewportRef != self.currentViewport.getNodeRef():
			if debug: print 'LayoutView.select: change viewport =',viewportRef
			self.displayViewport(viewportRef)
					
	# ensure that the region is in showing state
	def __showRegion(self, regionRef):
		type = regionRef.GetAttrDef('chsubtype', None)
		if type != None:
			# if the region is typed, we show only the region if visible
			import ChannelMap
			if not ChannelMap.isvisiblechannel(type):
				return 
				
		if regionRef not in self.currentRegionRefListM: 
			self.currentRegionRefListM.append(regionRef)
		regionNode = self.getNode(regionRef)
		if regionNode != None:
			regionNode.toShowedState()									

	# ensure that the media is in showing state
	def __showMedia(self, mediaRef):
		# show only visible medias in the preview area
		chtype = mediaRef.GetChannelType()
		import ChannelMap
		if not ChannelMap.isvisiblechannel(chtype):
			return
		
		appendList = []
		if mediaRef not in self.currentMediaRefListM:
			appendList.append(mediaRef)
			self.currentMediaRefListM.append(mediaRef)

			# append and update media node list
			self.__appendMediaNodeList(appendList)

	def removeAllMedias(self):
		for mediaRef in self.currentMediaRefListM:
			node = self.getNode(mediaRef)
			parentNode = node.getParent()
			# remove from region tree
			if parentNode != None:
				parentNode.removeNode(node)
			del self._nodeRefToNodeTree[mediaRef]
		self.currentMediaRefListM = []
					
	def removeMedia(self, mediaRef):
		node = self.getNode(mediaRef)
		if node != None:
			parentNode = node.getParent()
			# remove from region tree
			if parentNode != None:
				parentNode.removeNode(node)
			if mediaRef in self.currentMediaRefListM:
				self.currentMediaRefListM.remove(mediaRef)
				del self._nodeRefToNodeTree[mediaRef]

	def removeRegionNode(self, regionRef):
		if regionRef in	self.currentRegionNodeListShowed:
			self.currentRegionNodeListShowed.remove(regionRef)
			regionNode = self.getNode(regionRef)
			regionNode.toHiddenState()
							 
	def __appendMediaNodeList(self, nodeList):
		# create the media region nodes according to nodeList
		appendMediaRegionList = []
		for nodeRef in nodeList:
			newNode = MediaRegion(nodeRef, self)
			parentRef = self._context.getParentNodeRef(nodeRef)
			parentNode = self.getNode(parentRef)
			if parentNode != None:
				self._nodeRefToNodeTree[nodeRef] = newNode
				parentNode.addNode(newNode)
				newNode.importAttrdict()
				newNode.show()

	def onSelectChanged(self, objectList):
		# prevent against infinite loop
		if self.__selecting:
			return
		if debugPreview: print 'PreviewWidget.onSelect ',nodeList

		# build the list of the reference nodes selected
		list = []
		# xxx to optimize
		for  nodeRef, nodeTree in self._nodeRefToNodeTree.items():
			for obj in objectList:
				if nodeTree._graphicCtrl is obj:
					list.append(nodeRef)

		self._context.onSelectChanged(list)

	# selected update nodes handler method
	# state = 1 means: add into selected list
	# state = 0 means: remove from selected list
	def onSelectUpdated(self, nodeList, state):
		# XXX todo
		pass
	
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
			print 'can''t show viewport ',viewportRef
			return
		self.currentViewport.showAllNodes()

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
						
class Node:
	def __init__(self, nodeRef, ctx):
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
	def __init__(self, nodeRef, ctx):
		Node.__init__(self, nodeRef, ctx)
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

		if self.isShowed():
			# hide this node and its sub-nodes
			self.hideAllNodes()
			
		if self._wantToShow and self._parent._graphicCtrl != None:
			self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self.getName())
			self._graphicCtrl.showName(self.getShowName())		
			self._graphicCtrl.setListener(self)

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

	def importAttrdict(self):
		Node.importAttrdict(self)
#		self._curattrdict['bgcolor'] = MMAttrdefs.getattr(self._nodeRef, 'bgcolor')
#		self._curattrdict['transparent'] = MMAttrdefs.getattr(self._nodeRef, 'transparent')
		self._curattrdict['transparent'] = 1
		
		# get wingeom according to the subregion positionning
		# note this step is not done during the parsing in order to maintains all constraint information
		# at some point we'll have to do the same thing for regions
		channel = self._nodeRef.GetChannel()
		wingeom = self._nodeRef.getPxGeom()

		# determinate the real fit attribute		
		self.fit = fit = self._nodeRef.GetAttrDef('fit','hidden')

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
		self._curattrdict['z'] = 0

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

		self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self.getName())
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
			mediadisplayrect  = self._nodeRef.getPxGeomMedia()[1]
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

	def importAttrdict(self):
		Node.importAttrdict(self)

		editBackground = None
		if self.isShowEditBackground():
			editBackground = self._nodeRef.GetAttrDef('editBackground',None)
			
#		if editBackground != None:				
#				self._curattrdict['bgcolor'] = editBackground
#				self._curattrdict['transparent'] = 0
#		else:
#			self._curattrdict['bgcolor'] = self._nodeRef.GetInherAttrDef('bgcolor', (0,0,0))
#			self._curattrdict['transparent'] = self._nodeRef.GetInherAttrDef('transparent', 1)
		self._curattrdict['bgcolor'] = 200,200,200
		self._curattrdict['transparent'] = 0
		
		w,h=self._nodeRef.getPxGeom()
		self._curattrdict['wingeom'] = (self.currentX,self.currentY,w,h)

	def show(self):
		if debug: print 'Viewport.show : ',self.getName()
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
		
	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())


		
