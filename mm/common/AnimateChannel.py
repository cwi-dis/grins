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
# It can play only when its target channel is playing.
# The strong relation with its target channel and the fact 
# that is an async channel is what makes it special.

import Channel
import MMAttrdefs
import time
import Animators

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
		self.__targetchan = None
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
		parser = Animators.AnimateElementParser(node, node.targetnode)
		self.__animator = parser.getAnimator()
		targetchname = MMAttrdefs.getattr(node.targetnode, 'channel') 
		self.__targetchan = self._player.getchannelbyname(targetchname)
		if self.__targetchan and self.__animator:
			context = self._player._animateContext
			self.__effAnimator = context.getEffectiveAnimator(node.targetnode, 
				self.__animator.getAttrName(), 
				self.__animator.getDOMValue())
		return 1

	def do_play(self, node):
		if debug: print 'AnimateChannel.do_play'
		
		if not self.__animator or not self.__targetchan:
			# arming failed, so don't even try playing
			self.playdone(0)
			return

		# get timing
		self.__animating = node
		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		#self.__duration = node.GetAttrDef('duration', None)
		self.__duration = self.__animator.getTimeManipulatedDur()

		self.__startAnimate()

	def stopplay(self, node):
		if debug: print 'AnimateChannel.stopplay'
		if self.__animating is node and node is not None:
			self.__stopAnimate()
		self.__animating = None
		Channel.ChannelAsync.stopplay(self, node)

	def setpaused(self, paused):
		self.__pauseAnimate(paused)
		Channel.ChannelAsync.setpaused(self, paused)

	def __startAnimate(self):
		if debug and self.__animator:
			print 'start animation, initial value', self.__animator.getValue(0)
		self.__start = time.time()

		targnode = self.__animating.targetnode
		self.__effAnimator.onAnimateBegin(self.__targetchan, targnode, self.__animator)

		self.__animate()
		self.__register_for_timeslices()

	def __stopAnimate(self):
		self.__unregister_for_timeslices()
		if not self.__animating or not self.__animator:
			return
		self.__effAnimator.onAnimateEnd(self.__animator)

	def __pauseAnimate(self, paused):
		if self.__animating:
			if paused:
				self.__unregister_for_timeslices()
			else:
				self.__register_for_timeslices()

	def __animate(self):
		dt = time.time()-self.__start
		node = self.__animating.targetnode
		attr = self.__animator.getAttrName()
		val = self.__animator.getValue(dt)
		if node and self.__targetchan:
			if self.__lastvalue != val:
				self.__effAnimator.update()
				self.__lastvalue = val
		if debug:
			msg = 'animating %s =' % attr
			print msg, self.__animator.getValue(dt)

	def __onAnimateDur(self):
		if not self.__animating:
			return	
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self.__animator.repeat()
				self.__startAnimate()
				return
			self.__playdone = 1
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self.__startAnimate()

	def on_idle_callback(self):
		if self.__animating and not self.__playdone:
			t_sec=time.time() - self.__start
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
