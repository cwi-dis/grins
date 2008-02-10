__version__ = "$Id$"

# Cache durations of movie files

import MMurl
from Carbon import Qt
import windowinterface
if not windowinterface._qtavailable():
    Qt = None
from Carbon import QuickTime

def get(url):
    if not Qt:
        print 'QuickTime not available, cannot obtain movie duration'
        return 0
    try:
        filename = MMurl.urlretrieve(url)[0]
    except IOError:
        return 0
    Qt.EnterMovies()
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
