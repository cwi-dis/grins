# Cache durations of movie files

import FileCache
import urllib
import Qt
import QuickTime

def getduration(filename):
	try:
		filename = urllib.urlretrieve(filename)[0]
	except IOError:
		return 0
	try:
		movieResRef = Qt.OpenMovieFile(filename, 1)
	except Qt.Error, arg:
		print 'Cannot open QT movie:',filename, arg
		return 0
	movie, dummy = Qt.NewMovieFromFile(movieResRef,
		QuickTime.newMovieDontResolveDataRefs)
	duration = movie.GetMovieDuration()
	scale = movie.GetMovieTimeScale()
	duration = duration/float(scale)
	return duration

duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
