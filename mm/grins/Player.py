__version__ = "$Id$"

# Player module -- mostly defines the Player class.


from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
import windowinterface, WMEVENTS
from usercmd import *

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
		self.showing = 0
		self.channelnames = []
		self.channels = {}
		self.channeltypes = {}
		self.toplevel = toplevel
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback
		self.userstarttime = 0
		self.commandlist = [
			CHANNELS(callback = self.channel_callback),
			MAGIC_PLAY(callback = (self.magic_play, ())),
			]
		if __debug__:
			self.commandlist.append(
				SCHEDDUMP(callback = (self.scheduler.dump, ())))

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
		self.alllist = self.pauselist
		self.cssResolver = self.context.cssResolver
		self._exporter = None # Bad, bad hack.
	
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
		del self.commandlist
		del self.stoplist
		del self.playlist
		del self.pauselist

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
		PlayerDialog.preshow(self)
		self.aftershow = afterfunc
		self.makechannels()
		self.fullreset()
		self.showing = 1
		self.showchannels()
		PlayerDialog.show(self)
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
		winsize = MMAttrdefs.getattr(self.root, 'player_winsize')
		width, height = winsize or (640, 480)
		return h, v, width, height

	def after_chan_show(self, chan = None):
		PlayerDialog.after_chan_show(self, chan)
		PlayerCore.after_chan_show(self, chan)

	#
	# FORMS callbacks.
	#
	def play_callback(self):
		self.toplevel.setwaiting()
		# RTIPA start
		import features
		if hasattr(features, 'RTIPA') and features.RTIPA:
			import settings
			settings.read_RTIPA()
		# RTIPA end
		if self.playing and self.pausing:
			# Case 1: user pressed play to cancel pause
			self.pause(0)
		elif not self.playing:
			# Case 2: starting to play from stopped mode
			self.play(self.userstarttime)
			self.userstarttime = 0
		else:
			# nothing, restore state.
			self.showstate()

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

	def stop_callback(self):
		self.toplevel.setwaiting()
		self.userstarttime = 0
		self.cc_stop()

	def magic_play(self):
		if self.playing:
			# toggle pause if playing
			self.pause_callback()
		else:
			# start playing if stopped
			self.play_callback()

	def channel_callback(self, name):
		import settings
		if settings.get('cmif'):
			# In CMIF mode hide only this single channel
			self.toplevel.setwaiting()
			isvis = self.channels[name].may_show()
			self.cc_enable_ch(name, (not isvis))
		else:
			# In SMIL mode simply close the player
			self.hide()

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
		self.setchannel(name, onoff)

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

	def isplaying(self):
		return self.playing

	def setstarttime(self, gototime):
		if self.playing:
			if not self.pausing:
				self.pause(1)
			timestamp = self.scheduler.timefunc()
			sctx = self.scheduler.sctx_list[0]
			self.scheduler.settime(gototime)
			sctx.gototime(self.userplayroot, gototime, timestamp)
		else:
			self.userstarttime = gototime

	def makemenu(self):
		channels = []
		for name in self.channelnames:
			channels.append((name, self.channels[name].is_showing()))
		channels.sort()
		self.setchannels(channels)
