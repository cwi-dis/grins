__version__ = "$Id$"

# Player module -- mostly defines the Player class.


from Scheduler import del_timing
from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
from ViewDialog import ViewDialog
import Timing
import windowinterface, WMEVENTS
from usercmd import *

# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

from PlayerDialog import *

class Player(ViewDialog, PlayerCore, PlayerDialog):
	#
	# Initialization.
	#
	def __init__(self, toplevel):
		self.updateuibaglist = self.dummy_updateuibaglist
		ViewDialog.__init__(self, 'player_')
		self.playing = self.pausing = self.locked = 0
		PlayerCore.__init__(self, toplevel)
		self.load_geometry()
		PlayerDialog.__init__(self, self.last_geometry,
				      'Player (' + toplevel.basename + ')')
		self.channelnames = []
		self.measure_armtimes = 0
		self.channels = {}
		self.channeltypes = {}
		self.seeking = 0
		self.seek_node = None
		self.seek_nodelist = []
		self.ignore_delays = 0
		self.ignore_pauses = 0
		self.play_all_bags = 0
		self.pause_minidoc = 1
		self.sync_cv = 1
		self.toplevel = toplevel
		self.showing = 0
		self.waiting = 0
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback
		self.commandlist = [
			CLOSE_WINDOW(callback = (self.close_callback, ()),
				     help = 'Close the Player View'),
			CHANNELS(callback = self.channel_callback),
			CALCTIMING(callback = (self.timing_callback, ())),
			SCHEDDUMP(callback = (self.scheduler.dump, ())),
			SYNCCV(callbac = (self.synccv_callback, ())),
			]
		play = PLAY(callback = (self.play_callback, ()))
		pause = PAUSE(callback = (self.pause_callback, ()))
		stop = STOP(callback = (self.stop_callback, ()))
		self.stoplist = self.commandlist + [
			# when stopped, we can play and pause
			play,
			pause,
			]
		self.playlist = self.commandlist + [
			# when playing, we can pause and stop
			pause,
			stop,
			]
		self.pauselist = self.commandlist + [
			# when pausing, we can continue (play or
			# pause) and stop
			play,
			pause,
			stop,
			]

	def destroy(self):
		if not hasattr(self, 'toplevel'):
			# already destroyed
			return
		self.hide()
		self.close()
		del self.channelnames
		del self.channels
		del self.channeltypes
		del self.seek_node
		del self.seek_nodelist
		del self.toplevel
		del self.set_timer
		del self.timer_callback
		del self.commandlist
		del self.stoplist
		del self.playlist
		del self.pauselist
		del self.updateuibaglist

	def fixtitle(self):
		self.settitle('Player (' + self.toplevel.basename + ')')

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
		self.toplevel.showstate(self, 1)
		self.makechannels()
		self.fullreset()
		self.toplevel.checkviews()
		PlayerDialog.show(self)
		self.showing = 1
		self.showchannels()
		self.showstate()

	def hide(self, *rest):
		if not self.showing: return
		self.showing = 0
		self.toplevel.showstate(self, 0)
		self.stop()
		self.fullreset()
		self.save_geometry()
		PlayerDialog.hide(self)
		self.toplevel.checkviews()
		self.destroychannels()

	def save_geometry(self):
		ViewDialog.save_geometry(self)
		for name in self.channelnames:
			self.channels[name].save_geometry()

	def get_geometry(self):
		geometry = self.getgeometry()
		if geometry is not None:
			self.last_geometry = geometry

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

	def stop_callback(self):
		self.toplevel.setwaiting()
		self.cc_stop()
		self.toplevel.setready()

	def close_callback(self):
		self.hide()

	def channel_callback(self, name):
		self.toplevel.setwaiting()
		isvis = self.channels[name].may_show()
		self.cc_enable_ch(name, (not isvis))
		self.toplevel.setready()

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
		self.toplevel.channelview.channels_changed()
		self.setchannel(name, onoff)

	def timing_callback(self):
		self.measure_armtimes = (not self.measure_armtimes)
		if self.measure_armtimes:
			del_timing(self.root)
			Timing.changedtimes(self.root)

	def synccv_callback(self):
		self.sync_cv = (not self.sync_cv)

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

	def dummy_updateuibaglist(self):
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

	def setready(self):
		self.waiting = 0
		for cname in self.channelnames:
			self.channels[cname].setready()
		self.setcursor('')
