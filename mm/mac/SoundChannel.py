from Channel import Channel
import windowinterface
import time
import audiodev
import aifc
import urllib
import os

debug = os.environ.has_key('CHANNELDEBUG')

class SoundChannel(Channel):
	def __repr__(self):
		return '<NonThreadedSoundChannel instance, name=' + `self._name` + '>'

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'SoundChannel: init', name
		self.port = None
		self.arm_fp = None
		self.play_fp = None
		self.has_callback = 0

	def _openport(self):
		if debug: print 'SoundChannel: openport'
		if self.port == 'no-audio':
			print 'Error: No audio available'
			return 0
		if self.port:
			return 1
		try:
			self.port = audiodev.AudioDev()
		except audiodev.error, arg:
			print 'Error: No audio available:', arg
			self.port = 'no-audio'
			return 0
		return 1

	def do_arm(self, node, same=0):
		if not self._openport():
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'SoundChannel: arm', node
		fn = self.getfileurl(node)
		fn = urllib.url2pathname(fn)

		try:
			self.arm_fp = aifc.open(fn, 'r')
		except IOError:
			print 'Cannot open audio file', fn
			self.arm_fp = None
			self.armed_duration = 0
			return 1
		self.arm_framerate = self.arm_fp.getframerate()
		self.arm_sampwidth = self.arm_fp.getsampwidth()
		self.arm_nchannels = self.arm_fp.getnchannels()
		self.arm_readsize = self.arm_framerate	# XXXX 1 second, tied to timer!!
		self.arm_data = self.arm_fp.readframes(self.arm_readsize)
		# XXXX armed_duration??
		return 1
		
	def _playsome(self, *dummy):
		if debug: print 'SoundChannel: playsome'
		if not self.play_fp or not self.port:
			return
		while self.port.getfillable() >= self.play_readsize and self.play_data:
			self.port.writeframes(self.play_data)
			self.play_data = self.play_fp.readframes(self.play_readsize)
		if self.play_data:
			windowinterface.settimer(0.5, (self._playsome, ()))
			
	def do_play(self, node):
		if not self.arm_fp or not self.port:
			self.play_fp = None
			return
			
		if debug: print 'SoundChannel: play', node
		self.play_fp = self.arm_fp
		self.play_readsize = self.arm_readsize
		self.play_data = self.arm_data
		self.arm_fp = None
		self.arm_data = None
		self.port.setoutrate(self.arm_framerate)
		self.port.setsampwidth(self.arm_sampwidth)
		self.port.setnchannels(self.arm_nchannels)
		self._playsome()
		

	def playstop(self):
		if not self.port:
			return
		if debug: print 'SoundChannel: playstop'
		pass # XXXX Stop playing

	def setpaused(self, paused):
		pass # XXXX pause!
