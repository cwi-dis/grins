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
		self.__curloop = 0

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
		
		# take into account accumulation effect
		# self.__curloop  is the zero based loop counter
		self.__curloop = 0
		value = node.GetAttrDef('loop', None)
		if value:
			self.__curloop = value - node.curloopcount - 1

		self.__animating = node

		# get duration in secs (float)
		self.__duration = self.__animator.getTimeManipulatedDur()

		self.__startAnimate()

	def setpaused(self, paused):
		Channel.ChannelAsync.setpaused(self, paused)
		self.__pauseAnimate(paused)

	def playstop(self):
		self.__stopAnimate()
		Channel.ChannelAsync.playstop(self)

	def stopplay(self, node):
		self.__stopAnimate()
		self.__removeAnimate()
		Channel.ChannelAsync.stopplay(self, node)

	#
	# Animation engine
	#

	def __initEngine(self, node):
		self.__animator = None
		self.__effAnimator = None

		self.__fiber_id = None
		self.__playdone = 0
		self.__targetChannel = None
		self.__lastvalue = None
		self.__start = None
		self._pausedt = 0

		if not hasattr(self._player,'_animateContext'):
			self._player._animateContext = Animators.AnimateContext(self._player)
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

		chname = MMAttrdefs.getattr(targnode, 'channel')
		if targnode.GetChannelType()!='layout':
			# XXX: not always correct
			# whats the method to  find node's channel (name %d)?	
			chname = chname + ' 0' 
		self.__targetChannel = self._player.getchannelbyname(chname)
		return self.__targetChannel
		
	def __startAnimate(self):
		self.__start = self.__animating.start_time
		if self.__start is None:
			print 'Warning: None start_time for node',self.__animating
			self.__start = 0
		self.__effAnimator.onAnimateBegin(self.__getTargetChannel(), self.__animator)
		
		# take into account accumulation effect
		for i in range(self.__curloop):
			self.__animator.setToEnd()

		self.__animate()
		self.__register_for_timeslices()

	def __stopAnimate(self):
		if self.__animating:
			self.__unregister_for_timeslices()
			self.__animator.setToEnd()
			self.__animating = None

	def __removeAnimate(self):
		if self.__effAnimator:
			self.__effAnimator.onAnimateEnd(self.__getTargetChannel(), self.__animator)
			self.__effAnimator = None

	def __pauseAnimate(self, paused):
		if self.__animating:
			if paused:
				self.__unregister_for_timeslices()
			else:
				self.__register_for_timeslices()

	def __animate(self):
		try:
			dt = self._scheduler.timefunc() - self.__start
		except TypeError, arg:
			print arg
			self.playdone(0)
			return
		dt = dt - self.__duration * int(float(dt) / self.__duration)
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
		self.playdone(0)

	def onIdle(self):
		if not USE_IDLE_PROC:
			self.__fiber_id = None
		if self.__animating:
			t_sec=self._scheduler.timefunc() - self.__start
			# end-point exclusive model
			if t_sec>=self.__duration:
				self.__unregister_for_timeslices()
				self.__onAnimateDur()
			else:
				self.__animate()
				if not USE_IDLE_PROC:
					self.__register_for_timeslices()
			
	def __register_for_timeslices(self):
		if self.__fiber_id is None:
			if USE_IDLE_PROC:
				self.__fiber_id = windowinterface.setidleproc(self.onIdle)
			else:
				self.__fiber_id = windowinterface.settimer(0.05, (self.onIdle,()))

	def __unregister_for_timeslices(self):
		if self.__fiber_id is not None:
			if USE_IDLE_PROC:
				windowinterface.cancelidleproc(self.__fiber_id)
			else:
				windowinterface.canceltimer(self.__fiber_id)
			self.__fiber_id = None
