__version__ = "$Id$"

from dev import Error
from format import *
from Carbon import Snd
from Carbon.Sound import *
import time
import struct
import sys
import MacOS

class AudioDevMAC:
	__formats = (linear_8_mono_excess,
			  linear_8_stereo_excess,
			  linear_16_mono_big,
			  linear_16_stereo_big)

	def __init__(self, fmt = None, qsize = None):
		if qsize is None:
			qsize = 48000
		self.__format = None
		self.__nchannels = self.__sampwidth = 0
		self.__chan = None
		self.__qsize = qsize
		self.__outrate = 0
		self.__gc = []
		self.__usercallback = None
		if fmt:
			self.setformat(fmt)

	def __del__(self):
		self.stop()
		self.__usercallback = None

	def getformats(self):
		return self.__formats

	def getframerates(self):
		return None		# XXX accept all for now

	def setformat(self, fmt):
		if fmt not in self.__formats:
			raise Error, 'bad format'
		self.__format = fmt
		self.__nchannels = fmt.getnchannels()
		self.__sampwidth = (fmt.getbps() + 7) / 8

	def getformat(self):
		return self.__format

	def setframerate(self, rate):
		self.__outrate = rate

	def getframerate(self):
		return self.__outrate

	def writeframes(self, data):
		if not self.__format or not self.__outrate:
			raise Error, 'params not specified'
		if not self.__chan:
			self.__chan = Snd.SndNewChannel(5, 0, self.__callback)
		nframes = len(data) / self.__nchannels / self.__sampwidth
		if len(data) != nframes * self.__nchannels * self.__sampwidth:
			raise error, 'data is not a whole number of frames'
		while self.__gc and \
			  self.getfilled() + nframes > self.__qsize:
			time.sleep(0.1)
		h1 = struct.pack('llHhllBb',
			id(data)+MacOS.string_id_to_buffer,	# ARGH!!!  HACK, HACK!
			self.__nchannels,
			self.__outrate, 0,
			0,
			0,
			extSH,
			60)
		h2 = struct.pack('l', 
			nframes)
		h3 = 22*'\0'
		h4 = struct.pack('hhlll',
			self.__sampwidth*8,
			0,
			0,
			0,
			0)
		header = h1+h2+h3+h4
		self.__gc.append((header, data))
		self.__chan.SndDoCommand((bufferCmd, 0, header), 0)
		self.__chan.SndDoCommand((callBackCmd, 0, 0), 0)

	def __callback(self, *args):
		del self.__gc[0]
		if self.__usercallback:
			self.__usercallback()

	def setcallback(self, callback):
		self.__usercallback = callback

	def wait(self):
		if not self.__chan:
			return
		while self.getfilled():
			time.sleep(0.1)
		self.__chan = None
		self.__gc = []

	def stop(self, quietNow = 1):
		##chan = self.__chan
		self.__chan = None
		##chan.SndDisposeChannel(1)
		self.__gc = []

	def getfilled(self):
		if not self.__chan:
			return 0
		filled = 0
		# Hack: we don't know how much of the first gc has been
		# played. Assume half.
		for header, data in self.__gc[:1]:
			filled = filled + len(data)/2
		for header, data in self.__gc[1:]:
			filled = filled + len(data)
		return filled / self.__nchannels / self.__sampwidth

	def getfillable(self):
		return self.__qsize - self.getfilled()
