# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from windowinterface import UNIT_PXL

from usercmd import *

import MMAttrdefs

ALL_LAYOUTS = '(All Channels)'

###########################
# helper class to build tree from list

TYPE_ABSTRACT, TYPE_REGION, TYPE_MEDIA, TYPE_VIEWPORT = range(4)

class Node:
	def __init__(self, name, dict, ctx):
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
			if child._name == node._name:
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
		# no share attributes
		pass
	
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
		if showEditBackground != None and showEditBackground == "on":
			return 1
		return 0		
					
class Region(Node):
	def __init__(self, name, dict, ctx):
		Node.__init__(self, name, dict, ctx)
		self._nodeType = TYPE_REGION
		
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
			if self._ctx.asOutLine:
				self._curattrdict['transparent'] = 1
			else:
				self._curattrdict['transparent'] = self._defattrdict.get('transparent')
		
		self._curattrdict['wingeom'] = self._defattrdict.get('base_winoff')
		self._curattrdict['z'] = self._defattrdict.get('z')
	
	def show(self):
		self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._curattrdict, self._name)
		self._graphicCtrl.showName(self.getShowName())		
		self._graphicCtrl.addListener(self)

	def showAllNodes(self):
		self.show()
		for child in self._children:
			child.showAllNodes()

	#
	# update of visualization attributes (not document)
	#

	def updateShowName(self,value):
		self._graphicCtrl.showName(value)
		
	def updateAllShowNames(self, value):
		self.updateShowName(value)
		for child in self._children:
			child.updateAllShowNames(value)

	def updateAllAsOutLines(self, value):
		if value:
			self._curattrdict['transparent'] = 1
		else:
			self._curattrdict['transparent'] = 0

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
		self._ctx.selectBgColor(self)

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
				
		self._curattrdict['wingeom'] = wingeom
		
		self._curattrdict['z'] = 0

	def updateShowName(self,value):
		# no name showed
		pass

	def onSelected(self):
		self._ctx.onPreviousSelectMedia(self)

	def show(self):
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
		self.showAllNodes()

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
		self.currentRegionNameList = None
		self.currentNodeSelected = None
		self.currentMediaRegionList = []		

		# init state of differents dialog controls
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

	def fill(self):
		# for now, I assume that region list doesn't change from another view
		self.displayViewport(self._first)

	def show(self):
		if self.is_showing():
			LayoutViewDialog2.show(self)
			return
		LayoutViewDialog2.show(self)
		self.buildRegionTree(self.context)
		self.initDialogBox()		
		self.displayViewport(self._first)
		self.editmgr.register(self, 1)

		#		
		# simulate the focus for test
		#
