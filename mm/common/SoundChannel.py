__version__ = "$Id$"

# XXXX Still needs some work, esp. in the callback time calc section
#
from Channel import ChannelAsync
import MMAttrdefs
import windowinterface
import time
import audio, audiodev, audiomerge, audioconvert
import urllib
import os

debug = os.environ.has_key('CHANNELDEBUG')

# This should be a channel option
SECONDS_TO_BUFFER=4

class SoundChannel(ChannelAsync):
	node_attrs = ChannelAsync.node_attrs + ['duration', 'loop']

	# shared between all instances
	__playing = 0			# # of active channels

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		if debug: print 'SoundChannel: init', name
		self.arm_fp = None
		self.play_fp = None
		self.__qid = None

	def do_arm(self, node, same=0):
		if same and self.arm_fp:
		        return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if debug: print 'SoundChannel: arm', node
		fn = self.getfileurl(node)
		try:
			fn = urllib.urlretrieve(fn)[0]
			self.arm_fp = audio.reader(fn)
		except IOError:
			self.errormsg(node, '%s: Cannot open audio file' % fn)
			self.arm_fp = None
			self.armed_duration = 0
			return 1
		except audio.Error:
			self.errormsg(node, '%s: Unknown audio file type' % fn)
			self.arm_fp = None
			self.armed_duration = 0
			return 1
		self.armed_loop = self.getloop(node)
		self.armed_duration = MMAttrdefs.getattr(node, 'duration')
		return 1
		
	def do_play(self, node):
		if not self.arm_fp:
			print 'SoundChannel: not playing'
			self.play_fp = None
			self.arm_fp = None
			self.playdone(0)
			return
			
		if debug: print 'SoundChannel: play', node
		self.play_fp = self.arm_fp
		self.arm_fp = None
		self.play_loop = self.armed_loop
		if self.armed_duration:
			self.__qid = self._scheduler.enter(
				self.armed_duration, 0, self.__stopplay, ())
		player.play(self.play_fp, (self.my_playdone, ()))

	def __stopplay(self):
		if self.play_fp:
			self.__qid = None
			player.stop(self.play_fp)
			self.play_fp = None
			self.playdone(0)

	def my_playdone(self):
		if debug: print 'SoundChannel: playdone',`self`
		if self.play_fp:
			if self.play_loop:
				self.play_loop = self.play_loop - 1
				if self.play_loop:
					self.play_fp.rewind()
					player.play(self.play_fp,
						    (self.my_playdone, ()))
					return
				if self.__qid:
					self._scheduler.cancel(self.__qid)
					self.__qid = None
				self.play_fp = None
				self.playdone(0)
				return
			self.play_fp.rewind()
			player.play(self.play_fp, (self.my_playdone, ()))

	def playstop(self):
		if debug: print 'SoundChannel: playstop'
		if self.__qid:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		if self.play_fp:
			player.stop(self.play_fp)
			self.play_fp = None
		self.playdone(1)

	def setpaused(self, paused):
		if debug:
			print 'setpaused', paused
		player.setpaused(paused)
		self._paused = paused

	def do_hide(self):
		if self.play_fp:
			player.stop(self.play_fp)
			nframes = self.play_fp.getnframes()
			if nframes == 0:
				nframes = 1
			rate = self.play_fp.getframerate()
			self.play_fp = None
			self._qid = self._scheduler.enter(
				float(nframes) / rate, 0,
				self.playdone, (0,))

