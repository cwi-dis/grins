# XXXX Still needs some work, esp. in the callback time calc section
#
from Channel import ChannelAsync
import windowinterface
import time
import audio, audiodev, audiomerge, audioconvert
import urllib
import os

debug = os.environ.has_key('CHANNELDEBUG')

class SoundChannel(ChannelAsync):
	# shared between all instances
	__maxbytes = 0			# queue size in bytes
	__playing = 0			# # of active channels

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'SoundChannel: init', name
		self.arm_fp = None
		self.play_fp = None
		self._timer_id = None
		self.play_data = ''

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'SoundChannel: arm', node
		fn = self.getfileurl(node)
		try:
			fn = urllib.urlretrieve(fn)[0]
			self.arm_fp = audio.reader(fn)
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
		return 1
		
	def do_play(self, node):
		if not self.arm_fp:
			self.play_fp = None
			self.arm_fp = None
			self.playdone(0)
			return
			
		if debug: print 'SoundChannel: play', node
		player.play(self.arm_fp, (self.my_playdone, (0,)))
		self.play_fp = self.arm_fp
		self.arm_fp = None
		
	def my_playdone(self, outside_induces):
		if debug: print 'SoundChannel: playdone',`self`
		if self.play_fp:
			player.stop(self.play_fp)
			self.play_fp = None
			self.playdone(outside_induces)

	def playstop(self):
		if debug: print 'SoundChannel: playstop'
		if self.play_fp:
			player.stop(self.play_fp)
			self.play_fp = None
		self.playdone(1)

	def setpaused(self, paused):
		if debug:
			print 'setpaused', paused, self.play_data
		self._paused = paused
		if not self._paused and self.play_data:
			self._playsome()

class Player:
	def __init__(self):
		self.__port = audiodev.writer(qsize = 400000)
		self.__merger = None
		self.__converter = None
		self.__tid = None
		self.__framerate = 0
		self.__readsize = 0
		self.__timeout = 0
		self.__data = ''
		self.__callbacks = []
		self.__is_playing = 0

	def __callback(self, arg):
		self.__callbacks.append(arg)

	def play(self, rdr, cb):
		first = 0
		if not self.__merger:
			first = 1
			self.__merger = audiomerge.merge()
		self.__is_playing = 1
		self.__merger.add(rdr, (self.__callback, (cb,)))
		if first:
			self.__converter = audioconvert.convert(self.__merger,
						 self.__port.getformats(),
						 self.__port.getframerates())
			self.__framerate = self.__converter.getframerate()
			self.__readsize = self.__framerate
			self.__port.setformat(self.__converter.getformat())
			self.__port.setframerate(self.__converter.getframerate())
			fillable = self.__port.getfillable()
			if fillable < self.__readsize:
				self.__readsize = fillable
			self.__timeout = 0.5 * self.__readsize / self.__framerate
			self.__data = self.__converter.readframes(self.__readsize)
			self.__playsome(1)

	def stop(self, rdr):
		if self.__merger:
			self.__merger.delete(rdr)
			self.__converter.setpos(self.__oldpos)
			self.__data = self.__converter.readframes(self.__readsize)
			if not self.__data:
				self.__is_playing = 0

	def __playsome(self, first = 0):
		self.__tid = None
		if not self.__is_playing:
			self.__port.wait()
			for cb in self.__callbacks:
				if cb:
					apply(cb[0], cb[1])
			self.__callbacks = []
			if not self.__is_playing:
				self.__merger = None
				self.__converter = None
				return
		self.__port.writeframes(self.__data)
		for cb in self.__callbacks:
			if cb:
				apply(cb[0], cb[1])
		self.__callbacks = []
		self.__oldpos = self.__converter.getpos()
		self.__data = self.__converter.readframes(self.__readsize)
		if not self.__data:
			self.__is_playing = 0
		timeout = float(self.__port.getfilled())/self.__framerate - self.__timeout
		if timeout <= 0:
			timeout = 0.001
		self.__tid = windowinterface.settimer(timeout,
						      (self.__playsome, ()))

player = Player()
