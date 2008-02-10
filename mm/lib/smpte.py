'''\
This module implements conversions between SMPTE time codes.

4 variants of SMPTE timecodes have been implemented, and conversions
between all 4 are possible.  The 4 SMPTE timecodes are:
SMPTE-30-drop (29.97 frames per second, frame numbers go from 0 to 29,
        but some frame numbers are skipped);
SMPTE-30 (30 frames per second, frames numbers go from 0 to 29);
SMPTE-25 (25 frames per second, frames numbers go from 0 to 24);
SMPTE-24 (24 frames per second, frames numbers go from 0 to 23).

This module defines 4 classes, one for each of the timecode systems.
The interface to the 4 classes are the same:
The constructor takes one argument, the timecode to be converted.
This timecode can be specified in several ways:
- as an integer: the timecode refers to a frame number;
- as a float: the argument is the time in seconds;
- as a tuple: the timecode is of the form (hours, minutes, seconds, frames),
  where the initial values are optional;
- as a string of the form hh:mm:ss.ff where all but the ss are
  optional;
- as an instance of one of the 4 classes defined in this module.  In
  this case the frame number of the initializer is converted to a time
  using the frame rate of the initializer, and this time is converted
  to a frame number using the frame rate of the class being created.
Instances have the following methods:
- GetHMSF() - returns a tuple giving (hours, minutes, seconds, frames)
- GetFrame() - returns the frame number
- GetTime() - returns the time
'''

__version__ = "$Id$"

from types import *
import string
import re
hmsf = re.compile(r'(?:(?:(?P<h>\d{2}):)?(?P<m>\d{2}):)?(?P<s>\d{2})(?P<f>\.\d{2})?$')

class _SMPTE:
    __timesep = ':'
    __framesep = ':'
    _label = ''

    def __init__(self, val):
        if type(val) is IntType:
            self._frames = val
        elif type(val) is FloatType:
            self._frames = int(val * self.FramesPerSecond + 0.5)
        elif type(val) is TupleType:
            if len(val) > 4:
                raise TypeError, 'tuple too long'
            if len(val) > 3:
                h = val[-4]
            else:
                h = 0
            if len(val) > 2:
                m = val[-3]
            else:
                m = 0
            if len(val) > 1:
                s = val[-2]
            else:
                s = 0
            if len(val) > 0:
                f = val[-1]
            else:
                f = 0
            self._frames = self._convert(h, m, s, f)
        elif type(val) is StringType:
            res = hmsf.match(val)
            if res is None:
                raise ValueError, 'bad SMPTE string'
            h, m, s, f = res.group('h', 'm', 's', 'f')
            if h is not None:
                h = string.atoi(h)
            else:
                h = 0
            if m is not None:
                m = string.atoi(m)
            else:
                m = 0
            if s is not None:
                s = string.atoi(s)
            else:
                s = 0
            if f is not None:
                f = string.atoi(f)
            else:
                f = 0
            self._frames = self._convert(h, m, s, f)
        else:
            self._frames = int(val.GetTime() * self.FramesPerSecond + 0.5)

    def __repr__(self):
        return '%s((%d,%d,%d,%d))' % ((self.__class__.__name__,) +
                                      self.GetHMSF())

    def __str__(self):
        h, m, s, f = self.GetHMSF()
        return '%s%d%s%d%s%d%s%d' % (self._label, h, self.__timesep, m,
                                     self.__timesep, s,
                                     self.__framesep, f)

    def SetFormat(self, label = '', timesep = ':', framesep = ':'):
        self._label = label
        self.__timesep = timesep
        self.__framesep = framesep

    def _convert(self, h, m, s, f):
        return ((h * 60 + m) * 60 + s) * self.FramesPerSecond + f

    def GetHMSF(self):
        h, f = divmod(self._frames, self.FramesPerHour)
        m, f = divmod(f, self.FramesPerMinute)
        s, f = divmod(f, self.FramesPerSecond)
        return h, m, s, f

    def GetFrame(self):
        return self._frames

    def GetTime(self):
        return float(self._frames) / self.FramesPerSecond

class Smpte30Drop(_SMPTE):
    FramesPerSecond = 29.97
    FramesPerMinute = FramesPerSecond * 60
    FramesPerHour = int(FramesPerMinute * 60)
    _label = 'smpte-30-drop:'

    def _convert(self, h, m, s, f):
        m = m + h * 60
        if s == 0 and m % 10 != 0 and f in (0, 1):
            raise ValueError, 'illegal frame number'
        drop = m / 10
        drop = drop * 18
        drop = drop + (m % 10) * 2
        return (m * 60 + s) * 30 + f - drop

    def GetHMSF(self):
        m, f = divmod(self._frames, 17982) # 17982 frames in 10 min
        h, m = divmod(m * 10, 60)
        if f < 2:
            return h, m, 0, f
        M, f = divmod(f-2, 1798)
        m = m + M
        f = f + 2
        s, f = divmod(f, 30)
        return h, m, s, f

class Smpte30(_SMPTE):
    FramesPerSecond = 30
    FramesPerMinute = FramesPerSecond * 60
    FramesPerHour = FramesPerMinute * 60
    _label = 'smpte-30:'

class Smpte25(_SMPTE):
    FramesPerSecond = 25
    FramesPerMinute = FramesPerSecond * 60
    FramesPerHour = FramesPerMinute * 60
    _label = 'smpte-25:'

class Smpte24(_SMPTE):
    FramesPerSecond = 24
    FramesPerMinute = FramesPerSecond * 60
    FramesPerHour = FramesPerMinute * 60
    _label = 'smpte-24:'
