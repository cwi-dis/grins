__version__ = "$Id$"

# PlayerCore module -- Player stuff not related to UI or scheduling


import windowinterface
#from MMExc import *
import MMAttrdefs
from Selecter import Selecter
from PlayerCommon import PlayerCommon

# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

class PlayerCore(Selecter, PlayerCommon):
	#
	# Initialization.
	#
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.playroot = self.root # top of current mini-document
		self.userplayroot = self.root # node specified by part play
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.editmgr.register(self)
		self.chans_showing = 0
		Selecter.__init__(self)
		PlayerCommon.__init__(self)
		self.context.registergetchannelbynode(self.getchannelbynode)
		self.__ichannels = {} # internal channels map

		# this flag allow to know if the renderer have to be checked (because edited)
		# it's used for optimization purpose: the renderers are checked only if this flag has changed
		self.mustCheckRenderer = 0 

	def destroy(self):
		self.editmgr.unregister(self)

	#
	# EditMgr interface (as dependent client).
	#
	def transaction(self, type):
		# in this particular case, it's possible to edit the document when pausing
		if type in ('REGION_GEOM','MEDIA_GEOM'):
			if self.pausing:
				return 1
		
		# Disallow changes while we are playing.
		if self.playing:
			m1 = 'You cannot change the document\n'
			m2 = 'while it is playing.\n'
			m3 = 'Do you want to stop playing?'
			if not windowinterface.showquestion(m1 + m2 + m3):
				return 0
			self.stop()
		self.locked = 1
		return 1
	#
	def commit(self, type):
		if type in ('REGION_GEOM', 'MEDIA_GEOM'):
			if self.playing:
				return

		self.mustCheckRenderer = 1
		
		self.checkchannels()
		if self.showing:
			# Check if any of the playroots has vanished
			if self.playroot.GetRoot() is not self.root:
				self.playroot = self.root
			if self.userplayroot.GetRoot() is not self.root:
				self.userplayroot = self.root
			self.makeugroups()
		self.locked = 0
		self.showstate()
	#
	def rollback(self):
		# Nothing has changed after all.
		self.locked = 0

	def kill(self):
		self.destroy()
	#
	# Internal reset.
	#
	def fullreset(self):
		self.reset()
		self.playroot = self.userplayroot = self.root
		if hasattr(self, '_animateContext'):
			self._animateContext.reset()

	#
	# play_done - Upcall by scheduler to indicate that all is done.
	#
	def play_done(self):
		self.playing = 0
		if self.pausing:
			self.pause(0)
		self.stopped()
	#
	def playsubtree(self, node):
		self.show()
		if self.playing:
			self.stop()
		if node.GetRoot() is not self.root:
			raise CheckError, 'playsubtree with bad arg'
		self.userplayroot = self.playroot = node
		self.play()
	#
	def playfrom(self, node):
		self.savecurlayout = self.curlayout
		self.savecurchannel = self.curchannel
		self.setlayout()
		self.playfromanchor(node, None)
	#
	def playfromanchor(self, node, anchor):
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		self.reset()
		self.pause(1)
		self.play()
		if not self.gotonode(node, anchor, None):
			return
		self.playing = 1
		self.showstate()

	def play(self):
		# if the document has been edited, we have to check (and rebuild) the renderer channels
		if self.mustCheckRenderer:
			self.checkRendererChannels()
			self.mustCheckRenderer = 0
		Selecter.play(self)
		
	#
	def anchorinit(self, node):
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		ch = self.getchannelbynode(node)
		if ch is None:
			return None
		if not ch.is_showing():
			ch.set_visible(1)
			self.setchannel(ch._name, 1)
		return ch
	#
	def defanchor(self, node, anchor, cb):
		ch = self.anchorinit(node)
		if ch is None:
			windowinterface.showmessage('Cannot set internal anchor\n' + \
				  '(node not on a channel)')
			apply(cb, (anchor,))
			return
		ch.defanchor(node, anchor, cb)
	#
	def updatefixedanchors(self, node):
		ch = self.getchannelbynode(node)
		if ch is None:
			return 1	# Cannot set on internal nodes
		return ch.updatefixedanchors(node)

	def updateFocus(self, focusNode):
		if focusNode != None:
			self.editmgr.setglobalfocus('MMNode', focusNode)

	def updatePlayerStateOnStop(self):
		# send the player state event					
		self.editmgr.setplayerstate('stopped', None)		
		
	# update the player state in order to update all views according to this state
	# for now, the state is a list of: playing nodes and showing channels
	# return a node which has the focus: temporarly
	def updatePlayerStateOnPause(self):
		# node list is a tuple of (nodetype/node)
		# here nodetype is either: 'MMChannel' or 'MMNode'
		nodeList = []

		focusNode = None
		
		channelListShowing = []	
		# first build the region list (only layoutchannel)		
		for name in self.channelnames:
			ch = self.channels.get(name)
			if ch != None:
				if ch.isShown():
					if ch._attrdict.get('type') == 'layout':
						chRef = self.context.getchannel(name)
						if chRef != None:
							nodeList.append(('MMChannel',chRef))
					else:
						channelListShowing.append(ch)

		# next stape: build a MMNode instance list
		for ch in channelListShowing:
			playingNode = ch.getPlayingNode()
			if playingNode != None:
				nodeList.append(('MMNode',playingNode))
				# for now, we give the focus to an arbitrare node
				focusNode = playingNode

		# send the player state event					
		self.editmgr.setplayerstate('paused', nodeList)

		return focusNode	
	#
	def pause(self, wantpause):
		if self.pausing == wantpause:
			print 'Funny: pause state already ok...'
			return
		self.pausing = wantpause
		if self.pausing:
			self.scheduler.setpaused(1)
			focusNode = self.updatePlayerStateOnPause()
			self.updateFocus(focusNode)
		else:
			self.scheduler.setpaused(0)
		self.showstate()
	#
	#
	def maystart(self):
		return not self.locked

	def checkRegions(self):
		# XXX Ought to detect renamed channels...
		# (1) Delete channels that have disappeared
		# or whose type has changed
		for name in self.channelnames[:]:
			channel = self.channels[name]
			if channel._attrdict.get('type') != 'layout':
				continue
			if name not in self.context.channelnames:
				self.killchannel(name)

		# (2) Add new channels that have appeared
		for name in self.context.channelnames:
			if name not in self.channelnames:
