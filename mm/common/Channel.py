__version__ = "$Id$"

# Channels should either use Channel, ChannelWindow, or ChannelThread
# as a superclass, but never more than one.

from AnchorDefs import *
import os
debug = os.environ.has_key('CHANNELDEBUG')
import MMAttrdefs
import windowinterface, WMEVENTS
from windowinterface import SINGLE, TEXT, HTM, MPEG
from windowinterface import TRUE, FALSE
import string
import MMurl
import regsub
error = 'Channel.error'

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
	node_attrs = ['file']
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
		self._paused = 0
		self._subchannels = []
		self._want_shown = 0
		self.nopop = 0
		self.syncarm = 0
		self.syncplay = 0
		self.is_layout_channel = 0
		self.seekargs = None
		if debug:
			print 'Channel() -> '+`self`
		channels.append(self)

	def __repr__(self):
		return '<%s instance, name=%s>' % (self.__class__.__name__, self._name)

	def destroy(self):
		# Destroy this instance of a Channel object.  This
		# will stop playing and arming on this channel and
		# release all used resources.  After this, none of the
		# methods of this instance may be called anymore.
		if debug:
			print 'Channel.destroy('+`self`+')'
		if self._is_shown:
			self.hide()
		del self._armcontext
		del self._armed_anchors
		del self._armed_node
		del self._armstate
		del self._attrdict
		del self._deviceno
		del self._name
		del self._anchors
		del self._playcontext
		del self._played_anchors
		del self._played_node
		del self._player
		del self._playstate
		del self._qid
		del self._scheduler
		channels.remove(self)

	def may_show(self):
		# Indicate to the higher level whether this channel is
		# visible and may be shown.
		if not self._attrdict.has_key('visible'):
			return 1
		else:
			return self._attrdict['visible']

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
				self.play(node)
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

	def show(self):
		if debug:
			print 'Channel.show('+`self`+')'
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
		# First, check that there is a base_window attribute
		# and that it isn't "undefined".
		pname = self._attrdict.get('base_window', 'undefined')
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
			if pchan and self in pchan._subchannels:
				windowinterface.showmessage(
					'Channel '+`self._name`+' is part of'+
					' a base-window loop',
					mtype = 'error')
				pchan = None
		if pchan:
			# Finally, check that the base window is being shown.
			pchan._subchannels.append(self)
			if not pchan._is_shown:
				# parent channel not shown, so cannot show self
				return
		# register that a channel wants to be shown
		self._player.before_chan_show(self)
		self._is_shown = self.do_show(pchan)
		if not self._is_shown:
			if self._is_shown == 0:
				self._player.after_chan_show(self)
			return
		self.after_show()

	def after_show(self):
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
				chan.show()
		self._player.after_chan_show(self)

	def hide(self):
		# Indicate that the channel must enter the HIDDEN state.
		if debug:
			print 'Channel.hide('+`self`+')'
		self._want_shown = 0
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
		for chan in channels:
			try:
				chan._subchannels.remove(self)
			except ValueError:
				pass
		self._subchannels = subchannels
		if self._armstate == ARMING:
			self.arm_1()
