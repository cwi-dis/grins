# Channels should either use Channel, ChannelWindow, or ChannelThread
# as a superclass, but never more than one.

from AnchorDefs import *
from debug import debug
import MMAttrdefs
##import events
error = 'Channel.error'

channel_device = 0x4001

# arm states
AIDLE = 1
ARMING = 2
ARMED = 3
# play states
PIDLE = 1
PLAYING = 2
PLAYED = 3

class Channel():
	#
	# The following methods can be called by higher levels.
	#
	chan_attrs = []
	node_attrs = ['file']

	def init(self, name, attrdict, scheduler, ui):
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
		self._playcontext = None
		self._played_anchors = []
		self._played_node = None
		self._player = ui
		self._playstate = PIDLE
		self._qid = None
		self._scheduler = scheduler
		self._paused = 1
		self.syncarm = 0
		self.syncplay = 0
		if debug:
			print 'Channel.init() -> '+`self`
		return self

	def __repr__(self):
		return '<Channel instance, name=' + `self._name` + '>'

	def destroy(self):
		# Destroy this instance of a Channel object.  This
		# will stop playing and arming on this channel and
		# release all used resources.  After this, none of the
		# methods of this instance may be called anymore.
		if debug:
			print 'Channel.destroy('+`self`+')'
		if self.is_showing():
			self.hide()
		del self._armcontext
		del self._armed_anchors
		del self._armed_node
		del self._armstate
		del self._attrdict
		del self._deviceno
		del self._is_shown
		del self._name
		del self._playcontext
		del self._played_anchors
		del self._played_node
		del self._player
		del self._playstate
		del self._qid
		del self._scheduler

	def may_show(self):
		# Indicate to the higher level whether this channel is
		# visible and may be shown.
		if not self._attrdict.has_key('visible'):
			return 1
		else:
			return self._attrdict['visible']

	def show(self):
		# Indicate that the channel must enter the SHOWN
		# state.
		if debug:
			print 'Channel.show('+`self`+')'
		if self._is_shown:
			return
		self._is_shown = 1
		if not self.do_show():
			self._is_shown = 0
			return
		# Since the calls to arm() and play() lied to the
		# scheduler when the channel was hidden, we must do a
		# few things so that the real state of things is once
		# again in accordance with what the scheduler thinks.
		# First wait for any outstanding arms so that the
		# armedstate is either AIDLE or ARMED but not ARMING.
		self.wait_for_arm()
		# Now we should replay the node that was played when
		# we were hidden.  This means that we must arm the
		# node first.  This in turn means that we must save
		# the information about the node that is armed
		# currently.
		armstate = self._armstate
		armed_node = self._armed_node
		# Don't do anything if the channel is PLAYING.  That
		# will change in due time and it is too hard to do
		# something about it here.
		if self._playstate == PLAYED:
			node = self._played_node
			self._armstate = AIDLE
			self.syncarm = 1
			self.arm(node)
			self._playstate = PIDLE
			self.armed_duration = 0
			self.syncplay = 1
			self.play(node)
			self._armstate = AIDLE
		if armstate == ARMED:
			self._armstate = AIDLE
			self.syncarm = 1
			dummy = self.arm(armed_node)
		if self._armstate != armstate:
			# maybe we should do something, but what?
			raise error, 'don\'t know if this can happen'
		self.syncarm = 0
		self.syncplay = 0

	def hide(self):
		# Indicate that the channel must enter the HIDDEN
		# state.
		if debug:
			print 'Channel.hide('+`self`+')'
		if not self._is_shown:
			return
		self._is_shown = 0
		self.do_hide()
		if self._armstate == ARMING:
			self.arm_1()
		if self._playstate == PLAYING:
			self.playstop()

	def pause(self):
		# Pause playing the current node.
		# Not yet implemented.
		if debug:
			print 'Channel.pause('+`self`+')'
		pass

	#
	# Methods called by CMIFed.
	#
	def check_visible(self):
		if self.may_show():
			self.show()
		else:
			self.hide()

	def setwaiting(self):
		pass
	def setready(self):
		pass
	def flip_visible(self):
		if self._attrdict.has_key('visible'):
			visible = self._attrdict['visible']
		else:
			visible = 1
		visible = (not visible)
		self._attrdict['visible'] = visible
		if visible:
			self.show()
		else:
			self.hide()
	def save_geometry(self):
		pass
	#
	# Methods used internally and by superclasses.
	#
	def is_showing(self):
		# Indicate whether the channel is being shown.
		return self._is_shown

	def do_show(self):
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
		self._armstate = ARMING
		self._armed_node = node
		self._armed_anchors = []
		self.armed_duration = self.getduration(node)

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
		self._armed_node = None

	def wait_for_arm(self):
		# Wait until the arm state is either AIDLE or ARMED so
		# that we don't get any asynchronous events that tell
		# us that arming finished.
		while self._armstate not in (AIDLE, ARMED):
			if not self._player.toplevel.waitevent():
				return

	def pause_triggered(self, node, anchorlist):
		# Callback which is called when the button of a pause
		# anchor is pressed.
		# If the anchor didn't fire, we're done playing the
		# node.
		if self._playstate == PLAYED:
			# someone pushed the button again, I guess
			return
		if not self._playcontext.anchorfired(node, anchorlist):
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
			self.playdone(None)

	def play_0(self, node):
		# This does the initial part of playing a node.
		# Superclasses should call this method when they are
		# starting to play a node.
		# If callback is `None', make sure we don't do any
		# callbacks.
		if debug:
			print 'Channel.play_0('+`self`+','+`node`+')'
		if self._armed_node != node:
			raise error, 'node was not the armed node '+`self,node`
		if self._playstate != PIDLE:
			raise error, 'play not idle'
		if self._armstate != ARMED:
			raise error, 'arm not ready'
		self._playcontext = self._armcontext
		self._playstate = PLAYING
		self._played_node = node
		for (name, type, button) in self._played_anchors:
			self._player.del_anchor(button)
		self._played_anchors = self._armed_anchors
		self._armed_anchors = []
		self._has_pause = 0
		for (name, type, button) in self._played_anchors:
			if type == ATYPE_PAUSE:
