__version__ = "$Id$"

# Cache durations of video files

import MMurl

def _get(url):
    import mv
    try:
        filename = MMurl.urlretrieve(url)[0]
        f = mv.OpenFile(filename, mv.MV_MPEG1_PRESCAN_OFF)
        if hasattr(f, 'GetEstMovieDuration'):
            # faster but not omnipresent
            duration = float(f.GetEstMovieDuration(1000)) / 1000
        else:
            # slower (and more accurate)
            duration = float(f.GetMovieDuration(1000)) / 1000
        f.Close()
    except (mv.error, IOError), msg:
        raise IOError, msg
##         print 'error in video file', filename, ':', msg
##         return 1.0
    if duration == 0: duration = 1.0
    return duration

try:
    import mv
except ImportError:
    from MpegVideoDuration import *
else:
    get = _get