##		if self._playstate == PLAYING:
##			self.playstop()

	def highlight(self):
		# highlight the channel instance (dummy for channels
		# without windows)
		pass

	def unhighlight(self):
		# stop highlighting the channel instance
		pass

	def popup(self):
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

	def setwaiting(self):
		pass

	def setready(self):
		pass

	def getaltvalue(self, node):
		# Return a value between 0 and 1 which gives "desirability"
		# of playing this node if there are alternatives. Should
		# return 0 for unplayable, 1 for no problems at all.
		# Intermedeate values may be returned depending on bandwidth,
		# quality, etc.
		return 1.0

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
		if debug:
			print 'Channel.arm_0('+`self`+','+`node`+')'
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
		self.armed_duration = self.getduration(node)
		return 0

	def arm_1(self):
		# This does the final part of arming a node.  This
		# method should be called by superclasses when they
		# are finished with arming.
		if debug:
			print 'Channel.arm_1('+`self`+')'
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
		if debug:
			print 'Channel.armdone('+`self`+')'
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

	def anchor_triggered(self, node, anchorlist, arg):
		return self._playcontext.anchorfired(node, anchorlist, arg)

	def pause_triggered(self, node, anchorlist, arg):
		# Callback which is called when the button of a pause
		# anchor is pressed.
		# If the anchor didn't fire, we're done playing the
		# node.
		if self._playstate == PLAYED:
			# someone pushed the button again, I guess
			return
		if not self._playcontext.anchorfired(node, anchorlist, arg):
			if self._qid:
				try:
					self._scheduler.cancel(self._qid)
				except RuntimeError:
					# It may be that the done
					# event was removed from the
					# queue and is now somewhere
					# in the internals of the
					# scheduler where we can't
					# remove it.  We ought to do
					# something about that.
					pass
				self._qid = None
			self._has_pause = 0
			self.playdone(0)

	def play_0(self, node):
		# This does the initial part of playing a node.
		# Superclasses should call this method when they are
		# starting to play a node.
		# If callback is `None', make sure we don't do any
		# callbacks.
		if debug:
			print 'Channel.play_0('+`self`+','+`node`+')'
		if self._armed_node is not node:
			raise error, 'node was not the armed node '+`self,node`
		if self._playstate != PIDLE:
			raise error, 'play not idle on '+self._name
		if self._armstate != ARMED:
			raise error, 'arm not ready'
		self._playcontext = self._armcontext
		self._playstate = PLAYING
		self._played_node = node
		self._anchors = {}
		self._played_anchors = self._armed_anchors[:]
		durationattr = MMAttrdefs.getattr(node, 'duration')
		self._has_pause = (durationattr < 0)
		for (name, type, button) in self._played_anchors:
			if type == ATYPE_PAUSE:
##				print 'found pause anchor'
				f = self.pause_triggered
				self._has_pause = 1
			else:
				f = self._playcontext.anchorfired
			self._anchors[button] = f, (node, [(name, type)], None)
		self._qid = None

	def play_1(self):
		# This does the final part of playing a node.  This
		# should only be called by superclasses when they
		# don't have an intrinsic duration.  Otherwise they
		# should just call armdone to indicate that the armed
		# information is not needed anymore, and call playdone
		# when they are finished playing the node.
		if debug:
			print 'Channel.play_1('+`self`+')'
		# armdone must come before playdone, since playdone
		# may trigger an autofiring anchor that terminates
		# this node
		self.armdone()
		if not self.syncplay:
			if self.armed_duration > 0:
				self._qid = self._scheduler.enter(
					  self.armed_duration, 0,
					  self.playdone, (0,))
			else:
				self.playdone(0)
		else:
			self.playdone(0)

	def playdone(self, outside_induced):
		# This method should be called by a superclass
		# (possibly through play_1) to indicate that the node
		# has finished playing.
		if debug:
			if self._has_pause:
				s = ' (pause)'
			else:
				s = ''
			print 'Channel.playdone('+`self`+')' + s
		if self._playstate != PLAYING:
			if not outside_induced and not self._qid:
				# timer callback couldn't be cancelled
				return
			raise error, 'not playing'
		self._qid = None
		# If this node has a pausing anchor, don't call the
		# callback just yet but wait till the anchor is hit.
		if self._has_pause:
			return
		if not self.syncplay:
			if not outside_induced:
				if self._try_auto_anchors():
					return
			self._playcontext.play_done(self._played_node)
		self._playstate = PLAYED

	def _try_auto_anchors(self):
	        node = self._played_node
	        anchorlist = MMAttrdefs.getattr(node, 'anchorlist')
		list = []
		for (name, type, args) in anchorlist:
			if type == ATYPE_AUTO:
