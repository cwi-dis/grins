__version__ = "$Id$"

# Channels should either use Channel, ChannelWindow, or ChannelThread
# (from module ChannelThread) as a superclass, but never more than
# one.

import os
debug = 0
import MMAttrdefs
from MMExc import NoSuchAttrError, CheckError
import windowinterface, WMEVENTS
from windowinterface import SINGLE, TEXT, HTM, MPEG
from windowinterface import TRUE, FALSE
import string
import MMurl
import urlparse
error = 'Channel.error'
from usercmd import *

channel_device = 1
channels = []				# list of channels

# arm states
AIDLE = 1
ARMING = 2
ARMED = 3
# play states
PIDLE = 1
PLAYING = 2
PLAYED = 3

import settings

ACTIVATEEVENT = 'activateEvent'

def isin(elem, list):
	# faster than "elem in list"
	for x in list:
		if elem is x:
			return 1
	return 0

class Channel:
	#
	# The following methods can be called by higher levels.
	#
	chan_attrs = ['visible', 'base_window']
	node_attrs = ['file', 'mimetype', 'project_convert', 'duration',
		      'repeatdur', 'loop']
	_visible = FALSE

	def __init__(self, name, attrdict, scheduler, ui):
		# Create and initialize a Channel object instance.
		# The arguments are the name of the channel, an
		# attribute dictionary and the scheduler and user
		# interface objects to which this instance belongs.
		global channel_device
		self._deviceno = channel_device
		channel_device = channel_device + 1
		self._armcontext = None
		self._armed_anchors = []
		self._armed_node = None
		self._armstate = AIDLE
		self._attrdict = attrdict
		self._is_shown = 0
		self._name = name
		self._anchors = {}
		self._playcontext = None
		self._played_anchors = []
		self._played_node = None
		self._player = ui
		self._playstate = PIDLE
		self._qid = None
		self._scheduler = scheduler
		self._paused = None
		self._subchannels = []
		self._want_shown = 0
		self._highlighted = None
		self._in_modeless_resize = 0
		self.armBox = (0.0, 0.0, 1.0, 1.0) # by default all window area
		self.playBox = (0.0, 0.0, 1.0, 1.0) # by default all window area
		self.nopop = 0
		self.need_reshow = 0
		self.syncarm = 1	# was: settings.noprearm (always 1)
		self.syncplay = 0
		self.is_layout_channel = 0
		self.seekargs = None
		self._armed_anchor2button = {}
		self._played_anchor2button = {}
		self._hide_pending = 0
		self._exporter = None
		self.cssResolver = self._player.cssResolver
		if debug: print 'Channel() -> '+`self`
		channels.append(self)
		if hasattr(ui, 'editmgr'):
			self.editmgr = ui.editmgr
			ui.editmgr.register(self)
		self._curvals = {}

	def __repr__(self):
		return '<%s instance, name=%s>' % (self.__class__.__name__, self._name)

	def destroy(self):
		# Destroy this instance of a Channel object.  This
		# will stop playing and arming on this channel and
		# release all used resources.  After this, none of the
		# methods of this instance may be called anymore.
		if debug: print 'Channel.destroy('+`self`+')'
		if self._is_shown:
			self.hide()
		if hasattr(self._player, 'editmgr'):
			self._player.editmgr.unregister(self)
		del self._armcontext
		del self._armed_anchors
		del self._armed_anchor2button
		del self._armed_node
		del self._armstate
		del self._attrdict
		del self._deviceno
		del self._anchors
		del self._playcontext
		del self._played_anchors
		self._played_anchor2button = {}	# I've seen irreproduceable crash due to this being deleted -sjoerd
		del self._played_node
		del self._player
		del self._playstate
		del self._qid
		del self._scheduler
		del self._exporter
		for i in range(len(channels)):
			if channels[i] is self:
				del channels[i]
				break
		for chan in channels:
			for i in range(len(chan._subchannels)):
				if chan._subchannels[i] is self:
					del chan._subchannels[i]
					break

	def commit(self, type):
		try:
			if debug: print 'Channel.commit'+`self,type`
			if type in ('REGION_GEOM', 'MEDIA_GEOM'):
				# for now we can't change the geom during pausing
				if self._player.playing or self._player.pausing:
					return
				
			self._armed_node = None
			if self._is_shown:
				reshow = 0
				for key, (val, default) in self._curvals.items():
					if key == 'winsize':
						curval = self.cssResolver.getPxGeom(self._attrdict._cssId)
					else:
						curval = self._attrdict.get(key, default)
					if curval != val:
						reshow = 1
						break
				if self.mustreshow() or reshow:
					self.need_reshow = 1
		except:
			# may be already destroyed
			pass

	def transaction(self, type):
		return 1

	def rollback(self):
		pass

	def mustreshow(self):
		# Return true if channel needs to be redisplayed after
		# a commit
		return 0

	# return true is the channel is showing
	def isShown(self):
		return self._is_shown

	# return the playing node
	# None is not in playing state
	def getPlayingNode(self):
		if self._playstate == PLAYING:
			return self._played_node
		return None
	
	def kill(self):
		if hasattr(self, '_player'):
			self.destroy()

	def may_show(self):
		# Indicate to the higher level whether this channel is
		# visible and may be shown.
		return self._attrdict.get('visible', 1)

	def check_visible(self):
		if self.may_show():
			self.show()
		else:
			self.hide()

	def flip_visible(self):
		self.set_visible(not self.may_show())

	def set_visible(self, visible):
		self._attrdict['visible'] = visible
		if visible:
			self.show()
		else:
			self.save_geometry()
			self.hide()

	def register_exporter(self, exporter):
		self._exporter = exporter

	def unregister_exporter(self, exporter):
		if self._exporter==exporter:
			self._exporter = None

	def replaynode(self):
		self.wait_for_arm()
		# Now we should replay the node that was played when
		# we were hidden.  This means that we must arm the
		# node first.  This in turn means that we must save
		# the information about the node that is armed
		# currently.
		armstate = self._armstate
		armed_node = self._armed_node
		if self._playstate in (PLAYING, PLAYED):
			node = self._played_node
			self._armstate = AIDLE
			save_syncarm = self.syncarm
			self.syncarm = 1
			self.arm(node)
			playstate = self._playstate
			if playstate in (PLAYING, PLAYED):
				# if still in one of these states...
				self._playstate = PIDLE
				save_syncplay = self.syncplay
				self.syncplay = 1
				save_nopop = self.nopop
				self.nopop = 1
				self._played_node = None
				self.play(node, None)
				self.syncplay = save_syncplay
				self.nopop = save_nopop
				self._playstate = playstate
			self.syncarm = save_syncarm
			self._armstate = AIDLE
		if armstate == ARMED:
			self._armstate = AIDLE
			save_syncarm = self.syncarm
			self.syncarm = 1
			self.arm(armed_node)
			self.syncarm = save_syncarm
		if self._armstate != armstate:
			# maybe we should do something, but what?
			raise error, 'don\'t know if this can happen'

	def show(self, force = 0):
		if debug: print 'Channel.show'+`self,force`
			
		if self.need_reshow:
			self.need_reshow = 0
			self.hide()

		# If we were still waiting for a hide we cancel that
		self._hide_pending = 0

		# force equal 1 is used only in internal. By default the channel is shown
		# only when showBackground attribute equal to always
		if self._visible and not force:
			if self._get_parent_channel() != None:
				# for now, we have to create a media channel only when it's active
				# it's important for sub-region positioning as long as that
				# the dynamic resizing won't be possible on all plateform
				if not self.is_layout_channel:
					return

				if self._attrdict.get('showBackground') == 'whenActive':
					return
			else:
				# case for the top window
				if self._attrdict.has_key('open'):
					if self._attrdict['open'] == 'whenActive':
						return

		# Indicate that the channel must enter the SHOWN state.
		self._want_shown = 1
		if self._is_shown:
			# already shown, so do nothing
			return
		# Deal with being a subchannel.
		for chan in channels:
			# Remove us from all subchannel lists.
			if self in chan._subchannels:
				chan._subchannels.remove(self)
		self.pchan = pchan = self._get_parent_channel(creating=1)
		if pchan:
			# Finally, check that the base window is being shown.
			pchan._subchannels.append(self)
			if not pchan._is_shown:
				# parent channel not shown, so cannot show self
				return
		# register that a channel wants to be shown
		self._player.before_chan_show(self)
		self._is_shown = None
		is_shown = self.do_show(pchan)
		if is_shown is not None:
			self._is_shown = is_shown
		if not self._is_shown:
			if self._is_shown == 0:
				self._player.after_chan_show(self)
			return

		self.after_show(force)

	def _get_parent_channel(self, creating=0):
		# Return the parent (basewindow) channel, if it exists
		# First, check that there is a base_window attribute
		# and that it isn't "undefined".
		pname = self._attrdict.get('base_window', 'undefined')
		self._curvals['base_window'] = (pname, 'undefined')
		if pname == self._name:
			pname = 'undefined'
		pchan = None
		if pname != 'undefined':
			# Next, check that the base window channel exists.
			try:
				pchan = self._player.ChannelWinDict[pname]
			except (AttributeError, KeyError):
				pchan = None
				windowinterface.showmessage(
					'Base window '+`pname`+' for '+
					`self._name`+' not found',
					mtype = 'error')
			if pchan:
				if creating and self in pchan._subchannels:
					windowinterface.showmessage(
						'Channel '+`self._name`+' is part of'+
						' a base-window loop',
						mtype = 'error')
					pchan = None
					pname = 'undefined'