#		focustype = 1
#		self.nodelist = []
#		for key,node in self.context.uidmap.items():
#			if node.type in ('imm','ext'):
#				self.nodelist.append(node)
#		self.globalfocuschanged(focustype, self.nodelist[0])
#		self.globalfocuschanged(focustype, self.nodelist[1])
		# ###
		
	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		LayoutViewDialog2.hide(self)

	def transaction(self):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		# for now, we assume here that no region has been added or supressed
		self.updateRegionTree()

	def globalfocuschanged(self, focustype, focusobject):
		from MMNode import MMNode

		# ensure that the last media selected node will be removed
		self.unSetMediaNode()
		
		from MMTypes import leaftypes
		if focusobject.type not in leaftypes or focusobject.GetChannelType() == 'sound':
			return
				
		self.setMediaNode(focusobject)
		self.fillMediaListOnDialogBox()
		if len(self.currentMediaRegionList) > 0:
			firstMediaRegion, parentRegion = self.currentMediaRegionList[0]
			self.currentNodeSelected = firstMediaRegion
			firstMediaRegion.select()
			self.enableMediaListOnDialogBox()
			self.updateMediaOnDialogBox(firstMediaRegion)
		else:			
			self.disableMediaListOnDialogBox()
				
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
			if chan.attrdict.get('type')=='layout':
				if chan.attrdict.has_key('base_window'):
					# region
					id2parentid[chan.name] = chan.attrdict['base_window']
				else:
					# no parent --> it's a viewport
					self._viewportsRegions[chan.name] = []
					self._viewports[chan.name] = Viewport(chan.name,chan.attrdict, self)
					# temporarly
					self._first = chan.name

		nodes = self._viewports.copy()
		for id in id2parentid.keys():
			chan = mmctx.channeldict[id]
			nodes[id] = Region(id, chan.attrdict, self)

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
		viewportNameList = self.getViewportList()
		for viewportName in viewportNameList:	
			viewport = self._viewports[viewportName]
			viewport.updateAllAttrdict()
		if self.currentNodeSelected != None:
			self.currentNodeSelected.select()

			# update dialog box as well
			nodeType = self.currentNodeSelected.getNodeType()
			if nodeType == TYPE_VIEWPORT:
				self.updateViewportOnDialogBox(self.currentNodeSelected)
			elif nodeType == TYPE_REGION:
				self.updateRegionOnDialogBox(self.currentNodeSelected)
			elif nodeType == TYPE_MEDIA:
				self.updateMediaOnDialogBox(self.currentNodeSelected)

	def unSetMediaNode(self):
		if len(self.currentMediaRegionList) > 0:
			for mediaRegion, parentRegion in self.currentMediaRegionList:
				# if the media region was selected, select its parent
				if mediaRegion == self.currentNodeSelected:
					parentRegion.select()
					self.updateRegionOnDialogBox(parentRegion)					
				mediaRegion.hide()
				# remove from region tree
				parentRegion.removeNode(mediaRegion)
		self.currentMediaRegionList = []
			
	def setMediaNode(self, node):
		channel = node.GetChannel()
		if channel == None: return
		layoutChannel = channel.GetLayoutChannel()
		if layoutChannel == Node: return
		layoutChannelName = layoutChannel.name
		regionNode = self.getRegion(layoutChannelName)
		if regionNode == None: return
		newname = node.attrdict.get("name")

		newRegionNode = MediaRegion(newname, node, self)

		# display the right viewport
		if self.currentViewport != regionNode.getViewport():
			self.displayViewport(regionNode.getViewport().getName())

		# add the new media region
		if self.currentViewport	!= None:
			self.currentMediaRegionList.append((newRegionNode, regionNode))

		# add the list of new media regions
		for mediaRegion, parentRegion in self.currentMediaRegionList:
			parentRegion.addNode(mediaRegion)
			mediaRegion.show()
						
	# extra pass to initialize map the region name list to the node object
	def __initRegionList(self, node, isRoot=1):
		if not isRoot:
			regionName = node._name
			self._nameToRegionNode[regionName] = node
		for child in node._children:
			self.__initRegionList(child,0)

	def getViewportList(self):
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
			
	def displayViewport(self, name):
		if self.currentViewport != None:
			self.currentViewport.hide()
			
		self.currentViewport = self._viewports[name]
		self.currentViewport.showAllNodes()
		self.currentViewport.select()
		self.updateViewportOnDialogBox(self.currentViewport)
		self.currentNodeSelected = self.currentViewport

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
		self.currentViewportList = self.getViewportList()
		self.dialogCtrl.fillSelecterCtrl('ViewportSel', self.currentViewportList)
		self.dialogCtrl.setCheckCtrl('ShowNames', self.showName)
		self.dialogCtrl.setCheckCtrl('AsOutLine', self.asOutLine)
							
	def applyGeomOnViewport(self, viewport, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible at this time
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(viewport.getName(), 'winsize', geom)
			self.editmgr.setchannelattr(viewport.getName(), 'units', UNIT_PXL)						
			self.editmgr.commit()

	def applyGeomOnRegion(self, region, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(region.getName(), 'base_winoff', geom)
			self.editmgr.setchannelattr(region.getName(), 'units', UNIT_PXL)			
			self.editmgr.commit()

	def applyGeomOnMedia(self, media, value):
		attrdict = media.mmnode.attrdict
		if self.editmgr.transaction():
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
			
			# todo: some ajustements for take into account all fit values
			self.editmgr.commit()
		
	def applyBgColor(self, node, bgcolor, transparent):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(node.getName(), 'bgcolor', bgcolor)
			self.editmgr.setchannelattr(node.getName(), 'transparent', transparent)
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
		
	def updateViewportOnDialogBox(self, viewport):
		# update region list
		self.currentRegionNameList = self.getRegionNameList(viewport.getName())		
		self.dialogCtrl.fillSelecterCtrl('RegionSel', self.currentRegionNameList)
		self.dialogCtrl.fillMultiSelCtrl('RegionList', self.currentRegionNameList)

		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
			
		# get the current geom value
		dict = viewport.getDocDict()
		geom = dict.get('winsize')		

		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = dict.get('showEditBackground')
		if showEditBackground == 'on':
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		# clear and disable not valid fields
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('RegionZ',0)

		self.dialogCtrl.enable('BgColor', 1)
		
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

	def updateViewportGeomOnDialogBox(self, geom):
		# update the fields dialog box
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[1])
		
	def updateRegionOnDialogBox(self, region):
		# update the selecter
		if self.currentRegionNameList != None:
			index = self.currentRegionNameList.index(region.getName())
			if index >= 0:
				self.dialogCtrl.setSelecterCtrl('RegionSel',index)

		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)
								
		# enable valid fields
		self.dialogCtrl.enable('SendBack',1)
		self.dialogCtrl.enable('BringFront',1)
		
		self.dialogCtrl.enable('RegionZ',1)

		self.dialogCtrl.enable('BgColor', 1)

		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)

		dict = region.getDocDict()
		geom = dict.get('base_winoff')

		self.dialogCtrl.enable('ShowRbg',1)
		showEditBackground = dict.get('showEditBackground')
		if showEditBackground == 'on':
			self.dialogCtrl.setCheckCtrl('ShowRbg', 0)
		else:
			self.dialogCtrl.setCheckCtrl('ShowRbg', 1)

		z = dict.get('z')
		self.dialogCtrl.setFieldCtrl('RegionZ',"%d"%z)		
								  
		self.updateRegionGeomOnDialogBox(geom)

	def updateRegionGeomOnDialogBox(self, geom):
		self.dialogCtrl.setFieldCtrl('RegionX',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionY',"%d"%geom[1])		
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])

	def fillMediaListOnDialogBox(self):
		list = []
		for mediaRegion, parentRegion in self.currentMediaRegionList:
			mmnode = mediaRegion.mmnode
			list.append(mmnode.attrdict.get('name'))
		self.currentMediaNameList = list
		self.dialogCtrl.fillSelecterCtrl('MediaSel', self.currentMediaNameList)

	def disableMediaListOnDialogBox(self):
		self.dialogCtrl.setSelecterCtrl('MediaSel',-1)		
		self.dialogCtrl.enable('MediaSel',0)
		self.currentMediaNameList = None

	def enableMediaListOnDialogBox(self):
		self.dialogCtrl.enable('MediaSel',1)
		
	def updateMediaOnDialogBox(self, media):
		mmnode = media.mmnode
		mediaName = mmnode.attrdict.get('name')
		# update the media selecter
		if self.currentMediaNameList != None:
			index = self.currentMediaNameList.index(mediaName)
			if index >= 0:
				self.dialogCtrl.setSelecterCtrl('MediaSel',index)
			
		# update the region selecter
		region = media.getParent()
		regionName = region.getName()
		if self.currentRegionNameList != None:
			index = self.currentRegionNameList.index(regionName)
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

		self.dialogCtrl.enable('BgColor', 0)
							   
		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)
		self.dialogCtrl.enable('RegionZ',0)
		self.dialogCtrl.setFieldCtrl('RegionZ',"")
		self.updateMediaGeomOnDialogBox(geom)
		
	def updateMediaGeomOnDialogBox(self, geom):
		self.updateRegionGeomOnDialogBox(geom)

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
				
	def __selectBgColor(self):
		if self.currentNodeSelected != None:
			self.selectBgColor(self.currentNodeSelected)

	def __sendBack(self):
		if self.currentNodeSelected != None:
			self.sendBack(self.currentNodeSelected)

	def __bringFront(self):
		if self.currentNodeSelected != None:
			self.bringFront(self.currentNodeSelected)

	def __selectRegion(self, name):
		region = self.getRegion(name)
		if region != None:
			region.select()
			self.currentNodeSelected = region												
			self.updateRegionOnDialogBox(region)

	def __selectMedia(self, name):
		media = self.getMedia(name)
		if media != None:
			media.select()
			self.currentNodeSelected = media
			self.updateMediaOnDialogBox(media)

	def __showEditBackground(self, value):
		node = self.currentNodeSelected
		if node.getNodeType() in (TYPE_REGION, TYPE_VIEWPORT):
			list = []
			if not value:
				dict = node.getDocDict()
				if not dict.has_key('showEditBackground'):
					list.append(('showEditBackground','on'))
				if not dict.has_key('editBackground'):	
					list.append(('editBackground',dict.get('bgcolor')))
			else:
				dict = node.getDocDict()
				if dict.has_key('showEditBackground'):
					list.append(('showEditBackground',None))
			self.applyEditorPreference(node, list)
		
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

	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onSelecterCtrl(self, ctrlName, value):
		if ctrlName == 'ViewportSel':
			self.displayViewport(value)
		elif ctrlName == 'RegionSel':
			self.__selectRegion(value)	
		elif ctrlName == 'MediaSel':
			self.__selectMedia(value)	

	def onMultiSelCtrl(self, ctrlName, itemList):
		if ctrlName == 'RegionList':
			# not implemented yet
			pass
			
	def onCheckCtrl(self, ctrlName, value):
		if ctrlName == 'ShowNames':
			self.showName = value
			if self.currentViewport != None:
				self.currentViewport.updateAllShowNames(self.showName)
		elif ctrlName == 'AsOutLine':
			self.asOutLine = value
			if self.currentViewport != None:
				self.currentViewport.updateAllAsOutLines(self.asOutLine)
		elif ctrlName == 'ShowRbg':
			self.__showEditBackground(value)			

	def onFieldCtrl(self, ctrlName, value):
		if ctrlName in ('RegionX','RegionY','RegionW','RegionH'):
			value = int(value)
			self.__updateGeom(ctrlName, value)
		elif ctrlName == 'RegionZ':
			value = int(value)
			self.__updateZOrder(value)

	def onButtonClickCtrl(self, ctrlName):
		if ctrlName == 'BgColor':
			self.__selectBgColor()
		elif ctrlName == 'SendBack':
			self.__sendBack()
		elif ctrlName == 'BringFront':
			self.__bringFront()


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

# ################################################################################################
			
					 