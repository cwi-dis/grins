# Cache durations of movie files

import FileCache
import urllib
import Qt
import QuickTime

def getduration(filename):
	filename = urllib.url2pathname(filename)
	movieResRef = Qt.OpenMovieFile(filename, 1)
	movie, dummy = Qt.NewMovieFromFile(movieResRef,
		QuickTime.newMovieDontResolveDataRefs)
	duration = movie.GetMovieDuration()
	scale = movie.GetMovieTimeScale()
	duration = duration/float(scale)
	return duration

duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
