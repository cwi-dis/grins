# This is the player module.

from MMExc import *
import fl
from FL import *

from Queue import Queue

HD, TL = 0, 1

from NullChannel import NullChannel
from TextChannel import TextChannel
from SoundChannel import SoundChannel
channelmap = {'sound':SoundChannel, 'text':TextChannel, 'null':NullChannel}

# Class representing player state.
# This will have a single instance.

class Player():
	#
	def run(self):
		self.queue.run()
	#
	# Initialization.
	#
	def init(self, root):
		self.root = root
		self.state = 'stopped'
		self.channels = {}
		self.channelnames = []
		self.queue = Queue().init()
		self.makechannels()
		# Create the control panel last, as a sign we're finally ready
		self.makecpanel()
		return self
	#
	def makecpanel(self):
		#
		cpanel = fl.make_form(FLAT_BOX, 200, 100)
		#
		self.playbutton = \
			cpanel.add_button(INOUT_BUTTON,0,50,100,50, 'Play')
		self.playbutton.set_call_back(self.play_callback, None)
		#
		self.pausebutton = \
			cpanel.add_button(INOUT_BUTTON,100,50,50,50, 'Pause')
		self.pausebutton.set_call_back(self.pause_callback, None)
		#
		self.stopbutton = \
			cpanel.add_button(INOUT_BUTTON,150,50,50,50, 'Stop')
		self.stopbutton.set_call_back(self.stop_callback, None)
		#
		self.quitbutton = \
			cpanel.add_button(NORMAL_BUTTON,0,0,50,50, 'Quit')
		self.quitbutton.set_call_back(self.quit_callback, None)
		#
		self.statebutton = \
			cpanel.add_button(NORMAL_BUTTON,50,0,100,50, \
			self.state)
		self.statebutton.set_call_back(self.state_callback, None)
		#
		cpanel.show_form(PLACE_SIZE, TRUE, 'Control Panel')
		self.cpanel = cpanel
	#
	# State transitions.
	#
	def play(self): # stopped --> playing
		if self.state <> 'stopped':
			raise CheckError, 'play in state ' + `self.state`
		self.setstate('playing')
		self.queue.setrate(1.0)
		self.start_playing()
	#
	def freeze(self): # playing --> frozen
		if self.state <> 'playing':
			raise CheckError, 'freeze in state ' + `self.state`
		self.setstate('frozen')
		self.queue.freeze()
		for cname in self.channelnames: self.channels[cname].freeze()
	#
	def unfreeze(self): # frozen --> playing
		if self.state <> 'frozen':
			raise CheckError, 'unfreeze in state ' + `self.state`
		self.setstate('playing')
		self.queue.unfreeze()
		for cname in self.channelnames: self.channels[cname].unfreeze()
	#
	def stop(self): # playing --> stopped
		if self.state <> 'playing':
			raise CheckError, 'stop in state ' + `self.state`
		self.setstate('stopped')
		self.queue.setrate(0.0)
		for cname in self.channelnames: self.channels[cname].stop()
		self.stop_playing()
	#
	def setstate(self, state):
		self.state = state
		self.showstate()
	#
	def showstate(self):
		self.statebutton.label = self.state
		self.playbutton.set_button(self.state = 'playing')
		self.pausebutton.set_button(self.state = 'frozen')
	#
	# FORMS callbacks (frankly, a mess right now).
	#
	def play_callback(self, (obj, arg)):
		if not obj.get_button():
			self.showstate()
		elif self.state = 'stopped':
			self.play()
		elif self.state = 'frozen':
			self.unfreeze()
		elif self.state = 'playing':
			self.showstate()
		else:
			raise AssertError, \
				'play callback: bad state ' + `self.state`
	#
	def pause_callback(self, (obj, arg)):
		if not obj.get_button():
			self.showstate()
		elif self.state = 'stopped':
			self.play()
			self.freeze()
		elif self.state = 'frozen':
			self.unfreeze()
		elif self.state = 'playing':
			self.freeze()
		else:
			raise AssertError, \
				'pause callback: bad state ' + `self.state`
	#
	def stop_callback(self, (obj, arg)):
		if not obj.get_button():
			self.showstate()
		if self.state = 'stopped':
			self.showstate()
		elif self.state = 'frozen':
			self.unfreeze()
			self.stop()
		elif self.state = 'playing':
			self.stop()
		else:
			raise AssertError, \
				'stop callback: bad state ' + `self.state`
	#
	def state_callback(self, (obj, arg)):
		pass
	#
	def quit_callback(self, (obj, arg)):
		self.stop_callback(self.stopbutton, None)
		raise ExitException, 0
	#
	# Channel administration.
	#
	def makechannels(self):
		#
		clist = self.root.GetAttrDef('channellist', [])
		if clist = []:
			cdict = self.root.GetAttr('channeldict')
			keys = cdict.keys()
			keys.sort()
			for key in keys:
				clist.append(key, cdict[key])
		#
		for name, attrdict in clist:
			self.channelnames.append(name)
			self.channels[name] = self.newchannel(name, attrdict)
	#
	def newchannel(self, (name, attrdict)):
		print 'Creating new channel named ' +`name`
		if not attrdict.has_key('type'):
			raise TypeError, \
				'channel ' +`name`+ ' has no type attribute'
		type = attrdict['type']
		if not channelmap.has_key(type):
			raise TypeError, \
				'channel ' +`name`+ ' has bad type ' +`type`
		chclass = channelmap[type]
		return chclass().init(name, attrdict, self)
	#
	# Playing algorithm.
	#
	def start_playing(self):
		self.prep1(self.root)
		self.prep2(self.root)
		if self.root.counter[HD] <> 0:
			raise TypeError, 'head of root has dependencies!?!?!'
		self.root.counter[HD] = 1
		self.decrement(0, self.root, HD)
	#
	def stop_playing(self):
		self.queue.queue[:] = [] # Erase all events with brute force!
		self.cleanup(self.root)
	#
	def cleanup(self, node):
		# XXX (doesn't need to be a method)
		del node.counter
		del node.deps
		type = node.GetType()
		if type in ('seq', 'par'):
			for c in node.GetChildren():
				self.cleanup(c)
	#
	def prep1(self, node):
		node.counter = [0, 0]
		node.deps = [], []
		type = node.GetType()
		if type = 'seq':
			xnode, xside = node, HD
			for c in node.GetChildren():
				self.prep1(c)
				self.adddep(xnode, xside, 0, c, HD)
				xnode, xside = c, TL
			self.adddep(xnode, xside, 0, node, TL)
		elif type = 'par':
			for c in node.GetChildren():
				self.prep1(c)
				self.adddep(node, HD, 0, c, HD)
				self.adddep(c, TL, 0, node, TL)
		else:
			# Special case -- delay -1 means execute leaf node
			# of leaf node when playing
			self.adddep(node, HD, -1, node, TL)
	#
	def prep2(self, node):
		pass
		# Should recursively do explicit deps (from synctolist attrs)
	#
	def adddep(self, (xnode, xside, delay, ynode, yside)):
		# XXX (doesn't need to be a method)
		ynode.counter[yside] = ynode.counter[yside] + 1
		if delay >= 0:
			xnode.deps[xside].append(delay, ynode, yside)
	#
	def decrement(self, (delay, node, side)):
#		print 'decrement', (delay, node.GetUID(), ('HD', 'TL')[side])
		if delay > 0:
			id = self.queue.enter(delay, 0, self.decrement, \
						(0, node, side))
			return
		x = node.counter[side] - 1
		node.counter[side] = x
		if x > 0: return
		if x < 0: raise RuntimeError, 'counter below zero!?!?'
		if node.GetType() not in ('seq', 'par'):
			if  side = HD:
#				print 'HEAD', node.GetUID(),
#				print node.GetInherAttr('channel')
				chan = self.getchannel(node)
				chan.play(node, self.decrement, (0, node, TL))
#			else:
#				print 'TAIL', node.GetUID(),
#				print node.GetInherAttr('channel')
		for arg in node.deps[side]:
			self.decrement(arg)
	#
	# Channel access utilities.
	#
	def getduration(self, node):
		chan = self.getchannel(node)
		return chan.getduration(node)
	#
	def getchannel(self, node):
		cname = node.GetInherAttr('channel')
		return self.channels[cname] # What? no channel on this node?
	#
