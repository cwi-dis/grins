__version__ = "$Id$"

#
# Animate Channel (Virtual)
#

# This channel is also a kind of a player as are the other channels.
# It belongs to the 'control' family of channels (python, socket, etc)
# It is not actually very different from a python channel.
# It also executes a kind of a script.
# The script it executes is build from the animate elements of the document.
# The special thing with this one is that it has no effect by itself.
# Its effect comes from the script's target channel.
# It acts on its target channel by changing its attributes.
# The strong relation with its target channel and the fact 
# that is an async channel is what makes it special.

import Channel
import MMAttrdefs
import time
import Animators

# for timer support
import windowinterface

debug = 0

class AnimateChannel(Channel.ChannelAsync):
	node_attrs = ['targetElement','attributeName',
		'attributeType','additive','accumulate',
		'calcMode', 'values', 'keyTimes',
		'keySplines', 'from', 'to', 'by',
		'path', 'origin',]

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__animating = None
		self.__duration = 0
		self.__fiber_id = 0
		self.__playdone = 0
		self.__animator = None
		self.__effAnimator = None
		self.__targetChannel = None
		self.__lastvalue = None
		if not hasattr(self._player,'_animateContext'):
			self._player._animateContext = Animators.AnimateContext()
		
	def __repr__(self):
		return '<AnimateChannel instance, name=' + `self._name` + '>'
		
	def do_show(self, pchan):
		if not Channel.ChannelAsync.do_show(self, pchan):
			return 0
		return 1

	def do_hide(self):
		self.__stopAnimate()
		self.__animating = None
		Channel.ChannelAsync.do_hide(self)

	def do_arm(self, node, same=0):
		parser = Animators.AnimateElementParser(node)
		self.__animator = parser.getAnimator()
		if self.__animator:
			# find and apply parent spped
			speed = node.GetParent().GetRawAttrDefProduct('speed', 1.0)
			self.__animator._setSpeed(speed)
			# get the effective animator of the attribute
			context = self._player._animateContext
			self.__effAnimator = context.getEffectiveAnimator(
				parser.getTargetNode(), 
				parser.getGrinsAttrName(), 
				parser.getDOMValue())
		return 1

	def do_play(self, node):
		if debug: print 'AnimateChannel.do_play'
		
		if not self.__animator or not self.__effAnimator:
			# arming failed, so don't even try playing
			self.playdone(0)
			return

		# the playing node
		self.__animating = node

		# get timing
		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		#self.__duration = node.GetAttrDef('duration', None)
		self.__duration = self.__animator.getTimeManipulatedDur()

		self.__startAnimate()

	def stopplay(self, node):
		if self.__animating is node and node is not None:
			self.__stopAnimate()
		self.__animating = None
		Channel.ChannelAsync.stopplay(self, node)

	def setpaused(self, paused):
		self.__pauseAnimate(paused)
		Channel.ChannelAsync.setpaused(self, paused)

	def __getTargetChannel(self):
		if self.__targetChannel:
			return self.__targetChannel
		targnode = self.__effAnimator.getTargetNode()
		chname =  MMAttrdefs.getattr(targnode, 'channel') 
		self.__targetChannel = self._player.getchannelbyname(chname)
		return self.__targetChannel
		
	def __startAnimate(self, repeat=0):
		self.__start = time.time()
		if not repeat:		
			self.__effAnimator.onAnimateBegin(self.__getTargetChannel(), self.__animator)
		self.__animate()
		self.__register_for_timeslices()

	def __stopAnimate(self):
		self.__unregister_for_timeslices()
		if not self.__animating or not self.__animator:
			return
		self.__effAnimator.onAnimateEnd(self.__getTargetChannel(), self.__animator)

	def __pauseAnimate(self, paused):
		if self.__animating:
			if paused:
				self.__unregister_for_timeslices()
			else:
				self.__register_for_timeslices()

	def __animate(self):
		dt = time.time()-self.__start
		val = self.__animator.getValue(dt)
		if self.__effAnimator:
			if self.__lastvalue != val:
				self.__effAnimator.update(self.__getTargetChannel())
				self.__lastvalue = val

	def __onAnimateDur(self):
		if not self.__animating:
			return
		# set to the end for the benefit of freeze and repeat
		self.__animator.setToEnd()
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self.__startAnimate(repeat=1)
				return
			self.__playdone = 1
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self.__startAnimate(repeat=1)

	def on_idle_callback(self):
		if self.__animating and not self.__playdone:
			t_sec=time.time() - self.__start
			# end-point exclusive model
			if t_sec>=self.__duration:
				self.__onAnimateDur()
			else:
				self.__animate()
		self.__fiber_id = windowinterface.settimer(0.05, (self.on_idle_callback,()))
			
	def __register_for_timeslices(self):
		if self.__fiber_id: return
		self.__fiber_id = windowinterface.settimer(0.05, (self.on_idle_callback,()))

	def __unregister_for_timeslices(self):
		if not self.__fiber_id: return
		windowinterface.canceltimer(self.__fiber_id)
		self.__fiber_id = 0
