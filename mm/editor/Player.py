# Player module -- mostly defines the Player class.


import gl
import GL
import fl
from FL import *
import flp
from Scheduler import del_timing
from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
from Dialog import BasicDialog
from ViewDialog import ViewDialog
import Timing


# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

class Player(ViewDialog, BasicDialog, PlayerCore):
	#
	# Initialization.
	#
	def init(self, toplevel):
		self = ViewDialog.init(self, 'player_')
		self = PlayerCore.init(self, toplevel)
		self.queue = []
		self.resettimer()
		self.setcurrenttime_callback = None
		self.playing = self.locked = 0
		self.channelnames = []
		self.measure_armtimes = 0
		self.channels = {}
		self.channeltypes = {}
		self.timing_changed = 0
		self.ff = 0
		self.seeking = 0
		self.seek_node = None
		self.seek_nodelist = []
		return BasicDialog.init(self, 0, 0, 'Player')
	#
	def __repr__(self):
		return '<Player instance, root=' + `self.root` + '>'
	#
	# Extend BasicDialog show/hide/destroy methods.
	#
	def show(self):
		if self.is_showing():
			self.pop()
			return
		self.makechannels()
		self.fullreset()
		BasicDialog.show(self)
		self.toplevel.checkviews()
		self.showchannels()
		self.showstate()
	#
	def hide(self):
		if not self.showing: return
		self.stop()
		self.fullreset()
		BasicDialog.hide(self)
		self.toplevel.checkviews()
		self.destroychannels()
	#
	def save_geometry(self):
		ViewDialog.save_geometry(self)
		for name in self.channelnames:
			self.channels[name].save_geometry()
	#
	def set_setcurrenttime_callback(self, setcurrenttime):
		self.setcurrenttime_callback = setcurrenttime
	#
	def make_form(self):
		ftemplate = flp.parse_form('PlayerForm', 'form')
		flp.create_full_form(self, ftemplate)
		self.speedbutton.set_counter_value(1)
		self.speedbutton.set_counter_bounds(1,128)
		self.speedbutton.set_counter_step(1,1)
		
	#
	# FORMS callbacks.
	#
	def play_callback(self, (obj, arg)):
		self.play()
	#
	def pause_callback(self, (obj, arg)):
		self.pause()
	#
	def stop_callback(self, (obj, arg)):
		self.stop()
	#
	def speed_callback(self, (obj, arg)):
		self.oldrate = obj.get_counter_value()
		if self.playing:
			self.setrate(self.oldrate)
		self.showstate()
	#
	def menu_callback(self, (obj, arg)):
		i = self.menubutton.get_menu() - 1
		if 0 <= i < len(self.channelnames):
			name = self.channelnames[i]
			#if self.channels[name].is_showing():
			#	self.channels[name].hide()
			#else:
			#	self.channels[name].show()
			self.channels[name].flip_visible()
			self.makemenu()
	#
	def calctiming_callback(self, (obj, arg)):
		if obj.get_button() or 1:
			del_timing(self.root)
			Timing.changedtimes(self.root)
			self.measure_armtimes = 1
			obj.set_button(1)
	#
	def ff_callback(self, (obj, arg)):
		#print 'Player:', self.queue # DBG
		if not self.playing:
			obj.set_button(not obj.get_button())
			return
		self.ff = obj.get_button()
		self.updatetimer()
	#
	def dummy_callback(self, dummy):
		pass
	#
	def timer_callback(self, (obj, arg)):
		gap = None
		while self.queue:
			when, prio, action, argument = self.queue[0]
			now = self.timefunc()
			delay = when - now
			if delay < -0.1:
				self.late_ind.lcol = GL.RED
				self.latecount = self.latecount - delay
				self.late_ind.label = `int(self.latecount)`
			else:
				self.late_ind.lcol = self.late_ind.col2
			if delay > 0.0:
				break
			del self.queue[0]
			void = apply(action, argument)
##		if not self.queue and self.rate > 0.0:
##			print 'Player: Huh? Nothing in the queue?'
		if not self.queue or self.rate == 0.0:
			delay = 10000.0		# Infinite
			now = self.timefunc()
		rtevent = self.rtpool.bestfit(now, delay)
		if rtevent:
			dummy, dummy2, action, argument = rtevent
			dummy = apply(action, argument)
		self.updatetimer()
		self.showtime()
	#
	def showstate(self):
		self.ffbutton.set_button(self.ff)
		if not self.playing:
			self.playbutton.set_button(0)
			self.pausebutton.set_button(0)
			self.stopbutton.set_button(1)
			self.speedbutton.set_counter_value(self.oldrate)
		else:
			self.stopbutton.set_button(0)
			self.playbutton.set_button(self.rate >= 1.0)
			self.pausebutton.set_button(0.0 == self.rate)
			self.speedbutton.set_counter_value(self.oldrate)
		if self.userplayroot is self.root:
			self.partbutton.label = ''
		else:
			name = MMAttrdefs.getattr(self.userplayroot, 'name')
			if name == '':
				label = 'part play'
			else:
				label = 'part play: ' + name
			self.partbutton.label = label
		if self.timing_changed:
			self.savelabel.lcol = self.savelabel.col2
		else:
			self.savelabel.lcol = self.savelabel.col1
		self.calctimingbutton.set_button(self.measure_armtimes)
		self.showtime()
	#
	def showtime(self):
		if self.msec_origin == 0:
			self.statebutton.label = '--:--'
			return
		now = int(self.timefunc())
		label = `now/60` + ':' + `now/10%6` + `now % 10`
		if self.statebutton.label <> label:
			self.statebutton.label = label
		#
	#
	def makemenu(self):
		self.menubutton.set_menu('')
		for name in self.channelnames:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = ' (off)'
			self.menubutton.addto_menu(name + onoff)
			# XXX This is for FORMS version 2.0b;
			# XXX for version 2.0 (beta), append a '|'.
	#
	def setwaiting(self):
		BasicDialog.setwaiting(self)
		for cname in self.channelnames:
			self.channels[cname].setwaiting()
	#
	def setready(self):
		BasicDialog.setready(self)
		for cname in self.channelnames:
			self.channels[cname].setready()
