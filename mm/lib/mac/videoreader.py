__version__ = "$Id$"

# Video file reader
import sys
from Carbon import Qt
from Carbon import QuickTime
from Carbon import Qd
from Carbon import Qdoffs
from Carbon import QDOffscreen
from Carbon import Res
from Carbon import MediaDescr
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
        self.movietimescale = self.movie.GetMovieTimeScale()
        try:
            self.audiotrack = self.movie.GetMovieIndTrackType(1,
                    QuickTime.AudioMediaCharacteristic, QuickTime.movieTrackCharacteristic)
            self.audiomedia = self.audiotrack.GetTrackMedia()
        except Qt.Error:
            self.audiotrack = self.audiomedia = None
            self.audiodescr = {}
        else:
            handle = Res.Handle('')
            n = self.audiomedia.GetMediaSampleDescriptionCount()
            self.audiomedia.GetMediaSampleDescription(1, handle)
            self.audiodescr = MediaDescr.SoundDescription.decode(handle.data)
            self.audiotimescale = self.audiomedia.GetMediaTimeScale()
            del handle

        try:
            self.videotrack = self.movie.GetMovieIndTrackType(1,
                    QuickTime.VisualMediaCharacteristic, QuickTime.movieTrackCharacteristic)
            self.videomedia = self.videotrack.GetTrackMedia()
        except Qt.Error:
            self.videotrack = self.videomedia = self.videotimescale = None
        if self.videotrack:
            self.videotimescale = self.videomedia.GetMediaTimeScale()
            x0, y0, x1, y1 = self.movie.GetMovieBox()
            self.videodescr = {'width':(x1-x0), 'height':(y1-y0)}
            self._initgworld()
        self.videocurtime = None
        self.audiocurtime = None


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
        finally:
            Qdoffs.SetGWorld(old_port, old_dev)

    def _gettrackduration_ms(self, track):
        tracktime = track.GetTrackDuration()
        return self._movietime_to_ms(tracktime)

    def _movietime_to_ms(self, time):
        value, d1, d2 = Qt.ConvertTimeScale((time, self.movietimescale, None), 1000)
        return value

    def _videotime_to_ms(self, time):
        value, d1, d2 = Qt.ConvertTimeScale((time, self.videotimescale, None), 1000)
        return value

    def _audiotime_to_ms(self, time):
        value, d1, d2 = Qt.ConvertTimeScale((time, self.audiotimescale, None), 1000)
        return value

    def _videotime_to_movietime(self, time):
        value, d1, d2 = Qt.ConvertTimeScale((time, self.videotimescale, None),
                        self.movietimescale)
        return value

    def HasAudio(self):
        return not self.audiotrack is None

    def HasVideo(self):
        return not self.videotrack is None

    def GetAudioDuration(self):
        if not self.audiotrack:
            return 0
        return self._gettrackduration_ms(self.audiotrack)

    def GetVideoDuration(self):
        if not self.videotrack:
            return 0
        return self._gettrackduration_ms(self.videotrack)

    def GetAudioFormat(self):
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
        tv = self.videocurtime
        if tv == None:
            tv = 0
        flags = QuickTime.nextTimeStep|QuickTime.nextTimeEdgeOK
        tv, dur = self.videomedia.GetMediaNextInterestingTime(flags, tv, 1.0)
        dur = self._videotime_to_ms(dur)
        return int((1000.0/dur)+0.5)

    def ReadAudio(self, nframes, time=None):
        if not time is None:
            self.audiocurtime = time
        flags = QuickTime.nextTimeStep|QuickTime.nextTimeEdgeOK
        if self.audiocurtime == None:
##             flags = flags | QuickTime.nextTimeEdgeOK
            self.audiocurtime = 0
        tv = self.audiomedia.GetMediaNextInterestingTimeOnly(flags, self.audiocurtime, 1.0)
##         print 'time', self.audiocurtime, 'tv', tv
        if tv < 0 or (self.audiocurtime and tv < self.audiocurtime):
            return self._audiotime_to_ms(self.audiocurtime), None
##         self.audiocurtime = tv
        h = Res.Handle('')
        desc_h = Res.Handle('')
        size, actualtime, sampleduration, desc_index, actualcount, flags = \
                self.audiomedia.GetMediaSample(h, 0, tv, desc_h, nframes)
##         print 'au', size, actualtime, sampleduration, desc_index, actualcount, flags, len(h.data)
        self.audiocurtime = actualtime + actualcount*sampleduration
##         print 'after in ms', self._audiotime_to_ms(self.audiocurtime)
##         moviecurtime = self._videotime_to_movietime(self.audiocurtime)
##         self.movie.SetMovieTimeValue(moviecurtime)
##         self.movie.MoviesTask(0)
        return self._audiotime_to_ms(actualtime), h.data

    def ReadVideo(self, time=None):
        if not time is None:
            self.videocurtime = time
        flags = QuickTime.nextTimeStep
        if self.videocurtime == None:
            flags = flags | QuickTime.nextTimeEdgeOK
            self.videocurtime = 0
        tv = self.videomedia.GetMediaNextInterestingTimeOnly(flags, self.videocurtime, 1.0)
        if tv < 0 or (self.videocurtime and tv <= self.videocurtime):
            return self._videotime_to_ms(self.videocurtime), None
        self.videocurtime = tv
        moviecurtime = self._videotime_to_movietime(self.videocurtime)
        self.movie.SetMovieTimeValue(moviecurtime)
        self.movie.MoviesTask(0)
        return self._videotime_to_ms(self.videocurtime), self._getpixmapcontent()

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
    try:
        rdr = _Reader(url)
    except IOError:
        return None
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
##         wrt = img.writer(imgfmt, pname)
##         wrt.width = imgw
##         wrt.height = imgh
##         wrt.write(data)
        timestamp, data = rdr.ReadVideo()
##         MacOS.SetCreatorAndType(pname, 'ogle', 'JPEG')
        if num > 20: break
    print 'Total frames:', num

if __name__ == '__main__':
    _test()
    sys.exit(1)