##				print 'found pause anchor'
				f = self.pause_triggered
				self._has_pause = 1
			else:
				f = self._playcontext.anchorfired
			self._player.add_anchor(button, f, \
				  (node, [(name, type)]))
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
		if self.armed_duration > 0:
			self._qid = self._scheduler.enter(self.armed_duration,\
				  0, self.playdone, 0)
		else:
			self.playdone(0)
		self.armdone()

	def playdone(self, dummy):
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
			raise error, 'not playing'
		self._qid = None
		# If this node has a pausing anchor, don't call the
		# callback just yet but wait till the anchor is hit.
		if self._has_pause:
			return
		if not self.syncplay:
			self._playcontext.play_done(self._played_node)
		self._playstate = PLAYED

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
		self.playdone(0)

	def do_arm(self, node):
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
		# Superclasses should define a method do_arm to do the
		# actual arming.  Do_arm should return 1
		# When arming is done, callback should be called with
		# the given arg.
		# Do_arm() is called to do the actual arming.  If it
		# returns 0, we should not call arm_1() because that
		# will happen later.
		self.arm_0(node)
		if self.is_showing() and not self.do_arm(node):
			return
		self.arm_1()

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
		self.do_play(node)
		self.play_1()

	def stopplay(self, node):
		# Indicate that the channel can revert from the
		# PLAYING or PLAYED state to PIDLE.
		# Node is only passed to do consistency checking.
		if debug:
			print 'Channel.stopplay('+`self`+','+`node`+')'
		if node and self._played_node != node:
			raise error, 'node was not the playing node '+`self,node,self._played_node`
		if self._playstate == PLAYING:
			self._has_pause = 0
			self.playstop()
		if self._playstate != PLAYED:
			raise error, 'not played'

		self._playstate = PIDLE

	def stoparm(self):
		# Indicate that the channel can revert from the
		# ARMING or ARMED state to AIDLE.
		if debug:
			print 'Channel.stoparm('+`self`+')'
		if self._armstate == ARMING:
			self.armstop()
		if self._armstate != ARMED:
			raise error, 'not armed'
		self._armstate = AIDLE

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
		if self._armcontext and self._armcontext != self._playcontext:
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
		if not ctx in (self._playcontext, self._armcontext):
			raise error, 'stopcontext with unknown context'
		if self._playcontext == ctx:
			if self._playstate in (PLAYING, PLAYED):
				self.stopplay(None)
			self._playcontext = None
		if self._armcontext == ctx:
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

	def getfilename(self, node):
		return node.context.findfile(MMAttrdefs.getattr(node, 'file'))

	def getduration(self, node):
		import Duration
		return Duration.get(node)

	def getbgcolor(self, node):
		return MMAttrdefs.getattr(node, 'bgcolor')

	def getfgcolor(self, node):
		return MMAttrdefs.getattr(node, 'fgcolor')

	def gethicolor(self, node):
		return MMAttrdefs.getattr(node, 'hicolor')

