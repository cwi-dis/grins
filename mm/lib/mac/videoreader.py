# Video file reader
import sys
import Qt
import QuickTime
import Qd
import Qdoffs
import QDOffscreen
import Res
import MediaDescr
import imgformat
import os
sys.path.append('swdev:jack:cmif:pylib:')
import audio.format
import MMurl
import macfs

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
		path = MMurl.urlretrieve(url)[0]
		fsspec = macfs.FSSpec(path)
		fd = Qt.OpenMovieFile(fsspec, 0)
		self.movie, d1, d2 = Qt.NewMovieFromFile(fd, 0, 0)
		try:
			self.audiotrack = self.movie.GetMovieIndTrackType(1,
				QuickTime.SoundMediaType, QuickTime.movieTrackMediaType)
			self.audiomedia = self.audiotrack.GetTrackMedia()
		except Qt.Error:
			self.audiotrack = self.audiomedia = None
			self.audiodescr = {}
		else:
			handle = Res.Resource('')
			self.audiomedia.GetMediaSampleDescription(1, handle)
			print len(handle.data)
			self.audiodescr = MediaDescr.SoundDescription.decode(handle.data)
			del handle
			print 'AUDIO DUR', self._gettrackduration_ms(self.audiotrack)
	
		try:	
			self.videotrack = self.movie.GetMovieIndTrackType(1,
					QuickTime.VideoMediaType, QuickTime.movieTrackMediaType)
			self.videomedia = self.videotrack.GetTrackMedia()
		except Qt.Error:
			self.videotrack = self.videomedia = self.videotimescale = None
		else:
			handle = Res.Resource('')
			self.videomedia.GetMediaSampleDescription(1, handle)
			print 'video', len(handle.data)
			self.videodescr = MediaDescr.ImageDescription.decode(handle.data)
			del handle
			self._initgworld()
			print 'VIDEO DUR', self._gettrackduration_ms(self.videotrack)
		
	def __del__(self):
		self.audiomedia = None
		self.audiotrack = None
		self.videomedia = None
		self.videotrack = None
		self.movie = None
		
	def _initgworld(self):
		old_port, old_dev = Qdoffs.GetGWorld()
		try:
			movie_w = self.videodescr['width']
			movie_h = self.videodescr['height']
			movie_rect = (0, 0, movie_w, movie_h)
			self.gworld = Qdoffs.NewGWorld(32,  movie_rect, None, None, QDOffscreen.keepLocal)
			self.pixmap = self.gworld.GetGWorldPixMap()
			Qdoffs.LockPixels(self.pixmap)
			Qdoffs.SetGWorld(self.gworld.as_GrafPtr(), None)
			Qd.EraseRect(movie_rect)
			self.movie.SetMovieGWorld(self.gworld.as_GrafPtr(), None)
			self.movie.SetMovieBox(movie_rect)
			self.movie.SetMovieActive(1)
			self.movie.MoviesTask(0)
			self.movie.SetMoviePlayHints(QuickTime.hintsHighQuality, QuickTime.hintsHighQuality)
			# XXXX framerate
			self.videocurtime = 0
		finally:
			Qdoffs.SetGWorld(old_port, old_dev)
		
	def _gettrackduration_ms(self, track):
		movietimescale = self.movie.GetMovieTimeScale()
		tracktime = track.GetTrackDuration()
		value, d1, d2 = Qt.ConvertTimeScale((tracktime, movietimescale, None), 1000)
		return value
		
	def HasAudio(self):
		return not self.audiotrack is None
		
	def HasVideo(self):
		return not self.videotrack is None
		
	def GetAudioFormat(self):
		print 'audiofmt', self.audiodescr
		bps = self.audiodescr['sampleSize']
		nch = self.audiodescr['numChannels']
		if nch == 1:
			channels = ['mono']
		elif nch == 2:
			channels = ['left', 'right']
		else:
			channels = map(lambda x: str(x+1), range(nch))
		if bps % 8:
			# Funny bits-per sample. We pretend not to understand
			blocksize = 0
			fpb = 0
		else:
			# QuickTime is easy (for as far as we support it): samples are always a whole
			# number of bytes, so frames are nchannels*samplesize, and there's one frame per block.
			blocksize = (bps/8)*nch
			fpb = 1
		if self.audiodescr['dataFormat'] == 'raw ':
			encoding = 'linear-excess'
		elif self.audiodescr['dataFormat'] == 'twos':
			encoding = 'linear-signed'
		else:
			encoding = 'quicktime-coding-%s'%self.audiodescr['dataFormat']
		return audio.format.AudioFormatLinear('quicktime_audio', 'QuickTime Audio Format', 
			['mono'], encoding, blocksize=blocksize, fpb=fpb, bps=bps)
			
	def GetAudioFrameRate(self):
		return int(self.audiodescr['sampleRate'])
		
	def GetVideoFormat(self):
		width = self.videodescr['width']
		height = self.videodescr['height']
		return VideoFormat('dummy_format', 'Dummy Video Format', width, height, imgformat.macrgb)
		
	def GetVideoFrameRate(self):
		return 25
		
	def ReadAudio(self, nframes):
		return ''
		
	def ReadVideo(self, time=None):
		if not time is None:
			self.videocurtime = time
		tv, dur = self.videomedia.GetMediaNextInterestingTime(
				QuickTime.nextTimeMediaSample|QuickTime.nextTimeEdgeOK,
				self.videocurtime, 1.0)
		if tv < 0:
			return self.videocurtime, None
		print 'DBG: old', self.videocurtime, 'tv, dur', tv, dur
		self.videocurtime = tv+dur
		self.movie.SetMovieTimeValue(self.videocurtime)
		self.movie.MoviesTask(0)
		return tv, self._getpixmapcontent()
		
	def _getpixmapcontent(self):
		"""Shuffle the offscreen PixMap data, because it may have funny stride values"""
		rowbytes = Qdoffs.GetPixRowBytes(self.pixmap)
		width = self.videodescr['width']
		height = self.videodescr['height']
		start = 0
		rv = ''
		for i in range(height):
			nextline = Qdoffs.GetPixMapBytes(self.pixmap, start, width*4)
			start = start + rowbytes
			rv = rv + nextline
		return rv

def reader(url):
##	print 'No video conversion yet'
##	return None
	try:
		rdr = _Reader(url)
	except IOError:
		return None
	if not rdr.HasVideo():
		print "DBG: No video in", url
		return None
	if not rdr.HasAudio():
		print "DBG: warning: no audio"
	return rdr

def _test():
	import img
	import MacOS
	Qt.EnterMovies()
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
	timestamp, data = rdr.ReadVideo()
	while data:
		fname = 'frame%04.4d.jpg'%num
		num = num+1
		pname = os.path.join(dstdir, fname)
		print 'Writing', fname, imgw, imgh, len(data)
##		wrt = img.writer(imgfmt, pname)
##		wrt.width = imgw
##		wrt.height = imgh
##		wrt.write(data)
		timestamp, data = rdr.ReadVideo()
##		MacOS.SetCreatorAndType(pname, 'ogle', 'JPEG')
		if num > 20: break
	print 'Total frames:', num
		
if __name__ == '__main__':
	_test()
	sys.exit(1)
		