class Player:
	def __init__(self):
		# __merger, __converter, __tid, and __data are all None/'',
		# or none of them are.
		self.__pausing = 0	# whether we're pausing
		self.__port = audiodev.writer(qsize = SECONDS_TO_BUFFER*48000) # Worst-case queuesize
		self.__merger = None	# merged readers
		self.__converter = None	# merged readers, converted to port
		self.__tid = None	# timer id
		self.__framerate = 0
		self.__readsize = 0
		self.__timeout = 0
		self.__callbacks = []
		self.__data = ''	# data already read but not yet played
		self.__nframes = 0	# # of frames in current __data
		self.__oldpos = None	# start position of current __data
		self.__prevpos = None	# previous value of __oldpos
		self.__prevframes = 0	# # of frames in previous __data

	def __callback(self, rdr, arg):
		self.__callbacks.append((rdr, arg))

	def play(self, rdr, cb):
		first = 0
		if not self.__merger:
			first = 1
			self.__merger = audiomerge.merge()
		else:
			if self.__tid:
				windowinterface.canceltimer(self.__tid)
				self.__tid = None
			filled = self.__port.getfilled()
			self.__port.stop()
			self.__converter.setpos(self.__prevpos)
			n = self.__prevframes - filled
			if n > 0:
				dummy, nframes = self.__converter.readframes(n)
		self.__merger.add(rdr, (self.__callback, (rdr, cb,)))
		if first:
			self.__converter = audioconvert.convert(self.__merger,
						 self.__port.getformats(),
						 self.__port.getframerates())
			self.__framerate = self.__converter.getframerate()
			self.__readsize = SECONDS_TO_BUFFER*self.__framerate/2
			self.__port.setformat(self.__converter.getformat())
			self.__port.setframerate(self.__converter.getframerate())
			fillable = self.__port.getfillable()
			if fillable < self.__readsize:
				self.__readsize = fillable
			self.__timeout = 0.5 * self.__readsize / self.__framerate
			self.__oldpos = self.__converter.getpos()
			self.__data, self.__nframes = self.__converter.readframes(self.__readsize)
		else:
			self.__oldpos = self.__converter.getpos()
			self.__prevpos = None
			self.__prevframes = 0
			self.__data, self.__nframes = self.__converter.readframes(self.__readsize)
		self.__playsome()

	def stop(self, rdr):
		for i in range(len(self.__callbacks)):
			if self.__callbacks[i][0] is rdr:
				del self.__callbacks[i]
				break
		if self.__merger:
			self.__converter.setpos(self.__oldpos)
			self.__merger.delete(rdr)
			self.__data, self.__nframes = self.__converter.readframes(self.__readsize)
			if not self.__data:
				# deleted the last one
				self.__port.stop()
				self.__merger = None
				self.__converter = None
				self.__oldpos = None
				self.__prevpos = None
				if self.__tid:
					windowinterface.canceltimer(self.__tid)
					self.__tid = None

	def setpaused(self, paused):
		if self.__pausing == paused:
			return
		self.__pausing = paused
		if not self.__merger:
			return
		if paused:
			filled = self.__port.getfilled()
			self.__port.stop()
			self.__converter.setpos(self.__prevpos)
			n = self.__prevframes - filled
			if n > 0:
				dummy, nframes = self.__converter.readframes(n)
			self.__oldpos = self.__converter.getpos()
			self.__prevpos = None
			self.__prevframes = 0
			self.__data, self.__nframes = self.__converter.readframes(self.__readsize)
			if self.__tid:
				windowinterface.canceltimer(self.__tid)
				self.__tid = None
		else:
			self.__playsome()

	def __playsome(self):
		self.__tid = None
		port = self.__port
		converter = self.__converter
		while 1:
			if not self.__data:
				port.wait()
				self.__merger = None
				self.__converter = None
				callbacks = self.__callbacks
				self.__callbacks = []
				for rdr, cb in callbacks:
					if cb:
						apply(cb[0], cb[1])
				return
			port.writeframes(self.__data)
			callbacks = self.__callbacks
			self.__callbacks = []
			for rdr, cb in callbacks:
				self.__merger.delete(rdr)
				if cb:
					apply(cb[0], cb[1])
			self.__prevpos = self.__oldpos
			self.__prevframes = self.__nframes
			self.__oldpos = converter.getpos()
			self.__data, self.__nframes = converter.readframes(self.__readsize)
			if not self.__data:
				timeout = float(port.getfilled())/self.__framerate - 0.1
				if timeout > 0:
					self.__tid = windowinterface.settimer(
						timeout, (self.__playsome, ()))
					return
				# else we go back into the loop to stop
				# playing immediately
			else:
				timeout = float(port.getfilled()/2)/self.__framerate
				self.__tid = windowinterface.settimer(timeout,
							(self.__playsome, ()))
				return

player = Player()
