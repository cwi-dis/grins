__version__ = "$Id$"

try:
	import Qt
except ImportError:
	Qt = None

import ddraw

# support flags
initialized = 0
refcount = 0 

def Initialize(incrref = 1):
	global initialized
	global refcount
	if initialized:
		if incrref:
			refcount = refcount + 1
		return 1
	if Qt is None:
		return 0
	try:
		Qt.InitializeQTML()
	except:
		return 0	
	Qt.EnterMovies()
	initialized = 1
	if incrref:
		refcount = refcount + 1
	return 1

def Terminate():
	global initialized
	global refcount
	if initialized:		
		refcount = refcount - 1
		if refcount == 0:
			Qt.ExitMovies()
			Qt.TerminateQTML()
			initialized = 0

class QtPlayer:
	def __init__(self):
		self.movie = None
		self._dds = None
		self._rect = None

	def __repr__(self):
		s = '<%s instance' % self.__class__.__name__
		s = s + '>'
		return s

	def open(self, url, exporter=None):
		try:
			movieResRef = Qt.OpenMovieFileWin(url, 1)
		except Exception, arg:
			print arg
			return 0
		try:
			self.movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0, 0)
		except Exception, arg:
			print arg
			Qt.CloseMovieFile(movieResRef)
			return 0
		Qt.CloseMovieFile(movieResRef)
		l, t, r, b = self.movie.GetMovieBox()
		self._rect = l, t, r-l, b-t
		return 1

	def getMovieRect(self):
		return self._rect

	def getCurrentMovieRect(self):
		if self.movie:
			l, t, r, b = self.movie.GetMovieBox()
			return l, t, r-l, b-t
		return 0, 0

	def setMovieActive(self, flag):
		if self.movie:
			self.movie.SetMovieActive(flag)

	def createVideoDDS(self, ddobj, size=None):
		if size is not None:
			w, h = size
		else:
			w, h = self._rect[2:]

		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
		ddsd.SetSize(w, h)
		self._dds = ddobj.CreateSurface(ddsd)

		Qt.SetDDObject(ddobj)
		Qt.SetDDPrimarySurface(self._dds)

		self.movie.SetMovieBox((0, 0, w, h))
		self.movie.SetMovieActive(1)

	def __del__(self):
		del self._dds
			
	def run(self):
		if self.movie:
			self.movie.StartMovie()

	def stop(self):
		if self.movie:
			self.movie.StopMovie()
		
	def update(self):
		if self.movie:
			self.movie.MoviesTask(0)
			self.movie.UpdateMovie()
			return 1
		return 0

	def seek(self, secs):
		if self.movie:
			msecs = int(1000*secs)
			self.movie.SetMovieTimeValue(msecs)

	def getDuration(self):
		if self.movie:
			return 0.001*self.movie.GetMovieDuration()
		return 0

	def getTime(self):
		if self.movie:
			msecs = self.movie.GetMovieTime()[0]
			return msecs/1000.0
		return 0