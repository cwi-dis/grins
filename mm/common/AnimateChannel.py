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
USE_IDLE_PROC=hasattr(windowinterface, 'setidleproc')

class AnimateChannel(Channel.ChannelAsync):
	node_attrs = ['targetElement','attributeName',
		'attributeType','additive','accumulate',
		'calcMode', 'values', 'keyTimes',
		'keySplines', 'from', 'to', 'by',
		'path', 'origin',]

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__duration = None
		self.__animating = None

	def __repr__(self):
		return '<AnimateChannel instance, name=' + `self._name` + '>'

	#
	# Channel overrides
	#

	def do_hide(self):
		Channel.ChannelAsync.do_hide(self)
		
	def do_play(self, node):
		Channel.ChannelAsync.do_play(self, node)

		self.__initEngine(node)

		if not self.__ready():
			self.playdone(0)
			return
		
		self.__animating = node

		# get timing
		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		#self.__duration = node.GetAttrDef('duration', None)
		self.__duration = self.__animator.getTimeManipulatedDur()
		
		self.__startAnimate()

	def setpaused(self, paused):
		Channel.ChannelAsync.setpaused(self, paused)
		self.__pauseAnimate(paused)

	def stopplay(self, node):
		if self.__animating:
			self.__stopAnimate()
			self.__animating = None
		Channel.ChannelAsync.stopplay(self, node)

	#
	# Animation engine
	#

	def __initEngine(self, node):
		self.__animator = None
		self.__effAnimator = None

		self.__fiber_id = 0
		self.__playdone = 0
		self.__targetChannel = None
		self.__lastvalue = None
		self.__start = None
		self._pausedt = 0

		if not hasattr(self._player,'_animateContext'):
			self._player._animateContext = Animators.AnimateContext()
		ctx = self._player._animateContext
		
		parser = Animators.AnimateElementParser(node)
		self.__animator = parser.getAnimator()
		if self.__animator:
			# find and apply parent speed
			speed = node.GetParent().GetRawAttrDefProduct('speed', 1.0)
			self.__animator._setSpeed(speed)
			# get the effective animator of the attribute
			self.__effAnimator = ctx.getEffectiveAnimator(
				parser.getTargetNode(), 
				parser.getGrinsAttrName(), 
				parser.getDOMValue())
	
	def __ready(self):
		return 	self.__animator!=None and self.__effAnimator!=None
	
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
		if self.__animating:
			self.__unregister_for_timeslices()
			self.__effAnimator.onAnimateEnd(self.__getTargetChannel(), self.__animator)
			self.__effAnimator = None

	def __pauseAnimate(self, paused):
		if self.__animating:
			if paused:
				self._pausedt = time.time() - self.__start
				self.__unregister_for_timeslices()
			else:
				self.__start = time.time() - self._pausedt
				self.__register_for_timeslices()

	def __animate(self):
		dt = time.time() - self.__start
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
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self.__startAnimate(repeat=1)

	def onIdle(self):
		if not USE_IDLE_PROC:
			self.__fiber_id = 0
		if self.__animating:
			t_sec=time.time() - self.__start
			# end-point exclusive model
			if t_sec>=self.__duration:
				self.__onAnimateDur()
				self.__unregister_for_timeslices()
			else:
				self.__animate()
				self.__register_for_timeslices()
			
	def __register_for_timeslices(self):
		if not self.__fiber_id:
			if USE_IDLE_PROC:
				windowinterface.setidleproc(self.onIdle)
				self.__fiber_id = 1
			else:
				self.__fiber_id = windowinterface.settimer(0.05, (self.onIdle,()))

	def __unregister_for_timeslices(self):
		if self.__fiber_id:
			if USE_IDLE_PROC:
				windowinterface.cancelidleproc(self.onIdle)
			else:
				windowinterface.canceltimer(self.__fiber_id)
			self.__fiber_id = 0
