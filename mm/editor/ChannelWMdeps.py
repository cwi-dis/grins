# Base class for other channels.
# Most methods should be overridden or at least extended.
# The default methods defined here are useful for a null channel.

from MMExc import *
import MMAttrdefs
import time


prearm_disabled = 0

channel_device = 0x4001

# Calling this routine disables the prearm facility. It is mainly
# meant to be able to demonstrate the effect of prearms on timing.

def disable_prearm():
	global prearm_disabled
	prearm_disabled = 1


class Channel:

	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	# This is used by AttrEdit.  (Node attributes that have type
	# 'channel' in the Attrdefs file are implied for the channel.)
	# Because of the rules for inheritance of class attributes,
	# channels that don't add any personal attributes needn't
	# define these variables.
	# A few additional attribute names are hardcoded in AttrEdit:
	# 'type' for channels, 'name', 'channel', 'duration' for nodes.

	chan_attrs = []
	node_attrs = []

	# Initialization method (returns self!).
	# Should be extended, not overridden.
	# NB: this *shares* the attribute dictionary with the context.
	# A good channel should modify the attribute dictionary
	# if it changes any of its internal parameters, so the change
	# in value is saved with the document and can be used as a default
	# by MMAttrdefs.getattr().  Also, a good channel reads its
	# parameters out of the attribute dictionary each time it
	# is reset, so changes made while it was dormant are noted.

	def init(self, name, attrdict, scheduler, ui):
		global channel_device
		self.name = name
		self.attrdict = attrdict
		self.scheduler = scheduler
		self.ui = ui
		self.qid = None
		self.showing = 0
		self.autoanchor = None
		self.haspauseanchor = 0
		self.node = None
		self.deviceno = channel_device
		channel_device = channel_device + 1
		return self

	def __repr__(self):
		return '<Channel instance, name=' + `self.name` + '>'

	def show(self):
		if self.may_show():
			self.showing = 1

	def hide(self):
		self.showing = 0

	def flip_visible(self):
		if self.attrdict.has_key('visible'):
			visible = self.attrdict['visible']
		else:
			visible = 1
		visible = (not visible)
		self.attrdict['visible'] = visible
		if visible:
			self.show()
		else:
			self.hide()
			
	def check_visible(self):
		if self.may_show():
			if not self.is_showing():
				self.show()
		else:
			self.hide()

	def may_show(self):
		if not self.attrdict.has_key('visible'):
			return 1
		else:
			return self.attrdict['visible']

	def is_showing(self):
		return self.showing

	def destroy(self):
		self.hide()

	def save_geometry(self):
		pass

	def defanchor(self, node, anchor):
		import fl
		fl.show_message('Cannot set internal anchor', \
			  '(this node\'s channel does not support them)', '')
		return None

	# Return the nominal duration of a node, in seconds.
	# (This does not depend on the playback rate!)

	def getduration(self, node):
		return MMAttrdefs.getattr(node, 'duration')

	# This function may be called before playing a node. It can make
	# preparations for playing the node.

	def arm(self, node):
		pass

	# This function should return true if there is a prearm outstanding.
	def did_prearm(self):
		return 0

	# This method calls the (probably overridden) arm method and times it.

	def arm_and_measure(self, node):
		if prearm_disabled: return
		now = time.millitimer()
		self.arm(node)
		duration = (time.millitimer() - now)/1000.0
		node.SetAttr('arm_duration', duration)
		print 'Arm-time now', duration

	def arm_only(self, node):
		if prearm_disabled:
			node.prearm_event = None
			del node.prearm_event
			return
		node.prearm_event = None
		self.arm(node)

	def clear(self):
		# Sanity checks:
		if self.qid:
			print 'Channel: clearnode with pending event'
		self.node = None
		
	def clearnode(self, node):
##		print 'Clearnode: ', node, self.node
		if node == self.node:
			self.clear()

	# Start playing a node.

	def play(self, node, callback, arg):
		secs = self.getduration(node)
		self.cb = (callback, arg)
		self.node = node
		self.qid = self.scheduler.enter(secs, 0, self.done, 0)

	# Function called when an even't time is up.

	def done(self, dummy):
		self.qid = None
		if not self.did_prearm():
			#XXXX This is wrong. did_prearm checks wether the
			# next arm has been *executed* and we want to know
			# whether it has been *scheduled*. Too much work to fix
			# it, though.
			self.scheduler.arm_ready(self.name)
		if self.haspauseanchor and not self.ui.ignore_pauses:
			return
		if self.cb:
			callback, arg = self.cb
			apply(callback, arg)
			self.cb = None
		if self.autoanchor:
			rv = self.scheduler.anchorfired(self.node, \
				  [self.autoanchor])
		self.autoanchor = None
	# Pauseanchor_done is similar to done, but should also cancel the
	# possible outstanding 'done' event.
	def pauseanchor_done(self, dummy):
		if self.qid:
			self.scheduler.cancel(self.qid)
			self.qid = 0
		self.done(dummy)

	# Setting the playback rate to 0.0 freezes the channel.
	# Ignored by null channels -- the timer queue already
	# takes care of this.  The initial value is 0.0!!!

	def setrate(self, rate):
		pass

	# Stop the current event immediately.

	def stop(self):
		if self.qid <> None:
			print 'cancel', self.name, self.qid
			self.scheduler.cancel(self.qid)
			self.qid = None
		self.clear()

	# Reset the channel's state.
	# This should only be called in stopped state.

	def reset(self):
		pass

	# Reset the channel's state if it currently has a node.

	def softreset(self):
		if self.node != None:
			self.reset()

	# Set or clear the watch cursor for the window (override in subclass)

	def setwaiting(self):
		pass

	def setready(self):
		pass

	# Get a node's filename, resolve it using the context's dirname

	def getfilename(self, node):
		return node.context.findfile(MMAttrdefs.getattr(node, 'file'))
