from audio import Error
from audioformat import *

_WAVE_FORMAT_PCM = 0x0001
_IBM_FORMAT_MULAW = 0x0101
_IBM_FORMAT_ALAW = 0x0102
_IBM_FORMAT_ADPCM = 0x0103

def _read_long(file):
	x = 0L
	for i in range(4):
		byte = file.read(1)
		if byte == '':
			raise EOFError
		x = x + (ord(byte) << (8 * i))
	if x >= 0x80000000L:
		x = x - 0x100000000L
	return int(x)

def _read_short(file):
	x = 0
	for i in range(2):
		byte = file.read(1)
		if byte == '':
			raise EOFError
		x = x + (ord(byte) << (8 * i))
	if x >= 0x8000:
		x = x - 0x10000
	return x

class Chunk:
	def __init__(self, file):
		self.file = file
		self.chunkname = self.file.read(4)
		if len(self.chunkname) < 4:
			raise EOFError
		self.chunksize = _read_long(self.file)
		self.size_read = 0
		self.offset = self.file.tell()

	def rewind(self):
		self.file.seek(self.offset, 0)
		self.size_read = 0

	def getpos(self):
		return self.size_read

	def setpos(self, pos):
		if pos < 0 or pos > self.chunksize:
			raise RuntimeError
		self.file.seek(self.offset + pos, 0)
		self.size_read = pos
		
	def read(self, length):
		if self.size_read >= self.chunksize:
			return ''
		if length > self.chunksize - self.size_read:
 			length = self.chunksize - self.size_read
		data = self.file.read(length)
		self.size_read = self.size_read + len(data)
		return data

	def skip(self):
		self.file.seek(self.chunksize - self.size_read, 1)

class reader:
	def __init__(self, filename):
		self.__filename = filename # only needed for __repr__
		self.__file = file = open(filename, 'rb')
		self.__soundpos = 0
		self.__framesread = 0
		# start parsing
		form = file.read(4)
		if form != 'RIFF':
			raise Error, 'file does not start with RIFF id'
		formlength = _read_long(file)
		if formlength <= 4:
			raise Error, 'invalid RIFF chunk data size'
		formdata = file.read(4)
		formlength = formlength - 4
		if formdata != 'WAVE':
			raise Error, 'not a WAVE file'
		fmt_chunk_read = 0
		while formlength > 0:
			data_seek_needed = 1
			chunk = Chunk(self.__file)
			if chunk.chunkname == 'fmt ':
				self.__read_fmt_chunk(chunk)
				fmt_chunk_read = 1
			elif chunk.chunkname == 'data':
				if not fmt_chunk_read:
					raise Error, 'data chunk before fmt chunk'
				self.__data_chunk = chunk
				fmt = self.__format
				self.__nframes = chunk.chunksize * \
						 fmt.getfpb() / \
						 fmt.getblocksize()
				data_seek_needed = 0
			formlength = formlength - 8 - chunk.chunksize
			if formlength > 0:
				chunk.skip()
		if not fmt_chunk_read or not self.__data_chunk:
			raise Error, 'fmt chunk and/or data chunk missing'
		if data_seek_needed:
			self.__data_chunk.rewind()

	def __repr__(self):
		return '<WAVreader instance, file=%s, format=%s, framerate=%d>' % (self.__filename, `self.__format`, self.__framerate)

	def __read_fmt_chunk(self, chunk):
		wFormatTag = _read_short(chunk)
		nchannels = _read_short(chunk)
		if nchannels < 1 or nchannels > 2:
			raise Error, 'Unsupported format'
		self.__framerate = _read_long(chunk)
		dwAvgBytesPerSec = _read_long(chunk)
		wBlockAlign = _read_short(chunk)
		if wFormatTag == _WAVE_FORMAT_PCM:
			bps = _read_short(chunk)
			if bps > 16:
				raise Error, 'Unsupported format'
			if bps <= 8:
				if nchannels == 1:
					self.__format = linear_8_mono_excess
				elif nchannels == 2:
					self.__format = linear_8_stereo_excess
			elif bps <= 16:
				self.__encoding = 'linear'
				if nchannels == 1:
					self.__format = linear_16_mono_little
				elif nchannels == 2:
					self.__format = linear_16_stereo_little
		else:
			raise Error, 'unknown WAVE format'

	def getformat(self):
		return self.__format

	def getnframes(self):
		return self.__nframes

	def getframerate(self):
		return self.__framerate

	def readframes(self, nframes = -1):
		fmt = self.__format
		if nframes >= 0:
			nbytes = (nframes / fmt.getfpb()) * fmt.getblocksize()
		else:
			nbytes = -1
		data = self.__data_chunk.read(nbytes)
		nframes = len(data) * fmt.getfpb() / fmt.getblocksize()
		self.__framesread = self.__framesread + nframes
		return data

	def rewind(self):
		self.__data_chunk.rewind()
		self.__framesread = 0

	def getpos(self):
		return self.__data_chunk.getpos(), self.__framesread

	def setpos(self, (pos, framesread)):
		self.__data_chunk.setpos(pos)
		self.__framesread = framesread

	def getmarkers(self):
		return []
