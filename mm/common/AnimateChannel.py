__version__ = "$Id$"

#
# Animate Channel (Virtual)
#

# This channel is not indended to be directly visible to users.
# Nodes of this channel (i.e animations) should play in parallel 
# with the animated node simulating the smil section:
# <par>
# <animatedNode>
# <animate ...>
# <animate ...>
# <par>
 

import Channel
import MMAttrdefs
import time

import Animators

debug=0
	

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
		self.__fiber_id=0
		self.__playdone = 0
		self.__animator = None

	def __repr__(self):
		return '<AnimateChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelAsync.do_show(self, pchan):
			return 0
		return 1

	def do_hide(self):
		self.__animating = None
		self.__stopAnimate()
		Channel.ChannelAsync.do_hide(self)

	def do_arm(self, node, same=0):
		print 'AnimateChannel.do_arm',node.attrdict
		print 'target node:',node.targetnode.attrdict
		
		parser = Animators.AnimateElementParser(node, node.targetnode)
		self.__animator = parser.getAnimator()
		if self.__animator:
			print 'animate attr start value:',self.__animator.getValue(0)
		
		return 1

	def do_play(self, node):
		print 'AnimateChannel.do_play'
		
		if not self.__animator:
			# arming failed, so don't even try playing
			self.playdone(0)
			return

		# get timing
		self.__animating = node
		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		self.__duration = node.GetAttrDef('duration', None)
		self.__startAnimate()

	def stopplay(self, node):
		print 'AnimateChannel.stopplay'
		if self.__animating is node and node is not None:
			self.__stopAnimate()
		self.__animating = None
		Channel.ChannelAsync.stopplay(self, node)

	def setpaused(self, paused):
		self.__pauseAnimate(paused)
		Channel.ChannelAsync.setpaused(self, paused)

	def __startAnimate(self):
		self.__start = time.time()
		self.__register_for_timeslices()
		print 'start animation'

	def __stopAnimate(self):
		if self.__animator:
			print 'stop animation, restoring dom value', self.__animator.getDOMValue()
		self.__unregister_for_timeslices()

	def __pauseAnimate(self, paused):
		if self.__animating:
			if paused:
				self.__unregister_for_timeslices()
			else:
				self.__register_for_timeslices()

	def __animate(self):
		# animate target node.attribute
		# taking into account additive, accumulate attrs
		dt = time.time()-self.__start
		print 'animating:', self.__animator.getValue(dt)

	def __onAnimateDur(self):
		if not self.__animating:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
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

	def is_callable(self):
		return self.__animating
	def __register_for_timeslices(self):
		if self.__fiber_id: return
		import windowinterface
		self.__fiber_id=windowinterface.register((self.is_callable,()),(self.on_idle_callback,()))
	def __unregister_for_timeslices(self):
		if not self.__fiber_id: return
		import windowinterface
		windowinterface.unregister(self.__fiber_id)
		self.__fiber_id=0
