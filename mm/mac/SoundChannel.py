# XXXX Still needs some work, esp. in the callback time calc section
#
from Channel import ChannelAsync
import windowinterface
import time
import Audio_mac
import aifc
import urllib
import os

debug = os.environ.has_key('CHANNELDEBUG')

class SoundChannel(ChannelAsync):
	def __repr__(self):
		return '<NonThreadedSoundChannel instance, name=' + `self._name` + '>'

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'SoundChannel: init', name
		self.port = None
		self.arm_fp = None
		self.play_fp = None
		self._timer_id = None
		self.maxbytes = 0

	def _openport(self):
		if debug: print 'SoundChannel: openport'
		if self.port == 'no-audio':
			print 'Error: No audio available'
			return 0
		if self.port:
			return 1
		try:
			self.port = Audio_mac.Play_Audio_mac(qsize=200000)
		except Audio_mac.error, arg:
			print 'Error: No audio available:', arg
			self.port = 'no-audio'
			return 0
		self.maxbytes = self.port.getfillable()
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
		self.arm_bps = self.arm_nchannels*self.arm_sampwidth
		self.arm_readsize = self.arm_framerate	# XXXX 1 second, tied to timer!!
		if self.arm_readsize*self.arm_bps*2 > self.maxbytes:
			# The audio output queue is too small to fit our readsize. Lower it.
			self.arm_readsize = self.maxbytes / self.arm_bps / 2
			print 'AudioChannel: Warning: reading',self.arm_readsize,'samples per cycle'
		self.arm_time = float(self.arm_readsize/self.arm_bps)/self.arm_framerate/2
		self.arm_data = self.arm_fp.readframes(self.arm_readsize)
		if debug:
			print 'Audio arm: framerate', self.arm_framerate
			print 'Audio arm: sampwidth', self.arm_sampwidth
			print 'Audio arm: nchannels', self.arm_nchannels
			print 'Audio arm: bps', self.arm_bps
			print 'Audio arm: readsize', self.arm_readsize
			print 'Audio arm: len(data)', len(self.arm_data)
			print 'Audio arm: timer', self.arm_time
		return 1
		
	def _playsome(self, *dummy):
		if self._paused or not self.play_fp or not self.port:
			if debug:
				print 'not playing some...', self._paused, self.play_fp, self.port
			return
		in_buffer = len(self.play_data)/self.play_bps
		if debug: print 'SoundChannel: playsome', in_buffer, self.port.getfillable()
		while self.port.getfillable() >= in_buffer and self.play_data:
			self.port.writeframes(self.play_data)
			self.play_data = self.play_fp.readframes(self.play_readsize)
		if self.play_data:
			self._timer_id = windowinterface.settimer(self.arm_time, (self._playsome, ()))
		else:
			samples_left = self.port.getfilled()
			time_left = samples_left/float(self.play_framerate)
			self._timer_id = windowinterface.settimer(time_left, (self.myplaydone, (0,)))
			
	def myplaydone(self, arg):
		self._timer_id = None
		self.playdone(arg)
			
	def do_play(self, node):
		if not self.arm_fp or not self.port:
			self.play_fp = None
			self.playdone(0)
			return
			
		if debug: print 'SoundChannel: play', node
		self.play_fp = self.arm_fp
		self.play_readsize = self.arm_readsize
		self.play_framerate = self.arm_framerate
		self.play_bps = self.arm_bps
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
		self.port.stop()
		if self._timer_id:
			windowinterface.canceltimer(self._timer_id)
		self.playdone(1)

	def setpaused(self, paused):
		if debug:
			print 'setpaused', paused, self.play_data
		self._paused = paused
		if not self._paused and self.play_data:
			self._playsome()