##				print 'found auto anchor'
				list.append((name, type))
		if not list:
			return 0
		didfire = self._playcontext.anchorfired(node, list, None)
		if didfire and self._playstate == PLAYING and \
		   self._played_node is node:
		    if not self.syncplay:
			self._playcontext.play_done(node)
		    self._playstate = PLAYED
		return didfire

	def playstop(self):
		# Internal method to stop playing.
		if debug:
			print 'Channel.playstop('+`self`+')'
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
		self._has_pause = 0
		self.playdone(1)

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

	def do_play(self, node):
		# Actually play the node.
		pass

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
		if self._is_shown and not self.do_arm(node, same):
			return
		self.arm_1()

	def seekanchor(self, node, aid, args):
		# Called before arm on the node. Signifies that the node
		# is played because a hyperjump to the specified anchor
		# was executed. The channels can override this method, for
		# instance to highlight the anchor. If the source anchor
		# had arguments (as in HTML forms) these args are passed to
		# the destination anchor here.
		self.seekargs = (node, aid, args)

	def play(self, node):
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
		if debug:
			print 'Channel.play('+`self`+','+`node`+')'
		self.play_0(node)
		if self._is_shown:
			self.do_play(node)
		self.play_1()

	def stopplay(self, node):
		# Indicate that the channel can revert from the
		# PLAYING or PLAYED state to PIDLE.
		# Node is only passed to do consistency checking.
		if debug:
			print 'Channel.stopplay('+`self`+','+`node`+')'
		if node and self._played_node is not node:
			raise error, 'node was not the playing node '+`self,node,self._played_node`
		if self._playstate == PLAYING:
			self._has_pause = 0
			self.playstop()
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
		if debug:
			print 'Channel.stoparm('+`self`+')'
		if self._armstate == ARMING:
			self.armstop()
			self._armed_node = None
		if self._armstate != ARMED:
			raise error, 'not armed'
		self._armstate = AIDLE
		# self._armed_node = None # XXXX Removed for arm-caching
		# self._armed_anchors = []

	def terminate(self, node):
		if debug:
			print 'Channel.terminate('+`self`+','+`node`+')'
		if self._armstate != AIDLE and self._armed_node is node:
			save_syncarm = self.syncarm
			self.syncarm = 1
			self.stoparm()
			self.syncarm = save_syncarm
			self._armcontext.arm_ready(self)
		if self._playstate != PIDLE and self._played_node is node:
			# hack to not generate play_done event
			save_syncplay = self.syncplay
			self.syncplay = 1
			self.stopplay(node)
			self.syncplay = save_syncplay

	def startcontext(self, ctx):
		# Called by the scheduler to start a new context.  The
		# following arm is done in the new context.
		if debug:
			print 'Channel.startcontext'+`(self, ctx)`
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

	def stopcontext(self, ctx):
		# Called by the scheduler to force the channel to the
		# complete idle state.
		if debug:
			print 'Channel.stopcontext'+`(self, ctx)`
		if ctx is not self._playcontext and \
		   ctx is not self._armcontext:
			raise error, 'stopcontext with unknown context'
		if self._playcontext is ctx:
			if self._playstate in (PLAYING, PLAYED):
				self.stopplay(None)
			self._playcontext = None
		if self._armcontext is ctx:
			if self._armstate in (ARMING, ARMED):
				self.stoparm()
			self._armcontext = None

	def setpaused(self, paused):
		if debug:
			print 'Channel.setpaused('+`self`+','+`paused`+')'
		self._paused = paused

	#
	# Methods used by derived classes.
	#
	def setanchor(self, name, type, button):
		# Define an anchor.  This method should be called by
		# superclasses to define an anchor while arming.  Name
		# is the name of the anchor, type is its type, button
		# is a button object which, when pressed, triggers the
		# anchor.
		self._armed_anchors.append((name, type, button))

	def getfileurl(self, node):
		name = node.GetAttrDef('name', None)
		if name and self.seekargs and self.seekargs[0] is node and self.seekargs[2]:
			name = name + '_file'
			for arg, val in self.seekargs[2]:
				if arg == name:
					return node.context.findurl(val)
		return node.context.findurl(MMAttrdefs.getattr(node, 'file'))

	def getstring(self, node):
		if node.type == 'imm':
			self.armed_url = ''
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			url = self.getfileurl(node)
			self.armed_url = url
			try:
				# use urlretrieve so that data gets cached
				fn = MMurl.urlretrieve(url)[0]
				self.armed_url = MMurl._urlopener.openedurl
				fp = open(fn, 'r')
				text = fp.read()
				fp.close()
			except IOError:
				import sys
				raise error, 'Cannot open %s: %s, %s'%(url, sys.exc_type, sys.exc_value)
			#
			# Convert dos/mac newlines to ours
			#
			text = regsub.gsub('\r\n', '\n', text)
			text = regsub.gsub('\r', '\n', text)
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

	def getbgcolor(self, node):
		return MMAttrdefs.getattr(node, 'bgcolor')

	def getfgcolor(self, node):
		return MMAttrdefs.getattr(node, 'fgcolor')

	def getbucolor(self, node):
		return MMAttrdefs.getattr(node, 'bucolor')

	def gethicolor(self, node):
		return MMAttrdefs.getattr(node, 'hicolor')

	def getloop(self, node):
		return MMAttrdefs.getattr(node, 'loop')

	def defanchor(self, node, anchor, cb):
		# This method is called when the user defines a new anchor. It
		# may be overridden by derived classes.
		windowinterface.showmessage('Channel '+self._name+
			  ' does not support\nediting of anchors (yet)',
					    mtype = 'warning')
		apply(cb, (anchor,))

	def updatefixedanchors(self, node):
		# This method is called by the anchor editor to ensure that
		# the 'anchorlist' attribute is correct for nodes on channels
		# that have anchors implicit in the document. Such channels
		# override this method by one that does the updating and
		# returns 1. A return of '1' causes the anchor editor to refuse
		# to edit an anchor.
		return 0

	def errormsg(self, node, msg):
		if node:
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			nmsg = ' node ' + name
		else:
			nmsg = ''
		windowinterface.showmessage(
			'While arming%s on channel %s:\n%s' %
				(nmsg, self._name, msg),
			mtype = 'warning')

