__version__ = "$Id$"

#
# WIN32 RealWindowChannel.
#

""" @win32doc|RealWindowChannel

"""
import Channel

# node attributes
import MMAttrdefs

# url parsing
import os, urllib, MMurl

# RMA SDK
import rma

# we need addclosecallback from windowinterface
import windowinterface

class RealWindowChannel(Channel.ChannelWindow):
	def __init__(self, name, attrdict, scheduler, ui):
		self._rmaplayer=None
		self._has_rma_support=1
		# release any resources on exit
		windowinterface.addclosecallback(self.release_player,())	
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<RealWindowChannel instance, name=' + `self._name` + '>'
	
	def do_hide(self):
		self.release_player()
		Channel.ChannelWindow.do_hide(self)

	def destroy(self):
		self.release_player()
		Channel.ChannelWindow.destroy(self)

	def release_player(self):
		if self._rmaplayer:
			del self._rmaplayer
			self._rmaplayer=None

	def do_arm(self, node, same = 0):
		if not self._rmaplayer:
			try:
				self._rmaplayer=rma.CreatePlayer()
			except:
				self._has_rma_support=0
				self.show_rm_message(node)
		return 1

	# Async Channel play
	def play(self, node):
		if not self._has_rma_support:
			Channel.ChannelWindow.play(self,node)
			return
		self.play_0(node)
		if not self._is_shown or not node.IsPlayable() \
		   or self.syncplay:
			self.play_1()
			return
		if self._is_shown:
			self.do_play(node)
		self.armdone()

	def do_play(self, node):
		if not self._has_rma_support:
			Channel.ChannelWindow.do_play(self,node)
			return
		url = MMurl.canonURL(self.getfileurl(node))
##		url = MMurl.basejoin(MMurl.pathname2url(os.getcwd())+'/',url)
##		type, url = MMurl.splittype(url)
##		url = 'file:/'+ url

		if not self._rmaplayer:
			self._rmaplayer=rma.CreatePlayer()
		self._rmaplayer.SetOsWindow(self.window.GetSafeHwnd())
		self._rmaplayer.OpenURL(url)	
		self._rmaplayer.Begin()

	def stopplay(self, node):
		self.release_player()
		Channel.ChannelWindow.stopplay(self, node)
		
	# toggles between pause and run
	def setpaused(self, paused):
		self._paused = paused
		if self._rmaplayer:
			if self._paused:
				self._rmaplayer.Pause()
			else:
				self._rmaplayer.Begin()

	def show_rm_message(self,node):
		import MMAttrdefs
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		msg = 'Warning:\nNo playback support for RealMedia on your system\n' \
		      'node %s on channel %s' % (name, self._name)
		parms = self.armed_display.fitfont('Times-Roman', msg)
		w, h = self.armed_display.strsize(msg)
		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
		self.armed_display.fgcolor((255, 0, 0))		# red
		box = self.armed_display.writestr(msg)
