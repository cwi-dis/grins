# Base class for other channels.
# Most methods should be overridden or at least extended.
# The default methods defined here are useful for a null channel.

class Channel():
	#
	# Initialization method (returns self!).
	# Should be extended, not overridden.
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
		return float(node.GetInherAttrDef('duration', 2.0))
	#
	# Start playing a node.
	#
	def play(self, (node, callback, arg)):
		secs = self.getduration(node)
		self.qid = self.player.queue.enter(secs, 0, self.done, \
							(callback, arg))
	#
	# Don't call done() directly -- it's a callback used internally.
	#
	def done(self, (callback, arg)):
		self.qid = None
		callback(arg)
	#
	# Freeze and unfreeze have a dummy implementation here --
	# they rely on the queue implementing the delay.
	#
	def freeze(self):
		pass
	#
	def unfreeze(self):
		pass
	#
	def stop(self):
		if self.qid <> None:
			self.player.queue.cancel(self.qid)
			self.qid = None
	#
