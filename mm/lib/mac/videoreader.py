# Video file reader
import sys
import Qt
import imgformat
import os
sys.path.append('swdev:jack:cmif:pylib:')
import audio.format

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
		return 1
		
	def GetAudioFormat(self):
		return audio.format.AudioFormatLinear('dummy_format', 'Dummy Audio Format', 
			['mono'], 'linear-signed', blocksize=2, fpb=1, bps=16)
			
	def GetAudioFrameRate(self):
		return 44100
		
	def GetVideoFormat(self):
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
		return '\020\040\060\077' * 320 * 240

def reader(url):
	print 'No video conversion yet'
	return None
	try:
		rdr = _Reader(url)
	except IOError:
		return None
	if not rdr.HasVideo():
		print "DBG: No video in", url
		return None
	return rdr

def _test():
	import macfs
	import urllib
	import img
	import os
	import MacOS
	fss, ok = macfs.PromptGetFile('Video to convert')
	if not ok: sys.exit(0)
	path = fss.as_pathname()
	url = urllib.pathname2url(path)
	rdr = reader(url)
	if not rdr:
		sys.exit(1)
	dstfss, ok = macfs.StandardPutFile('Name for output folder')
	if not ok: sys.exit(0)
	dstdir = dstfss.as_pathname()
	num = 0
	os.mkdir(dstdir)
	videofmt = rdr.GetVideoFormat()
	imgfmt = videofmt.getformat()
	imgw, imgh = videofmt.getsize()
	data = rdr.ReadVideo()
	while data:
		fname = 'frame%04.4d.jpg'%num
		num = num+1
		pname = os.path.join(dstdir, fname)
		print 'Writing', fname
		wrt = img.writer(imgfmt, pname)
		wrt.width = imgw
		wrt.height = imgh
		wrt.write(data)
		data = rdr.ReadVideo()
		del rdr
		MacOS.SetCreatorAndType(pname, 'ogle', 'JPEG')
	print 'Total frames:', num
		
if __name__ == '__main__':
	_test()
	sys.exit(1)
		