### dictionary with channels that have windows
##ChannelWinDict = {}

_button = None				# the currently highlighted button

class ChannelWindow(Channel):
	chan_attrs = Channel.chan_attrs + ['base_winoff', 'transparent', 'units', 'popup', 'z']
	node_attrs = Channel.node_attrs + ['duration', 'bgcolor']
	_visible = TRUE
	_window_type = SINGLE

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		if not hasattr(self._player, 'ChannelWinDict'):
			self._player.ChannelWinDict = {}
		self._player.ChannelWinDict[self._name] = self
		self.window = None
		self.armed_display = self.played_display = None
		self._is_waiting = 0
		self.want_default_colormap = 0

	def destroy(self):
		del self._player.ChannelWinDict[self._name]
		Channel.destroy(self)
		del self.window
		del self.armed_display
		del self.played_display

	def highlight(self):
		if self._is_shown and self.window:
			self.window.pop()
			self.window.showwindow()

	def unhighlight(self):
		if self._is_shown and self.window:
			self.window.dontshowwindow()

	def popup(self):
		if self._is_shown and self.window:
			self.window.pop()

	def check_popup(self):
		if self.nopop or not self._is_shown or not self.window:
			return
		if self._attrdict.has_key('popup'):
			if self._attrdict['popup'] == 0:
				return
		self.window.pop()

	def popdown(self):
		if self._is_shown and self.window:
			self.window.push()

	def focuscall(self):
		if self._playstate in (PLAYING, PLAYED):
			node = self._played_node
			top = self._player.toplevel
			top.hierarchyview.globalsetfocus(node)
			top.channelview.globalsetfocus(node)
		else:
			if self.window:
				grab = self.window
			else:
				grab = 1
			windowinterface.showmessage('Can only push focus when playing', mtype = 'warning', grab = grab)

	def save_geometry(self):
		if self._is_shown and self.window:
			units = self._attrdict('units',
					       windowinterface.UNIT_MM)
			x, y, w, h = self.window.getgeometry(units = units)
			self._attrdict['winpos'] = x, y
			self._attrdict['winsize'] = w, h

	def setwaiting(self):
		self._is_waiting = 1
		if self._is_shown and self.window:
			self.window.setcursor('watch')

	def setready(self):
		self._is_waiting = 0
		if self._is_shown and self.window:
			self.window.setcursor('')

	def mousepress(self, arg, window, event, value):
		global _button
		# a mouse button was pressed
		if _button is not None and not _button.is_closed():
			# probably doesn't occur...
			_button.unhighlight()
		_button = None
		buttons = value[2]
		if len(buttons) == 0:
			if self._attrdict.get('transparent', 0):
				raise windowinterface.Continue