# dictionary with channels that have windows
ChannelWinDict = {}

class ChannelWindow(Channel):
	chan_attrs = Channel.chan_attrs + ['base_window', 'base_winoff']
	node_attrs = Channel.node_attrs + ['duration', 'bgcolor', 'hicolor']

	def init(self, name, attrdict, scheduler, ui):
		self = Channel.init(self, name, attrdict, scheduler, ui)
		ChannelWinDict[self._name] = self
		self.window = None
		self.armed_display = self.played_display = None
		return self

	def __repr__(self):
		return '<ChannelWindow instance, name=' + `self._name` + '>'

	def destroy(self):
		Channel.destroy(self)
		del self.window
		del self.armed_display
		del self.played_display

	def do_show(self):
		if debug:
			print 'ChannelWindow.do_show('+`self`+')'
		# create a window for this channel
		pgeom = None
		pchan = None
		if self._attrdict.has_key('base_window'):
			# there is a base window, create a subwindow
			pname = self._attrdict['base_window']
			if ChannelWinDict.has_key(pname):
				pchan = ChannelWinDict[pname]
			else:
				raise error, \
					  'base window '+`pname`+' for '+\
					  `self._name`+' not found'
			if self._attrdict.has_key('base_winoff'):
				pgeom = self._attrdict['base_winoff']
			else:
				raise error, 'no geometry for '+`self._name`
			if not pchan.window:
				pchan.show()
			if not pchan.window:
				raise error, 'parent window for ' + \
					  `self._name` + ' not shown'
			self.window = pchan.window.newwindow(pgeom)
		else:
			# no basewindow, create a top-level window
			if self._attrdict.has_key('winsize'):
				width, height = self._attrdict['winsize']
			else:
				raise error, \
					  'no size specified for '+`self._name`
			if self._attrdict.has_key('winpos'):
				x, y = self._attrdict['winpos']
			else:
				raise error, \
					  'no position specified for '+\
					  `self._name`
			import windowinterface
			self.window = windowinterface.newwindow(x, y, \
				  width, height, self._name)
		if self._attrdict.has_key('bgcolor'):
			self.window.bgcolor(self._attrdict['bgcolor'])
		if self._attrdict.has_key('fgcolor'):
			self.window.fgcolor(self._attrdict['fgcolor'])
		return 1

	def do_hide(self):
		if debug:
			print 'ChannelWindow.do_hide('+`self`+')'
		if self.window:
			self.window.close()
			self.window = None
			self.armed_display = self.played_display = None

	def arm_0(self, node):
		Channel.arm_0(self, node)
		if not self.is_showing():
			return
		if self.armed_display:
			self.armed_display.close()
		bgcolor = self.getbgcolor(node)
		self.armed_display = self.window.newdisplaylist(bgcolor)
		self.armed_display.fgcolor(self.getfgcolor(node))

	def play(self, node):
		if debug:
			print 'ChannelWindow.play('+`self`+','+`node`+')'
		self.play_0(node)
		if self.is_showing():
			self.window.pop()
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

	def save_geometry(self):
		if self.is_showing():
			x, y, w, h = self.window.getgeometry()
			self._attrdict['winpos'] = x, y
			self._attrdict['winsize'] = w, h

class _ChannelThread():
	def init(self):
		self.threads = None
		return self

	def destroy(self):
		del self.threads

	def threadstart(self):
		# This method should be overridden by the superclass.
		# It should be something like
		#	import xxxchannel
		#	return xxxchannel.init()
		raise error, 'threadstart method should be overridden'

	def do_show(self):
		if debug:
			print 'ChannelThread.do_show('+`self`+')'
		try:
			import mm
			self.threads = mm.init(self.threadstart(), 0, \
				  self._deviceno, None)
		except ImportError:
			print 'Warning: cannot import mm, so channel ' + \
				  `self._name` + ' remains hidden'
			return 0
