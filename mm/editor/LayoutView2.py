# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from usercmd import *

ALL_LAYOUTS = '(All Channels)'

###########################
# helper class to build tree from list

class Node:
	def __init__(self, name, dict, ctx):
		self._name = name
		self._defattrdict = dict
		self._parent = None
		self._children = []
		self._ctx = ctx
		self._isviewport = 0

		# default attribute		
		self.importAttrdict()

	def importAttrdict(self):
		self._curattrdict = {}
		# no share attributes
		pass
	
	def getDocDict(self):
		return self._defattrdict
	
	def getShowName(self):
		return self._ctx.showName		

	def getName(self):
		return self._name
	
	def _do_init(self, parent):
		self._parent = parent
		parent._children.append(self)
			
	def applyOnAllNode(self, fnc, params):
		apply(fnc, params)
		for child in self._children:
			child.applyOnAllNode(fnc, params)

	def select(self):
		if self._graphicCtrl != None:
			self._graphicCtrl.select()

	def hide(self):
		self._graphicCtrl = None

	def hideAllNodes(self):
		self.hide()
		for child in self._children:
			child.hideAllNodes()

	def updateAttrdict(self):
		self.importAttrdict()
		if self._graphicCtrl != None:
			self._graphicCtrl.setAttrdict(self._curattrdict)

	def updateAllAttrdict(self):
		self.updateAttrdict()
		for child in self._children:
			child.updateAllAttrdict()
					
class Region(Node):
	def __init__(self, name, dict, ctx):
		Node.__init__(self, name, dict, ctx)

		# graphic control (implementation: system dependant)
		self._graphicCtrl = None		

	def importAttrdict(self):
		Node.importAttrdict(self)		
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
	
	def updateAllShowNames(self, value):
		self._graphicCtrl.showName(value)
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
		print 'region unselected : ',self._name
		
	def onGeomChanging(self, geom):
		# update only the geom field on dialog box
		self._ctx.updateRegionGeomOnDialogBox(geom)
		
	def onGeomChanged(self, geom):
		# apply the new value
		self._ctx.applyGeomOnRegion(self, geom)

	def onProperties(self):
		self._ctx.selectBgColor(self)
		
class Viewport(Node):
	def __init__(self, name, dict, ctx):
		self.currentX = 8
		self.currentY = 8
		
		Node.__init__(self, name, dict, ctx)
		self._isviewport = 1

		# graphic control (implementation: system dependant)
		self._graphicCtrl = None

	def importAttrdict(self):
		Node.importAttrdict(self)
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
		if self._graphicCtrl != None:
			self.showAllNodes()
		
	def onSelected(self):
		self._ctx.onPreviousSelectViewport(self)

	def onUnselected(self):
		print 'viewport unselected',self._name
		
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
		self.editmgr.register(self)

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

	def displayViewport(self, name):
		if self.currentViewport != None:
			self.currentViewport.hide()
			
		self.currentViewport = self._viewports[name]
		self.currentViewport.showAllNodes()
		self.currentViewport.select()
		self.updateViewportOnDialogBox(self.currentViewport)
		self.currentNodeSelected = self.currentViewport

	def selectRegion(self, name):
		if self.currentViewport != None:
			vpName = self.currentViewport.getName()
			regionNameList = self.getRegionNameList(vpName)
			for regionName in regionNameList:
				if regionName == name:
					region = self.getRegion(regionName)
					if region != None:
						region.select()
						self.currentNodeSelected = region												
						self.updateRegionOnDialogBox(region)
						break

	def selectBgColor(self, node):
		dict = node.getDocDict()
		bgcolor = dict.get('bgcolor')
		transparent = dict.get('transparent')
		
		newbg = self.chooseBgColor(bgcolor)
		if newbg != None:
			self.applyBgColor(node, newbg, transparent)
	
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
			self.editmgr.commit()

	def applyGeomOnRegion(self, region, geom):
		# apply new size
		# pass by edit manager
		
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(region.getName(), 'base_winoff', geom)
			self.editmgr.commit()

	def applyBgColor(self, node, bgcolor, transparent):
		# test if possible 
		if self.editmgr.transaction():
			self.editmgr.setchannelattr(node.getName(), 'bgcolor', bgcolor)
			self.editmgr.setchannelattr(node.getName(), 'transparent', transparent)
			self.editmgr.commit()
	
	def updateViewportOnDialogBox(self, viewport):

		# update region list
		self.currentRegionNameList = self.getRegionNameList(viewport.getName())		
		self.dialogCtrl.fillSelecterCtrl('RegionSel', self.currentRegionNameList)
		self.dialogCtrl.fillMultiSelCtrl('RegionList', self.currentRegionNameList)
		
		# get the current geom value
		dict = viewport.getDocDict()
		geom = dict.get('winsize')		

		# clear and disable not valid fields
		self.dialogCtrl.setSelecterCtrl('RegionSel',-1)
		self.dialogCtrl.enable('SendBack',0)
		self.dialogCtrl.enable('BringFront',0)
		self.dialogCtrl.enable('ShowRbg',0)
		self.dialogCtrl.enable('RegionZ',0)
		
		self.dialogCtrl.enable('RegionX',0)
		self.dialogCtrl.enable('RegionY',0)
		self.dialogCtrl.setFieldCtrl('RegionX',"")		
		self.dialogCtrl.setFieldCtrl('RegionY',"")		
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
								
		# enable valid fields
		self.dialogCtrl.enable('SendBack',1)
		self.dialogCtrl.enable('BringFront',1)
		self.dialogCtrl.enable('ShowRbg',1)
		self.dialogCtrl.enable('RegionZ',1)

		self.dialogCtrl.enable('RegionX',1)
		self.dialogCtrl.enable('RegionY',1)

		dict = region.getDocDict()
		geom = dict.get('base_winoff')
								  
		self.updateRegionGeomOnDialogBox(geom)

	def updateRegionGeomOnDialogBox(self, geom):
		self.dialogCtrl.setFieldCtrl('RegionX',"%d"%geom[0])		
		self.dialogCtrl.setFieldCtrl('RegionY',"%d"%geom[1])		
		self.dialogCtrl.setFieldCtrl('RegionW',"%d"%geom[2])		
		self.dialogCtrl.setFieldCtrl('RegionH',"%d"%geom[3])

	#
	# internal methods
	#
	
	def __updateZOrder(self, value):
		pass

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
		
	def __updateGeom(self, ctrlName, value):
		if self.currentNodeSelected != None:
			if self.currentNodeSelected._isviewport:
				self.__updateGeomOnViewport(ctrlName, value)
			else:
				self.__updateGeomOnRegion(ctrlName, value)
				

	def __selectBgColor(self):
		if self.currentNodeSelected != None:
			self.selectBgColor(self.currentNodeSelected)
	#
	# interface implementation of 'previous tree node' 
	#
	
	def onPreviousSelectRegion(self, region):
		self.selectRegion(region.getName())				

	def onPreviousSelectViewport(self, viewport):
		self.currentNodeSelected = viewport	
		self.updateViewportOnDialogBox(viewport)
		
	#
	# interface implementation of 'dialog controls callback' 
	#
	
	def onSelecterCtrl(self, ctrlName, value):
		if ctrlName == 'ViewportSel':
			self.displayViewport(value)
		elif ctrlName == 'RegionSel':
			self.selectRegion(value)	

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
			print 'send back pressed'
		elif ctrlName == 'BringFront':
			print 'bring front pressed'
		elif ctrlName == 'ShowRbg':
			print 'ShowRbg pressed'
					 