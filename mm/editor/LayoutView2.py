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
					else:
						tNode.checkMainUpdate()
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
		else:
			tNode.checkMainUpdate()
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
			# detect if need to update the main attributes. basicly id and type
			if node.isUpdated:
				self._context.onMainUpdate(node.nodeRef)
				node.isUpdated = 0
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
		self.isUpdated = 0
		self.nodeRef = nodeRef
		self.children = {}
		self.type = type
		if type == TYPE_MEDIA:
			self.name = nodeRef.attrdict.get('name')
			self.mediatype = nodeRef.GetChannelType()
		else:
			self.name = nodeRef.name

	def hasChild(self, child):
		return self.children.has_key(child)
	
	def addChild(self, child):
		self.children[child] = 1

	def checkMainUpdate(self):
		nodeRef = self.nodeRef
		if self.type == TYPE_MEDIA:
			name = nodeRef.attrdict.get('name')
			mediatype = nodeRef.GetChannelType()
			if name != self.name or mediatype != self.mediatype:
				self.isUpdated = 1
				self.name = name
				self.mediatype = mediatype
		else:
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
		self.currentSelectedNodeList = None
		self.currentFocus = None
		self.currentFocusType = None
		# allow to identify if the focus has been fixed by this view
		self.myfocus = None

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
				]
		else:
			self.commandViewportList = [
				ATTRIBUTES(callback = (self.onSelectBgColor, ())),
				]

	def mkregioncommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandRegionList = [
				ATTRIBUTES(callback = (self.onEditProperties, ())),
				NEW_REGION(callback = (self.onNewRegion, ())),
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				DELETE(callback = (self.onDelNode, ())),
				]
		else:
			self.commandRegionList = [
				ATTRIBUTES(callback = (self.onSelectBgColor, ())),
				]

	def mkmediacommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMediaList = [
				ATTRIBUTES(callback = (self.onEditProperties, ())),
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMediaList = []

	def mknositemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandNoSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandNoSItemList = []

	# available command when several items are selected
	def mkmultisitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMultiSItemList = []		

	def mkmultisiblingsitemcommandlist(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self.commandMultiSiblingSItemList = [
				NEW_TOPLAYOUT(callback = (self.onNewViewport, ())),
				]
		else:
			self.commandMultiSiblingSItemList = []
		self.__appendAlignCommands()

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
		self.currentFocusType,self.currentFocus = self.editmgr.getglobalfocus()
		self.updateFocus()
		
	def hide(self):
		if not self.is_showing():
			return
		self.__channelTreeRef = None
		self.editmgr.unregister(self)
		LayoutViewDialog2.hide(self)

		# XXX to do: destroy all objects and to check that they are garbage collected
		# destroy the widgets
		for id, widget in self.widgetList.items():
			widget.destroy()
		
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
			self.treeWidget.appendViewport(nodeRef)
		elif nodeType == TYPE_REGION:
			self.previousWidget.addRegion(parentRef, nodeRef)
			self.treeWidget.appendRegion(parentRef, nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.treeWidget.appendMedia(parentRef, nodeRef)
		
	def onDelNodeRef(self, parentRef, nodeRef):
		nodeType = self.getNodeType(nodeRef)
		if nodeType == TYPE_VIEWPORT:
			self.previousWidget.removeViewport(nodeRef)
			self.treeWidget.removeNode(nodeRef)
		elif nodeType == TYPE_REGION:
			self.previousWidget.removeRegion(nodeRef)
			self.treeWidget.removeNode(nodeRef)
		elif nodeType == TYPE_MEDIA:
			self.treeWidget.removeNode(nodeRef)

	def onMainUpdate(self, nodeRef):
		self.treeWidget.updateNode(nodeRef)
		
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
			self.setcommandlist(self.commandRegionList)
		elif nodeType == TYPE_VIEWPORT:
			self.setcommandlist(self.commandViewportList)

		self.currentSelectedNodeList = [focusobject]
		
		# update widgets
		for id, widget in self.widgetList.items():
			widget.selectNodeList([focusobject])
						
	def focusOnMMNode(self, focusobject):
		# update command list
		self.setcommandlist(self.commandMediaList)
					
		self.currentSelectedNodeList = [focusobject]
		
		# update widgets
		for id, widget in self.widgetList.items():
			widget.selectNodeList([focusobject])

	def focusOnList(self, focusobject):
		# update command list

		areSibling = 1

		# build a list of valid objects which are the focus
		# and determinates if all the object list are sibling
		list = []
		previousObject = None
		for type, object in focusobject:
			list.append(object)
			if areSibling:
				if previousObject != None and not self.areSibling(previousObject, object):
					areSibling = 0
			previousObject = object

		if areSibling:
			self.setcommandlist(self.commandMultiSiblingSItemList)
		else:
			self.setcommandlist(self.commandMultiSItemList)

		self.currentSelectedNodeList = list
		
		# update widgets
		for id, widget in self.widgetList.items():
			widget.selectNodeList(list)
		
	def focusOnUnknown(self, focusobject):
		# update command list
		self.setcommandlist(self.commandNoSItemList)
		
		# update widgets
		for id, widget in self.widgetList.items():
			widget.selectNodeList([])
							
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
		elif self.currentFocusType == 'List':
			if debug: print 'LayoutView.updateFocus: focus on List'
			self.focusOnList(self.currentFocus)
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

		self.updateFocus()
		
	def setglobalfocus(self, list):
		if debug: print 'LayoutView.setglobalfocus list=',list
		
		focusobject = None
		if len(list) == 0:
			# no item selected
			self.editmgr.setglobalfocus(None, None)
		elif len(list) == 1:
			# simple selection
			focusobject = nodeRef = list[0]
			nodeType = self.getNodeType(nodeRef)
			if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
				self.myfocus = nodeRef
				self.editmgr.setglobalfocus('MMChannel', nodeRef)
			elif nodeType  == TYPE_MEDIA:
				self.myfocus = nodeRef
				self.editmgr.setglobalfocus('MMNode', nodeRef)
		else:
			# multi-selection, make a list compatible with the global focus
			focusobject = []
			for nodeRef in list:
				nodeType = self.getNodeType(nodeRef)
				if nodeType in (TYPE_VIEWPORT, TYPE_REGION):
					focusobject.append(('MMChannel', nodeRef))
				elif nodeType  == TYPE_MEDIA:
					focusobject.append(('MMNode', nodeRef))
			self.myfocus = focusobject
			self.editmgr.setglobalfocus('List', focusobject)
			
		self.currentSelectedNodeList = focusobject
		
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
		return parent1 != None and parent2 != None and \
			   parent1 is parent2
		
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

	def __makeAttrListToApplyFromGeom(self, nodeRef, geom, list):
		if self.getNodeType(nodeRef) == TYPE_VIEWPORT:
			w,h = geom
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

	def applyAttrList(self, nodeRefAndValueList):
		if self.editmgr.transaction():
			for nodeRef, attrName, attrValue in nodeRefAndValueList:
				nodeType = self.getNodeType(nodeRef)
				if nodeType in (TYPE_VIEWPORT, TYPE_REGION):					
					self.editmgr.setchannelattr(nodeRef.name, attrName, attrValue)
				elif nodeType == TYPE_MEDIA:
					self.editmgr.setnodeattr(nodeRef, attrName, attrValue)
			self.editmgr.commit()
		
	#
	# Alignment/Distribute commands
	#
	
	def onAlignLeft(self):
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
		if debugAlign: print 'distribute horizontally : ',self.currentSelectedNodeList
		nodeNumber = len(self.currentSelectedNodeList)
		if nodeNumber <= 1:
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
		if debugAlign: print 'distribute vertically : ',self.currentSelectedNodeList
		nodeNumber = len(self.currentSelectedNodeList)
		if nodeNumber <= 1:
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
	
	def onEditProperties(self):
		if self.currentSelectedNodeList != None:
			self.editProperties(self.currentSelectedNodeList[0])
						
	def onSelectBgColor(self):
		if self.currentSelectedNodeList != None:
			self.selectBgColor(self.currentSelectedNodeList[0])

	def onSendBack(self):
		if self.currentSelectedNodeList != None:
			self.sendBack(self.currentSelectedNodeList[0])

	def onBringFront(self):
		if self.currentSelectedNodeList != None:
			self.bringFront(self.currentSelectedNodeList[0])

	def onShowEditBackground(self, value):
		if self.currentSelectedNodeList != None:
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
		if self.currentSelectedNodeList != None:
			nodeType = self.getNodeType(self.currentSelectedNodeList[0])
			if nodeType == TYPE_VIEWPORT:
				self.delViewport(self.currentSelectedNodeList[0])
			elif nodeType == TYPE_REGION:
				self.delRegion(self.currentSelectedNodeList[0])

	def onNewRegion(self):
		if self.currentSelectedNodeList != None:
			self.newRegion(self.currentSelectedNodeList[0])

	def onNewViewport(self):
		self.newViewport()

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
		self.setglobalfocus([self.nameToNodeRef(name)])
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
		self.setglobalfocus([self.nameToNodeRef(name)])
		self.updateFocus()

	def delRegion(self, regionRef):
		# for now, we can only erase an empty viewport
#		if not self.isEmpty(regionRef):
#			msg = "you have to delete before the sub regions and associated medias"
#			windowinterface.showmessage(msg, mtype = 'error')
#			return
		
		parentRef = self.getParentNodeRef(regionRef, TYPE_REGION)
		self.setglobalfocus([parentRef])
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
				self.setglobalfocus([viewportRef])
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
	
	def onSelect(self, nodeRefList):
		self.setglobalfocus(nodeRefList)

		self.updateFocus()	
#
# common class for all widgets
#

class Widget:
	def __init__(self, context):
		self._context = context

	#
	# overrided methods
	#
	
	def selectNodeList(self, nodeRefList):
		pass

	def show(self):
		pass

	def destroy(self):
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
		
	def selectNodeList(self, nodeRefList):
		if len(nodeRefList) != 1:
			# if no node selected or several nodes are selected in the same time, disable the fields
			self.__unselect()
			return
		nodeRef = nodeRefList[0]
		nodeType = self._context.getNodeType(nodeRef)
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
		if self._context.currentSelectedNodeList != None:
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
	
	def selectNodeList(self, nodeRefList):
		# if no node selected or several nodes are selected in the same time, disable the fields
		if len(nodeRefList) != 1:
			self.__unselect()
			return
		nodeRef = nodeRefList[0]
		nodeType = self._context.getNodeType(nodeRef)
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
		
		geom = nodeRef.getPxGeom()
		self.updateViewportGeom(geom)				

	def updateViewportGeom(self, geom):
		# update the fields dialog box
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[1])
		
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
		if self._context.currentSelectedNodeList != None:
			nodeRef = self._context.currentSelectedNodeList[0]
			w,h = nodeRef.getPxGeom()
			if ctrlName == 'RegionW':
				w = value
			elif ctrlName == 'RegionH':
				h = value
			self._context.applyGeom(nodeRef, (w,h))

	def __onGeomOnRegionChanged(self, ctrlName, value):
		if self._context.currentSelectedNodeList != None:		
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
		if self._context.currentSelectedNodeList != None:
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
		self.treeCtrl.setHandler(self)

	#
	# inherited methods
	#

	def show(self):
		# XXX temporare. expand all region nodes by default
		self.expandAllNodes(0)
		

	def selectNodeList(self, nodeRefList):
		list = []
		for nodeRef in nodeRefList:
			nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
			if nodeTreeCtrlId != None:
				list.append(nodeTreeCtrlId)
		self.treeCtrl.selectNodeList(list)

	#
	#
	#

	def __unselect(self):
		# todo
		pass
	
	def appendMedia(self, pNodeRef, nodeRef):
		mediaType = nodeRef.GetChannelType()
		name = nodeRef.attrdict.get('name')
		if name == None:
			name=''
		ret = self.treeCtrl.insertNode(self.nodeRefToNodeTreeCtrlId[pNodeRef], name, mediaType, mediaType)
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef

	def appendViewport(self, nodeRef):
		ret = self.treeCtrl.insertNode(0, nodeRef.name, 'viewport', 'viewport')
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef
			
	def appendRegion(self, pNodeRef, nodeRef):
		ret = self.treeCtrl.insertNode(self.nodeRefToNodeTreeCtrlId[pNodeRef], nodeRef.name, 'region', 'region')
		self.nodeRefToNodeTreeCtrlId[nodeRef] = ret
		self.nodeTreeCtrlIdToNodeRef[ret] = nodeRef

	def updateNode(self, nodeRef):
		nodeType = self._context.getNodeType(nodeRef)
		if nodeType == TYPE_MEDIA:
			type = nodeRef.GetChannelType()
			name = nodeRef.attrdict.get('name')
		elif nodeType == TYPE_REGION:
			type = 'region'
			name = nodeRef.name
		else:
			type = 'viewport'
			name = nodeRef.name
		if name == None:
			name=''
		self.treeCtrl.updateNode(self.nodeRefToNodeTreeCtrlId[nodeRef], name, type, type)
		
	def removeNode(self, nodeRef):
		nodeTreeCtrlId = self.nodeRefToNodeTreeCtrlId.get(nodeRef)
		if nodeTreeCtrlId != None:
			self.treeCtrl.removeNode(nodeTreeCtrlId)
			del self.nodeRefToNodeTreeCtrlId[nodeRef]
			del self.nodeTreeCtrlIdToNodeRef[nodeTreeCtrlId]
				
	# selected node handler method
	def onSelectTreeNodeCtrl(self, nodeTreeCtrlIdList):
		nodeRefList = []
		for nodeTreeCtrlId in nodeTreeCtrlIdList:
			nodeRef = self.nodeTreeCtrlIdToNodeRef.get(nodeTreeCtrlId)
			nodeRefList.append(nodeRef)
		self._context.onSelect(nodeRefList)

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

class PreviousWidget(Widget):
	def __init__(self, context):
		self._viewports = {}
		self._nodeRefToNodeTree = {}
		self._context = context

		# current state
		self.currentViewport = None		

		self.localSelect = 0
		
		# media list currently showed whichever the node which are the focus
		self.currentMediaRefListM = []

		# region list currently showed whichever the node which are the focus
		self.currentRegionRefListM = []
		# region list which are showing
		self.currentRegionNodeListShowed = []

		self.previousCtrl = self._context.previousCtrl

	#
	# inherited methods
	#
	
	def show(self):
		# show the first viewport in the list		
		currentViewportList = self._context.getViewportRefList()
		viewport = currentViewportList[0]
		self.displayViewport(viewport)

	def selectNodeList(self, nodeRefList):
		if not self.localSelect:
		# remove previous medias which are not selected anymore
			mediaToRemove = []
			for nodeRef in self.currentMediaRefListM:
				if not nodeRef in nodeRefList:
					mediaToRemove.append(nodeRef)
			for nodeRef in mediaToRemove:
				self.removeMedia(nodeRef)
		self.localSelect = 0
			
		if len(nodeRefList) == 0:
			self.unselect()
			return
		for nodeRef in nodeRefList:			
			nodeType = self._context.getNodeType(nodeRef)
			if nodeType == TYPE_VIEWPORT:
				self.selectViewport(nodeRef)
			elif nodeType == TYPE_REGION:
				self.selectRegion(nodeRef)
			elif nodeType == TYPE_MEDIA:
				self.selectMedia(nodeRef)

	#
	#
	#
	
	def updateRegionTree(self):
		if debug: print 'LayoutView.updateRegionTree begin'
		# We assume here that no region has been added or supressed
		viewportRefList = self._context.getViewportRefList()
		for viewportRef in viewportRefList:
			viewportNode = self.getNode(viewportRef)
			if debug: print 'LayoutView.updateRegionTree: update viewport',viewportNode.getName()
			viewportNode.updateAllAttrdict()
		if debug: print 'LayoutView.updateRegionTree end'

	def addRegion(self, parentRef, regionRef):
		pNode = self.getNode(parentRef)
		self._nodeRefToNodeTree[regionRef] = regionNode = Region(regionRef.name, regionRef, self)
		pNode.addNode(regionNode)

		if self._context.showAllRegions:
			if regionRef not in self.currentRegionRefListM:
				self.currentRegionRefListM.append(regionRef)

			# append and update region node list
			self.appendRegionNodeList([regionRef])

	def addViewport(self, viewportRef):
		viewportNode = Viewport(viewportRef.name, viewportRef, self)
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

	def selectRegion(self, regionRef):		
		appendList = []
		if regionRef not in self.currentRegionRefListM: 
			appendList.append(regionRef)
			self.currentRegionRefListM.append(regionRef)

		# append and update region node list
		self.appendRegionNodeList(appendList)
		self.__select(regionRef)
			
	def selectViewport(self, viewportRef):
		self.__select(viewportRef)

	def unselect(self):
		self.__unselect()
									
	def selectMedia(self, mediaRef):
		appendList = []
		if mediaRef not in self.currentMediaRefListM:
			appendList.append(mediaRef)
			self.currentMediaRefListM.append(mediaRef)

		# append and update media node list
		self.appendMediaNodeList(appendList)
		
		self.__select(mediaRef)

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
							 
	def appendAllRegionNodeList(self):
		self.appendRegionNodeList(self.currentRegionRefListM)
	
	def appendRegionNodeList(self, nodeList):
		# change to show state each region node
		for nodeRef in nodeList:
			regionNode = self.getNode(nodeRef)
			if regionNode != None:
				regionNode.toShowedState()
			self.currentRegionNodeListShowed.append(nodeRef)
									
	def appendMediaNodeList(self, nodeList):
		# create the media region nodes according to nodeList
		appendMediaRegionList = []
		for nodeRef in nodeList:
			name = nodeRef.attrdict.get("name")
			newNode = MediaRegion(name, nodeRef, self)
			parentRef = self._context.getParentNodeRef(nodeRef)
			parentNode = self.getNode(parentRef)
			if parentNode != None:
				self._nodeRefToNodeTree[nodeRef] = newNode
				parentNode.addNode(newNode)
				newNode.importAttrdict()
				newNode.show()

	def onSelect(self, nodeList):
		self.localSelect = 1
		self._context.onSelect(nodeList)
		
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

	def getNode(self, nodeRef):
		node = self._nodeRefToNodeTree.get(nodeRef)
		return node

	def displayViewport(self, viewportRef):
		if debug: print 'LayoutView.displayViewport: change viewport =',viewportRef
		if self.currentViewport != None:
			self.currentViewport.hide()
		self.currentViewport = self.getNode(viewportRef)
		self.currentViewport.showAllNodes()
								
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
		self._ctx._context.onSelect([])

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

	def onSelected(self):
		if not self._selecting:
			if debug: print 'PreviousWidget.Node.onSelected : ',self.getName()
			self._ctx.onSelect([self._nodeRef])
		
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

	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx._context.onFastGeomUpdate(self._nodeRef, geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.localSelect = 1 # temporare
		self._ctx._context.applyGeom(self.getNodeRef(), geom)

	def onProperties(self):
		self._ctx.localSelect = 1 # temporare
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
		# update only the geom field on dialog box
		self._ctx._context.onFastGeomUpdate(self._nodeRef, geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.localSelect = 1 # temporare
		self._ctx._context.applyGeom(self.getNodeRef(), geom)

	def onProperties(self):
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx.localSelect = 1 # temporare
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
		
	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx._context.onFastGeomUpdate(self._nodeRef, geom[2:])

	def onGeomChanged(self, geom):
		self._ctx.localSelect = 1 # temporare
		# apply the new value
		self.currentX = geom[0]
		self.currentY = geom[1]
		self._ctx._context.applyGeom(self._nodeRef, geom[2:])

	def onProperties(self):
		self._ctx.localSelect = 1 # temporare
		if features.CUSTOM_REGIONS in features.feature_set:
			self._ctx._context.editProperties(self.getNodeRef())
		else:
			self._ctx._context.selectBgColor(self.getNodeRef())

		