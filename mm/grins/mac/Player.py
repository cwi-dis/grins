__version__ = "$Id$"

from Selecter import Selecter
import windowinterface, WMEVENTS

class Player(Selecter):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.playroot = self.root # top of current mini-document
		self.userplayroot = self.root # node specified by part play
		self.context = self.root.GetContext()
		self.channels = {}
		self.pause_minidoc = 1	# used by Scheduler
		self.playing = 0
		self.showing = 0
		self.waiting = 0
		self.do_makemenu = 0
		Selecter.__init__(self)
		# A few dummies to keep Selecter and Scheduler happy:
		self.sync_cv = 0
		self._tracing = 0
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback
		self.pause = self.scheduler.setpaused
		self.chans_showing = 0


	# A few routines from Selecter that are overridden:
	def updateuibaglist(self):
		pass
	def showpauseanchor(self, arg):
		pass
	def play_done(self):
		self.playing = 0
		self.scheduler.setpaused(0)
##		if self.toplevel.main.nocontrol:
		if 1:	# Grins-only
			self.toplevel.main.closetop(self.toplevel)
			return
		self.showstate()
		pass  # XXXX WRONG, should do more.

	def makechannels(self):
		for name in self.context.channelnames:
			attrdict = self.context.channeldict[name]
			self.newchannel(name, attrdict)

	def destroychannels(self):
		for name in self.channels.keys():
			self.killchannel(name)

	def before_chan_show(self, chan = None):
		self.chans_showing = self.chans_showing + 1

	def after_chan_show(self, chan = None):
		self.chans_showing = self.chans_showing - 1
		if self.chans_showing == 0:
			self.after_showchannels()

	def after_showchannels(self):
		aftershow = self.aftershow
		self.aftershow = None
		if aftershow:
			apply(aftershow[0], aftershow[1])

	def showchannels(self):
		self.before_chan_show()
		for ch in self.channels.values():
			if ch.may_show():
				ch.show()
			# XXX hack to get keyboard events in all windows
			if ch.__dict__.has_key('window') and ch.window:
				ch.window.register(WMEVENTS.KeyboardInput,
					  self.toplevel.keyboard_callback,
					  None)
		self.after_chan_show()

	def cc_enable_ch(self, name, onoff):
		try:
			ch = self.channels[name]
		except KeyError:
			windowinterface.showmessage('No such channel: '+name)
			return
		ch.set_visible(onoff)
		self.makemenu()

	cc_stop = Selecter.stop

	def newchannel(self, name, attrdict):
		if not attrdict.has_key('type'):
			raise TypeError, \
				  'channel '+`name`+' has no type attribute'
		type = attrdict['type']
		from ChannelMap import channelmap
		if not channelmap.has_key(type):
			raise TypeError, \
				  'channel '+`name`+' has bad type '+`type`
		chclass = channelmap[type]
		ch = chclass(name, attrdict, self.scheduler, self)
		self.channels[name] = ch

	def killchannel(self, name):
		self.channels[name].destroy()
		del self.channels[name]

	def getchannelbyname(self, name):
		if self.channels.has_key(name):
			return self.channels[name]
		else:
			return None

	def getchannelbynode(self, node):
		import MMAttrdefs
		cname = MMAttrdefs.getattr(node, 'channel')
		return self.getchannelbyname(cname)

	def playsubtree(self, node):
		self.userplayroot = self.playroot = node
		self.play()

	def playfromanchor(self, node, anchor):
		self.userplayroot = self.playroot = self.root
		dummy = self.gotonode(node, anchor, None)
	#
	# Internal reset.
	#
	def fullreset(self):
		self.reset()
		self.playroot = self.userplayroot = self.root

#	def play(self):
#		self.reset()
#		if self.playing:
#			self.scheduler.setpaused(0)
#		else:
#			self.playroot = self.userplayroot
#			dummy = self.scheduler.start_playing(0)
#
#	def stop(self):
#		if self.playing:
#			self.scheduler.stop_playing()
#		self.toplevel.setready()

	def maystart(self):
		return 1

	def reset(self):
		self.scheduler.resettimer()
##		self.softresetchannels()

##	def softresetchannels(self):
##		for name in self.channels.keys():
##			self.channels[name].softreset()

	def cmenu_callback(self, name):
		self.channels[name].flip_visible()
		self.makemenu()

	def show(self, afterfunc = None):
		if self.showing:
			if afterfunc is not None:
				apply(afterfunc[0], afterfunc[1])
			return
		self.aftershow = afterfunc
		self.showing = 1
		self.makechannels()
		self.showchannels()
##		if self.toplevel.main.nocontrol:
##			self.control = None
##			return
		import pdb
		self.control = windowinterface.MainDialog(
			[('Play', (self.toplevel.play, ()), 'r'),
			 ('Stop', (self.toplevel.stop, ()), 'r'),
			 ('Pause', (self.toplevel.pause, ()), 't'),
			 None,
			 ('Quit', (self.do_exit, ())),
			 None,
			 ('Show console', (self.show_console, ())),
			 ('Debug', (pdb.set_trace, ())),
			 ('Trace', (self.trace_callback, ()), 't')],
			title = self.toplevel.filename,
			prompt = 'Player Control Window',
			grab = 0, vertical = 1)
		self.control.setbutton(1, 1)
		self.makemenu()
		
	def do_exit(self):
		sys.exit(0)

	def hide(self):
		if not self.showing: return
		self.stop()
		self.showing  = 0
		self.destroychannels()
		# We must still have a window when channels with
		# threads are closed because they may do a qenter call
		# which is only allowed when there are windows, so we
		# close the control window after destroying the channels.
		if self.control:
			self.control.close()

	def togglepause(self):
		if self.playing:
			if self.scheduler.getpaused():
				self.scheduler.setpaused(0)
			else:
				self.scheduler.setpaused(1)

	def showstate(self):
		if self.control:
			self.control.setbutton(0, self.playing)
			self.control.setbutton(1, not self.playing)
			self.control.setbutton(2, self.scheduler.getpaused())

	def showtime(self):
		pass

	def setwaiting(self):
		self.waiting = 1

	def setready(self):
		self.waiting = 0
		if self.do_makemenu:
			self.makemenu()

	def makemenu(self):
		if self.waiting:
			self.do_makemenu = 1
			return
		self.do_makemenu = 0
		names = self.channels.keys()
		names.sort()
		menu = []
		for name in names:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = ' (off)'
			menu.append(name + onoff,
				    (self.cmenu_callback, (name,)))
		self.control.create_menu(menu, title = 'Channels')

	def trace_callback(self):
		import trace
		if self._tracing:
			trace.unset_trace()
			self._tracing = 0
		else:
			self._tracing = 1
			trace.set_trace()
			
	def show_console(self):
		import quietconsole
		quietconsole.revert()