## 			if hasattr(self._player, 'editmgr'):
## 				self.highlight()
		else:
			button = buttons[0]
			button.highlight()
			_button = button

	def mouserelease(self, arg, window, event, value):
		global _button
## 		if hasattr(self._player, 'editmgr'):
## 			self.unhighlight()
		buttons = value[2]
		if len(buttons) == 0:
			if self._attrdict.get('transparent', 0):
				raise windowinterface.Continue
		else:
			button = buttons[0]
			if _button is button:
				try:
					f, a = self._anchors[button]
				except KeyError:
					pass
				else:
					a = self.setanchorargs(a, button, value)
					self._player.toplevel.setwaiting()
					dummy = apply(f, a) # may close channel
					if hasattr(self, '_player'):
						self._player.toplevel.setready()
		if _button and not _button.is_closed():
			_button.unhighlight()
		_button = None

	def setanchorargs(self, (node, nametypelist, args), button, value):
		# Return the (node, nametypelist, args) tuple.
		# Channels can override this to modify the args passed
		# through the hyperjump (default: None)
		return (node, nametypelist, args)

	def create_window(self, pchan, pgeom):
		menu = []
		if pchan:
			if hasattr(self._player, 'editmgr'):
				menu.append('', 'raise', (self.popup, ()))
				menu.append('', 'lower', (self.popdown, ()))
				menu.append(None)
				menu.append('', 'push focus',
					    (self.focuscall, ()))
				menu.append(None)
				menu.append('', 'highlight',
					    (self.highlight, ()))
				menu.append('', 'unhighlight',
					    (self.unhighlight, ()))
			transparent = self._attrdict.get('transparent', 0)
			z = self._attrdict.get('z', 0)
			if self.want_default_colormap:
				self.window = pchan.window.newcmwindow(pgeom,
						transparent = transparent,
						z = z,
						type_channel = self._window_type)
			else:
				self.window = pchan.window.newwindow(pgeom,
						transparent = transparent,
						z = z,
						type_channel = self._window_type)
			if hasattr(self._player, 'editmgr'):
				menu.append(None)
				menu.append('', 'resize',
					    (self.resize_window, (pchan,)))
		else:
			# no basewindow, create a top-level window
			units = self._attrdict.get('units',
						   windowinterface.UNIT_MM)
			width, height = self._attrdict.get('winsize', (50, 50))
			x, y = self._attrdict.get('winpos', (None, None))
			if self.want_default_colormap:
				self.window = windowinterface.newcmwindow(x, y,
					width, height, self._name,
					visible_channel = self._visible,
					type_channel = self._window_type,
					units = units)
			else:
				self.window = windowinterface.newwindow(x, y,
					width, height, self._name,
					visible_channel = self._visible,
					type_channel = self._window_type,
					units = units)
			self.window.register(WMEVENTS.WindowExit,
					     self._destroy_callback, None)
			if hasattr(self._player, 'editmgr'):
				menu.append('', 'push focus',
					    (self.focuscall, ()))
		if self._is_waiting:
			self.window.setcursor('watch')
		if self._attrdict.has_key('bgcolor'):
			self.window.bgcolor(self._attrdict['bgcolor'])
		if self._attrdict.has_key('fgcolor'):
			self.window.fgcolor(self._attrdict['fgcolor'])
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.Mouse0Press, self.mousepress, None)
		self.window.register(WMEVENTS.Mouse0Release, self.mouserelease,
				     None)
		if menu:
			self.window.create_menu(menu, title = self._name)

	def _destroy_callback(self, *rest):
		self._player.cmenu_callback(self._name)

	def resize_window(self, pchan):
		if not self._player.editmgr.transaction():
			return
		# we now know for sure we're not playing
		pchan.window.create_box(
			'Resize window for channel ' + self._name,
			self._resize_callback,
			self._attrdict['base_winoff'])

	def _resize_callback(self, *box):
		if box:
			self._attrdict['base_winoff'] = box
			self.hide()
			self.show()
			self._player.editmgr.commit()
		else:
			self._player.editmgr.rollback()

	def do_show(self, pchan):
		if debug:
			print 'ChannelWindow.do_show('+`self`+')'
		try:
			del self.winoff
		except AttributeError:
			pass
		# create a window for this channel
		pgeom = None
		if pchan:
			#
			# Find the base window offsets, or ask for them.
			#
			if self._played_node:
				try:
					pgeom = MMAttrdefs.getattr(self._played_node, 'base_winoff')
				except KeyError:
					pass
			if pgeom:
				self.winoff = pgeom
			elif self._attrdict.has_key('base_winoff'):
				self.winoff = pgeom = self._attrdict['base_winoff']
			elif self._player.playing:
				windowinterface.showmessage(
					'No geometry for subchannel %s known' % self._name,
					mtype = 'error', grab = 1)
				pchan._subchannels.remove(self)
				pchan = None
			else:
				pchan.window.create_box(
					'Draw a subwindow for %s in %s' %
						(self._name, pchan._name),
					self._box_callback)
				return None
		self.create_window(pchan, pgeom)
		return 1

	def _box_callback(self, *pgeom):
		pname = self._attrdict['base_window']
		pchan = self._player.ChannelWinDict[pname]
		if pgeom:
			self._attrdict['base_winoff'] = pgeom
		else:
			# subwindow was not drawn, draw top-level window.
			pchan._subchannels.remove(self)
			pchan = None
		self.create_window(pchan, pgeom)
		self._is_shown = 1
		self.after_show()

	def do_hide(self):
		if debug:
			print 'ChannelWindow.do_hide('+`self`+')'
		if self.window:
			self.window.unregister(WMEVENTS.ResizeWindow)
			self.window.close()
			self.window = None
			self.armed_display = self.played_display = None

	def resize(self, arg, window, event, value):
		if debug:
			print 'ChannelWindow.resize'+`self,arg,window,event,value`
		windowinterface.setcursor('watch')
		if hasattr(self, 'threads'):
			# hack for MovieChannel
			if hasattr(window, '_gc'):
				window._gc.SetRegion(window._clip)
				window._gc.foreground = window._convert_color(window._bgcolor)
			apply(self.threads.resized, window._rect)
			windowinterface.setcursor('')
			return
		self.replaynode()
		windowinterface.setcursor('')

	def arm_0(self, node):
		same = Channel.arm_0(self, node)
		if same and self.armed_display and \
		   not self.armed_display.is_closed():
		        return 1
		#if same: print 'Same, but no armed_display' # DBG
		if not self._is_shown or not self.window:
			return 0
		if self.armed_display:
			self.armed_display.close()
		bgcolor = self.getbgcolor(node)
		self.armed_display = self.window.newdisplaylist(bgcolor)
		fgcolor = self.getfgcolor(node)
		self.armed_display.fgcolor(fgcolor)
		alist = node.GetRawAttrDef('anchorlist', [])
		armed_anchor = None
		for i in range(len(alist)-1,-1,-1):
			a = alist[i]
			atype = a[A_TYPE]
			if atype == ATYPE_WHOLE:
				if armed_anchor:
					print 'multiple whole-node anchors on node'
				armed_anchor = a
		if armed_anchor:
			self.armed_display.fgcolor(self.getbucolor(node))
			b = self.armed_display.newbutton((0.0, 0.0, 1.0, 1.0))
			b.hiwidth(3)
			b.hicolor(self.gethicolor(node))
			self.armed_display.fgcolor(fgcolor)
			self.setanchor(armed_anchor[A_ID],
				       armed_anchor[A_TYPE], b)
		return 0

	def play(self, node):
		if debug:
			print 'ChannelWindow.play('+`self`+','+`node`+')'
		self.play_0(node)
		if self._is_shown and self.window:
			try:
				winoff = self.winoff
				winoff = MMAttrdefs.getattr(node, 'base_winoff')
			except (AttributeError, KeyError):
				pass
			else:
				if winoff != self.winoff:
					self.hide()
					self.show()
			self.check_popup()
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
			self.do_play(node)
		self.play_1()

	def stopplay(self, node):
		if debug:
			print 'ChannelWindow.stopplay('+`self`+','+`node`+')'
		Channel.stopplay(self, node)
		if self.played_display:
			self.played_display.close()
			self.played_display = None

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

	# use this code to get the error message on top of the window
	# it belongs to (so that a subsequent pop() does not obscure
	# the message).
	def errormsg(self, node, msg):
		if node:
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			nmsg = ' node ' + name
		else:
			nmsg = ''
		windowinterface.showmessage(
			'While arming%s on channel %s:\n%s' %
				(nmsg, self._name, msg),
			mtype = 'warning', grab = self.window)

	def defanchor(self, node, anchor, cb):
		# This method is called when the user defines a new anchor. It
		# may be overridden by derived classes.
		if self.window:
			grab = self.window
		else:
			grab = 1
		windowinterface.showmessage('Channel '+self._name+
			  ' does not support\nediting of anchors (yet)',
					    mtype = 'warning', grab = grab)
		apply(cb, (anchor,))

