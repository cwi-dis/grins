# XXXX Still needs some work, esp. in the callback time calc section
#
from Channel import ChannelAsync
import windowinterface
import time
import audio, audiodev
import urllib
import os

debug = os.environ.has_key('CHANNELDEBUG')

class SoundChannel(ChannelAsync):
	# shared between all instances
	__port = None			# the audio device
	__maxbytes = 0			# queue size in bytes
	__playing = 0			# # of active channels

	def __repr__(self):
		return '<NonThreadedSoundChannel instance, name=' + `self._name` + '>'

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'SoundChannel: init', name
		self.arm_fp = None
		self.play_fp = None
		self._timer_id = None
		self.play_data = ''

	def _openport(self):
		if debug: print 'SoundChannel: openport'
		if self.__port == 'no-audio':
			print 'Error: No audio available'
			return 0
		if self.__port:
			return 1
		try:
			SoundChannel.__port = audiodev.writer(qsize=400000)
		except audiodev.Error, arg:
			print 'Error: No audio available:', arg
			SoundChannel.__port = 'no-audio'
			return 0
		# initialize to known state to find out queuesize in bytes
## 		self.__port.setsampwidth(2)
## 		self.__port.setnchannels(2)
## 		SoundChannel.__maxbytes = self.__port.getfillable() * 4
		return 1

	def do_arm(self, node, same=0):
		if not self._openport():
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'SoundChannel: arm', node
		fn = self.getfileurl(node)
		try:
			fn = urllib.urlretrieve(fn)[0]
			self.arm_fp = audio.reader(fn,
						   self.__port.getformats(),
						   self.__port.getframerates())
		except IOError:
			print 'Cannot open audio file', fn
			self.arm_fp = None
			self.armed_duration = 0
			return 1
		except audio.Error:
			print 'Unknown audio file type', fn
			self.arm_fp = None
			self.armed_duration = 0
			return 1
		self.arm_framerate = self.arm_fp.getframerate()
		self.arm_format = self.arm_fp.getformat()
		self.arm_readsize = self.arm_framerate	# XXXX 1 second, tied to timer!!
## 		if self.arm_readsize*self.arm_bps*2 > self.__maxbytes:
## 			# The audio output queue is too small to fit
## 			# our readsize. Lower it.
## 			self.arm_readsize = self.__maxbytes / self.arm_bps / 2
## 			print 'AudioChannel: Warning: reading', \
## 			      self.arm_readsize, 'samples per cycle'
## 		self.arm_time = float(self.arm_readsize/self.arm_bps)/self.arm_framerate/2
		self.arm_data = self.arm_fp.readframes(self.arm_readsize)
		if debug:
			print 'Audio arm: framerate', self.arm_framerate
			print 'Audio arm: format', self.arm_format
			print 'Audio arm: readsize', self.arm_readsize
			print 'Audio arm: len(data)', len(self.arm_data)
		return 1
		
	def _playsome(self, *dummy):
		if self._paused or not self.play_fp or not self.__port:
			if debug:
				print 'not playing some...', self._paused, \
				      self.play_fp, self.__port
			return
		in_buffer = len(self.play_data)
		if debug:
			print 'SoundChannel: playsome', in_buffer, \
			      self.__port.getfillable()
## 		while self.__port.getfillable() >= in_buffer and \
## 		      self.play_data:
		if self.play_data:
			self.__port.writeframes(self.play_data)	# may hang :-(
			self.play_data = self.play_fp.readframes(self.play_readsize)
		if self.play_data:
			self._timer_id = windowinterface.settimer(self.play_time, (self._playsome, ()))
		else:
			samples_left = self.__port.getfilled()
			time_left = samples_left/float(self.play_framerate)
			self._timer_id = windowinterface.settimer(time_left, (self.myplaydone, (0,)))
			
	def myplaydone(self, arg):
		self._timer_id = None
		self.__port.wait()
		SoundChannel.__playing = SoundChannel.__playing - 1
		self.playdone(arg)
			
	def do_play(self, node):
		if not self.arm_fp or not self.__port:
			self.play_fp = None
			self.playdone(0)
			return
			
		if debug: print 'SoundChannel: play', node
		SoundChannel.__playing = SoundChannel.__playing + 1
		if self.__playing > 1:
			print 'Warning: %d sound channels active' % SoundChannel.__playing
		self.play_fp = self.arm_fp
		self.play_readsize = self.arm_readsize
		self.play_framerate = self.arm_framerate
		self.play_format = self.arm_format
		self.play_data = self.arm_data
		self.play_time = float(self.play_readsize)/self.play_framerate/2
		self.arm_fp = None
		self.arm_data = None
		self.__port.setformat(self.play_format)
		self.__port.setframerate(self.play_framerate)
		self._playsome()
		
	def playstop(self):
		if not self.__port:
			return
		if debug: print 'SoundChannel: playstop'
		self.__port.stop()
		SoundChannel.__playing = SoundChannel.__playing - 1
		if self._timer_id:
			windowinterface.canceltimer(self._timer_id)
		self.playdone(1)

	def setpaused(self, paused):
		if debug:
			print 'setpaused', paused, self.play_data
		self._paused = paused
		if not self._paused and self.play_data:
			self._playsome()
