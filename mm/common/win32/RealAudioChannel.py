__version__ = "$Id$"

#
# WIN32 RealAudioChannel.
#

""" @win32doc|RealAudioChannel

"""
import Channel

# node attributes
import MMAttrdefs

# url parsing
import os, urllib, MMurl

# RMA
import rma

# we need addclosecallback
import windowinterface

class RealAudioChannel(Channel.Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		self._rmaplayer=None
		self._has_rma_support=1
		# release any resources on exit
		windowinterface.addclosecallback(self.release_player,())		
		Channel.Channel.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<RealAudioChannel instance, name=' + `self._name` + '>'
	
	def do_hide(self):
		self.release_player()
		Channel.Channel.do_hide(self)

	def destroy(self):
		self.release_player()
		Channel.Channel.destroy(self)

	def release_player(self):
		if self._rmaplayer:
			del self._rmaplayer
			self._rmaplayer=None

	def do_arm(self, node, same=0):
		if not self._rmaplayer:
			try:
				self._rmaplayer=rma.CreatePlayer()
			except:
				self._has_rma_support=0
				self.show_rm_message(node)
				return 0
		return 1

	# Async Channel play
	def play(self, node):
		if not self._has_rma_support:
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
			Channel.Channel.play(self,node)
			return

		url = MMurl.canonURL(self.getfileurl(node))
##		url = MMurl.basejoin(MMurl.pathname2url(os.getcwd())+'/',url)
##		type, url = MMurl.splittype(url)
##		url = 'file:/'+ url

		if not self._rmaplayer:
			self._rmaplayer=rma.CreatePlayer()
		self._rmaplayer.OpenURL(url)	
		self._rmaplayer.Begin()

	# part of stop sequence
	def stopplay(self, node):
		self.release_player()
		Channel.Channel.stopplay(self, node)
		
	# toggles between pause and run
	def setpaused(self, paused):
		self._paused = paused
		if self._rmaplayer:
			if self._paused:
				self._rmaplayer.Pause()
			else:
				self._rmaplayer.Begin()


	def show_rm_message(self,node):
		import windowinterface, MMAttrdefs
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		windowinterface.showmessage('No playback support for RealAudio on your system\n'
					    'node %s on channel %s' % (name, self._name), mtype = 'warning')