##				Can't do this: during close the info is gone.
##				elif not creating and not self in pchan._subchannels:
##					raise 'Parent window does not contain child', (self, pchan)
		return pchan

	def after_show(self, force=0):
		# Since the calls to arm() and play() lied to the
		# scheduler when the channel was hidden, we must do a
		# few things so that the real state of things is once
		# again in accordance with what the scheduler thinks.
		# First wait for any outstanding arms so that the
		# armedstate is either AIDLE or ARMED but not ARMING.
		self.replaynode()
		# now that we are visible, see if any other channels
		# can become visible
		for chan in self._subchannels[:]:
			if chan._want_shown:
				chan.show(force)
		self._player.after_chan_show(self)

	def hide(self, force=1):
		# Indicate that the channel must enter the HIDDEN state.
		if debug: print 'Channel.hide('+`self`+')'

		self.need_reshow = 0
		# force equal 0 is used only in internal. By default the channel is hide
		# only when showBackground attribute equal whenActive
		if not force:
			if self._get_parent_channel() is not None:
				if self._attrdict.get('showBackground', 'always') == 'always':
					return
			else:
				# case for the top window
				if self._attrdict.has_key('close'):
					if self._attrdict['close'] == 'onRequest':
						return

		self._want_shown = 0
		self._highlighted = None
		self.cancel_modeless_resize()
		self.sensitive()
		if not self._is_shown:
			return
		self._is_shown = 0
		subchannels = self._subchannels
		self._subchannels = []
		for chan in subchannels:
			want_shown = chan._want_shown
			chan.hide()
			chan._want_shown = want_shown
		self.do_hide()
		del self.pchan
		self._curvals = {}
		for chan in channels:
			if self in chan._subchannels:
				chan._subchannels.remove(self)
		self._subchannels = subchannels
		if self._armstate == ARMING:
			self.arm_1()

	def highlight(self, color = (255, 0, 0)):
		# highlight the channel instance (dummy for channels
		# without windows)
		pass

	def unhighlight(self):
		# stop highlighting the channel instance
		pass

	def modeless_resize_window(self):
		# Set a channel in modeless resize mode
		pass

	def cancel_modeless_resize(self):
		pass

	def sensitive(self, callback = None):
		pass

	def popup(self, poptop = 0):
		# raise the window to the front (dummy for channels
		# without windows)
		pass

	def check_popup(self):
		# raise the window unless disabled (dummy)
		pass

	def popdown(self):
		# lower the window to the back (dummy for channels
		# without windows)
		pass

	def save_geometry(self):
		pass

	def getaltvalue(self, node):
		# Return 1 if this node is playable, 0 otherwise
		return 1

	#
	# Methods used internally and by superclasses.
	#
	def is_showing(self):
		# Indicate whether the channel is being shown.
		return self._want_shown

	def do_show(self, pchan):
		# Actually do the work to show the channel.  Return 1
		# if successful, 0 otherwise.
		# This method is only called when the channel is
		# hidden.
		return 1		# indicate success

	def do_hide(self):
		# Actulally do the work to hide the channel.
		# This method is only called when the channel is being
		# shown.
		pass

	def arm_0(self, node):
		# This does the initial part of arming a node.  This
		# method should be called by superclasses when they
		# start arming.
		if debug: print 'Channel.arm_0('+`self`+','+`node`+')'
		if self._armstate != AIDLE:
			raise error, 'arm not idle'
		if not self._armcontext:
			raise error, 'no context to arm in'
		self._armstate = ARMING
		if self._armed_node is node:
			# Same as last time, apparently
			return 1
		self._armed_node = node
		self._armed_anchors = []
		self._armed_anchor2button = {}
		duration = node.GetAttrDef('duration', None)
		self.armed_duration = duration
			
		return 0

	def add_arc(self, node, arc):
		pass

	def arm_1(self):
		# This does the final part of arming a node.  This
		# method should be called by superclasses when they
		# are finished with arming.
		if debug: print 'Channel.arm_1('+`self`+')'
		if self._armstate != ARMING:
			raise error, 'not arming'
		self._armstate = ARMED
		# Only tell scheduler if not synchronous.
		if not self.syncarm:
			self._armcontext.arm_done(self._armed_node)

	def armdone(self):
		# This method should be called by superclasses to
		# indicate that the armed information is not needed
		# anymore and that a new arm may be done.
		if debug: print 'Channel.armdone('+`self`+')'
		if self._armstate != ARMED:
			raise error, 'not arming'
		self._armstate = AIDLE
		# Only tell scheduler if not synchronous.
		if not self.syncarm:
			self._playcontext.arm_ready(self)
		# self._armed_node = None # XXXX Removed for arm-caching

	def wait_for_arm(self):
		# Wait until the arm state is either AIDLE or ARMED so
		# that we don't get any asynchronous events that tell
		# us that arming finished.
		while self._armstate not in (AIDLE, ARMED):
			if not self._player.toplevel.waitevent():
				return

	def anchor_triggered(self, node, arg = None):
		return self._playcontext.anchorfired(node, arg)

	def play_0(self, node, curtime):
	
		# This does the initial part of playing a node.
		# Superclasses should call this method when they are
		# starting to play a node.
		if debug: print 'Channel.play_0('+`self`+','+`node`+')'
		if self._played_node is not None:
