# PlayerCore module -- Player stuff not related to UI or scheduling


import fl
from Scheduler import Scheduler, flushchannelcache
from MMExc import *
import Timing


# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

class PlayerCore(Scheduler):
	#
	# Initialization.
	#
	def init(self, toplevel):
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.playroot = self.root # top of current mini-document
		self.userplayroot = self.root # node specified by part play
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.editmgr.register(self)
		return Scheduler.init(self)
	#
	# EditMgr interface (as dependent client).
	#
	def transaction(self):
		# Disallow changes while we are playing.
		if self.playing:
			m1 = 'You cannot change the document'
			m2 = 'while it is playing.'
			m3 = 'Do you want to stop playing?'
			if not fl.show_question(m1, m2, m3):
				return 0
			self.stop()
		self.locked = 1
		return 1
	#
	def commit(self):
		if self.showing:
			self.checkchannels()
			# Check if any of the playroots has vanished
			if self.playroot.GetRoot() <> self.root:
				self.playroot = self.root
			if self.userplayroot.GetRoot() <> self.root:
				self.userplayroot = self.root
		self.locked = 0
		self.measure_armtimes = 1
		flushchannelcache(self.root)
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
		self.resetchannels()
		self.reset()
		self.playroot = self.userplayroot = self.root
		self.measure_armtimes = 0
	#
	def reset(self):
		self.resettimer()
		self.softresetchannels()
		if self.setcurrenttime_callback:
			self.setcurrenttime_callback(0.0)
	#
	# State transitions.
	#
	def play(self):
		self.seeking = 0
		if not self.playing:
			self.playroot = self.userplayroot
			if not self.start_playing(1.0):
				return
		else:
			self.setrate(1.0)
			self.showstate()
	#
	def playsubtree(self, node):
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		if node.GetRoot() <> self.root:
			raise CheckError, 'playsubtree with bad arg'
		self.userplayroot = self.playroot = node
		self.play()
	#
	def defanchor(self, node, anchor):
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		ch = self.getchannel(node)
		if ch == None:
			fl.show_message('Cannot set internal anchor', \
				  '(node not on a channel)', '')
			return
		if not ch.is_showing():
			ch.flip_visible()
			self.makemenu()
		return ch.defanchor(node, anchor)
	#
	def pause(self):
		self.seeking = 0
		if self.playing:
			if self.rate == 0.0:	# Paused: continue
				self.setrate(1)
			else:			# Running: pause
				self.setrate(0)
				self.setready() # Cancel possible watch cursor
		else:
			dummy = self.start_playing(0.0)
			self.setready()
		self.showstate()
	#
	def stop(self):
		self.seeking = 0
		if self.playing:
			self.stop_playing()
		else:
			self.fullreset()
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
	def checkchannels(self):
		chchanged = 0
		# XXX Ought to detect renamed channels...
		# (1) Delete channels that have disappeared
		# or whose type has changed
		for name in self.channelnames[:]:
			if name not in self.context.channelnames:
				chchanged = 1
				print 'Detected deleted channel'
				self.killchannel(name)
				flushchannelcache(self.root)
			else:
				oldtype = self.channeltypes[name]
				newtype = \
				    self.context.channeldict[name]['type']
				if oldtype <> newtype:
					print 'Detected retyped channel'
					self.killchannel(name)
					flushchannelcache(self.root)
					chchanged = 1
		# (2) Add new channels that have appeared
		for name in self.context.channelnames:
			if name not in self.channelnames:
				print 'Detected new channel'
				attrdict = self.context.channeldict[name]
				self.newchannel(name, attrdict)
				i = self.context.channelnames.index(name)
				self.channelnames.insert(i, name)
				self.channels[name].show()
				chchanged = 1
		# (3) Update visibility of all channels
		for name in self.channelnames:
			self.channels[name].check_visible()
		# (4) Update menu
		self.makemenu()
		if chchanged:
			self.toplevel.channelview.channels_changed()
	#
	def showchannels(self):
		for name in self.channelnames:
			self.channels[name].show()
		self.makemenu()
	#
	def hidechannels(self):
		for name in self.channelnames:
			self.channels[name].hide()
		self.makemenu()
	#
	def destroychannels(self):
		flushchannelcache(self.root)
		for name in self.channelnames[:]:
			self.killchannel(name)
		self.makemenu()
	#
	def killchannel(self, name):
		self.channels[name].destroy()
		self.channelnames.remove(name)
		del self.channels[name]
		del self.channeltypes[name]
	#
	def newchannel(self, (name, attrdict)):
		if not attrdict.has_key('type'):
			raise TypeError, \
				'channel ' +`name`+ ' has no type attribute'
		type = attrdict['type']
		from ChannelMap import channelmap
		if not channelmap.has_key(type):
			raise TypeError, \
				'channel ' +`name`+ ' has bad type ' +`type`
		chclass = channelmap[type]
		ch = chclass().init(name, attrdict, self)
		self.channels[name] = ch
		self.channeltypes[name] = type
	#
	def resetchannels(self):
		for cname in self.channelnames:
			self.channels[cname].reset()
	#
	def softresetchannels(self):
		for cname in self.channelnames:
			self.channels[cname].softreset()
	#
	def stopchannels(self):
		for cname in self.channelnames:
			self.channels[cname].stop()
