# Video file reader

class VideoFormat:
	def __init__(self, name, descr, width, height, format):
		self.__name = name
		self.__descr = descr
		self.__width = width
		self.__height = height
		self.__format = format
		
	def getname(self):
		return self.__name
		
	def getdescr(self):
		return self.__descr
		
	def getsize(self):
		return self.__width, self.__height
		
	def getformat(self):
		return self.__format
		
class _Reader:
	def __init__(self, url):
		self._did_audio = 0
		self._did_video = 0
		
	def HasAudio(self):
		return 1
		
	def HasVideo(self):
		return 0
		
	def GetAudioFormat(self):
		import audio.format
		return audio.format.AudioFormatLinear('dummy_format', 'Dummy Audio Format', 
			['mono'], 'linear-signed', blocksize=2, fpb=1, bps=16)
			
	def GetAudioFrameRate(self):
		return 44100
		
	def GetVideoFormat(self):
		import imgformat
		return VideoFormat('dummy_format', 'Dummy Video Format', 320, 240, imgformat.macrgb)
		
	def GetVideoFrameRate(self):
		return 25
		
	def ReadAudio(self, nframes):
		if self._did_audio:
			return ''
		self._did_audio = 1
		return '\0' * nframes * 2
		
	def ReadVideo(self):
		if self._did_video:
			return ''
		self._did_video = 1
		return '\0\0\0\0' * 320 * 240

def reader(url):
	try:
		rdr = _Reader(url)
	except IOError:
		return None
	if not rdr.HasVideo():
		print "DBG: No video in", url
		return None
	return rdr
