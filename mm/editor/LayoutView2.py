# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from usercmd import *

ALL_LAYOUTS = '(All Channels)'

###########################
# helper class to build tree from list

class Node:
	def __init__(self, name, dict, ctx):
		self._name = name
		self._attrdict = dict
		self._parent = None
		self._children = []
		self._ctx = ctx

	def getShowName(self):
		return self._ctx.showName		
		
	def _do_init(self, parent):
		self._parent = parent
		parent._children.append(self)

	def showChildren(self):
		for child in self._children:
			child.show()
			
class Region(Node):
	def __init__(self, name, dict, ctx):
		Node.__init__(self, name, dict, ctx)
		# graphic control (implementation: system dependant)
		self._graphicCtrl = None		

	def show(self):
		self._graphicCtrl = self._parent._graphicCtrl.addRegion(self._attrdict, self._name)
		self._graphicCtrl.showName(self.getShowName())		
		self._graphicCtrl.addListener(self)
		self.showChildren()

	def updateShowName(self, showName):
		self._graphicCtrl.showName(showName)
		for child in self._children:
			child.updateShowName(showName)

	def onSelected(self):
		print 'region selected : ',self._name

	def onUnselected(self):
		print 'region unselected : ',self._name
		
	def onGeomChanging(self, geom):
		print 'region geom is changing : ',self._name

	def onGeomChanged(self, geom):
		print 'region geom has changed : ',self._name

	def onProperties(self):
		print 'properties on region'
		
class Viewport(Node):
	def __init__(self, name, dict, ctx):
		Node.__init__(self, name, dict, ctx)
		# graphic control (implementation: system dependant)
		self._graphicCtrl = None
		
	def show(self):
		self._graphicCtrl = self._ctx.previousCtrl.newViewport(self._attrdict, self._name)
		self._graphicCtrl.addListener(self)
		self.showChildren()
		self._ctx.previousCtrl.update()

	def updateShowName(self, showName):
		for child in self._children:
			child.updateShowName(showName)
				
	def onSelected(self):
		print 'viewport selected',self._name

	def onUnselected(self):
		print 'viewport unselected',self._name
		
	def onGeomChanging(self, geom):
		print 'viewport geom is changing : ',self._name

	def onGeomChanged(self, geom):
		print 'viewport geom has changed : ',self._name

	def onProperties(self):
		print 'properties on viewport'
		
###########################

class LayoutView2(LayoutViewDialog2):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		LayoutViewDialog2.__init__(self)

		# current viewport showed
		self.currentViewport = None
		
		# init state of differents dialog controls
		self.showName = 1
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
		self.buildRegionTree(self.context)
		self.initDialogBox()
		self.displayViewport(self._first)
#		self.editmgr.register(self)

	def hide(self):
		if not self.is_showing():
			return
#		self.editmgr.unregister(self)
		LayoutViewDialog2.hide(self)

	def transaction(self):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		self.fill()

	def kill(self):
		self.destroy()

	#
	# interface implementation of 'dialog controls callback' 
	#

	def onViewportSelCtrl(self, name):
		self.displayViewport(name)
		
	def onRegionSelCtrl(self, name):
		self.previousCtrl.selectRegion(name)		

	def onRegionNamesChCtrl(self, value):
		self.showName = value
		if self.currentViewport != None:
			self.currentViewport.updateShowName(self.showName)

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

	def getViewports(self):
		return self._viewportsRegions.keys()

	def initDialogBox(self):
		viewportList = self.getViewports()
		self.dialogCtrl.fillViewportSelCtrl(viewportList)
		self.dialogCtrl.setShowNamesCtrl(self.showName)
		
	def displayViewport(self, name):
		self.currentViewport = self._viewports[name]
		self.currentViewport.show()
