__version__ = "$Id$"

# Player module -- mostly defines the Player class.


from PlayerCore import PlayerCore
from MMExc import *
import MMAttrdefs
from ViewDialog import ViewDialog
import windowinterface, WMEVENTS
from usercmd import *

RED = 255, 0, 0
GREEN = 0, 255, 0
BLACK = 0, 0, 0

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
		ViewDialog.__init__(self, 'player_')
		self.playing = self.pausing = self.locked = 0
		PlayerCore.__init__(self, toplevel)
		self.load_geometry()
		
		from SMILCssResolver import SMILCssResolver
		self.cssResolver = self.context.cssResolver
			
		PlayerDialog.__init__(self, self.last_geometry,
				      'Player (' + toplevel.basename + ')')
		self.channelnames = []
		self.channels = {}
		self.channeltypes = {}
		self.seeking = 0
		self.seek_node = None
		self.seek_nodelist = []
		self.ignore_delays = 0
		self.ignore_pauses = 0
		self.pause_minidoc = 1
		self.toplevel = toplevel
		self.curlayout = None
		self.savecurlayout = None
		self.curchannel = None
		self.savecurchannel = None
		self.savecallback = None
		self.showing = 0
		self.set_timer = toplevel.set_timer
		self.timer_callback = self.scheduler.timer_callback
		self.makechannels()
		self._exporter = None
		self.commandlist = [
			CLOSE_WINDOW(callback = (self.close_callback, ()),
				     help = 'Close the Player View'),
			USERGROUPS(callback = self.usergroup_callback),
			CHANNELS(callback = self.channel_callback),
			SCHEDDUMP(callback = (self.scheduler.dump, ())),
			MAGIC_PLAY(callback = (self.magic_play, ())),
			]
