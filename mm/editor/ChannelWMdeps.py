# Base class for other channels.
# Most methods should be overridden or at least extended.
# The default methods defined here are useful for a null channel.

from MMExc import *
import MMAttrdefs

class Channel():
	#
	# Initialization method (returns self!).
	# Should be extended, not overridden.
	# NB: this *shares* the attribute dictionary with the context.
	# A good channel should modify the attribute dictionary
	# if it changes any of its internal parameters, so the change
	# in value is saved with the document and can be used as a default
	# by MMAttrdefs.getattr().  Also, a good channel reads its
	# parameters out of the attribute dictionary each time it
	# is reset, so changes made while it was dormant are noted.
	#
	def init(self, (name, attrdict, player)):
		self.name = name
		self.attrdict = attrdict
		self.rate = 1.0
		self.player = player
		self.qid = None
		return self
	#
	# Set the playback rate.  
	# The rate argument should be 1.0 for normal playback,
	# > 1.0 for fast forward, 0.0 < rate < 1.0 for slow motion.
	# Don't use a rate of 0.0 to pause; use freeze/unfreeze instead.
	# Don't use negative rates for reverse playback (yet).
	#
	def setrate(self, rate):
		self.rate = float(rate)
	#
	# Return the nominal duration of a node, in seconds.
	# (This does not depend on the playback rate!)
	#
	def getduration(self, node):
		return MMAttrdefs.getattr(node, 'duration')
	#
	# Start playing a node.
	#
	def play(self, (node, callback, arg)):
		secs = self.getduration(node)
		self.qid = self.player.enter(secs, 0, self.done, \
							(callback, arg))
	#
	# Don't call done() directly -- it's a callback used internally.
	#
	def done(self, (callback, arg)):
		self.qid = None
		callback(arg)
	#
	# Setting the playback rate to 0.0 freezes the channel.
	# Ignored by null channels -- the timer queue already
	# takes care of this.  The initial value is 0.0!!!
	#
	def setrate(self, rate):
		pass
	#
	# Stop the current event immediately.
	#
	def stop(self):
		if self.qid <> None:
			self.player.cancel(self.qid)
			self.qid = None
	#
	# Reset the channel's state.
	# This should only be called in stopped state.
	#
	def reset(self):
		pass
	#
