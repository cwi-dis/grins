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
		self.seeking = 0
		self.seek_node = None
		self.seek_nodelist = []
		self.ignore_delays = 0
		self.ignore_pauses = 0
		self.play_all_bags = 0
		self.sync_cv = 0
		self.toplevel = toplevel
		title = 'Player (' + toplevel.basename + ')'
		return BasicDialog.init(self, 0, 0, title)
	#
	def fixtitle(self):
		self.settitle('Player (' + self.toplevel.basename + ')')
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
		self.toplevel.setwaiting()
		self.toplevel.checkviews()
		self.showchannels()
		self.showstate()
		self.toplevel.setready()
	#
	def hide(self):
		if not self.showing: return
		self.toplevel.setwaiting()
		self.stop()
		self.fullreset()
		BasicDialog.hide(self)
		self.toplevel.checkviews()
		self.destroychannels()
		self.toplevel.setready()
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
		self.makeomenu()
		
	#
	# FORMS callbacks.
	#
	def play_callback(self, obj, arg):
		self.play()
	#
	def pause_callback(self, obj, arg):
		self.pause()
	#
	def stop_callback(self, obj, arg):
		self.stop()
	#
	def cmenu_callback(self, obj, arg):
		i = self.cmenubutton.get_menu() - 1
		if 0 <= i < len(self.channelnames):
			name = self.channelnames[i]
			#if self.channels[name].is_showing():
			#	self.channels[name].hide()
			#else:
			#	self.channels[name].show()
			self.channels[name].flip_visible()
			self.toplevel.channelview.channels_changed()
			self.makemenu()
	#
	#def calctiming_callback(self, (obj, arg)):
	#	if obj.get_button() or 1:
	#		del_timing(self.root)
	#		Timing.changedtimes(self.root)
	#		self.measure_armtimes = 1
	#		obj.set_button(1)
	#
	def omenu_callback(self, obj, arg):
		i = self.omenubutton.get_menu()
		if i == 1:
			self.measure_armtimes = (not self.measure_armtimes)
			if self.measure_armtimes:
				del_timing(self.root)
				Timing.changedtimes(self.root)
		elif i == 2:
			self.play_all_bags = (not self.play_all_bags)
		elif i == 3:
			self.ignore_delays = (not self.ignore_delays)
		elif i == 4:
			self.ignore_pauses = (not self.ignore_pauses)
		elif i == 5:
			self.sync_cv = (not self.sync_cv)
		else:
			print 'Player: Option menu: funny choice', i
		self.makeomenu()
		
	def dummy_callback(self, *dummy):
		pass
	#
	def timer_callback(self, obj, arg):
		gap = None
		while self.queue:
			when, prio, action, argument = self.queue[0]
			now = self.timefunc()
			delay = when - now
			if delay < -0.1:
				self.statebutton.lcol = GL.MAGENTA
			else:
				self.statebutton.lcol = self.statebutton.col2
			if delay > 0.0:
				break
			del self.queue[0]
			void = apply(action, argument)
		if not self.queue:
			if self.rate:
				# We were playing, but not anymore.
				self.setrate(0.0)
				self.showstate()
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
		if not self.playing:
			self.playbutton.set_button(0)
			self.pausebutton.set_button(0)
			self.stopbutton.set_button(1)
		else:
			self.stopbutton.set_button(0)
			self.playbutton.set_button(self.rate == 1.0)
			self.pausebutton.set_button(self.rate == 0.0)
		if self.userplayroot is self.root:
			self.partbutton.label = ''
		else:
			name = MMAttrdefs.getattr(self.userplayroot, 'name')
			if name == '':
				label = 'part play'
			else:
				label =  name
			self.partbutton.label = label
		#self.calctimingbutton.set_button(self.measure_armtimes)
		self.makeomenu()
		self.showtime()
	#
	def showtime(self):
		if self.rate:
			self.statebutton.lcol = self.statebutton.col2
		else:
			self.statebutton.lcol = GL.YELLOW
		if self.msec_origin == 0:
			self.statebutton.label = '--:--'
			return
		now = int(self.timefunc())
		label = `now/60` + ':' + `now/10%6` + `now % 10`
		if self.statebutton.label <> label:
			self.statebutton.label = label
		#
	#
	def makeomenu(self):
		self.omenubutton.set_menu('')
		if self.measure_armtimes:
			self.omenubutton.addto_menu('\xa4 Calculate timing')
		else:
			self.omenubutton.addto_menu('   Calculate timing')
		if self.play_all_bags:
			self.omenubutton.addto_menu('\xa4 Play all bags')
		else:
			self.omenubutton.addto_menu('   Play all bags')
		if self.ignore_delays:
			self.omenubutton.addto_menu('\xa4 Ignore delays')
		else:
			self.omenubutton.addto_menu('   Ignore delays')
		if self.ignore_pauses:
			self.omenubutton.addto_menu('\xa4 Ignore pauses')
		else:
			self.omenubutton.addto_menu('   Ignore pauses')
		if self.sync_cv:
			self.omenubutton.addto_menu('\xa4 Keep Timechart in sync')
		else:
			self.omenubutton.addto_menu('   Keep Timechart in sync')

	def makemenu(self):
		self.cmenubutton.set_menu('')
		for name in self.channelnames:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = ' (off)'
			self.cmenubutton.addto_menu(name + onoff)
			# XXX This is for FORMS version 2.0b;
			# XXX for version 2.0 (beta), append a '|'.
	#
	def setwaiting(self):
		self.statebutton.lcol = GL.MAGENTA
		BasicDialog.setwaiting(self)
		for cname in self.channelnames:
			self.channels[cname].setwaiting()
	#
	def setready(self):
		BasicDialog.setready(self)
		for cname in self.channelnames:
			self.channels[cname].setready()