## These commands are implemented by TopLevel nowadays.
##		play = PLAY(callback = (self.play_callback, ()))
##		pause = PAUSE(callback = (self.pause_callback, ()))
##		stop = STOP(callback = (self.stop_callback, ()))
##		mark = MARK(callback = (self.mark_callback, ()))

		self.stoplist = self.commandlist + [
##			# when stopped, we can play and pause
##			play,
##			pause,
##			stop,
##			mark, # DBG
			]
		self.playlist = self.commandlist + [
##			# when playing, we can pause and stop
##			pause,
##			stop,
##			mark,
			]
		self.pauselist = self.commandlist + [
##			# when pausing, we can continue (play or
##			# pause) and stop
##			play,
##			pause,
##			stop,
##			mark,
			]
		self.alllist = self.pauselist
		
	def destroy(self):
		PlayerCore.destroy(self)
		if not hasattr(self, 'toplevel'):
			# already destroyed
			return
		self.hide()
		self.destroychannels()
		self.close()
		del self._exporter
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

	def fixtitle(self):
		import MMurl
		basename = MMurl.unquote(self.toplevel.basename)
		self.settitle('Player (' + basename + ')')

	def __repr__(self):
		return '<Player instance, root=' + `self.root` + '>'

	#
	# Extend BasicDialog show/hide/destroy methods.
	#
	def is_showing(self):
		return self.showing

	def show(self, afterfunc = None, offscreen = 0):
		if self.is_showing():
			PlayerDialog.show(self)
			for ch in self.channels.values():
				ch.popup(poptop = 1)
			if afterfunc is not None:
				apply(apply, afterfunc)
			return
		self.aftershow = afterfunc
		self.fullreset()
		self.toplevel.checkviews()
		PlayerDialog.show(self)
		self.showing = 1
		self.checkRenderer()		
		self.before_chan_show()
		if self.curlayout is None:
			self.showchannels()
		else:
			self.setlayout(self.curlayout, self.curchannel, self.savecallback)
		self.makeugroups()
		self.showstate()
		self.after_chan_show()

	def hide(self, *rest):
		if self.toplevel.layoutview is not None:
			self.toplevel.layoutview.hide()
		if not self.showing: return
		self.showing = 0
		self.stop()
		self.fullreset()
		self.save_geometry()
		PlayerDialog.hide(self)
		self.toplevel.checkviews()
		self.hidechannels()
		self.savecallback = None

	def save_geometry(self):
		ViewDialog.save_geometry(self)
		for name in self.channelnames:
			self.channels[name].save_geometry()

	def get_geometry(self):
		geometry = self.getgeometry()
		if geometry is not None:
			self.last_geometry = geometry
			return self.last_geometry

	def setlayout(self, layout = None, channel = None, selectchannelcb = None, excludeRenderer = 0):
		self.curlayout = layout
		self.curchannel = channel
		if selectchannelcb is not None:
			self.savecallback = selectchannelcb
		if not self.showing or self.playing:
			return
		context = self.context
		channels = None
		if layout is not None:
			from LayoutView import ALL_LAYOUTS
			if layout == ALL_LAYOUTS:
				channels = context.channels
			else:
				channels = context.layouts.get(layout)
			if channels is None:
				self.curlayout = layout = None
		if layout is None:
			channels = context.channels
			channeldict = {}
		
		# add the new regions/viewports/rendererchannels
		import MMTypes
		for ch in channels:
			# exclude regions/viewport which are not a part of the document
			if ch.GetType() == 'layout' and not ch.isInDocument() or \
				ch.GetType() != 'layout' and excludeRenderer:
				continue
			
			chname = ch.name
			channeldict[chname] = 0
			if not self.channels.has_key(chname):
				self.newchannel(chname,
						context.channeldict[chname])
				self.channelnames.append(chname)
		for chname in self.channelnames:
			ch = self.channels[chname]
			# if regions/viewport is still there
			if channeldict.has_key(chname):
				del channeldict[chname]
				
				if layout is None:
					ch.check_visible()
					ch.unhighlight()
					ch.sensitive()
				else:
					ch.show()
					if channel is not None and \
					   channel == chname:
						##ch.highlight(RED)
						ch.modeless_resize_window()
					else:
						ch.cancel_modeless_resize()
						# get a color that is different
						# than the background
						bgcolor = ch._attrdict.get('bgcolor')
						if bgcolor:
							import colorsys
							hsv = colorsys.rgb_to_hsv(bgcolor[0]/255.,bgcolor[1]/255.,bgcolor[2]/255.)
							color = colorsys.hsv_to_rgb((hsv[0]+0.25)%1.0,hsv[1],(hsv[2]+0.5)%1.0)
							color = int(color[0]*255+.5),int(color[2]*255+.5),int(color[2]*255+.5)
							ch.highlight(color)
					ch.sensitive((selectchannelcb, (chname,)))
			elif not ch._attrdict.has_key('base_window'):
				ch.show()
				ch.sensitive((selectchannelcb, (chname,)))
			else:
				ch.hide()
				ch.sensitive()
		self.makemenu()

	def play(self):
		self.savecurlayout = self.curlayout
		self.savecurchannel = self.curchannel
		PlayerCore.play(self)

	def stopped(self):
		PlayerCore.stopped(self)
		self.updatePlayerStateOnStop()
		if self._exporter:
			self._exporter.finished()
			for ch in self.channels.values():
				ch.unregister_exporter(self._exporter) 
			self._exporter = None
			self.hide()
		if self.curlayout is None:
			self.setlayout(self.savecurlayout, self.savecurchannel, self.savecallback)
		else:
			self.setlayout(self.curlayout, self.curchannel, self.savecallback)
			
	def exportplay(self, exporter):
		self.hide()
		self._exporter = exporter
		self.show(offscreen=1)
		for ch in self.channels.values():
			ch.register_exporter(exporter) 
		self.play()

	def can_mark(self):
		return self.playing
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
			settings.commit(auto=1)
		# RTIPA end
		self.show()
		if self.playing and self.pausing:
			# Case 1: user pressed play to cancel pause
			self.pause(0)
		elif not self.playing:
			# Case 2: starting to play from stopped mode
			self.fullreset()
			self.play()
		else:
			# nothing, restore state.
			self.showstate()

	def pause_callback(self):
		if self.showing:			
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
		if self.showing:			
			self.toplevel.setwaiting()
			self.cc_stop()

	def magic_play(self):
		if self.playing:
			# toggle pause if playing
			self.pause_callback()
		else:
			# start playing if stopped
			self.play_callback()

	def close_callback(self):
		self.hide()

	def usergroup_callback(self, name):
		self.toplevel.setwaiting()
		title, u_state, override, uid = self.context.usergroups[name]
		em = self.context.editmgr
		if not em.transaction():
			return
		if u_state == 'RENDERED':
			u_state = 'NOT_RENDERED'
		else:
			u_state = 'RENDERED'
		em.delusergroup(name)
		em.addusergroup(name, (title, u_state, override, uid))
		em.commit()
		self.setusergroup(name, u_state == 'RENDERED')

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

	def makemenu(self):
		channels = []
		for name in self.channelnames:
			channels.append((name, self.channels[name].is_showing()))
		channels.sort()
		self.setchannels(channels)

	def makeugroups(self):
		import settings
		ugroups = []
		showhidden = settings.get('showhidden')
		for name, (title, u_state, override, uid) in self.context.usergroups.items():
			if not showhidden and override != 'visible':
				continue
			if not title:
				title = name
			ugroups.append((name, title, u_state == 'RENDERED'))
		self.setusergroups(ugroups)
