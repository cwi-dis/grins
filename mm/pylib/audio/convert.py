__version__ = "$Id$"

import audio
from format import *
import string

class audio_filter:
    def __init__(self, rdr, fmt):
        self._rdr = rdr
        self._srcfmt = rdr.getformat()
        self._dstfmt = fmt

    def __repr__(self):
        return '<%s instance, src=%s, format=%s>' % (self.__class__.__name__, `self._rdr`, `self._srcfmt`)

    def getformat(self):
        return self._dstfmt

    def readframes(self, nframes = -1):
        return self._rdr.readframes(nframes)

    def getnframes(self):
        return self._rdr.getnframes()

    def getframerate(self):
        return self._rdr.getframerate()

    def rewind(self):
        self._rdr.rewind()

    def getpos(self):
        return self._rdr.getpos()

    def setpos(self, pos):
        self._rdr.setpos(pos)

    def getmarkers(self):
        return self._rdr.getmarkers()

class linear2linear(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__owidth = (self._srcfmt.getbps() + 7) / 8
        self.__nwidth = (self._dstfmt.getbps() + 7) / 8

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        return audioop.lin2lin(data, self.__owidth, self.__nwidth), nframes

class ulaw2linear(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__width = (self._dstfmt.getbps() + 7) / 8

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        return audioop.ulaw2lin(data, self.__width), nframes

class linear2ulaw(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__width = (self._srcfmt.getbps() + 7) / 8

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        return audioop.lin2ulaw(data, self.__width), nframes

class dvi2linear(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__width = (self._dstfmt.getbps() + 7) / 8
        self.__state = None
        self.__positions = []

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        data, self.__state = audioop.adpcm2lin(data, self.__width,
                                               self.__state)
        return data, nframes

    def rewind(self):
        self._rdr.rewind()
        self.__state = None

    def getpos(self):
        pos = self._rdr.getpos()
        self.__positions.append((pos, self.__state))
        return pos

    def setpos(self, pos):
        for p, s in self.__positions:
            if pos is p:
                break
        else:
            raise audio.Error, 'seeking to position not retrieved with getpos'
        self._rdr.setpos(pos)
        self.__state = s

class linear2dvi(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__width = (self._srcfmt.getbps() + 7) / 8
        self.__state = None
        self.__positions = []

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        data, self.__state = audioop.lin2adpcm(data, self.__width,
                                               self.__state)
        return data, nframes

    def rewind(self):
        self._rdr.rewind()
        self.__state = None

    def getpos(self):
        pos = self._rdr.getpos()
        self.__positions.append((pos, self.__state))
        return pos

    def setpos(self, pos):
        for p, s in self.__positions:
            if pos is p:
                break
        else:
            raise audio.Error, 'seeking to position not retrieved with getpos'
        self._rdr.setpos(pos)
        self.__state = s

class stereo2mono(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__width = (self._srcfmt.getbps() + 7) / 8
        self.__fac1 = self.__fac2 = .5

    def setfactors(self, fac1, fac2):
        self.__fac1 = fac1
        self.__fac2 = fac2

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        return audioop.tomono(data, self.__width,
                              self.__fac1, self.__fac2), nframes

class mono2stereo(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__width = (self._srcfmt.getbps() + 7) / 8
        self.__fac1 = self.__fac2 = 1.0

    def setfactors(self, fac1, fac2):
        self.__fac1 = fac1
        self.__fac2 = fac2

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes)
        return audioop.tostereo(data, self.__width,
                                self.__fac1, self.__fac2), nframes

class unsigned2linear8(audio_filter):
    __translation = None

    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        if not unsigned2linear8.__translation:
            # initialize class variable __translation
            unsigned2linear8.__translation = string.join(
                    map(chr, range(128, 256) + range(0, 128)), '')

    def readframes(self, nframes = -1):
        data, nframes = self._rdr.readframes(nframes)
        return string.translate(data, self.__translation), nframes

# not very efficient...
class unsigned2linear16(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        self.__endian = fmt.getendian()

    def readframes(self, nframes = -1):
        import array
        data, nframes = self._rdr.readframes(nframes)
        a = array.array('h', data)
        if self.__endian != endian:
            a.byteswap()
        for i in range(len(a)):
            a[i] = (a[i] + 0x8000) & 0xffff
        if self.__endian != endian:
            a.byteswap()
        return a.tostring(), nframes

class swap(audio_filter):
    def __init__(self, rdr, fmt):
        audio_filter.__init__(self, rdr, fmt)
        width = (self._srcfmt.getbps() + 7) / 8
        if width == 1:
            self.__fmt = 'b'
        elif width == 2:
            self.__fmt = 'h'
        elif width == 4:
            self.__fmt = 'l'
        else:
            raise audio.Error, "can't swap this width"

    def readframes(self, nframes = -1):
        import array
        data, nframes = self._rdr.readframes(nframes)
        a = array.array(self.__fmt, data)
        a.byteswap()
        return a.tostring(), nframes

class cvrate(audio_filter):
    def __init__(self, rdr, rate):
        audio_filter.__init__(self, rdr, rdr.getformat())
        self.__width = (self._srcfmt.getbps() + 7) / 8
        self.__nchannels = self._srcfmt.getnchannels()
        self.__inrate = rdr.getframerate()
        self.__outrate = rate
        self.__state = None
        self.__positions = []

    def __repr__(self):
        return '<%s instance, src=%s, format=%s, framerate=%d>' % (self.__class__.__name__, `self._rdr`, `self._srcfmt`, self.__outrate)

    def readframes(self, nframes = -1):
        import audioop
        data, nframes = self._rdr.readframes(nframes * self.__inrate / self.__outrate)
        data, self.__state = audioop.ratecv(data, self.__width,
                                self.__nchannels, self.__inrate,
                                self.__outrate, self.__state)
        return data, len(data) / (self.__width * self.__nchannels)

    def rewind(self):
        self._rdr.rewind()
        self.__state = None

    def getpos(self):
        pos = self._rdr.getpos()
        self.__positions.append((pos, self.__state))
        return pos

    def setpos(self, pos):
        for p, s in self.__positions:
            if pos is p:
                break
        else:
            raise audio.Error, 'seeking to position not retrieved with getpos'
        self._rdr.setpos(pos)
        self.__state = s

    def getframerate(self):
        return self.__outrate

    def getnframes(self):
        nframes = self._rdr.getnframes()
        if nframes < 0:
            return nframes
        return (nframes * self.__outrate + self.__inrate - 1) / self.__inrate

    def getmarkers(self):
        markers = []
        for id, pos, name in self._rdr.getmarkers():
            markers.append((id, (pos * self.__outrate + self.__inrate - 1) / self.__inrate, name))
        return markers

class looper(audio_filter):
    def __init__(self, rdr, count):
        audio_filter.__init__(self, rdr, rdr.getformat())
        self.__count = count

    def readframes(self, nframes = -1):
        data, gotframes = self._rdr.readframes(nframes)
        if not gotframes:
            if self.__count is None or self.__count > 1:
                if not self.__count is None:
                    self.__count = self.__count - 1
                self._rdr.rewind()
                data, gotframes = self._rdr.readframes(nframes)
        return data, gotframes

    def getmarkers(self):
        omarkers = self._rdr.getmarkers()
        nframes = self._rdr.getnframes()
        if nframes < 0:
            return omarkers
        markers = []
        if self.__count == None:
            if omarkers:
                # XXX How should we handle this??
                print "Warning: skipping markers on indefinitely repeating audio"
        else:
            for i in range(self.__count):
                for id, pos, name in omarkers:
                    markers.append((id, pos + i*nframes, name))
        return markers

## This one is incorrect, really:
##     def getnframes(self):
##         return self._rdr.getnframes()

# table of conversions.
# tuples are (src_formats, dst_formats, converter, lossiness)
# lossiness is one of:
SHUFFLE = 0     # just reshuffle bits (no information loss)
WASTEFUL = 1    # use more bits than necessary (loose information about range)
LOSSY = 2       # use fewer bits than needed (loss of information)

_converters = [
        (linear_8_mono_signed,
         linear_16_mono,
         linear2linear,
         WASTEFUL),

        (linear_16_mono,
         linear_8_mono_signed,
         linear2linear,
         LOSSY),

        (linear_8_stereo_signed,
         linear_16_stereo,
         linear2linear,
         WASTEFUL),

        (linear_16_stereo,
         linear_8_stereo_signed,
         linear2linear,
         LOSSY),

        (ulaw_mono,
         linear_8_mono_signed,
         ulaw2linear,
         LOSSY),

        (ulaw_mono,
         linear_16_mono,
         ulaw2linear,
         WASTEFUL),

        (ulaw_stereo,
         linear_8_stereo_signed,
         ulaw2linear,
         LOSSY),

        (ulaw_stereo,
         linear_16_stereo,
         ulaw2linear,
         WASTEFUL),

        (linear_8_mono_signed,
         ulaw_mono,
         linear2ulaw,
         LOSSY),

        (linear_16_mono,
         ulaw_mono,
         linear2ulaw,
         LOSSY),

        (linear_8_stereo_signed,
         ulaw_stereo,
         linear2ulaw,
         LOSSY),

        (linear_16_stereo,
         ulaw_stereo,
         linear2ulaw,
         LOSSY),

        (dvi_mono,
         linear_8_mono_signed,
         dvi2linear,
         LOSSY),

        (dvi_mono,
         linear_16_mono,
         dvi2linear,
         WASTEFUL),

# XXX can dvi2linear really do this?
##     (dvi_stereo,
##      linear_8_stereo_signed,
##      dvi2linear,
##      LOSSY),

##     (dvi_stereo,
##      linear_16_stereo,
##      dvi2linear,
##      WASTEFUL),

        (linear_8_mono_signed,
         dvi_mono,
         linear2dvi,
         LOSSY),

        (linear_16_mono,
         dvi_mono,
         linear2dvi,
         LOSSY),

# XXX can linear2dvi really do this?
##     (linear_8_stereo_signed,
##      dvi_stereo,
##      linear2dvi,
##      LOSSY),

##     (linear_16_stereo,
##      dvi_stereo,
##      linear2dvi,
##      WASTEFUL),

        (linear_8_stereo_signed,
         linear_8_mono_signed,
         stereo2mono,
         LOSSY),

        (linear_16_stereo,
         linear_16_mono,
         stereo2mono,
         LOSSY),

        (linear_8_mono_signed,
         linear_8_stereo_signed,
         mono2stereo,
         WASTEFUL),

        (linear_16_mono,
         linear_16_stereo,
         mono2stereo,
         WASTEFUL),

        (linear_8_mono_excess,
         linear_8_mono_signed,
         unsigned2linear8,
         SHUFFLE),

        (linear_8_mono_signed,
         linear_8_mono_excess,
         unsigned2linear8,
         SHUFFLE),

        (linear_8_stereo_excess,
         linear_8_stereo_signed,
         unsigned2linear8,
         SHUFFLE),

        (linear_8_stereo_signed,
         linear_8_stereo_excess,
         unsigned2linear8,
         SHUFFLE),

        (linear_16_mono_big_excess,
         linear_16_mono_big_signed,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_mono_big_signed,
         linear_16_mono_big_excess,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_mono_little_excess,
         linear_16_mono_little_signed,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_mono_little_signed,
         linear_16_mono_little_excess,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_stereo_big_excess,
         linear_16_stereo_big_signed,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_stereo_big_signed,
         linear_16_stereo_big_excess,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_stereo_little_excess,
         linear_16_stereo_little_signed,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_stereo_little_signed,
         linear_16_stereo_little_excess,
         unsigned2linear16,
         SHUFFLE),

        (linear_16_mono_big_excess,
         linear_16_mono_little_excess,
         swap,
         SHUFFLE),

        (linear_16_mono_little_excess,
         linear_16_mono_big_excess,
         swap,
         SHUFFLE),

        (linear_16_stereo_big_excess,
         linear_16_stereo_little_excess,
         swap,
         SHUFFLE),

        (linear_16_stereo_little_excess,
         linear_16_stereo_big_excess,
         swap,
         SHUFFLE),

        (linear_16_mono_big_signed,
         linear_16_mono_little_signed,
         swap,
         SHUFFLE),

        (linear_16_mono_little_signed,
         linear_16_mono_big_signed,
         swap,
         SHUFFLE),

        (linear_16_stereo_big_signed,
         linear_16_stereo_little_signed,
         swap,
         SHUFFLE),

        (linear_16_stereo_little_signed,
         linear_16_stereo_big_signed,
         swap,
         SHUFFLE),
        ]

def convert(rdr, dstfmts = None, rates = None, loop=1):
    if dstfmts is not None:
        try:
            dummy = dstfmts[0]
        except:
            # can't index, so make into tuple
            dstfmts = (dstfmts,)

    if rates is not None:
        try:
            dummy = rates[0]
        except:
            # can't index, so make into tuple
            rates = (rates,)

    if rates is not None:
        # XXX this needs work to find the best rate to convert to
        rate = rdr.getframerate()
        if rate in rates:
            rates = None    # no rate conversion necessary
        else:
            if 2*rate in rates:
                # twice the original rate is best
                best = 2*rate
            else:
                best = rates[0]
                for r in rates:
                    if abs(r - rate) < abs(best - rate):
                        best = r
                if best == 0:
                    rates = None

    # do the rate conversion
    if rates is not None:
        rdr = _convert(rdr, (linear_8_mono_signed, linear_8_stereo_signed, linear_16_mono, linear_16_stereo))
        rdr = cvrate(rdr, best)

    # do the format conversion
    if dstfmts is not None:
        rdr = _convert(rdr, dstfmts)

    # Do the looping
    if loop != 1:
        rdr = looper(rdr, loop)
    # return the result of our efforts
    return rdr

def _convert(rdr, dstfmts):
    srcfmt = rdr.getformat()
    if srcfmt in dstfmts:
        return rdr
    converters = []
    for dstfmt in dstfmts:
        try:
            cv = _find_converter(srcfmt, dstfmt)
        except audio.Error:
            pass
        else:
            if cv:
                converters.append(cv)
    if not converters:
        raise audio.Error, 'no conversion possible'
    best = min(converters)
##     for (fmt, func) in best:
##         rdr = func(rdr, fmt)
    for (isrcfmt, idstfmt, irtn, ilossy) in best[2]:
        rdr = irtn(rdr, idstfmt)
    return rdr

## def _find_converter(srcfmt, dstfmt):
##     todo = [(srcfmt, [])]
##     fmt_seen = [srcfmt]
##     while todo:
##         fmt, converters = todo[0]
##         del todo[0]
##         for entry in _converters:
##             if fmt is entry[0]:
##                 f = entry[1]
##                 cv = converters + [(f, entry[2])]
##                 if f is dstfmt:
##                     return cv
##                 if f not in fmt_seen:
##                     fmt_seen.append(f)
##                     todo.append((f, cv))

_generated = {}

def _find_converter(srcfmt, dstfmt):
    """Return a converter from srcfmt to dstfmt.
    A converter is a list [lossy, length, list-of-tuples],
    where each tuple is (srcfmt, dstfmt, func, lossy).
    Calling each of the functions in order will convert your image.
    """

    global _generated
    #
    # If formats are the same return the dummy converter
    #
    if srcfmt is dstfmt: return []
    #
    # Otherwise, if we have a converter, return that one
    #
    for this in _converters:
        isrcfmt, idstfmt, irtn, ilossy = this
        if (srcfmt, dstfmt) == (isrcfmt, idstfmt):
            return [ilossy, 1, [this]]
    #
    # Finally, we try to create a converter
    #
    if not _generated.has_key(srcfmt):
        # Not there yet. Try to create it.
        _generated[srcfmt] = _enumerate_converters(srcfmt)

    if not _generated[srcfmt].has_key(dstfmt):
        raise audio.Error, 'no conversion from %s to %s possible' % \
                     (srcfmt.getname(), dstfmt.getname())

    cf = _generated[srcfmt][dstfmt]
    return cf

def _enumerate_converters(srcfmt):
    cvs = {}
    steps = 0
    while 1:
        workdone = 0
        for this in _converters:
            isrcfmt, idstfmt, irtn, ilossy = this
            #
            # First see if the source format is of any use.
            #
            if isrcfmt == srcfmt:
                #
                # This converter directly understands our
                # source format. Remember it.
                #
                template = [ilossy, 1, [this]]
            elif cvs.has_key(isrcfmt):
                #
                # We have a path to this format, so
                # this converter can help us further.
                #
                template = cvs[isrcfmt][:]
                template[0] = max(template[0], ilossy)
                template[1] = template[1] + 1
                template[2] = template[2] + [this]
            else:
                continue
            #
            # Next, check whether we want this converter
            # (if it is the first one for this dstfmt, or
            # if it is better than what we have)
            #
            if not cvs.has_key(idstfmt):
                cvs[idstfmt] = template
                workdone = 1
            else:
                previous = cvs[idstfmt]
                if template < previous:
                    cvs[idstfmt] = template
                    workdone = 1
        if not workdone:
            break
        #
        # Finally, a check for loops.
        #
        steps = steps + 1
        if steps > len(_converters):
            print '------------------loop in emunerate_converters--------'
            print 'CONVERTERS:'
            print _converters
            print 'RESULTS:'
            print cvs
            raise audio.Error, 'Internal error - loop'
    return cvs
