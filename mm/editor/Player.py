# Player module -- mostly defines the Player class.


from Scheduler import del_timing
from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
from ViewDialog import ViewDialog
import Timing
import windowinterface, EVENTS

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
titles = ['Channels', 'Options']

# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

class Player(ViewDialog, PlayerCore):
	#
	# Initialization.
	#
	def __init__(self, toplevel):
		ViewDialog.__init__(self, 'player_')
		self.playing = self.pausing = self.locked = 0
		PlayerCore.__init__(self, toplevel)
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
		self.last_geometry = None
		self.window = None
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback

	def destroy(self):
		self.close()

	def close(self):
		self.hide()

	def fixtitle(self):
		self.settitle('Player (' + self.toplevel.basename + ')')

	def settitle(self, title):
		if self.is_showing():
			self.window.settitle(title)

	def __repr__(self):
		return '<Player instance, root=' + `self.root` + '>'
	#
	# Extend BasicDialog show/hide/destroy methods.
	#
	def is_showing(self):
		return self.showing

	def show(self):
		if self.is_showing():
			self.window.pop()
			return
		self.toplevel.showstate(self, 1)
		title = 'Player (' + self.toplevel.basename + ')'
		self.makechannels()
		self.fullreset()
		self.load_geometry()
		x, y, w, h = self.last_geometry
		window = windowinterface.newcmwindow(x, y, w, h, title)
		self.window = window
		window.bgcolor(BGCOLOR)
		if self.waiting:
			window.setcursor('watch')
		self.subwin = []
		self.resize()
		self.showing = 1
		window.register(EVENTS.Mouse0Release, self._mouse, None)
		window.register(EVENTS.ResizeWindow, self.resize, None)
		window.register(EVENTS.WindowExit, self.hide, None)
		self.toplevel.setwaiting()
		self.toplevel.checkviews()
		self.showchannels()
		self.showstate()
		self.toplevel.setready()

	def resize(self, *rest):
		window = self.window
		for w in self.subwin:
			w.close()
		font = windowinterface.findfont('Helvetica', 10)
		d = window.newdisplaylist()
		dummy = d.usefont(font)
		mw, mh = 0, 0
		for t in titles:
			w, h = d.strsize(t)
			if w > mw: mw = w
			if h > mh: mh = h
		if mw > .5: mw = .5
		self.width = 1.0 - mw	# useful width
		d.close()
		self.subwin = []
		n = len(titles)
		for i in range(n):
			self.subwin.append(window.newcmwindow(
				(1.0 - mw, i / float(n), mw, 1.0 / float(n))))
		self.redraw()

	def drawplaybutton(self, active, d):
		if active:
			color = GREEN
			cl, ct, cr, cb = FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP
		else:
			color = GREY
			cl, ct, cr, cb = FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM
		points = []
		for x, y in [(.2, .1), (.2, .4), (.3, .25)]:
			points.append(x * self.width, y)
		d.drawfpolygon(color, points)
		d.draw3dbox(cl, ct, cr, cb,
			    (.01 * self.width, .01, .48 * self.width, .48))

	def drawpausebutton(self, active, d):
		if active:
			color = YELLOW
			cl, ct, cr, cb = FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP
		else:
			color = GREY
			cl, ct, cr, cb = FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM
		d.drawfbox(color, (.7 * self.width, .1, .03 * self.width, .3))
		d.drawfbox(color, (.77 * self.width, .1, .03 * self.width, .3))
		d.draw3dbox(cl, ct, cr, cb,
			    (.51 * self.width, .01, .48 * self.width, .48))

	def drawstopbutton(self, active, d):
		if active:
			color = BLACK
			cl, ct, cr, cb = FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP
		else:
			color = GREY
			cl, ct, cr, cb = FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM
		d.drawfbox(color, (.2 * self.width, .6, .6 * self.width, .3))
		d.draw3dbox(cl, ct, cr, cb,
			    (.01 * self.width, .51, .98 * self.width, .48))

	def redraw(self, *rest):
		import StringStuff
		font = windowinterface.findfont('Helvetica', 10)
		for i in range(len(titles)):
			w = self.subwin[i]
			t = titles[i]
			d = w.newdisplaylist()
			dummy = d.usefont(font)
			StringStuff.centerstring(d, 0, 0, 1, 1, t)
			d.render()
		d = self.window.newdisplaylist()
		self.drawplaybutton(self.playing, d)
		self.drawpausebutton(self.pausing, d)
		self.drawstopbutton(not self.playing, d)
		d.render()
		self.displist = d

	def hide(self, *rest):
		if not self.showing: return
		self.showing = 0
		self.toplevel.showstate(self, 0)
		self.toplevel.setwaiting()
		self.stop()
		self.fullreset()
		self.save_geometry()
		self.window.close()
		self.window = None
		self.toplevel.checkviews()
		self.destroychannels()
		self.toplevel.setready()

	def save_geometry(self):
		ViewDialog.save_geometry(self)
		for name in self.channelnames:
			self.channels[name].save_geometry()

	def get_geometry(self):
		if self.window:
			self.last_geometry = self.window.getgeometry()

	def _mouse(self, dummy, window, ev, val):
		if window is not self.window:
			return
		x, y = val[:2]
		if .01 < y < .49:
			if .01 * self.width < x < .49 * self.width:
				self.play_callback()
			elif .51 * self.width < x < .99 * self.width:
				self.pause_callback()
		elif .51 < y < .99 and .01 * self.width < x < .99 * self.width:
			self.stop_callback()
	#
	# FORMS callbacks.
	#
	def play_callback(self):