##			print 'stopping playing node first',`self._played_node`
			self.stopplay(self._played_node, curtime)
		if self._armed_node is not node:
			self.arm(node)
			if not self._armcontext:
				# aborted
				return
		if self._playstate != PIDLE:
			raise error, 'play not idle on '+self._name
		if self._armstate != ARMED:
			self.arm(node)
		self._playcontext = self._armcontext
		self._playstate = PLAYING
		self._played_node = node
		self.playBox = self.armBox
		self._anchors = {}
		self._played_anchors = self._armed_anchors[:]
		self._played_anchor2button.update(self._armed_anchor2button)
		for (button, a) in self._played_anchors:
			self._anchors[button] = self.onclick, (a,)
			if button._sensitive:
				tabindex = MMAttrdefs.getattr(a, 'tabindex') or 0x10000
				if tabindex > 0:
					self._player.addtabindex(tabindex, a, self)
		self._qid = None

	def onclick(self, node):
		if debug: print 'Channel.onclick'+`self,node`
		if not self._scheduler.playing:
			# not currently interested in events
			return

		if self._player.context.hyperlinks.findsrclinks(node):
			return self.anchor_triggered(node)

		# check if anchor is source of event
		for arc in node.sched_children:
			if arc.event == ACTIVATEEVENT and \
			   arc.refnode() is node:
				self._playcontext.sched_arcs(node, self._scheduler.timefunc(), ACTIVATEEVENT, external = 1)

	def event(self, event):
		if debug: print 'Channel.event'+`self,event`
		if not self._scheduler.playing:
			# not currently interested in events
			return
		node = self._player.root.GetSchedRoot()
		sctx = self._scheduler.sctx_list[0] # XXX HACK!
		sctx.sched_arcs(node, self._scheduler.timefunc(), event, external = 1)

	def play_1(self, curtime):
		# This does the final part of playing a node.  This
		# should only be called by superclasses when they
		# don't have an intrinsic duration.  Otherwise they
		# should just call armdone to indicate that the armed
		# information is not needed anymore, and call playdone
		# when they are finished playing the node.
		if debug: print 'Channel.play_1('+`self`+')'
		# armdone must come before playdone, since playdone
		# may trigger an autofiring anchor that terminates
		# this node
		self.armdone()
		if not self.syncplay:
##			node = self._played_node
##			start_time = node.get_start_time()
			if not self.armed_duration:
				self.playdone(0, curtime)
##			elif self.armed_duration > 0:
##				self._qid = self._scheduler.enterabs(
##					start_time+self.armed_duration, 0,
##					self.playdone, (0, start_time+self.armed_duration))
		else:
			self.playdone(0, curtime)
			
	def playdone(self, outside_induced, curtime):
		# This method should be called by a superclass
		# (possibly through play_1) to indicate that the node
		# has finished playing.
		if debug: print 'Channel.playdone('+`self`+')'
		if self._playstate != PLAYING:
			if not outside_induced and not self._qid:
				# timer callback couldn't be cancelled
				return
			raise error, 'not playing'
		self._qid = None
		# If this node has a pausing anchor, don't call the
		# callback just yet but wait till the anchor is hit.
		if not self.syncplay:
			self._playcontext.play_done(self._played_node, curtime, curtime)
		self._playstate = PLAYED

	def freeze(self, node, curtime):
		# Called by the Scheduler to stop playing and start freezing.
		# The node is passed for consistency checking.
		if debug: print 'Channel.freeze'+`self,node`
		if node.GetType() == 'anchor':
			return
		if self._played_node is not node or self._playstate != PLAYING:
			return
		self.playstop(curtime)

	def playstop(self, curtime):
		# Internal method to stop playing.
		if debug: print 'Channel.playstop('+`self`+')'
		if self._playstate != PLAYING:
			raise error, 'playstop called when not playing'
		# there may be a done event scheduled; cancel it
		if self._qid:
			try:
				self._scheduler.cancel(self._qid)
			except RuntimeError:
				# XXX
				# It may be that the done
				# event was removed from the
				# queue and is now somewhere
				# in the internals of the
				# scheduler where we can't
				# remove it.  We ought to do
				# something about that.
				pass
			self._qid = None
		self.playdone(1, curtime)

	def do_arm(self, node, same=0):
		# Do the actual arm.
		# Expect to override this method.
		# Return 1 if arm is finished when this returns,
		# otherwise return 0.  In the latter case, a callback
		# should be done later.
		# If self.syncarm is set, the arm should be finished
		# when do_arm() returns.
		return 1

	def armstop(self):
		# Internal method to stop arming.
		if self._armstate != ARMING:
			raise error, 'armstop called when not arming'
		self.arm_1()

	def do_play(self, node, curtime):
		# Actually play the node.
		pass

	#
	# The following methods can be called by the animation module.
	#
	def updateattr(self, node, name, value):
		# Updates the display value of the attribute
		if self._playstate != PIDLE:
			self.do_updateattr(node, name, value)

	def do_updateattr(self, node, name, value):
		# Override this method to enable animations.
		pass

	def canupdateattr(self, node, name):
		# This is for efficiency
		# Override this method to enable animations.
		# Return true for supported attributes
		return 0

	#
	# The following methods can be called by the scheduler.
	#
	def arm(self, node):
		# Arm the specified node.  This will change the arming
		# state from AIDLE to ARMING.  When the arm is
		# finished, the state changes to ARMED.
		# Subclasses should define a method do_arm to do the
		# actual arming.
		# Do_arm() is called to do the actual arming.  If it
		# returns 0, we should not call arm_1() because that
		# will happen later.
		same = self.arm_0(node)
		if not self._armcontext:
			# The player has aborted
			return
		if self._is_shown and node.ShouldPlay():
			if not self.do_arm(node, same):
				return
			self._prepareAnchors(node)

		if not self._armcontext:
			# The player has aborted
			return

		self.arm_1()

	# this method have to be override by visible channels
	# Warning: it can't be called by the arm_1 because arm_1 may called from others locations
	def _prepareAnchors(self, node):
		pass

	# Called by the scheduler when it is not sure whether this
	# node is armed or not.
	def optional_arm(self, node):
		if self._armed_node is node and self._armstate == ARMED:
			if not self.syncarm:
				self._armcontext.arm_done(node)
			return
		self.arm(node)

	def seekanchor(self, node, args):
		# Called before arm on the node. Signifies that the node
		# is played because a hyperjump to the specified anchor
		# was executed. The channels can override this method, for
		# instance to highlight the anchor. If the source anchor
		# had arguments (as in HTML forms) these args are passed to
		# the destination anchor here.
		self.seekargs = (node, args)

	def play_anchor(self, anchor, curtime):
		if debug: print 'Channel.play_anchor',self,anchor,curtime
		# XXX should this come before or after the actuate="onLoad" check?
		tabindex = MMAttrdefs.getattr(anchor, 'tabindex') or 0x10000
		actuate = MMAttrdefs.getattr(anchor, 'actuate')
		if actuate == 'onLoad':
			self.onclick(anchor)
			return

		b = self._played_anchor2button.get(anchor)
		if b is None:
			return

		# make button sensitive if there is a listener
		for arc in anchor.sched_children:
			if arc.event == ACTIVATEEVENT:
				b.setsensitive(1)
				if tabindex > 0:
					self._player.addtabindex(tabindex, anchor, self)
				return

		ctx = self._player.context
		root = anchor.GetRoot()
		for link in ctx.hyperlinks.findsrclinks(anchor):
			if ctx.isgoodlink(link, root):
				b.setsensitive(1)
				if tabindex > 0:
					self._player.addtabindex(tabindex, anchor, self)
				return

	def stop_anchor(self, anchor, curtime):
		if debug: print 'Channel.stop_anchor',self,anchor,curtime
		actuate = MMAttrdefs.getattr(anchor, 'actuate')
		if actuate == 'onLoad':
			return

		b = self._played_anchor2button.get(anchor)
		if b is not None:
			b.setsensitive(0)

	def anchor_highlight(self, anchor, highlight):
		b = self._played_anchor2button.get(anchor)
		if b is None:
			return
		if highlight:
			b.highlight()
		else:
			b.unhighlight()

	def play(self, node, curtime):
		# Play the node that was last armed.  This will change
		# the playing state from PIDLE to PLAYING.  This can
		# only be called when the arming state is ARMED.
		# When the playing is done, the state changes to
		# PLAYED.
		# This is called by the scheduler.  When playing is done,
		# callback should be called with the given arg.
		# Node is only passed to do consistency checking.
		# If a channel derives the duration of nodes from the
		# data instead of from node attributes, the channel
		# should override this method.  The channel should
		# then call play_0 at the start of its play method and
		# call playdone when playing is finished.  It should call
		# armdone when the armed information is not needed
		# anymore.
		if debug: print 'Channel.play('+`self`+','+`node`+')'
		if node.GetType() == 'anchor':
			self.play_anchor(node, curtime)
			return
		self.play_0(node, curtime)
		if not self._armcontext:
			return
		if self._is_shown and node.ShouldPlay():
			# XXXX This depends on node playability not changing,
			# otherwise we may have to re-arm.
			self.do_play(node, curtime)
		self.play_1(curtime)

	def stopplay(self, node, curtime):
		# Indicate that the channel can revert from the
		# PLAYING or PLAYED state to PIDLE.
		# Node is only passed to do consistency checking.
		if debug: print 'Channel.stopplay('+`self`+','+`node`+')'
		tabindex = MMAttrdefs.getattr(node, 'tabindex') or 0x10000
		if tabindex > 0:
			self._player.deltabindex(tabindex, node, self)
		if node.GetType() == 'anchor':
			self.stop_anchor(node, curtime)
			return
		if node and self._played_node is not node:
