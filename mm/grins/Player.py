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

class Player(PlayerCore):
	#
	# Initialization.
	#
	def __init__(self, toplevel):
		self.playing = self.pausing = self.locked = 0
		PlayerCore.__init__(self, toplevel)
		self.channelnames = []
		self.measure_armtimes = 0
		self.channels = {}
		self.channeltypes = {}
		self.seeking = 0
		self.seek_node = None
		self.seek_nodelist = []
		self.sync_cv = 0
		self.ignore_delays = 0
		self.ignore_pauses = 0
		self.play_all_bags = 0
		self.pause_minidoc = 1
		self.toplevel = toplevel
		self.showing = 0
		self.waiting = 0
		self.do_makemenu = 0
		self.last_geometry = None
		self.window = None
		self.source = None
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback

	def destroy(self):
		if not self.showing: return
		self.showing = 0
		self.stop()
		self.fullreset()
		self.window.close()
		self.window = None
		self.destroychannels()

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

	def show(self, afterfunc = None):
		if self.is_showing():
			self.window.pop()
			if afterfunc is not None:
				apply(afterfunc[0], afterfunc[1])
			return
		self.aftershow = afterfunc
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
		window.register(WMEVENTS.Mouse0Release, self._mouse, None)
		window.register(WMEVENTS.ResizeWindow, self.resize, None)
		window.register(WMEVENTS.WindowExit, self.hide, None)
		self.showchannels()
		self.showstate()

	def load_geometry(self):
		name = 'player_'
		h, v = self.root.GetRawAttrDef(name + 'winpos', (None, None))
		width, height = MMAttrdefs.getattr(self.root, name + 'winsize')
		self.last_geometry = h, v, width, height

	def resize(self, *rest):
		window = self.window
		for w in self.subwin:
			w.close()
		font = windowinterface.findfont('Helvetica', 10)
		d = window.newdisplaylist()
		dummy = d.usefont(font)
		mw, mh = 0, 0
		self.titles = titles[:]
		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'TextEdit'):
			self.titles.insert(1, 'Source...')
		for t in self.titles:
			w, h = d.strsize(t)
			if w > mw: mw = w
			if h > mh: mh = h
		if mw > .5: mw = .5
		self.width = 1.0 - mw	# useful width
		d.close()
		self.subwin = []
		n = len(self.titles)
		for i in range(n):
			self.subwin.append(window.newcmwindow(
				(1.0 - mw, i / float(n), mw, 1.0 / float(n))))
		self.subwin[-1].register(WMEVENTS.Mouse0Release, self.hide, None)
		if len(self.titles) == 3:
			self.subwin[1].register(WMEVENTS.Mouse0Release, self.source_callback, None)
		self.redraw()

	def source_callback(self, *rest):
		if self.source is not None and not self.source.is_closed():
			self.source.show()
			return
		w = windowinterface.Window('Source', resizable = 1,
					   deleteCallback = 'hide')
		b = w.ButtonRow([('Close', (w.hide, ()))],
				top = None, left = None, right = None,
				vertical = 0)
		t = w.TextEdit(self.root.source, None, editable = 0,
			       top = b, left = None, right = None,
			       bottom = None, rows = 30, columns = 80)
		w.show()
		self.source = w

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
		for i in range(len(self.titles)):
			w = self.subwin[i]
			t = self.titles[i]
			d = w.newdisplaylist()
			if i > 0:
				cl, ct, cr, cb = FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM
				d.draw3dbox(cl, ct, cr, cb, (0.0, 0.0, 1.0, 1.0))
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
		self.toplevel.close_callback()

	def get_geometry(self):
		if self.window:
			self.last_geometry = self.window.getgeometry()

	def _mouse(self, dummy, window, ev, val):
		if window is not self.window:
			return
		self.toplevel.setwaiting()
		x, y = val[:2]
		if .01 < y < .49:
			if .01 * self.width < x < .49 * self.width:
				self.play_callback()
			elif .51 * self.width < x < .99 * self.width:
				self.pause_callback()
		elif .51 < y < .99 and .01 * self.width < x < .99 * self.width:
			self.stop_callback()
		self.toplevel.setready()
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

	def channel_callback(self, name):
		isvis = self.channels[name].may_show()
		self.cc_enable_ch(name, (not isvis))

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
		d = self.displist.clone()
		self.drawplaybutton(self.playing, d)
		self.drawstopbutton(not self.playing, d)
		self.drawpausebutton(self.pausing, d)
		d.render()
		self.displist.close()
		self.displist = d

	def showpauseanchor(self, pausing):
		d = self.displist.clone()
		self.drawpausebutton(pausing, d)
		d.render()
		self.displist.close()
		self.displist = d
		
	def updateuibaglist(self):
		pass

	def makemenu(self):
		if not self.is_showing():
			return
		if self.waiting:
			self.do_makemenu = 1
			return
		self.do_makemenu = 0
		menu = []
		for name in self.channelnames:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = ' (off)'
			menu.append('', name + onoff,
				    (self.channel_callback, (name,)))
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
		if self.do_makemenu:
			self.makemenu()
		if self.window:
			self.window.setcursor('')
		for cname in self.channelnames:
			self.channels[cname].setready()
