from audiodev import error

class Play_Audio_sun:
	def __init__(self, qsize = None):
		self.__outrate = 0
		self.__sampwidth = 0
		self.__nchannels = 0
		self.__inited_outrate = 0
		self.__inited_width = 0
		self.__inited_nchannels = 0
		self.__converter = None
		self.__port = None
		return

	def __del__(self):
		self.stop()

	def setoutrate(self, rate):
		self.__outrate = rate
		self.__inited_outrate = 1

	def setsampwidth(self, width):
		self.__sampwidth = width
		self.__inited_width = 1

	def setnchannels(self, nchannels):
		self.__nchannels = nchannels
		self.__inited_nchannels = 1

	def writeframes(self, data):
		if not (self.__inited_outrate and self.__inited_width and self.__inited_nchannels):
			raise error, 'params not specified'
		if not self.__port:
			import sunaudiodev, SUNAUDIODEV
			self.__port = sunaudiodev.open('w')
			info = self.__port.getinfo()
			info.o_sample_rate = self.__outrate
			info.o_channels = self.__nchannels
			if self.__sampwidth == 0:
				info.o_precision = 8
				self.o_encoding = SUNAUDIODEV.ENCODING_ULAW
				# XXX Hack, hack -- leave defaults
			else:
				info.o_precision = 8 * self.__sampwidth
				info.o_encoding = SUNAUDIODEV.ENCODING_LINEAR
				self.__port.setinfo(info)
		if self.__converter:
			data = self.__converter(data)
		self.__port.write(data)

	def wait(self):
		if not self.__port:
			return
		self.__port.drain()
		self.stop()

	def stop(self):
		if self.__port:
			self.__port.flush()
			self.__port.close()
			self.__port = None

	def getfilled(self):
		if self.__port:
			return self.__port.obufcount()
		else:
			return 0

	def getfillable(self):
		return BUFFERSIZE - self.getfilled()
