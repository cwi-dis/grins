__version__ = "$Id$"

try:
    import Qt
except ImportError:
    Qt = None

mcTopLeftMovie = 1
mcScaleMovieToFit = 1 << 1
mcWithBadge = 1 << 2
mcNotVisible = 1 << 3
mcWithFrame = 1 << 4

if Qt is not None:
    VisualMediaCharacteristic   = Qt.BuildOSType('eyes')
    AudioMediaCharacteristic= Qt.BuildOSType('ears')
    kCharacteristicCanSendVideo = Qt.BuildOSType('vsnd')
    kCharacteristicProvidesActions = Qt.BuildOSType('actn')
    kCharacteristicNonLinear= Qt.BuildOSType('nonl')
    kCharacteristicCanStep  = Qt.BuildOSType('step')
    kCharacteristicHasNoDuration = Qt.BuildOSType('noti')

movieTrackMediaType = 1 << 0
movieTrackCharacteristic= 1 << 1
movieTrackEnabledOnly   = 1 << 2

hintsScrubMode  = 1 << 0
hintsLoop   = 1 << 1
hintsDontPurge  = 1 << 2
hintsUseScreenBuffer= 1 << 5
hintsAllowInterlace = 1 << 6
hintsUseSoundInterp = 1 << 7
hintsHighQuality= 1 << 8
hintsPalindrome = 1 << 9
hintsInactive   = 1 << 11
hintsOffscreen  = 1 << 12
hintsDontDraw   = 1 << 13
hintsAllowBlacklining   = 1 << 14
hintsDontUseVideoOverlaySurface = 1 << 16
hintsIgnoreBandwidthRestrictions = 1 << 17
hintsPlayingEveryFrame  = 1 << 18
hintsAllowDynamicResize = 1 << 19
hintsSingleField= 1 << 20
hintsNoRenderingTimeOut = 1 << 21

nextTimeMediaSample         = 1 << 0
nextTimeMediaEdit           = 1 << 1
nextTimeTrackEdit           = 1 << 2
nextTimeSyncSample          = 1 << 3
nextTimeStep                = 1 << 4
nextTimeEdgeOK              = 1 << 14
nextTimeIgnoreActiveSegment = 1 << 15