class _ChannelThread:
	def __init__(self):
		self.threads = None

	def destroy(self):
		del self.threads

	def threadstart(self):
		# This method should be overridden by the superclass.
		# It should be something like
		#	import xxxchannel
		#	return xxxchannel.init()
		raise error, 'threadstart method should be overridden'

	def do_show(self, pchan):
		if debug:
			print 'ChannelThread.do_show('+`self`+')'
		attrdict = {}
		if hasattr(self, 'window'):
			attrdict['rect'] = self.window._rect
			if hasattr(self.window, '_window_id'):
				# GL window interface
				import GLLock
				attrdict['wid'] = self.window._window_id
				attrdict['gl_lock'] = GLLock.gl_rawlock
			elif hasattr(self.window, '_form'):
				# Motif windowinterface
				attrdict['widget'] = self.window._form
				attrdict['gc'] = self.window._gc
				attrdict['visual'] = self.window._topwindow._visual
			elif hasattr(self.window, '_hWnd'):
				# Win32 windowinterface
				attrdict['HWND'] = self.window._hWnd
			else:
				print 'can\' work with this windowinterface'
				return 0
		if self._attrdict.has_key('queuesize'):
			attrdict['queuesize'] = self._attrdict['queuesize']
		try:
			import mm
			self.threads = mm.init(self.threadstart(),
					       self._deviceno, attrdict)
		except ImportError:
			print 'Warning: cannot import mm, so channel ' + \
				  `self._name` + ' remains hidden'
			return 0
		self._player.toplevel.main.setmmcallback(self._deviceno & 0x3f,
			  self._mmcallback)
		return 1

	def do_hide(self):
		if debug:
			print 'ChannelThread.do_hide('+`self`+')'
		if self.threads:
			self.threads.close()
			self.threads = None

	def play(self, node):
		if debug:
			print 'ChannelThread.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		thread_play_called = 0
		if self.threads.armed:
			self.threads.play()
			thread_play_called = 1
		if self._is_shown:
			self.do_play(node)
		self.armdone()
		if not thread_play_called:
			self.playdone(0)

	def playstop(self):
		if debug:
			print 'ChannelThread.playstop('+`self`+')'
		if self._is_shown:
			self.threads.playstop()

	def armstop(self):
		if debug:
			print 'ChannelThread.armstop('+`self`+')'
		if self._is_shown:
			self.threads.armstop()

	def setpaused(self, paused):
		if self._is_shown:
			self.threads.setrate(not paused)

	def stopplay(self, node):
		if self.threads:
			self.threads.finished()

	def callback(self, dummy1, dummy2, event, value):
		if debug:
			print 'ChannelThread.callback'+`self,dummy1,dummy2,event,value`
		if not hasattr(self, '_name'):
			# already destroyed
			return
		import mm
		if value == mm.playdone:
			if self._playstate == PLAYING:
				self.playdone(0)
			elif self._playstate != PIDLE:
				raise error, 'playdone event when not playing'
		elif value == mm.armdone:
			if self._armstate == ARMING:
				self.arm_1()
			elif self._armstate != AIDLE:
				raise error, 'armdone event when not arming'
		elif value == 3:	# KLUDGE for X movies
			try:
				self.window._gc.SetRegion(self.window._clip)
				self.threads.do_display()
			except AttributeError:
				pass
		else:
			raise error, 'unrecognized event '+`value`

	def _mmcallback(self, val):
		self.callback(0, 0, 0, val)

