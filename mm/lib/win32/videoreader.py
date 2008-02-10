__version__ = "$Id$"

# QuickTime video file reader for windows
# (see mac prototype video file reader)

import Qt

# windows Qt support
import winqt
import winqtcon

# windows direct draw support
import ddraw

import audio.format
import imgformat

import sys

import MMurl

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
        self.movie = None

        self.videotrack = None
        self.videomedia = None
        self.videotimescale = None

        self.audiotrack = None
        self.audiomedia = None
        self.audiotimescale = None
        self.audiodescr = {}

        self.videocurtime = None
        self.audiocurtime = None

        winqt.Initialize()

        path = MMurl.urlretrieve(url)[0]
        try:
            movieResRef = Qt.OpenMovieFileWin(path, 1)
        except Qt.Error, arg:
            print arg
        else:
            try:
                self.movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0, 0)
            except Qt.Error, arg:
                print arg
                self.movie = None
            Qt.CloseMovieFile(movieResRef)

        if not self.movie:
            raise IOError, "Cannot open: %s" % url

        self.movietimescale = self.movie.GetMovieTimeScale()

        try:
            self.audiotrack = self.movie.GetMovieIndTrackType(1,
                    winqtcon.AudioMediaCharacteristic, winqtcon.movieTrackCharacteristic)
            self.audiomedia = self.audiotrack.GetTrackMedia()
        except Qt.Error, arg:
            print arg
            self.audiotrack = self.audiomedia = None
            self.audiodescr = {}
        else:
            n = self.audiomedia.GetMediaSampleDescriptionCount()
            self.audiodescr = self.audiomedia.GetAudioMediaSampleDescription(1)
            self.audiotimescale = self.audiomedia.GetMediaTimeScale()

        try:
            self.videotrack = self.movie.GetMovieIndTrackType(1,
                    winqtcon.VisualMediaCharacteristic, winqtcon.movieTrackCharacteristic)
            self.videomedia = self.videotrack.GetTrackMedia()
        except Qt.Error, arg:
            print arg
            self.videotrack = self.videomedia = self.videotimescale = None
        if self.videotrack:
            self.videotimescale = self.videomedia.GetMediaTimeScale()
            x0, y0, x1, y1 = self.movie.GetMovieBox()
            self.videodescr = {'width':(x1-x0), 'height':(y1-y0)}
            self._initddraw()

    def __del__(self):
        self.audiomedia = None
        self.audiotrack = None
        self.videomedia = None
        self.videotrack = None
        self.movie = None
        winqt.Terminate()

    def _initddraw(self):
        movie_w = self.videodescr['width']
        movie_h = self.videodescr['height']
        movie_rect = (0, 0, movie_w, movie_h)

        ddrawobj = ddraw.CreateDirectDraw()
        ddrawobj.SetCooperativeLevel(0, ddraw.DDSCL_NORMAL)

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(movie_w, movie_h)
        dds = ddrawobj.CreateSurface(ddsd)
        pxlfmt = dds.GetPixelFormat()
        Qt.SetDDObject(ddrawobj)
        Qt.SetDDPrimarySurface(dds)
        self._ddrawobj = ddrawobj
        self._dds = dds
        self.pxlfmt = pxlfmt

        self.movie.SetMovieBox(movie_rect)
        self.movie.SetMovieActive(1)
        self.movie.MoviesTask(0)
        self.movie.SetMoviePlayHints(winqtcon.hintsHighQuality, winqtcon.hintsHighQuality)

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
        #print 'audio encoding', encoding
        return audio.format.AudioFormatLinear('quicktime_audio', 'QuickTime Audio Format',
                ['mono'], encoding, blocksize=blocksize, fpb=fpb, bps=bps)

    def GetAudioFrameRate(self):
        return int(self.audiodescr['sampleRate'])

    def GetVideoFormat(self):
        width = self.videodescr['width']
        height = self.videodescr['height']
        return VideoFormat('dummy_format', 'Dummy Video Format', width, height, imgformat.bmprgble_noalign)

    def GetVideoFrameRate(self):
        tv = self.videocurtime
        if tv == None:
            tv = 0
        flags = winqtcon.nextTimeStep|winqtcon.nextTimeEdgeOK
        tv, dur = self.videomedia.GetMediaNextInterestingTime(flags, tv, 1.0)
        dur = self._videotime_to_ms(dur)
        return int((1000.0/dur)+0.5)

    def ReadAudio(self, nframes, time=None):
        if not time is None:
            self.audiocurtime = time
        if self.audiocurtime == None:
            self.audiocurtime = 0
        flags = winqtcon.nextTimeStep | winqtcon.nextTimeEdgeOK
        tv = self.audiomedia.GetMediaNextInterestingTimeOnly(flags, self.audiocurtime, 1.0)
        if tv < 0 or (self.audiocurtime and tv < self.audiocurtime):
            return self._audiotime_to_ms(self.audiocurtime), None
        size, actualtime, sampleduration, desc_index, actualcount, flags, data = \
                self.audiomedia.GetAudioMediaSample(self.audiocurtime, nframes)
        self.audiocurtime = actualtime + actualcount*sampleduration
        return self._audiotime_to_ms(actualtime), data

    def ReadVideo(self, time=None):
        if not time is None:
            self.videocurtime = time
        flags = winqtcon.nextTimeStep
        if self.videocurtime == None:
            flags = flags | winqtcon.nextTimeEdgeOK
            self.videocurtime = 0
        tv = self.videomedia.GetMediaNextInterestingTimeOnly(flags, self.videocurtime, 1.0)
        if tv < 0 or (self.videocurtime and tv <= self.videocurtime):
            return self._videotime_to_ms(self.videocurtime), None
        self.videocurtime = tv
        moviecurtime = self._videotime_to_movietime(self.videocurtime)
        self.movie.SetMovieTimeValue(moviecurtime)
        self.movie.MoviesTask(0)
        return self._videotime_to_ms(self.videocurtime), self._dds.GetDataAsRGB24()

def reader(url):
    if not winqt.HasQtSupport():
        return None
    try:
        rdr = _Reader(url)
    except IOError, arg:
        print arg
        return None
    return rdr