##			print 'node was not the playing node '+`self,node,self._played_node`
			return
		b = self._played_anchor2button.get(node)
		if b is not None:
			b.setsensitive(0)
		if self._playstate == PLAYING:
			self.playstop(curtime)
		if self._playstate != PLAYED:
			raise error, 'not played'
		self._playstate = PIDLE
		# delete any anchors that may still exist
		self._anchors = {}
		self._played_anchors = []
		self._played_node = None

	def stoparm(self):
		# Indicate that the channel can revert from the
		# ARMING or ARMED state to AIDLE.
		if debug: print 'Channel.stoparm('+`self`+')'
		if self._armstate == ARMING:
			self.armstop()
			self._armed_node = None
		if self._armstate != ARMED:
			raise error, 'not armed'
		self._armstate = AIDLE
		# self._armed_node = None # XXXX Removed for arm-caching
		# self._armed_anchors = []

	def startcontext(self, ctx):
		# Called by the scheduler to start a new context.  The
		# following arm is done in the new context.
		if debug: print 'Channel.startcontext'+`(self, ctx)`
		if self._armcontext and not self._playcontext:
			# New startcontext without having played in
			# the old context.  Save the old context for
			# when we get a stopcontext for it.
			self._playcontext = self._armcontext
		if self._armcontext and self._armcontext is not self._playcontext:
			# When we get a startcontext while there are
			# already two contexts active, raise an error.
			# The test is sufficient, since this comes
			# after the previous if statement.
			raise error, 'startcontext without prior stopcontext'
		if self._armstate != AIDLE:
			# This can only happen if the arm and play
			# contexts were the same.  Just abort arming.
			self.stoparm()
		self._armcontext = ctx

	def stopcontext(self, ctx, curtime):
		# Called by the scheduler to force the channel to the
		# complete idle state.
		if debug: print 'Channel.stopcontext'+`(self, ctx)`
		if ctx is not self._playcontext and \
		   ctx is not self._armcontext:
			raise error, 'stopcontext with unknown context'
		if self._playcontext is ctx:
			if self._playstate in (PLAYING, PLAYED):
				for c in self._played_node.GetSchedChildren():
					self.stopplay(c, curtime)
				self.stopplay(self._played_node, curtime)
			self._playcontext = None
		if self._armcontext is ctx:
			if self._armstate in (ARMING, ARMED):
				self.stoparm()
			self._armcontext = None

	def setpaused(self, paused, timestamp):
		if debug: print 'Channel.setpaused('+`self`+','+`paused`+')'
		if paused and self._qid:
			try:
				self._scheduler.cancel(self._qid)
			except RuntimeError:
				# XXX
				# It may be that the done
				# event was removed from the
				# queue and is now somewhere
				# in the internals of the
				# scheduler where we can't
				# remove it.  We ought to do
				# something about that.
				pass
			self._qid = None
		self._paused = paused

	def pause(self, node, action, timestamp):
		tabindex = MMAttrdefs.getattr(node, 'tabindex') or 0x10000
		if tabindex > 0:
			self._player.deltabindex(tabindex, node, self)
		if node.GetType() == 'anchor':
			return
		if node is self._played_node:
			self.setpaused(action, timestamp)

	def resume(self, node, timestamp):
		tabindex = MMAttrdefs.getattr(node, 'tabindex') or 0x10000
		if tabindex > 0:
			for b, a in self._played_anchor2button.items():
				if a is node and b._sensitive:
					self._player.addtabindex(tabindex, node, self)
		if node.GetType() == 'anchor':
			return
		if node is self._played_node:
			self.setpaused(None, timestamp)

	def uipaused(self, wantpause):
		if wantpause:
			if not self._paused:
				self.setpaused('uipause', None)
		else:
			if self._paused == 'uipause':
				self.setpaused(None, None)

	#
	# Methods used by derived classes.
	#
	def setanchor(self, button, a, arming = 1):
		# Define an anchor.  This method should be called by
		# superclasses to define an anchor while arming.
		if arming:
			self._armed_anchors.append((button, a))
			self._armed_anchor2button[a] = button
		else:
			self._played_anchors.append((button, a))
			self._played_anchor2button[a] = button

	def getfileurl(self, node, animated=0):
		url = MMAttrdefs.getattr(node, 'file', animated)
		if not url:
			return ''
		return node.context.findurl(url)

	def getstring(self, node):
		if node.type == 'imm':
			self.armed_url = ''
			return string.join(node.GetValues(), '\n')
		elif node.type == 'ext':
			url = self.getfileurl(node)
			if not url:
				raise error, 'No URL set on node'
			self.armed_url = url
			utype, host, path, params, query, tag = urlparse.urlparse(url)
			url = urlparse.urlunparse((utype, host, path, params, query, ''))
			try:
				# use urlretrieve so that data gets cached
				fn, hdr = MMurl.urlretrieve(url)
				if hdr.has_key('Content-Location'):
					url = hdr['Content-Location']
				self.armed_url = url
				if tag:
					self.armed_url = self.armed_url+'#'+tag
				fp = open(fn, 'r')
				text = fp.read()
				fp.close()
			except IOError:
				import sys
				raise error, 'Cannot open %s: %s, %s'%(url, sys.exc_type, sys.exc_value)
			#
			# Convert dos/mac newlines to ours
			#
			text = string.join(string.split(text, '\r\n'), '\n')
			text = string.join(string.split(text, '\r'), '\n')
			#
			# For the mac convert ISO encoding to Mac encoding.
			# This *ONLY* works for Greek (and, hence, is a hack)
			#
			if os.name == 'mac':
				import greekconv
				text = string.translate(text, greekconv.iso_8859_7_to_mac)

			if text[-1:] == '\n':
				text = text[:-1]
			return text
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`

	def getduration(self, node):
		return MMAttrdefs.getattr(node, 'duration')

	def getbgcolor(self, node, animated=0):
		return MMAttrdefs.getattr(node, 'bgcolor', animated)

	def getfgcolor(self, node, animated=0):
##		return MMAttrdefs.getattr(node, 'fgcolor', animated)
		fgcolor = node.GetAttrDef('fgcolor', None)
		if fgcolor is not None:
			return fgcolor
		r,g,b = self.getbgcolor(node, animated)
		if MMAttrdefs.getattr(node, 'transparent', animated) or r*r + g*g + b*b >= 3*128*128:
			return 0,0,0
		else:
			return 255,255,255

	def gethicolor(self, node, animated=0):
		# The hicolor property doesn't exist anymore, but the HTML channels still use
		# it to set hyperlink color. For that reason this method still exists, and returns
		# red.
		return (255, 0, 0)

	def getloop(self, node):
		return MMAttrdefs.getattr(node, 'loop')

	def gettransition(self, node, which, animated=0):
		import Transitions
		trclasses = MMAttrdefs.getattr(node, which, animated)
		if not trclasses:
			return None
		transitions = node.context.transitions
		for trclass in trclasses:
			if transitions.has_key(trclass):
				if Transitions.IsImplemented(transitions[trclass]):
					return transitions[trclass]
##			else:
##				# Shouldn't happen, I think.
##				self.errormsg(node, 'Unknown transition name: %s\n'%trclass)
		return None

	def getclipval(self, node, attr, units):
		try:
			return node.GetClip(attr, units)
		except ValueError, msg:
			self.errormsg(node, str(msg))
			return 0

	def getclipbegin(self, node, units):
		return self.getclipval(node, 'clipbegin', units)

	def getclipend(self, node, units):
		return self.getclipval(node, 'clipend', units)

	def defanchor(self, node, anchor, cb):
		# This method is called when the user defines a new anchor. It
		# may be overridden by derived classes.
		windowinterface.showmessage('Channel '+self._name+
			  ' does not support\nediting of anchors (yet)',
					    mtype = 'warning')
		apply(cb, (anchor,))

	__stopping = 0
	def errormsg(self, node, msg):
		if self.__stopping:
			# don't put up second error message dialog if we're
			# already stopping
			return
		nmsg = ''
		if node:
			node.set_infoicon('error', msg)
			name = MMAttrdefs.getattr(node, 'name')
			if name:
				nmsg = 'Media item ' + name + ': \n'
			# And give the node focus.
			if hasattr(self, 'editmgr'):
				self.editmgr.setglobalfocus([node])
		if hasattr(self, 'window'):
			pwindow = self.window
		else:
			pwindow = None
		windowinterface.showmessage(
			'%s%s\n\nContinue playing?' %
				(nmsg, msg),
			mtype = 'question', parent = pwindow,
			cancelCallback = (self.__delaystop, ()))

	def __delaystop(self):
		Channel.__stopping = 1
		self._player.pause(1)
		windowinterface.settimer(0.001, (self.__stop, ()))

	def __stop(self):
		self._player.cc_stop()
		Channel.__stopping = 0

### dictionary with channels that have windows
##ChannelWinDict = {}

_button = None				# the currently pressed button

class ChannelWindow(Channel):
	chan_attrs = Channel.chan_attrs + ['base_winoff', 'z']
	node_attrs = Channel.node_attrs[:]
	node_attrs.append('cssbgcolor')
	chan_attrs.append('cssbgcolor')
	if 1: # XXX Should depend on SMIL-Boston. Can I test for that here??
		node_attrs.append('transIn')
		node_attrs.append('transOut')
	_visible = TRUE

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		if not hasattr(self._player, 'ChannelWinDict'):
			self._player.ChannelWinDict = {}
		self._player.ChannelWinDict[self._name] = self
		self.window = None
		self.armed_display = self.played_display = None
		self.update_display = None
		self.want_default_colormap = 0
		self.__callback = None
		self.__out_trans_qid = None
		self.__out_trans = None
		self._active_multiregion_transition = None
		self._wingeom = None
		self._winabsgeom = None
		self._mediaabsgeom = None
		self._mediageom = None
		self.__transparent = 1
		self.__z = -1
		self.__bgcolor = None
		self.__viewportChan = None

		self.commandlist = [
			CLOSE_WINDOW(callback = (ui.channel_callback, (self._name,))),
			PLAY(callback = (ui.play_callback, ())),
			PAUSE(callback = (ui.pause_callback, ())),
			STOP(callback = (ui.stop_callback, ())),
			MAGIC_PLAY(callback = (ui.magic_play, ())),
			CHANNELS(callback = ui.channel_callback),
			]
		if __debug__:
			self.commandlist.append(
				SCHEDDUMP(callback = (ui.scheduler.dump, ())))

	def destroy(self):
		del self._player.ChannelWinDict[self._name]
		Channel.destroy(self)
		self.window = None
		del self.armed_display
		del self.played_display
		del self.update_display

	def highlight(self, color = (255,0,0)):
		if self._is_shown and self.window:
			self._highlighted = color
			self.window.pop(poptop=0)
			self.window.showwindow(color = color)

	def unhighlight(self):
		if self._is_shown and self.window:
			self._highlighted = None
			self.cancel_modeless_resize()
			self.window.dontshowwindow()

	def sensitive(self, callback = None):
		self.__callback = None
		if self._is_shown and self.window:
			self.__callback = callback

	def popup(self, poptop = 0):
		if self._is_shown and self.window:
			self.window.pop(poptop = poptop)

	def check_popup(self, poptop = 0):
		if self.nopop or not self._is_shown or not self.window:
			return
		if not self._attrdict.get('popup', 1):
			return
		self.window.pop(poptop = poptop)

	def popdown(self):
		if self._is_shown and self.window:
			self.window.push()

##	def focuscall(self):
##		if self._playstate in (PLAYING, PLAYED):
##			node = self._played_node
##			top = self._player.toplevel
##			if top.hierarchyview is not None:
##				top.hierarchyview.globalsetfocus(node)
##		else:
##			windowinterface.showmessage('No node currently playing on %s'%self._name, mtype = 'warning', grab = 1, parent = self.window)

##	def save_geometry(self):
##		if self._is_shown and self.window:
##			units = self._attrdict.get('units',
##						   windowinterface.UNIT_MM)
##			x, y, w, h = self.window.getgeometry(units = units)
##			self._attrdict['winpos'] = x, y
##			self._attrdict['winsize'] = w, h

	def mousepress(self, arg, window, event, value):
		# arg is a tuple of (x, y, buttons, params)
		# x and y are expressed in percent values (relative to the channel geometry)
		# buttons is a list of button. A button is a sensitive area associated to each anchor
		# it can be a rectangle, circle or a polygon (see displaylist._Button class)
		global _button
		# a mouse button was pressed
		_button = None
		if self.__callback is not None:
			apply(apply, self.__callback)
			return
		buttons = value[2]
		if buttons:
			button = buttons[0]
			_button = button
##		else:
##			if self.__transparent:
##				raise windowinterface.Continue		
##			if hasattr(self._player, 'editmgr'):
##				self.highlight()

	def mouserelease(self, arg, window, event, value):
		# arg is a tuple of (x, y, buttons, params)
		# x and y are expressed in percent values (relative to the channel geometry)
		# buttons is a list of button. A button is a sensitive area associated to each anchor
		# it can be a rectangle, circle or a polygon (see displaylist._Button class)
		global _button
##		if hasattr(self._player, 'editmgr'):
##			self.unhighlight()
		buttons = value[2]
		if buttons and self._paused not in ('hide', 'disable'):
			button = buttons[0]
			if _button is button:
				try:
					func, arg = self._anchors[button]
				except KeyError:
					pass
				else:
					self._player.toplevel.setwaiting()
					apply(func, arg) # may close channel
##		elif len(buttons) == 0:
##			if self.__transparent:
##				raise windowinterface.Continue		
		_button = None

	# set the display size of media after arming according to the size of media, fit attribute, ...
	# this method is called by descendant
	def setArmBox(self, armBox):
		self.armBox = armBox

	# return the display size of media after arming according to the size of media, fit attribute, ...
	def getArmBox(self):
		return self.armBox

	def getPlayBox(self):
		return self.playBox

	def create_window(self, pchan, pgeom, units = None):
##		menu = []
		if pchan:
##			if hasattr(self._player, 'editmgr'):
##				menu.append(('', 'raise', (self.popup, ())))
##				menu.append(('', 'lower', (self.popdown, ())))
##				menu.append(None)
##				menu.append(('', 'select in timeline view',
##					     (self.focuscall, ())))
##				menu.append(None)
##				menu.append(('', 'highlight',
##					     (self.highlight, ())))
##				menu.append(('', 'unhighlight',
##					     (self.unhighlight, ())))

			self._curvals['transparent'] = (self.__transparent, 0)

#			print self.__transparent
#			print self.__bgcolor
			# determinate the z-index
			if self.want_default_colormap:
				self.window = pchan.window.newcmwindow(pgeom,
						transparent = self.__transparent,
						z = self.__z,
						units = units)
			else:
				self.window = pchan.window.newwindow(pgeom,
						transparent = self.__transparent,
						z = self.__z,
						units = units)

			# fix the background color
			if self.__transparent == 0 and self.__bgcolor != None:
				self.window.bgcolor(self.__bgcolor)
		else:
			# case not possible in internal channel
			# only possible in LayoutChannel (look at LayoutChannel.py)
			pass

		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.Mouse0Press, self.mousepress, None)
		self.window.register(WMEVENTS.Mouse0Release, self.mouserelease,
				     None)
		self.window.register(WMEVENTS.KeyboardInput, self.keyinput, None)
		if self._exporter:
			self.register_exporter(self._exporter)
##		if menu:
##			self.window.create_menu(menu, title = self._name)

	def register_exporter(self, exporter):
		self._exporter = exporter
		if self.window:
			self.window.register(WMEVENTS.WindowContentChanged, exporter.changed, 
				self.find_layout_channel())

	def unregister_exporter(self, exporter):
		self._exporter = None
		if self.window:
			self.window.unregister(WMEVENTS.WindowContentChanged)
				
	def keyinput(self, arg, window, event, value):
		if value == '\t':
			self._player.tab()
		elif value == '\r':
			self._player.activate()
		elif value:
			self.event((None, 'accesskey', value))

	def resize_window(self, pchan):
		if not self._player.editmgr.transaction():
			return
		self._player.toplevel.setwaiting()
		self.unhighlight()
		# we now know for sure we're not playing
		pchan.window.create_box(
			'Resize window for channel ' + self._name,
			self._resize_callback,
			self._attrdict['base_winoff'],
			units = self._attrdict.get('units', windowinterface.UNIT_SCREEN))

	def _resize_callback(self, *box):
		if box:
			self._attrdict['base_winoff'] = box
			self.hide()
			self.show()
			self._player.editmgr.commit()
		else:
			self._player.editmgr.rollback()
		self.highlight()

	def modeless_resize_window(self):
		pchan = self.pchan
		if not pchan:
			return
##		self._player.toplevel.setwaiting()
##		self.unhighlight()
		self._in_modeless_resize = 1
		# we now know for sure we're not playing
		pchan.window.create_box(
			None,
			self._modeless_resize_callback,
			self._attrdict['base_winoff'],
			units = self._attrdict.get('units', windowinterface.UNIT_SCREEN),
			modeless=1)

	def cancel_modeless_resize(self):
		if not self._in_modeless_resize:
			return
		pchan = self.pchan
		if not pchan or not pchan.window:
			return
		pchan.window.cancel_create_box()

	def _modeless_resize_callback(self, *box):
		self._in_modeless_resize = 0
		if box:
			if not self._player.editmgr.transaction():
				return
			self._attrdict['base_winoff'] = box
			self.hide()
			self.show()
			self._player.editmgr.commit()
##		self.highlight()

	def do_show(self, pchan):
		if debug: print 'ChannelWindow.do_show('+`self`+')'
			
		if self._wingeom == None:
			# shouldn't happen
			return 0
		
		self._curvals['base_winoff'] = self._wingeom, None

		# the window size is determinate from arm method. self._wingeom is all the time 
		# expressed in pixel value.
		units = windowinterface.UNIT_PXL
		self.create_window(pchan, self._wingeom, units)

		return 1

	# return the viewport in which this channel is playing
	def getViewportChannel(self):
		if self.__viewportChan == None:
			parent = self._get_parent_channel()
			if parent != None:
				self.__viewportChan = parent.getViewportChannel()
			else:
				# it the root channel
				self.__viewportChan = self
				
		return self.__viewportChan	
				
	# Updates channels to visible if according to the showBackground/open and close attributes.
	# Also: derterminate the background color before to show the channel
	# for now, we set the window bg color equal to the displylist bg color in to order
	# to avoid "flashing" if window is not transparent
	def updateToActiveState(self, node):

		# determine the transparent and background color attributes
		transparent = MMAttrdefs.getattr(node, 'transparent')
		if transparent:
			bgcolor = None
		else:
			bgcolor = self.getbgcolor(node)

		self.__transparent = transparent
		self.__bgcolor = bgcolor

		# get the local z-index value from the node
		self.__z = node.GetAttrDef('z', -1)
		
		pchan = self._get_parent_channel()
		pchan.childToActiveState()

		pchan = self._get_parent_channel()

		self.updateGeom(node)
		# updateGeom can take a while, maybe we were stopped...
		if not self._armcontext:
			return
		
		# force show of channel.
		self.show(1)			
			
		self.getViewportChannel().addActiveVisibleChannel(self, node)


	# Updates channels to unvisible if according to the showBackground/open and close attributes
	def updateToInactiveState(self):

		# force hide the channel.
		self.hide(1)

		self.__transparent = 1
		self.__bgcolor = None

		pchan = self._get_parent_channel()
		pchan.childToInactiveState()
		self.getViewportChannel().removeActiveVisibleChannel(self)

##	def _box_callback(self, *pgeom):
##		if not pgeom:
##			# subwindow was not drawn, so hide it
##			self._is_shown = 0
##			self._want_shown = 0
##			return
##		pname = self._attrdict['base_window']
##		pchan = self._player.ChannelWinDict[pname]
##		self._attrdict['base_winoff'] = pgeom
##		self.create_window(pchan, pgeom,
##				   units = self._attrdict.get('units',
##						windowinterface.UNIT_SCREEN))
##		self._is_shown = 1
##		self.after_show()

	def do_hide(self):
		if debug: print 'ChannelWindow.do_hide('+`self`+')'
		if self.window:
			self.window.unregister(WMEVENTS.ResizeWindow)
			self.window.close()
			self.window = None
			self.armed_display = self.played_display = None
			self.update_display = None
			if self._attrdict.get('base_window', 'undefined') == 'undefined':
				self.event((self._attrdict, 'topLayoutCloseEvent'))

	def resize(self, arg, window, event, value):
		if debug: print 'ChannelWindow.resize'+`self,arg,window,event,value`
		self._player.toplevel.setwaiting()
		self.replaynode()
##		if not self._player.playing and \
##		   self._attrdict.get('base_window','undefined') == 'undefined' and \
##		   hasattr(self, 'editmgr'):
##			units = self._attrdict.get('units',
##						   windowinterface.UNIT_MM)
##			x, y, w, h = self.window.getgeometry(units = units)
##			if self._attrdict.get('winsize') != (w, h) and \
##			   self.editmgr.transaction():
##				self.save_geometry()
##				self.editmgr.commit()

	def arm_0(self, node):
		self.updateToActiveState(node)
		if not self._armcontext:
			return
		same = Channel.arm_0(self, node)
		if same and self.armed_display and \
		   not self.armed_display.is_closed():
			return 1
		#if same: print 'Same, but no armed_display' # DBG
		if not self._is_shown or not node.ShouldPlay() \
		   or not self.window:
			return 0

		if self.armed_display:
			self.armed_display.close()

		# experimental subregion and regpoint code
		# we have to resize the window before the do_arm() method call, because
		# do_arm use the real window size to determinate the real scale of an image
		# when the scale computation will be clean, we'll be able to resize the
		# window from play method just before display the media.
#		if wingeom != self._wingeom:
#			self._wingeom = wingeom
			# print 'old geom : ',self._wingeom
			# print 'new geom : ',wingeom
#			units = self._attrdict.get('units',
#				   windowinterface.UNIT_SCREEN)
#			self.window.updatecoordinates(wingeom, units)
		# experimental subregion and regpoint code

		self.__transparent = transparent = MMAttrdefs.getattr(node, 'transparent')
		if transparent:
			bgcolor = None
		else:
			bgcolor = self.getbgcolor(node)
		self.armed_display = self.window.newdisplaylist(bgcolor)

		# by default all window area
		self.armBox = (0.0, 0.0, 1.0, 1.0)

		# set foreground color
		fgcolor = self.getfgcolor(node)
		self.armed_display.fgcolor(fgcolor)

		# set alpha sentitivity
		alphaSensitivity = MMAttrdefs.getattr(node, 'sensitivity')
		self.armed_display.setAlphaSensitivity(alphaSensitivity)
		
		return 0

	# Activate a sensitive area in display list according to the anchors.
	# Warning: this method has to be called after do_arm
	def _prepareAnchors(self, node):
		tabindex = MMAttrdefs.getattr(node, 'tabindex') or 0x10000
		if MMAttrdefs.getattr(node, 'transparent'):
			bgcolor = None
		else:
			bgcolor = self.getbgcolor(node)
		self.armed_display.fgcolor(bgcolor)

		# create a button that covers the whole region, just
		# in case we need one later on
		# make buttons sensitive for which there is already a
		# sync arc active
		sensitive = 0
		for arc in node.sched_children:
			if arc.event == ACTIVATEEVENT:
				sensitive = 1
				break

		windowCoordinates = self.convertShapeRelImageToRelWindow(['rect', 0.0, 0.0, 1.0, 1.0])
		b = self.armed_display.newbutton(windowCoordinates, z = -1, sensitive = sensitive)
		self.setanchor(b, node)
		if tabindex > 0 and sensitive:
			self._player.addtabindex(tabindex, node, self)

		# create buttons for all anchors
		for a in node.GetChildren():
			if a.GetType() != 'anchor':
				continue
			if MMAttrdefs.getattr(a, 'fragment'):
				continue

			# convert coordinates relative to the window size
			windowCoordinates = self.convertShapeToRelWindow(MMAttrdefs.getattr(a, 'ashape'),
									 MMAttrdefs.getattr(a, 'acoords'))

			b = self.armed_display.newbutton(windowCoordinates, sensitive = 0)
			self.setanchor(b, a)

	def add_arc(self, node, arc):
		if node.GetType() == 'anchor':
			node = node.GetParent()
		if node is not self._played_node or \
		   arc.event != ACTIVATEEVENT:
			return
		node = arc.refnode()
		b = self._played_anchor2button.get(node)
		if b is not None:
			b.setsensitive(1)
			tabindex = MMAttrdefs.getattr(node, 'tabindex') or 0x10000
			if tabindex > 0:
				self._player.addtabindex(tabindex, node, self)

	# update internal geometry variables. Get geometry from MMContext structure
	def updateGeom(self, node):
		self._wingeom, self._mediageom = node.getPxGeomMedia()
		self._winabsgeom, self._winabsmedia = node.getPxAbsGeomMedia()

	# get the space display area of media
	# return absolute values to the subregion or region:
	# tuple of (left/top/width/height)
	def getmediageom(self, node):
		return self._mediageom

	# get the channel geometry
	# return pixel values relative to the parent region: tuple of (left/top/width/height)
	def getwingeom(self):
		return self._wingeom

	# get the channel geometry
	# return pixel values relative to the viewport
	def getabswingeom(self):
		return self._winabsgeom
	
	def play(self, node, curtime):
		if debug: print 'ChannelWindow.play('+`self`+','+`node`+')'
		if node.GetType() == 'anchor':
			self.play_anchor(node, curtime)
			return
		self.play_0(node, curtime)
		if not self._armcontext:
			return
		if self._is_shown and node.ShouldPlay() \
			and self.window:
			self.check_popup()
			self.schedule_transitions(node, curtime)
			if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
				pass
			else:
				self.armed_display.render()
			if self.played_display:
				self.played_display.close()
			self.played_display = self.armed_display
			self.armed_display = None
			self.do_play(node, curtime)
		self.play_1(curtime)

	def stopplay(self, node, curtime):
		if debug: print 'ChannelWindow.stopplay('+`self`+','+`node`+')'
		if node.GetType() == 'anchor':
			Channel.stopplay(self, node, curtime)
			return
		if node and self._played_node is not node:
##			print 'node was not the playing node '+`self,node,self._played_node`
			return
		Channel.stopplay(self, node, curtime)
		self.cleanup_transitions()
		self.updateToInactiveState()
		if self.played_display:
##			self.played_display.close()
			self.played_display = None


	def setpaused(self, paused, timestamp):
		if debug: print 'ChannelWindow.setpaused('+`self`+','+`paused`+')'
		if self.__out_trans_qid and timestamp is not None:
			if paused:
				self.__pausetime = timestamp
				self._scheduler.cancel(self.__out_trans_qid)
			else:
				out_trans, outtranstime, outtransdur, node = self.__out_trans
				outtranstime = outtranstime + timestamp - self.__pausetime
				self.__out_trans_qid = self._scheduler.enterabs(outtranstime, 0,
					self.schedule_out_trans, (out_trans, outtranstime, outtransdur, node))
		if paused == 'hide' and self.played_display:
			# we need an unrender() method here...
			d = self.played_display.clone()
			self.played_display.close()
			self.played_display = d
		elif not paused and self._paused == 'hide' and self.played_display:
			self.played_display.render()
		Channel.setpaused(self, paused, timestamp)

	def playstop(self, curtime):
		return Channel.playstop(self, curtime)

	def schedule_transitions(self, node, curtime):
		in_trans = self.gettransition(node, 'transIn')
		out_trans = self.gettransition(node, 'transOut')
		if out_trans <> None:
			outtransdur = out_trans.get('dur', 1.0)
			outtranstime = node.calcendfreezetime(self._playcontext)
			# don't schedule out transition if time unresolved
			if outtranstime is not None and outtranstime > 0:
				outtranstime = outtranstime-outtransdur
				self.__out_trans_qid = self._scheduler.enterabs(outtranstime, 0,
					self.schedule_out_trans, (out_trans, outtranstime, outtransdur, node))
				self.__out_trans = out_trans, outtranstime, outtransdur, node
		if in_trans is not None and in_trans.get('dur', 1.0) > 0 and self.window:
			start_time = node.get_start_time()
			otherwindow = self._find_multiregion_transition(in_trans, start_time)
			if otherwindow:
				self.window.jointransition(otherwindow, (self.endtransition, (node, max(curtime,start_time+in_trans.get('dur',1.0)))))
			else:
				self.window.begintransition(0, 1, in_trans, (self.endtransition, (node, max(curtime,start_time+in_trans.get('dur',1.0)))))

	def schedule_out_trans(self, out_trans, outtranstime, outtransdur, node):
		self.__out_trans_qid = None
		self.__out_trans = None
		if not self.window:
			return
		otherwindow = self._find_multiregion_transition(out_trans, outtranstime)
##		print 'OTHERWINDOW', otherwindow
		if otherwindow:
			self.window.jointransition(otherwindow)
		else:
			self.window.begintransition(1, 1, out_trans, (self.endtransition, (node, outtranstime+outtransdur)))

	def endtransition(self, node, curtime):
		# callback, called at end of transition
		chlist = self.getViewportChannel().getOverlapRendererList(self, node)
		for ch, nd in chlist:
			self._playcontext.transitiondone(nd, curtime)

	def cleanup_transitions(self):
		if self.__out_trans_qid:
			try:
				self._scheduler.cancel(self.__out_trans_qid)
			except ValueError:
				# maybe pausing, so don't worry about it
				pass
			self.__out_trans_qid = None
			self.__out_trans = None
		if self.window:
			self.window.endtransition()
		lchan = self.find_layout_channel()
		lchan._active_multiregion_transition = None

	def _find_multiregion_transition(self, trans, transtime):
		if not trans.get('coordinated', 0):
			return None
		# Unfortunately the transition name isn't in the dictionary.
		# We use the id of the dictionary as its unique value
		trid = id(trans)
		#
		# Tricky code ahead. For transitions we want to look at the channel hierarchy ignoring
		# all non-layout channels (since layout channels correspond to regions, and multielement
		# transitions are region-based).
		# XXXX The code may be incorrect too: it looks up one level to find a matching transition,
		# but downwards all the way through the tree. This means that if the regions have
		# a grandparent/grandchild relation it will depend on scheduling order whether they match
		# up. I think the standard doesn't allow this, but we should check.
		#
		our_lchan = self.find_layout_channel()
		if our_lchan.pchan:
			top_lchan = our_lchan.pchan.find_layout_channel()
		else:
			top_lchan = our_lchan
		rv = top_lchan._has_multiregion_transition(trid, transtime, recursive=1)
		our_lchan._active_multiregion_transition = (trid, transtime, self.window)
		return rv

	def _has_multiregion_transition(self, trid, transtime, recursive=0):
		if self._active_multiregion_transition and \
				(trid, transtime) == self._active_multiregion_transition[:2]:
			return self._active_multiregion_transition[2]
		if recursive:
			for child in self._subchannels:
				rv = child._has_multiregion_transition(trid, transtime, recursive=1)
				if rv:
					return rv
		return None

	def find_layout_channel(self):
		if self.is_layout_channel or not hasattr(self, 'pchan') or not self.pchan:
			return self
		return self.pchan.find_layout_channel()

	# use this code to get the error message in the window instead
	# of in a popup window
##	def errormsg(self, node, msg):
##		if node:
##			name = MMAttrdefs.getattr(node, 'name')
##			if not name:
##				name = '<unnamed node>'
##			nmsg = ' node ' + name
##		else:
##			nmsg = ''
##		msg = 'Warning:\nWhile arming' + nmsg + ' on channel ' + self._name + ':\n' + msg
##		parms = self.armed_display.fitfont('Times-Roman', msg)
##		w, h = self.armed_display.strsize(msg)
##		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
##		self.armed_display.fgcolor((255, 0, 0))		# red
##		box = self.armed_display.writestr(msg)

	def defanchor(self, node, anchor, cb):
		# This method is called when the user defines a new anchor. It
		# may be overridden by derived classes.
		windowinterface.showmessage('Channel '+self._name+
			  ' does not support\nediting of anchors (yet)',
					    mtype = 'warning', grab = 1,
					    parent = self.window)
		apply(cb, (anchor,))


	# convert relative image offsets to relative window offsets
	# For this, we need to know the real size of media which fit inside the region
	# --> method getArmBox (channel dependent)
	# This box is known only after the call of do_arm method
	def convertShapeRelImageToRelWindow(self, args, arming = 1):
		shapeType = args[0]

		if arming:
			box = self.getArmBox()
		else:
			box = self.getPlayBox()
		rArgs = [shapeType]
		n=0
		for a in args[1:]:
			# test if xCoordinates or yCoordinates
			if n%2 == 0:
				# convert coordinates from image to window size
				rArgs.append(float(a*box[2] + box[0]) / box[2])
			else:
				rArgs.append(float(a*box[3] + box[1]) / box[3])
			n = n+1

		return rArgs

	# convert shape coordinates (as defined in SMIL specification) relative to the window. The result is float values
	# For this, we need to know the real size of media which fit inside the region
	# --> method getArmBox (channel dependent)
	# This box is defined only after the call of do_arm method
	def convertShapeToRelWindow(self, shape, coords, arming = 1):
		# in this case we assume it's a rectangle area
		if not coords:
			coords = [0.0, 0.0, 1.0, 1.0]
			shape = 'rect'

		# note: mLeft, mTop, ... is the geometry of the media after centering, scaling, ...
		if arming:
			mLeftInPercent, mTopInPercent, mWidthInPercent, mHeightInPercent = self.getArmBox()
		else:
			mLeftInPercent, mTopInPercent, mWidthInPercent, mHeightInPercent = self.getPlayBox()
			
		wLeftInPixel, wTopInPixel, wWidthInPixel, wHeightInPixel = self.getwingeom()
		
		if shape != 'circle':
			if shape == 'rect':
				rArgs = ['rect']
			else:		# poly
				rArgs = ['poly']

			for n in range(len(coords)):
				a = coords[n]
				if type(a) is type(0):	# any integer number
					# integer values: the coordinates aren't related to the arm/play box
					# test if xCoordinates or yCoordinates
					if n%2 == 0:
						rArgs.append(float(a)/wWidthInPixel)
					else:
						rArgs.append(float(a)/wHeightInPixel)
				else:
					# percent values: the coordinates are related to the arm/play box
					# test if xCoordinates or yCoordinates
					if n%2 == 0:
						# convert coordinates from image to window size
						rArgs.append(a*mWidthInPercent + mLeftInPercent)
					else:
						rArgs.append(a*mHeightInPercent + mTopInPercent)
		else:
			# Internally, we manage only ellipses
			# note: for an ellipse, the meaning of rArg is a tuple of (xcenter, ycenter, xradius, yradius) 
			rArgs = ['ellipse']
			xCenter, yCenter, radius = coords
#			xsize, ysize = node.GetDefaultMediaSize(100, 100)
#			# after a arming default, xsize or ysize value are equal to 0 !
#			if xsize == 0: xsize=1
#			if ysize == 0: ysize=1
			
			if type(xCenter) is type(0): # any integer number
				# integer values: the coordinates aren't related to the arm/play box
				rArgs.append(float(xCenter)/wWidthInPixel)
			else:
				# percent values: the coordinates are related to the arm/play box
				rArgs.append(xCenter*mWidthInPercent + mLeftInPercent)
				
			if type(yCenter) is type(0): # any integer number
				# integer values: the coordinates aren't related to the arm/play box
				rArgs.append(float(yCenter)/wHeightInPixel)
			else:
				# percent values: the coordinates are related to the arm/play box
				rArgs.append(yCenter*mHeightInPercent + mTopInPercent)
	
			if type(radius) is type(0): 
				# integer values: the coordinates aren't related to the arm/play box
				rArgs.append(float(radius)/wWidthInPixel)
				rArgs.append(float(radius)/wHeightInPixel)
			else:
				mWidthInPixel = mWidthInPercent*wWidthInPixel
				mHeightInPixel = mHeightInPercent*wHeightInPixel
#				if xsize > ysize:
				if mWidthInPixel > mHeightInPixel:
					# radius is relative to the height
					radiusInPixel = radius*mHeightInPixel
				else:
					# radius is relative to the width
					radiusInPixel = radius*mWidthInPixel
				rArgs.append(radiusInPixel/wWidthInPixel)
				rArgs.append(radiusInPixel/wHeightInPixel)
		return rArgs
	
class ChannelAsync(Channel):

	def play(self, node, curtime):
		if debug: print 'ChannelAsync.play('+`self`+','+`node`+')'
		if node.GetType() == 'anchor':
			self.play_anchor(node, curtime)
			return
		self.play_0(node, curtime)
		if not self._armcontext:
			return
		if not self._is_shown or not node.ShouldPlay() \
		   or self.syncplay:
			self.play_1(curtime)
			return
		if self._is_shown:
			self.do_play(node, curtime)
		self.armdone()

class ChannelWindowAsync(ChannelWindow):
	def play(self, node, curtime):
		if debug: print 'ChannelWindowAsync.play('+`self`+','+`node`+')'
		if node.GetType() == 'anchor':
			self.play_anchor(node, curtime)
			return
		self.play_0(node, curtime)
		if not self._armcontext:
			return
		if self._is_shown and node.ShouldPlay() \
		   and self.window and not self.syncplay:
##			try:
##				winoff = self.winoff
##				winoff = MMAttrdefs.getattr(node, 'base_winoff')
##			except (AttributeError, KeyError):
##				pass
##			else:
##				if winoff != self.winoff:
##					self.hide()
##					self.show()
			self.check_popup()
			self.schedule_transitions(node, curtime)
			if self.armed_display.is_closed():
				# assume that we are going to get a
				# resize event
				pass
			else:
				self.armed_display.render()
			if self.played_display:
				self.played_display.close()
			self.played_display = self.armed_display
			self.armed_display = None
			self.do_play(node, curtime)
			self.armdone()
		else:
			self.play_1(curtime)

def dummy_callback(arg):
	pass

class AnchorContext:
	def arm_done(self, node):
		raise error, 'AnchorContext.arm_done() called'

	def arm_ready(self, channel):
		raise error, 'AnchorContext.arm_ready() called'

	def anchorfired(self, node, arg):
		raise error, 'AnchorContext.anchorfired() called'

	def play_done(self, node, curtime, timestamp = None):
		raise error, 'AnchorContext.play_done() called'

# cleanup temporary files when we finish
windowinterface.addclosecallback(MMurl.urlcleanup, ())