class ChannelThread(_ChannelThread, Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		_ChannelThread.__init__(self)

	def destroy(self):
		Channel.destroy(self)
		_ChannelThread.destroy(self)

	def playstop(self):
		_ChannelThread.playstop(self)
		Channel.playstop(self)

	def armstop(self):
		_ChannelThread.armstop(self)
		Channel.armstop(self)

	def stopplay(self, node):
		Channel.stopplay(self, node)
		_ChannelThread.stopplay(self, node)

	def setpaused(self, paused):
		Channel.setpaused(self, paused)
		_ChannelThread.setpaused(self, paused)

class ChannelWindowThread(_ChannelThread, ChannelWindow):
	def __init__(self, name, attrdict, scheduler, ui):
		import GLLock
		windowinterface.usewindowlock(GLLock.gl_lock)
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		_ChannelThread.__init__(self)

	def destroy(self):
		ChannelWindow.destroy(self)
		_ChannelThread.destroy(self)

	def do_show(self, pchan):
		if ChannelWindow.do_show(self, pchan):
			if _ChannelThread.do_show(self, pchan):
				return 1
			ChannelWindow.do_hide(self)
		return 0

	def do_hide(self):
		self.window.setredrawfunc(None)
		_ChannelThread.do_hide(self)
		ChannelWindow.do_hide(self)

	def playstop(self):
		import GLLock
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.release()
		_ChannelThread.playstop(self)
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.acquire()
		ChannelWindow.playstop(self)

	def armstop(self):
		import GLLock
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.release()
		_ChannelThread.armstop(self)
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.acquire()
		ChannelWindow.armstop(self)

	def stopplay(self, node):
		w = self.window
		if w:
			w.setredrawfunc(None)
##		ChannelWindow.stopplay(self, node)
		Channel.stopplay(self, node)   # These 2 lines repl prev.
		self.played_display = None
		if hasattr(w, '_gc'):
			w._gc.SetRegion(w._clip)
			w._gc.foreground = w._convert_color(w._bgcolor)
		_ChannelThread.stopplay(self, node)

	def setpaused(self, paused):
		ChannelWindow.setpaused(self, paused)
		_ChannelThread.setpaused(self, paused)

	def play(self, node):
		if debug:
			print 'ChannelWindowThread.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		self.check_popup()
		if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
#		else:
#			self.armed_display.render()
#		if self.played_display:
#			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		thread_play_called = 0
		if self.threads.armed:
			w = self.window
			w.setredrawfunc(self.do_redraw)
			try:
				w._gc.SetRegion(w._clip)
				w._gc.foreground = w._convert_color(self.getbgcolor(node))
			except AttributeError:
				pass
			self.threads.play()
			thread_play_called = 1
		if self._is_shown:
			self.do_play(node)
		self.armdone()
		if not thread_play_called:
			self.playdone(0)

	def do_redraw(self):
		w = self.window
		w._gc.SetRegion(w._clip)
		w._gc.foreground = w._convert_color(w._bgcolor)
		apply(self.threads.resized, w._rect)
		
class ChannelAsync(Channel):

	def play(self, node):
		if debug:
			print 'ChannelAsync.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		if self._is_shown:
			self.do_play(node)
		self.armdone()

class ChannelWindowAsync(ChannelWindow):
	def play(self, node):
		if debug:
			print 'ChannelWindowAsync.play('+`self`+','+`node`+')'
		self.play_0(node)
		if self._is_shown and self.window and not self.syncplay:
			try:
				winoff = self.winoff
				winoff = MMAttrdefs.getattr(node, 'base_winoff')
			except (AttributeError, KeyError):
				pass
			else:
				if winoff != self.winoff:
					self.hide()
					self.show()
			self.check_popup()
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
			self.do_play(node)
			self.armdone()
		else:
			self.play_1()
		
def dummy_callback(arg):
	pass

class AnchorContext:
	def arm_done(self, node):
		raise error, 'AnchorContext.arm_done() called'

	def arm_ready(self, channel):
		raise error, 'AnchorContext.arm_ready() called'

	def anchorfired(self, node, anchorlist, arg):
		raise error, 'AnchorContext.anchorfired() called'

	def play_done(self, node):
		raise error, 'AnchorContext.play_done() called'

# cleanup temporary files when we finish
windowinterface.addclosecallback(MMurl.urlcleanup, ())
