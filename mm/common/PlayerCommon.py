# This module implements some common treatments between the player version and the editor version
# Currently, all renderers (and create/destroy optimization) are created in this module

# allow to create all renderer before to play.
# For now, don't turn off this flag, it doesn't work for the sound channels
MAKE_RENDERERS_FIRST = 1

# allow to create one renderer by media (without optimization)
ONE_RENDERER_BY_MEDIA_NODE = 0

debug = 0

class PlayerCommon:
	def __init__(self):
		self.nodeToRenderer = {}
		# optimization variables which allow optimizations
		self.__region2RendererList = {}
		self.__pnode2RendererList = {}
		self.__rendererNoreuse = {}
		
	def clearRendererChannels(self):
		# kill all renderers
		for node, renderer in self.nodeToRenderer.items():
			self.killRenderer(renderer._name)
		self.nodeToRenderer = {}
						
		# optimization variables which allow optimizations
		self.__region2RendererList = {}
		self.__pnode2RendererList = {}
		self.__rendererNoreuse = {}

	def makeRendererChannels(self):
		if MAKE_RENDERERS_FIRST:				
			nodeList = self.root.GetAllMediaNodes()
			for node in nodeList:
				renderer = self.getRenderer(node)
	
	def checkRendererChannels(self):
		#self.clearRendererChannels()
		self.makeRendererChannels()
				
	def getRenderer(self, node):
		chan = self.nodeToRenderer.get(node)
		if chan is None:
			# check if valid region
			regionName = node.GetChannelName()
			if not regionName or regionName == 'undefined':
				return None
		
			# the renderer doesn't exist yet
			if not ONE_RENDERER_BY_MEDIA_NODE:
				chan = self.findRenderer(node)
			else:
				chan = self.makeRenderer(node)
			self.nodeToRenderer[node] = chan

		return chan		
		
	def makeRenderer(self, node):
		regionName = node.GetChannelName()
		
		chtype = node.GetChannelType()
		chname = self.newChannelName(regionName)
		if debug: print 'make a new renderer : ',chname
		# create just the minimum channel attributes for creating a new channel
		import MMNode
		ctx = self.context
		chan = MMNode.MMChannel(ctx, chname, chtype)		
		chan['base_window'] = regionName
		chan['type'] = chtype
		
		# XXX store in reference document to keep working the player !
		# very bad, but the only way if we don't want change the setlayout method and break something
		ctx.channels.append(chan)
		ctx.channelnames.append(chname)
		ctx.channeldict[chname] = chan
		#

		# XXX store the name of the new channel (for the scheduler: GetAllChannels method) in the node
		node._rendererName = chname
		#
		
		self.newchannel(chname, chan)
		self.channelnames.append(chname)
		renderer = self.channels[chname]
		
		return renderer

	def killRenderer(self, name):
		if debug: print 'PlayerCore, killRenderer ',name
		# XXX remove channel from reference document
		ctx = self.context
		i = ctx.channelnames.index(name)
		del ctx.channels[i]
		del ctx.channelnames[i]
		del ctx.channeldict[name]
		#
		
		self.killchannel(name)
	
	def findRenderer(self, node):
		if debug: print 'PlayerCore, findRenderer, for node ',node
				
		renderer = None
		regionName = node.GetChannelName()
		chtype = node.GetChannelType()
		pnode = node.GetSchedParent()
		
		# first 
		# check if the renderer can be shared
		if (pnode.GetType() == 'seq' and \
			node.GetFill() == 'hold') or \
			node.GetFill() == 'transition':
			noreuse = 1
			if debug: print 'PlayerCore, renderer can''t be shared'
		else:
			noreuse = 0

		# if at this stage, the renderer can't be shared, ignore this section
		if not noreuse:
			if debug: print 'PlayerCore, check for a compatible renderer'
			# second pass
			for ch in self.__region2RendererList.get(regionName, []):
				if ch._attrdict.get('type') == chtype:
					# found existing renderer of correct type
					renderer = ch
					# check whether renderer can be used
					# we can only use a renderer if it isn't used
					# by another node parallel/excl to this one
					parent = pnode
					while parent is not None:
						pchanlist = self.__pnode2RendererList.get(parent)
						if pchanlist != None and pchanlist.has_key(renderer):
							ptype = parent.GetType()
							if ptype == 'par':
								# conflict
								renderer = None
								break
							elif ptype == 'excl':
								# potential conflict
								renderer = None
								break
							else:
								# no conflict
								break
						parent = parent.GetSchedParent()
					if renderer is not None:
						# this renderer can't be reused
						if self.__rendererNoreuse.get(renderer) is None:
							if debug: print 'compatible renderer found : ',renderer
							break
						else:
							if debug: print 'compatible renderer found but can''t be reused : ',renderer
							renderer = None

		# if 'renderer' = None, we haven't found a compatible renderer
		if not renderer or not noreuse:
			renderer = self.makeRenderer(node)
			if noreuse:
				self.__rendererNoreuse[renderer] = 1
			
			# update local variables
			# allow optimizations
			rdList = self.__region2RendererList.get(regionName)
			if rdList == None:
				rdList = self.__region2RendererList[regionName] = []
			rdList.append(renderer)
		
			rdList = self.__pnode2RendererList.get(pnode)
			if rdList == None:
				rdList = self.__pnode2RendererList[pnode] = {}
			rdList[renderer] = 1
		
		if debug: print 'PlayerCore, findRenderer, end renderer=',renderer,' node=',node
		return renderer

	# compute a channel name according to the region name
	def newChannelName(self, regionName):
		# search a new channel name
		name = regionName + ' %d'
		i = 0
		while self.channels.has_key(name % i):
			i = i + 1

		return name	% i


		
