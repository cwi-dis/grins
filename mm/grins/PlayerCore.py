__version__ = "$Id$"

# PlayerCore module -- Player stuff not related to UI or scheduling


import windowinterface
#from MMExc import *
import MMAttrdefs
from Selecter import Selecter


# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

class PlayerCore(Selecter):
	#
	# Initialization.
	#
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.playroot = self.root # top of current mini-document
		self.userplayroot = self.root # node specified by part play
		self.context = self.root.GetContext()
		self.chans_showing = 0
		Selecter.__init__(self)
	#
	# Internal reset.
	#
	def fullreset(self):
		self.reset()
		self.playroot = self.userplayroot = self.root
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
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		if node.GetRoot() is not self.root:
			raise CheckError, 'playsubtree with bad arg'
		self.userplayroot = self.playroot = node
		self.play()
	#
	def playfrom(self, node):
		self.playfromanchor(node, None)
	#
	def playfromanchor(self, node, anchor):
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		self.reset()
		if not self.gotonode(node, anchor, None):
			return
		self.playing = 1
		self.showstate()

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
			self.makemenu()
		return ch
	#
	def updatefixedanchors(self, node):
		ch = self.anchorinit(node)
		if ch is None:
			return 1	# Cannot set on internal nodes
		return ch.updatefixedanchors(node)

	#
	def pause(self, wantpause):
		if self.pausing == wantpause:
			print 'Funny: pause state already ok...'
			return
		self.pausing = wantpause
		if self.pausing:
			self.scheduler.setpaused(1)
		else:
			self.scheduler.setpaused(0)
		self.showstate()
	#
	#
	def maystart(self):
		return not self.locked
	#
	# Channels.
	#
	def makechannels(self):
		for name in self.context.channelnames:
			attrdict = self.context.channeldict[name]
			self.newchannel(name, attrdict)
			self.channelnames.append(name)
		self.makemenu()
	#
	def getchannelbyname(self, name):
	        if self.channels.has_key(name):
		    return self.channels[name]
		else:
		    return None
	#
	def getchannelbynode(self, node):
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
			apply(aftershow[0], aftershow[1])

	def showchannels(self):
		self.before_chan_show()
		for name in self.channelnames:
			ch = self.channels[name]
			if ch.may_show():
				ch.show()
		self.after_chan_show()
		self.makemenu()
	#
	def hidechannels(self):
		for name in self.channelnames:
			self.channels[name].hide()
		self.makemenu()
	#
	def destroychannels(self):
		for name in self.channelnames[:]:
			self.killchannel(name)
		self.makemenu()
	#
	def killchannel(self, name):
		self.channels[name].destroy()
		self.channelnames.remove(name)
		del self.channels[name]
		del self.channeltypes[name]

	def newchannel(self, name, attrdict):
		type = attrdict.get('type')
		if type is None:
			raise TypeError, \
				'channel ' +`name`+ ' has no type attribute'
		from ChannelMap import channelmap
		chclass = channelmap.get(type)
		if chclass is None:
			raise TypeError, \
				'channel ' +`name`+ ' has bad type ' +`type`
		ch = chclass(name, attrdict, self.scheduler, self)
		if self.pausing:
			ch.setpaused(self.pausing)
		if not self.waiting:
			ch.setready()
		self.channels[name] = ch
		self.channeltypes[name] = type
