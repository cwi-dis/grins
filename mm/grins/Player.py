__version__ = "$Id$"

# Player module -- mostly defines the Player class.


from Scheduler import del_timing
from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
import Timing
import windowinterface, WMEVENTS

BLACK = 0, 0, 0
GREY = 100, 100, 100
GREEN = 0, 255, 0
YELLOW = 255, 255, 0
BGCOLOR = 200, 200, 200
FOCUSLEFT = 244, 244, 244
FOCUSTOP = 204, 204, 204
FOCUSRIGHT = 40, 40, 40
FOCUSBOTTOM = 91, 91, 91

##titles = ['Channels', 'Options', 'Run slots']
titles = ['Channels', 'Close']

# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

from PlayerDialog import *

class Player(PlayerCore, PlayerDialog):
	#
	# Initialization.
	#
	def __init__(self, toplevel):
		self.playing = self.pausing = self.locked = 0
		PlayerCore.__init__(self, toplevel)
		PlayerDialog.__init__(self, self.get_geometry(),
				      'Player (' + toplevel.basename + ')')
		self.channelnames = []
		self.channels = {}
		self.channeltypes = {}
		self.sync_cv = 0
		self.toplevel = toplevel
		self.showing = 0
		self.waiting = 0
		self.source = None
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback

	def destroy(self):
		if not hasattr(self, 'toplevel'):
			# already destroyed
			return
		self.hide()
		self.close()
		del self.channelnames
		del self.channels
		del self.channeltypes
		del self.toplevel
		del self.set_timer
		del self.timer_callback
		if self.source is not None:
			self.source.close()
		del self.source

	def __repr__(self):
		return '<Player instance, root=' + `self.root` + '>'
	#
	# Extend BasicDialog show/hide/destroy methods.
	#
	def is_showing(self):
		return self.showing

	def show(self, afterfunc = None):
		if self.is_showing():
			PlayerDialog.show(self)
			if afterfunc is not None:
				apply(afterfunc[0], afterfunc[1])
			return
		self.aftershow = afterfunc
		self.makechannels()
		if hasattr(self.root, 'source'):
			self.setoptions(['Source...'])
		self.fullreset()
		PlayerDialog.show(self)
		self.showing = 1
		self.showchannels()
		self.showstate()

	def hide(self):
		if not self.showing: return
		self.showing = 0
		self.stop()
		self.fullreset()
		PlayerDialog.hide(self)
		self.destroychannels()

	def get_geometry(self):
		h, v = self.root.GetRawAttrDef('player_winpos', (None, None))
		width, height = MMAttrdefs.getattr(self.root, 'player_winsize')
		return h, v, width, height

	#
	# FORMS callbacks.
	#
	def play_callback(self):
		self.toplevel.setwaiting()
		if self.playing and self.pausing:
			# Case 1: user pressed play to cancel pause
			self.pause(0)
		elif not self.playing:
			# Case 2: starting to play from stopped mode
			self.play()
		else:
			# nothing, restore state.
			self.showstate()
		self.toplevel.setready()

	def pause_callback(self):
		self.toplevel.setwaiting()
		if self.playing and self.pausing:
			# Case 1: press pause to cancel pause
			self.pause(0)
		elif self.playing:
			# Case 2: press pause to pause
			self.pause(1)
		else:
			# Case 3: not playing. Go to paused mode
			self.pause(1)
			self.play()
		self.toplevel.setready()
	#
	def stop_callback(self):
		self.toplevel.setwaiting()
		self.cc_stop()
		self.toplevel.setready()

	def close_callback(self):
		self.toplevel.close_callback()

	def channel_callback(self, name):
		self.toplevel.setwaiting()
		isvis = self.channels[name].may_show()
		self.cc_enable_ch(name, (not isvis))
		self.toplevel.setready()

	def option_callback(self, option):
		if option == 'Source...':
			self.source_callback()

	def source_callback(self):
		if self.source is not None and not self.source.is_closed():
			self.source.show()
			return
		self.source = windowinterface.textwindow(self.root.source)

	def cc_stop(self):
		self.stop()
		if self.pausing:
			self.pause(0)

	def cc_enable_ch(self, name, onoff):
		try:
			ch = self.channels[name]
		except KeyError:
			windowinterface.showmessage('No such channel: '+name)
			return
		ch.set_visible(onoff)
		self.makemenu()

	def showstate(self):
		if not self.is_showing():
			return
		if self.playing:
			if self.pausing:
				state = PAUSING
			else:
				state = PLAYING
		else:
			state = STOPPED
		self.setstate(state)

	def showpauseanchor(self, pausing):
		if pausing:
			state = PAUSING
		else:
			state = PLAYING
		self.setstate(state)

	def updateuibaglist(self):
		pass

	def makemenu(self):
		channels = []
		for name in self.channelnames:
			channels.append((name, self.channels[name].is_showing()))
		channels.sort()
		self.setchannels(channels)

	def setwaiting(self):
		self.waiting = 1
		self.setcursor('watch')
		for cname in self.channelnames:
			self.channels[cname].setwaiting()
	#
	def setready(self):
		self.waiting = 0
		for cname in self.channelnames:
			self.channels[cname].setready()
		self.setcursor('')