## 				print 'Detected new channel'
				attrdict = self.context.channeldict[name]
				if attrdict.get('type') != 'layout':
					continue
				self.newchannel(name, attrdict)
				i = self.context.channelnames.index(name)
				self.channelnames.insert(i, name)			
			
	#
	def checkchannels(self):
		self.checkRegions()
		self.__checkichannels()
		if self.showing:
			# (3) reset all variable _want_shown to zero
			for name in self.channelnames:
				self.channels[name]._want_shown = 0
			# (4) Update visibility of all channels
			for name in self.channelnames:
				self.channels[name].check_visible()
			# (5) Update layout and menu
			self.setlayout(self.curlayout, self.curchannel)
		return

	#
	def getchannelbyname(self, name):
		if self.channels.has_key(name):
			return self.channels[name]
		elif self.__ichannels.has_key(name):
			return self.__ichannels[name]
		else:
			return None
	#

	def getchannelbynode(self, node):
		import MMTypes
		if node.GetType() in MMTypes.mediatypes:
			return self.getRenderer(node)
		else:
			cname = MMAttrdefs.getattr(node, 'channel')
			return self.getchannelbyname(cname)		

	#
	def before_chan_show(self, chan = None):
		self.chans_showing = self.chans_showing + 1

	def after_chan_show(self, chan = None):
		self.chans_showing = self.chans_showing - 1
		if self.chans_showing == 0:
			self.after_showchannels()

	def after_showchannels(self):
		aftershow = self.aftershow
		self.aftershow = None
		if aftershow:
			apply(apply, aftershow)

	#
	# Channels.
	#
	def makechannels(self):
		# make layout channels
		for name in self.context.channelnames:
			attrdict = self.context.channeldict[name]
			if attrdict.get('type') == 'layout':
				self.newchannel(name, attrdict)
				self.channelnames.append(name)
		# make renderer channels
		self.makeRendererChannels()
		
		# make internal channels
		self.__makeichannels()
		
		self.makemenu()
								
	def showchannels(self):
		for name in self.channelnames:
			ch = self.channels[name]
			if ch.may_show():
				ch.show()
		self.__showichannels()
		self.makemenu()
	#
	def hidechannels(self):
		for name in self.channelnames:
			self.channels[name].hide()
		self.__hideichannels()
		self.makemenu()
	#
	def destroychannels(self):
		for name in self.channelnames[:]:
			self.killchannel(name)
		self.__destroyichannels()
		self.makemenu()
	#
	def killchannel(self, name):
		self.channels[name].destroy()
		self.channelnames.remove(name)
		del self.channels[name]
		del self.channeltypes[name]

	#
	def newchannel(self, name, attrdict):
		if not attrdict.has_key('type'):
			raise TypeError, \
				'channel ' +`name`+ ' has no type attribute'
		type = attrdict['type']
		from ChannelMap import channelmap
		if not channelmap.has_key(type):
			raise TypeError, \
				'channel ' +`name`+ ' has bad type ' +`type`
		chclass = channelmap[type]
		ch = chclass(name, attrdict, self.scheduler, self)
		ch.uipaused(self.pausing)
		self.channels[name] = ch
		self.channeltypes[name] = type

	##########################
	#
	# Internal channels support.
	# 

	def __makeichannels(self):
		for name in self.context._ichannelnames:
			if not self.__ichannels.has_key(name):
				attrdict = self.context._ichanneldict[name]
				self.__newichannel(name, attrdict)

	def __showichannels(self):
		for name in self.__ichannels.keys():
			ch = self.__ichannels[name]
			if ch.may_show():
				ch.show()

	#
	def __hideichannels(self):
		for name in self.__ichannels.keys():
			self.__ichannels[name].hide()

	def __killchannel(self, name):
		if self.__ichannels.has_key(name):
			self.__ichannels[name].destroy()
			del self.__ichannels[name]

	#
	def __destroyichannels(self):
		ichnames = self.__ichannels.keys()
		for name in ichnames:
			self.__ichannels[name].destroy()
			del self.__ichannels[name]

	#
	def __checkichannels(self):
		ichannelnames = self.__ichannels.keys()
		for name in ichannelnames[:]:
			if name not in self.context._ichannelnames:
				self.__killchannel(name)

		ichannelnames = self.__ichannels.keys()
		for name in self.context._ichannelnames:
			if name not in ichannelnames:
				attrdict = self.context._ichanneldict[name]
				self.__newichannel(name, attrdict)

	#
	def __newichannel(self, name, attrdict):
		if not attrdict.has_key('type'):
			raise TypeError, \
				'channel ' +`name`+ ' has no type attribute'
		type = attrdict['type']
		from ChannelMap import internalchannelmap
		if not internalchannelmap.has_key(type):
			raise TypeError, \
				'internal channel ' +`name`+ ' has bad type ' +`type`
		chclass = internalchannelmap[type]
		ch = chclass(name, attrdict, self.scheduler, self)
		self.__ichannels[name] = ch

	#
	# End of Internal channels support.
	##########################

