__version__ = "$Id$"

# Cache durations of movie files

import FileCache
import MMurl
import Qt
import QuickTime

def getduration(filename):
	try:
		filename = MMurl.urlretrieve(filename)[0]
	except IOError:
		return 0
	try:
		movieResRef = Qt.OpenMovieFile(filename, 1)
	except (ValueError, Qt.Error), arg:
		print 'Cannot open QT movie:',filename, arg
		return 0
	try:
		movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0,
			QuickTime.newMovieDontResolveDataRefs)
		duration = movie.GetMovieDuration()
		scale = movie.GetMovieTimeScale()
		duration = duration/float(scale)
	except Qt.Error:
		print 'Cannot obtain movie duration for', filename
		duration = 0
	return duration

duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
