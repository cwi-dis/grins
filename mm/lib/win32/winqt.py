__version__ = "$Id$"

try:
	import Qt
except ImportError:
	Qt = None

import ddraw

# support flags
qtenvironment = None
initialized = 0
refcount = 0 

# Qt should be initialized once per session (application instance)
# Here is referenced counted and thus can be called per use 
# (remember to call Terminate() per use if used this way)
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

# Qt session terminate (application exit instance)
def Terminate():
	global initialized
	global refcount
	if initialized:		
		refcount = refcount - 1
		if refcount == 0:
			Qt.ExitMovies()
			Qt.TerminateQTML()
			initialized = 0

# module level Qt lifetime
# keep alive Qt for module lifetime
class QtEnvironment:
	def __init__(self):
		Initialize()
	def __del__(self):
		global qtenvironment
		qtenvironment = None
		Terminate()

# pay (a delay) for Qt initializarion only if used
def HasQtSupport():
	global qtenvironment
	if qtenvironment is not None:
		return 1
	if Qt is not None and Initialize(incrref = 0):
		qtenvironment = QtEnvironment()
		return 1
	return 0

# avoid overhead of setting DD on each update when not needed
QtPlayerInstances = 0

class QtPlayer:
	def __init__(self):
		Initialize()
		self.movie = None
		self._ddobj = None
		self._dds = None
		self._rect = None
		global QtPlayerInstances
		QtPlayerInstances = QtPlayerInstances + 1

	def __del__(self):
		self.movie = None
		self._dds = None
		self._ddobj = None
		self._rect = None
		Terminate()
		global QtPlayerInstances
		QtPlayerInstances = QtPlayerInstances - 1

	def __repr__(self):
		s = '<%s instance' % self.__class__.__name__
		s = s + '>'
		return s

	def open(self, url, exporter = None, asaudio = 0):
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
		if not asaudio:
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

	def setMovieRect(self, rect):
		x, y, w, h = self._rect = rect
		if self.movie:
			self.movie.SetMovieBox((x, y, x+w, y+h))

	def setMovieActive(self, flag):
		if self.movie:
			self.movie.SetMovieActive(flag)

	def createVideoDDS(self, ddobj, size = None):
		if self._rect is None:
			return
		if size is not None:
			w, h = size
		else:
			w, h = self._rect[2:]

		if ddobj is None:
			intefacePtr = Qt.GetDDObject()
			if intefacePtr:
				ddobj = ddraw.CreateDirectDrawWrapper(intefacePtr)
							
		if ddobj:
			self._ddobj = ddobj
			ddsd = ddraw.CreateDDSURFACEDESC()
			ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
			ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
			ddsd.SetSize(w, h)
			self._dds = ddobj.CreateSurface(ddsd)
			Qt.SetDDObject(self._ddobj)
			Qt.SetDDPrimarySurface(self._dds)

		self.movie.SetMovieBox((0, 0, w, h))
		self.movie.SetMovieActive(1)
			
	def run(self):
		if self.movie:
			self.movie.StartMovie()

	def stop(self):
		if self.movie:
			self.movie.StopMovie()
		
	def update(self):
		if self.movie:
			global QtPlayerInstances
			if self._dds is not None and QtPlayerInstances>1:
				Qt.SetDDObject(self._ddobj)
				Qt.SetDDPrimarySurface(self._dds)
			self.movie.MoviesTask(0)
			self.movie.UpdateMovie()
			return not self.movie.IsMovieDone()
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