##		events.setcallback(self._deviceno, self.callback, None)
		import glwindow
		glwindow.devregister(`self._deviceno`+':'+`mm.playdone`, \
			  self._playdone, None)
		glwindow.devregister(`self._deviceno`+':'+`mm.armdone`, \
			  self._armdone, None)
		return 1

	def _playdone(self, dummy):
		if self._playstate == PLAYING:
			self.playdone(None)

	def _armdone(self, dummy):
		if self._armstate == ARMING:
			self.arm_1()

	def do_hide(self):
		if debug:
			print 'ChannelThread.do_hide('+`self`+')'
		if self.threads:
			self.threads.close()
			self.threads = None
##		events.setcallback(self._deviceno, None, None)

	def play(self, node):
		if debug:
			print 'ChannelThread.play('+`self`+','+`node`+')'
##		dummy = events.testevent()
		self.play_0(node)
		if not self.is_showing() or self.syncplay:
			self.play_1()
			return
		self.threads.play()
		self.do_play(node)
		self.armdone()

	def playstop(self):
		if debug:
			print 'ChannelThread.playstop('+`self`+')'
		if self.is_showing():
			self.threads.playstop()

	def armstop(self):
		if debug:
			print 'ChannelThread.armstop('+`self`+')'
		if self.is_showing():
			self.threads.armstop()

	def setpaused(self, paused):
		if self.is_showing():
			self.threads.setrate(not paused)

	def callback(self, dummy1, dummy2, event, value):
		if debug:
			print 'ChannelThread.callback'+`self,dummy1,dummy2,event,value`
		import mm
		if value == mm.playdone:
			if self._playstate == PLAYING:
				self.playdone(None)
			elif self._playstate != PIDLE:
				raise error, 'playdone event when not playing'
		elif value == mm.armdone:
			if self._armstate == ARMING:
				self.arm_1()
			elif self._armstate != AIDLE:
				raise error, 'armdone event when not arming'
		else:
			raise error, 'unrecognized event '+`value`

class ChannelThread(_ChannelThread, Channel):
	def init(self, name, attrdict, scheduler, ui):
		self = Channel.init(self, name, attrdict, scheduler, ui)
		self = _ChannelThread.init(self)
		return self

	def __repr__(self):
		return '<ChannelThread instance, name=' + `self._name` + '>'

	def destroy(self):
		Channel.destroy(self)
		_ChannelThread.destroy(self)

	def playstop(self):
		_ChannelThread.playstop(self)
		Channel.playstop(self)

	def armstop(self):
		_ChannelThread.armstop(self)
		Channel.armstop(self)

	def setpaused(self, paused):
		Channel.setpaused(self, paused)
		_ChannelThread.setpaused(self, paused)

class ChannelWindowThread(_ChannelThread, ChannelWindow):
	def init(self, name, attrdict, scheduler, ui):
		import GLLock, windowinterface
		windowinterface.usewindowlock(GLLock.gl_lock)
		self = ChannelWindow.init(self, name, attrdict, scheduler, ui)
		self = _ChannelThread.init(self)
		return self

	def __repr__(self):
		return '<ChannelWindowThread instance, name=' + `self._name` + '>'

	def destroy(self):
		ChannelWindow.destroy(self)
		_ChannelThread.destroy(self)

	def do_show(self):
		if ChannelWindow.do_show(self):
			if _ChannelThread.do_show(self):
				return 1
			ChannelWindow.do_hide(self)
		return 0

	def do_hide(self):
		_ChannelThread.do_hide(self)
		ChannelWindow.do_hide(self)

	def playstop(self):
		_ChannelThread.playstop(self)
		ChannelWindow.playstop(self)

	def armstop(self):
		_ChannelThread.armstop(self)
		ChannelWindow.armstop(self)

	def setpaused(self, paused):
		ChannelWindow.setpaused(self, paused)
		_ChannelThread.setpaused(self, paused)

	def play(self, node):
		if debug:
			print 'ChannelWindowThread.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self.is_showing() or self.syncplay:
			self.play_1()
			return
		self.window.pop()
		self.armed_display.render()
		if self.played_display:
			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		self.threads.play()
		self.armdone()

def dummy_callback(arg):
	pass
