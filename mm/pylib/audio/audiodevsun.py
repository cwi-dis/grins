from audiodev import Error
from audioformat import *

import sunaudiodev, SUNAUDIODEV

class AudioDevSUN:
	__formats = (ulaw_mono,
		     ulaw_stereo,
		     linear_16_mono_big,
		     linear_16_stereo_big)

	def __init__(self, fmt = None, qsize = None):
		self.__format = None
		self.__port = None
		self.__framerate = 0
		if fmt:
			self.setformat(fmt)

	def __del__(self):
		self.stop()

	def getformats(self):
		return self.__formats

	def getframerates(self):
		return (8000, 11025, 16000, 22050, 32000, 44100, 48000)

	def setformat(self, fmt):
		if fmt not in self.__formats:
			raise Error, 'bad format'
		self.__format = fmt

	def setframerate(self, rate):
		self.__framerate = rate

	def writeframes(self, data):
		if not self.__format or not self.__framerate:
			raise Error, 'params not specified'
		if not self.__port:
			fmt = self.__fmt
			self.__port = sunaudiodev.open('w')
			info = self.__port.getinfo()
			info.o_sample_rate = self.__framerate
			info.o_channels = fmt.getnchannels()
			if fmt.getencoding() == 'u-law':
				info.o_encoding = SUNAUDIODEV.ENCODING_ULAW
				info.o_precission = 8
			else:
				info.o_precission = (fmt.getbps() + 7) & ~7
				info.o_encoding = SUNAUDIODEV.ENCODING_LINEAR
			self.__port.setinfo(info)
		self.__port.write(data)

	def wait(self):
		if not self.__port:
			return
		self.__port.drain()
		self.stop()

	def stop(self):
		port = self.__port
		if port:
			port.flush()
			port.close()
			self.__port = None

	def getfilled(self):
		if self.__port:
			return self.__port.obufcount()
		else:
			return 0

	def getfillable(self):
		return BUFFERSIZE - self.getfilled()