##		self.playbutton.lcol = MYBLUE
		if self.playing and self.pausing:
			# Case 1: user pressed play to cancel pause
			self.pause(0)
		elif not self.playing:
			# Case 2: starting to play from stopped mode
			self.play()
		else:
			# nothing, restore state.
			self.showstate()
	#
	def pause_callback(self):
##		self.pausebutton.lcol = MYBLUE
		if self.playing and self.pausing:
			# Case 1: press pause to cancel pause
			self.pause(0)
		elif self.playing:
			# Case 2: press pause to pause
			self.pause(1)
		else:
			# Case 3: not playing. Go to paused mode
			self.pause(1)
##			self.playbutton.lcol = MYBLUE
			self.play()
	#
	def stop_callback(self):
		self.cc_stop()

	def cc_stop(self):
##		self.stopbutton.lcol = MYBLUE
		self.stop()
		if self.pausing:
			self.pause(0)

	def cmenu_callback(self, name):
		isvis = self.channels[name].may_show()
		self.cc_enable_ch(name, (not isvis))

	def cc_enable_ch(self, name, onoff):
		try:
			ch = self.channels[name]
		except KeyError:
			windowinterface.showmessage('No such channel: '+name)
			return
		ch.set_visible(onoff)
		self.toplevel.channelview.channels_changed()
		self.makemenu()
	#
	def omenu_callback(self, i):
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
		else:
			print 'Player: Option menu: funny choice', i
		self.makeomenu()

	def slotmenu_callback(self, slot):
		node = self.runslots[slot][0]
		if node:
			self.toplevel.channelview.globalsetfocus(node)
		else:
			windowinterface.showmessage('That slot is not active')
		
	def dummy_callback(self, *dummy):
		pass
	#
	#
	def showstate(self):
		if not self.is_showing():
			return
		d = self.displist.clone()
		self.drawplaybutton(self.playing, d)
		self.drawstopbutton(not self.playing, d)
		self.drawpausebutton(self.pausing, d)
		d.render()
		self.displist.close()
		self.displist = d

		#self.calctimingbutton.set_button(self.measure_armtimes)
		self.makeomenu()
		self.showtime()
	#
	def showpauseanchor(self, pausing):
		d = self.displist.clone()
		self.drawpausebutton(self.pausing, d)
		d.render()
		self.displist.close()
		self.displist = d
		
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
		if not self.is_showing() or len(titles) < 3:
			return
		menu = []
		for i in range(len(list)):
			l = list[i]
			menu.append('', l, (self.slotmenu_callback, (i,)))
		self.subwin[2].create_menu(menu, title = 'Run slots')

	def makeomenu(self):
		if not self.is_showing():
			return
		menu = []
		if self.measure_armtimes:
			menu.append('', '\xa4 Calculate timing',
				    (self.omenu_callback, (1,)))
		else:
			menu.append('', '   Calculate timing',
				    (self.omenu_callback, (1,)))
		if self.play_all_bags:
			menu.append('', '\xa4 Play all bags',
				    (self.omenu_callback, (2,)))
		else:
			menu.append('', '   Play all bags',
				    (self.omenu_callback, (2,)))
		if self.ignore_delays:
			menu.append('', '\xa4 Ignore delays',
				    (self.omenu_callback, (3,)))
		else:
			menu.append('', '   Ignore delays',
				    (self.omenu_callback, (3,)))
		if self.ignore_pauses:
			menu.append('', '\xa4 Ignore pauses',
				    (self.omenu_callback, (4,)))
		else:
			menu.append('', '   Ignore pauses',
				    (self.omenu_callback, (4,)))
		if self.sync_cv:
			menu.append('', '\xa4 Keep Timechart in sync',
				    (self.omenu_callback, (5,)))
		else:
			menu.append('', '   Keep Timechart in sync',
				    (self.omenu_callback, (5,)))
		if self.pause_minidoc:
			menu.append('', '\xa4 autopause minidoc',
				    (self.omenu_callback, (6,)))
		else:
			menu.append('', '   autopause minidoc',
				    (self.omenu_callback, (6,)))
		menu.append('', '   Crash CMIF', (self.omenu_callback, (7,)))
		menu.append('', '   Dump scheduler data',
			    (self.omenu_callback, (8,)))
		self.subwin[1].create_menu(menu, title = 'Options')
			
	def makemenu(self):
		if not self.is_showing():
			return
		menu = []
		m = menu
		for name in self.channelnames:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = ' (off)'
			if len(m) == 20:
				n = []
				m.append('', 'More', n)
				m = n
			m.append('', name + onoff,
				 (self.cmenu_callback, (name,)))
		self.subwin[0].create_menu(menu, title = 'Channels')
	#
	def setwaiting(self):
		self.waiting = 1
		if self.window:
			self.window.setcursor('watch')
		for cname in self.channelnames:
			self.channels[cname].setwaiting()
	#
	def setready(self):
		self.waiting = 0
		if self.window:
			self.window.setcursor('')
		for cname in self.channelnames:
			self.channels[cname].setready()
