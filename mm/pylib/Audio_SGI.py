from audiodev import error

class Play_Audio_sgi:
	# Private instance variables
	__classinited = 0
	__frameratedict = __nchannelsdict = __sampwidthdict = None

	def __initclass(self):
		import AL
		Play_Audio_sgi.__frameratedict = {
			48000: AL.RATE_48000,
			44100: AL.RATE_44100,
			32000: AL.RATE_32000,
			22050: AL.RATE_22050,
			16000: AL.RATE_16000,
			11025: AL.RATE_11025,
			 8000: AL.RATE_8000,
			}
		Play_Audio_sgi.__nchannelsdict = {
			1: AL.MONO,
			2: AL.STEREO,
			}
		Play_Audio_sgi.__sampwidthdict = {
			1: AL.SAMPLE_8,
			2: AL.SAMPLE_16,
			3: AL.SAMPLE_24,
			}
		Play_Audio_sgi.__classinited = 1

	def __init__(self, qsize = None):
		import al, AL
		if not self.__classinited:
			self.__initclass()
		self.__oldparams = []
		self.__params = [AL.OUTPUT_RATE, 0]
		self.__config = c = al.newconfig()
		self.__inited_outrate = 0
		self.__inited_width = 0
		self.__inited_nchannels = 0
		self.__converter = None
		self.__port = None
		self.__qsize = qsize
		if qsize:
			c.setqueuesize(qsize / c.getwidth() / c.getchannels())

	def __del__(self):
		if self.__port:
			self.stop()
		if self.__oldparams:
			import al, AL
			al.setparams(AL.DEFAULT_DEVICE, self.__oldparams)
			self.__oldparams = []

	def wait(self):
		if not self.__port:
			return
		import time
		while self.__port.getfilled() > 0:
			time.sleep(0.1)
		self.stop()

	def stop(self):
		if self.__port:
			self.__port.closeport()
			self.__port = None
		if self.__oldparams:
			import al, AL
			al.setparams(AL.DEFAULT_DEVICE, self.__oldparams)
			self.__oldparams = []

	def setoutrate(self, rate):
		try:
			cooked = self.__frameratedict[rate]
		except AttributeError:
			raise error, 'bad output rate'
		else:
			self.__params[1] = cooked
			self.__inited_outrate = 1

	def setsampwidth(self, width):
		try:
			cooked = self.__sampwidthdict[width]
		except AttributeError:
			if width == 0:
				import AL
				self.__inited_width = 1
				self.__config.setwidth(AL.SAMPLE_16)
				self.__converter = self.__ulaw2lin
			else:
				raise error, 'bad sample width'
		else:
			self.__config.setwidth(cooked)
			self.__inited_width = 1

	def setnchannels(self, nchannels):
		try:
			cooked = self.__nchannelsdict[nchannels]
		except AttributeError:
			raise error, 'bad # of channels'
		else:
			self.__config.setchannels(cooked)
			self.__inited_nchannels = 1

	def writeframes(self, data):
		if not (self.__inited_outrate and self.__inited_nchannels):
			raise error, 'params not specified'
		if not self.__port:
			import al, AL
			self.__port = al.openport('Python', 'w', self.__config)
			self.__oldparams = self.__params[:]
			al.getparams(AL.DEFAULT_DEVICE, self.__oldparams)
			al.setparams(AL.DEFAULT_DEVICE, self.__params)
		if self.__converter:
			data = self.__converter(data)
		self.__port.writesamps(data)

	def getfilled(self):
		if self.__port:
			return self.__port.getfilled()
		else:
			return 0

	def getfillable(self):
		if self.__port:
			return self.__port.getfillable()
		else:
			return self.__config.getqueuesize()

	def __ulaw2lin(self, data):
		import audioop
		return audioop.ulaw2lin(data, 2)
