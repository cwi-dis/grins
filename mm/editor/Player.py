# Player module -- mostly defines the Player class.


import gl
import GL
import fl
from FL import *
import GLLock
import flp
from Scheduler import del_timing
from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
from Dialog import BasicDialog
from ViewDialog import ViewDialog
import Timing
import dialogs

MYGREY=8
MYRED=9
MYGREEN=GL.GREEN
MYYELLOW=GL.YELLOW
MYBLUE=MYGREY

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
		self.playing = self.pausing = self.locked = 0
		self = PlayerCore.init(self, toplevel)
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
		self.continuous = 0
		self.toplevel = toplevel
		title = 'Player (' + toplevel.basename + ')'
		self = BasicDialog.init(self, 0, 0, title)
		self.set_timer = self.timerobject.set_timer
		return self
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
	def make_form(self):
		ftemplate = flp.parse_form('PlayerForm', 'form')
		flp.create_full_form(self, ftemplate)
		self.makeomenu()
		
	#
	# FORMS callbacks.
	#
	#
## 	def before_call(self):
##		print 'callback start'
##		self.waslocked = 0
##		if GLLock.gl_lock:
##			print 'try acquire'
##			if not GLLock.gl_lock.acquire(0):
##				print 'acquire failed'
##				self.waslocked = 1
##			print 'release'
##			GLLock.gl_lock.release()
##	#
##	def after_call(self):
##		print 'callback end'
##		if self.waslocked:
##			print 're-acquire'
##			GLLock.gl_lock.acquire()
	#
	def play_callback(self, obj, arg):
##		self.before_call()
		self.playbutton.lcol = MYBLUE
		if self.playing and self.pausing:
			# Case 1: user pressed play to cancel pause
			self.pause(0)
		elif not self.playing:
			# Case 2: starting to play from stopped mode
			self.play()
		else:
			# nothing, restore state.
			self.showstate()
##		self.after_call()
	#
	def pause_callback(self, obj, arg):
##		self.before_call()
		self.pausebutton.lcol = MYBLUE
		if self.playing and self.pausing:
			# Case 1: press pause to cancel pause
			self.pause(0)
		elif self.playing:
			# Case 2: press pause to pause
			self.pause(1)
		else:
			# Case 3: not playing. Go to paused mode
			self.pause(1)
			self.playbutton.lcol = MYBLUE
			self.play()
##		self.after_call()
	#
	def stop_callback(self, obj, arg):
##		self.before_call()
		self.cc_stop()
##		self.after_call()

	def cc_stop(self):
		self.stopbutton.lcol = MYBLUE
		self.continuous = 0
		self.stop()
		if self.pausing:
			self.pause(0)

	def timer_callback(self, obj, arg):
##		self.before_call()
		self.scheduler.timer_callback()
##		self.after_call()
	#
	def cmenu_callback(self, obj, arg):
##		self.before_call()
		i = self.cmenubutton.get_menu() - 1
		if 0 <= i < len(self.channelnames):
			name = self.channelnames[i]
			isvis = self.channels[name].get_visible()
			self.cc_enable_ch(name, (not isvis))
##		self.after_call()

	def cc_enable_ch(self, name, onoff):
		try:
			ch = self.channels[name]
		except KeyError:
			dialogs.showmessage('No such channel: '+name)
			return
		ch.set_visible(onoff)
		self.toplevel.channelview.channels_changed()
		self.makemenu()
	#
	def omenu_callback(self, obj, arg):
##		self.before_call()
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
		elif i == 6:
			self.pause_minidoc = (not self.pause_minidoc)
		elif i == 7:
			raise 'Crash requested by user'
		elif i == 8:
			self.scheduler.dump()
		elif i == 9:
			self.continuous = (not self.continuous)
		else:
			print 'Player: Option menu: funny choice', i
		self.makeomenu()
##		self.after_call()

	def slotmenu_callback(self, obj, arg):
##		self.before_call()
		slot = obj.get_menu()
		if slot:
			node = self.runslots[slot-1][0]
			if node:
				self.toplevel.channelview.globalsetfocus(node)
			else:
				dialogs.showmessage('That slot is not active')
##		self.after_call()
		
	def dummy_callback(self, *dummy):
		pass
	#
	#
	def showstate(self):
		if self.playing:
			self.playbutton.lcol = MYGREEN
			self.stopbutton.lcol = MYGREY
		else:
			self.playbutton.lcol = MYGREY
			self.stopbutton.lcol = GL.BLACK
		if self.pausing:
			self.pausebutton.lcol = MYYELLOW
		else:
			self.pausebutton.lcol = MYGREY
		self.playbutton.set_button(self.playing)
		self.stopbutton.set_button(not self.playing)
		self.pausebutton.set_button(self.pausing)

		#self.calctimingbutton.set_button(self.measure_armtimes)
		self.makeomenu()
		self.showtime()
	#
	def showpauseanchor(self, pausing):
		if pausing:
			self.pausebutton.lcol = MYYELLOW
		else:
			self.pausebutton.lcol = MYGREY
		
	def showtime(self):
		pass
#		if self.scheduler.getrate():
#			self.statebutton.lcol = self.statebutton.col2
#		else:
#			self.statebutton.lcol = GL.YELLOW
#		#if self.msec_origin == 0:
#		#	self.statebutton.label = '--:--'
#		#	return
#		now = int(self.scheduler.timefunc())
#		label = `now/60` + ':' + `now/10%6` + `now % 10`
#		if self.statebutton.label <> label:
#			self.statebutton.label = label
#		#
        #
	def makeslotmenu(self, list):
		self.slotmenubutton.set_menu('')
		for l in list:
			self.slotmenubutton.addto_menu(l)
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
		if self.pause_minidoc:
			self.omenubutton.addto_menu('\xa4 autopause minidoc')
		else:
			self.omenubutton.addto_menu('   autopause minidoc')
		self.omenubutton.addto_menu('   Crash CMIF')
		self.omenubutton.addto_menu('   Dump scheduler data')
		if not self.continuous:
			self.omenubutton.addto_menu('   Continuous play')
		else:
			self.omenubutton.addto_menu('\xa4 Continuous play')
			
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
##		self.statebutton.lcol = GL.MAGENTA
		BasicDialog.setwaiting(self)
		for cname in self.channelnames:
			self.channels[cname].setwaiting()
	#
	def setready(self):
		BasicDialog.setready(self)
		for cname in self.channelnames:
			self.channels[cname].setready()
