__version__ = "$Id$"

import audio
from format import *
import struct
from chunk import Chunk

_AIFC_VERSION = 0xA2805140              # Version 1 of AIFF-C

def _read_long(file):
    try:
        return struct.unpack('>l', file.read(4))[0]
    except struct.error:
        raise EOFError

def _read_ulong(file):
    try:
        return struct.unpack('>L', file.read(4))[0]
    except struct.error:
        raise EOFError

def _read_short(file):
    try:
        return struct.unpack('>h', file.read(2))[0]
    except struct.error:
        raise EOFError

def _read_string(file):
    length = ord(file.read(1))
    if length == 0:
        data = ''
    else:
        data = file.read(length)
    if length & 1 == 0:
        dummy = file.read(1)
    return data

_HUGE_VAL = 1.79769313486231e+308 # See <limits.h>

def _read_float(f): # 10 bytes
    expon = _read_short(f) # 2 bytes
    sign = 1
    if expon < 0:
        sign = -1
        expon = expon + 0x8000
    himant = _read_ulong(f) # 4 bytes
    lomant = _read_ulong(f) # 4 bytes
    if expon == himant == lomant == 0:
        f = 0.0
    elif expon == 0x7FFF:
        f = _HUGE_VAL
    else:
        expon = expon - 16383
        shift = expon - 63
##         f = (himant * 0x100000000L + lomant) * pow(2.0, expon - 63)
        mant = himant * 0x100000000L + lomant
        if shift < 0:
            shift = -shift
            f = float(mant >> shift)
            rest = mant & ((1L << shift) - 1)
            if rest:
                f = f + float(rest) / float(1L << shift)
        else:
            f = float(mant << shift)
    return sign * f

def _write_short(f, x):
    f.write(struct.pack('>h', x))

def _write_long(f, x):
    f.write(struct.pack('>L', x))

def _write_string(f, s):
    f.write(chr(len(s)))
    f.write(s)
    if len(s) & 1 == 0:
        f.write(chr(0))

def _write_float(f, x):
    import math
    if x < 0:
        sign = 0x8000
        x = x * -1
    else:
        sign = 0
    if x == 0:
        expon = 0
        himant = 0
        lomant = 0
    else:
        fmant, expon = math.frexp(x)
        if expon > 16384 or fmant >= 1:         # Infinity or NaN
            expon = sign|0x7FFF
            himant = 0
            lomant = 0
        else:                                   # Finite
            expon = expon + 16382
            if expon < 0:                   # denormalized
                fmant = math.ldexp(fmant, expon)
                expon = 0
            expon = expon | sign
            fmant = math.ldexp(fmant, 32)
            fsmant = math.floor(fmant)
            himant = long(fsmant)
            fmant = math.ldexp(fmant - fsmant, 32)
            fsmant = math.floor(fmant)
            lomant = long(fsmant)
    _write_short(f, expon)
    _write_long(f, himant)
    _write_long(f, lomant)

class reader:
    def __init__(self, file):
        if type(file) == type(''):
            self.__filename = file # only needed for __repr__
            self.__file = file = open(file, 'rb')
        else:
            self.__filename = '<unknown filename>'
            self.__file = file
        # initialization
        self.__chunk = None     # the chunk currently being read
        self.__format = None
        self.__ssnd_chunk = None
        self.__version = None
        self.__markers = None
        self.__soundpos = 0
        self.__framesread = 0
        # start parsing
        self.__file = file = Chunk(file)
        if file.getname() != 'FORM':
            raise audio.Error, 'file does not start with FORM id'
        formdata = file.read(4)
        if formdata == 'AIFF':
            self.__aifc = 0
        elif formdata == 'AIFC':
            self.__aifc = 1
        else:
            raise audio.Error, 'not an AIFF or AIFF-C file'

    def __repr__(self):
        if self.__format is None:
            return '<AIFCreader instance, file=%s, unknown format>' % self.__filename
        return '<AIFCreader instance, file=%s, format=%s, framerate=%d>' % (self.__filename, `self.__format`, self.__framerate)

    def __read_until(self, name):
        if self.__chunk is not None:
            self.__chunk.skip()
            self.__chunk = None
        while 1:
            try:
                chunk = Chunk(self.__file)
            except EOFError:
                raise audio.Error, 'chunk %s not found' % name
            else:
                self.__chunk = chunk
            chunkname = chunk.getname()
            if chunkname == 'COMM':
                self.__read_comm_chunk(chunk)
            elif chunkname == 'SSND':
                self.__read_ssnd_chunk(chunk)
            elif chunkname == 'FVER':
                self.__read_vfer_chunk(chunk)
            elif chunkname == 'MARK':
                self.__read_mark_chunk(chunk)
            elif chunkname in ('COMT','INST','MIDI','AESD','APPL','NAME','AUTH','(c) ','ANNO'):
                self.__skip_chunk(chunk)
            else:
                raise audio.Error, 'unrecognized chunk type '+chunkname
            if name == chunkname:
                return
            chunk.skip()
            self.__chunk = None

    def __read_comm_chunk(self, chunk):
        nchannels = _read_short(chunk)
        self.__nframes = _read_long(chunk)
        bps = _read_short(chunk)
        self.__framerate = int(_read_float(chunk))
        if self.__aifc:
            #DEBUG: SGI's soundeditor produces a bad size :-(
            kludge = 0
            if chunk.chunksize == 18:
                kludge = 1
                print 'Warning: bad COMM chunk size'
                chunk.chunksize = 23
            #DEBUG end
            self.__comptype = chunk.read(4)
            #DEBUG start
            if kludge:
                length = ord(chunk.file.read(1))
                if length & 1 == 0:
                    length = length + 1
                chunk.chunksize = chunk.chunksize + length
                chunk.file.seek(-1, 1)
            #DEBUG end
            self.__compname = _read_string(chunk)
        else:
            self.__comptype = 'NONE'
            self.__compname = 'not compressed'
        if nchannels > 2:
            raise audio.Error, 'Unsupported format (nchannels=%d)'%nchannels
        if self.__comptype == 'NONE':
            if bps > 16:
                raise audio.Error, 'Unsupported format (bps=%d)'%bps
            if nchannels == 1:
                if bps <= 8:
                    self.__format = linear_8_mono_signed
                elif bps <= 16:
                    self.__format = linear_16_mono_big
            elif nchannels == 2:
                if bps <= 8:
                    self.__format = linear_8_stereo_signed
                elif bps <= 16:
                    self.__format = linear_16_stereo_big
        elif self.__comptype == 'ULAW':
            if nchannels == 1:
                self.__format = ulaw_mono
            elif nchannels == 2:
                self.__format = ulaw_stereo
        else:
            raise audio.Error, 'Unsupported format (compression=%s)'%self.__comptype

    def __read_ssnd_chunk(self, chunk):
        self.__ssnd_chunk = chunk
        self.__ssnd_offset = _read_long(chunk)
        self.__ssnd_block_size = _read_long(chunk)
        self.__ssnd_curpos = self.getpos()

    def __read_vfer_chunk(self, chunk):
        self.__version = _read_long(chunk)

    def __read_mark_chunk(self, chunk):
        self.__markers = []
        nmarkers = _read_short(chunk)
        # Some files appear to contain invalid counts.
        # Cope with this by testing for EOF.
        try:
            for i in range(nmarkers):
                id = _read_short(chunk)
                pos = _read_long(chunk)
                name = _read_string(chunk)
                if pos or name:
                    # some files appear to have
                    # dummy markers consisting of
                    # a position 0 and name ''
                    self.__markers.append((id, pos, name))
        except EOFError:
            print 'Warning: MARK chunk contains only',
            print len(self.__markers),
            if len(self.__markers) == 1: print 'marker',
            else: print 'markers',
            print 'instead of', nmarkers

    def __skip_chunk(self, chunk):
        pass

    def getformat(self):
        if self.__format is None:
            self.__read_until('COMM')
        return self.__format

    def getnframes(self):
        if self.__format is None:
            self.__read_until('COMM')
        return self.__nframes - self.__framesread

    def getframerate(self):
        if self.__format is None:
            self.__read_until('COMM')
        return self.__framerate

    def readframes(self, nframes = -1):
        if self.__format is None:
            self.__read_until('COMM')
        if self.__ssnd_chunk is None:
            self.__read_until('SSND')
        if self.__chunk is not self.__ssnd_chunk:
            self.setpos(self.__ssnd_curpos)
        fmt = self.__format
        if nframes >= 0:
            nbytes = (nframes / fmt.getfpb()) * fmt.getblocksize()
        else:
            nbytes = -1
        data = self.__ssnd_chunk.read(nbytes)
        nframes = len(data) * fmt.getfpb() / fmt.getblocksize()
        self.__framesread = self.__framesread + nframes
        self.__ssnd_curpos = self.getpos()
        return data, nframes

    def rewind(self):
        self.__ssnd_chunk.seek(8 + self.__ssnd_offset)
        self.__framesread = 0
        self.__ssnd_curpos = self.getpos()
        self.__chunk = self.__ssnd_chunk

    def getpos(self):
        if self.__ssnd_chunk is None:
            self.__read_until('SSND')
        return self.__ssnd_chunk.tell(), self.__framesread

    def setpos(self, (pos, framesread)):
        self.__ssnd_chunk.seek(pos)
        self.__framesread = framesread
        self.__chunk = self.__ssnd_chunk

    def getmarkers(self):
        if self.__markers is None:
            try:
                self.__read_until('MARK')
            except audio.Error:
                # no markers found
                self.__markers = []
        return self.__markers

class writer:
    __aiff_formats = (linear_8_mono_signed,
                      linear_16_mono_big,
                      linear_8_stereo_signed,
                      linear_16_stereo_big)
    __aifc_formats = (ulaw_mono,
                      ulaw_stereo)
    __formats = __aiff_formats + __aifc_formats

    __rates = None

    def __init__(self, filename, fmt = None, rate = None, aifc = 1):
        self.__format = None
        self.__framerate = None
        self.__initialized = 0
        self.__filename = filename # only needed for __repr__
        self.__file = open(filename, 'wb')
        self.__aifc = aifc
        if not aifc:
            self.__formats = self.__aiff_formats
        if fmt:
            self.setformat(fmt)
        if rate:
            self.setframerate(rate)

    def __repr__(self):
        return '<AIFCwriter instance, file=%s, format=%s, rate=%s>' % \
               (self.__filename, `self.__format`, `self.__framerate`)

    def __del__(self):
        self.close()

    def getformats(self):
        return self.__formats

    def getformat(self):
        return self.__format

    def setformat(self, fmt):
        if fmt not in self.__formats:
            raise audio.Error, 'bad format'
        self.__format = fmt
        self.__blocksize = fmt.getblocksize()

    def getframerates(self):
        return self.__rates

    def getframerate(self):
        return self.__framerate

    def setframerate(self, rate):
        if self.__rates and rate not in self.__rates:
            raise audio.Error, 'bad frame rate'
        self.__framerate = rate

    def writeframes(self, data):
        if not self.__initialized:
            self.__init()
        if len(data) % self.__blocksize != 0:
            raise audio.Error, 'not a whole number of frames'
        self.__length = self.__length + len(data)
        self.__file.write(data)

    def close(self):
        if not self.__initialized:
            return
        file = self.__file
        fmt = self.__format
        datalength = self.__length
        if datalength & 1:
            file.write('\000')
            datalength = datalength + 1
        file.seek(self.__form_length_pos)
        _write_long(file, datalength + self.__headersize + 16)
        file.seek(self.__nframes_pos)
        _write_long(file, self.__length * fmt.getfpb() / self.__blocksize)
        file.seek(self.__ssnd_length_pos)
        _write_long(file, datalength + 8)
        file.close()
        del self.__file
        self.__initialized = 0

    def __init(self):
        if not self.__format or not self.__framerate:
            raise audio.Error, 'no format or frame rate specified'
        import StringIO
        file = self.__file
        fmt = self.__format
        file.write('FORM')
        self.__form_length_pos = file.tell()
        _write_long(file, 0)    # to be filled in later
        self.__headersize = 0
        if self.__aifc:
            file.write('AIFC')
            file.write('FVER')
            _write_long(file, 4)
            _write_long(file, _AIFC_VERSION)
            self.__headersize = self.__headersize + 16
        else:
            file.write('AIFF')
            self.__headersize = self.__headersize + 4
        file.write('COMM')
        # measure size of COMM chunk
        comm = StringIO.StringIO()
        encoding = fmt.getencoding()
        if encoding[:6] == 'linear':
            bps = fmt.getbps()
        else:
            bps = 8
        _write_short(comm, bps)
        _write_float(comm, self.__framerate)
        if self.__aifc:
            if encoding[:6] == 'linear':
                comm.write('NONE')
                _write_string(comm, 'Not compressed')
            elif encoding == 'u-law':
                comm.write('ULAW')
                _write_string(comm, 'u-law compressed')
            else:
                raise audio.Error, 'internal error'
        data = comm.getvalue()
        comm.close()
        _write_long(file, len(data) + 6)
        _write_short(file, fmt.getnchannels())
        self.__nframes_pos = file.tell()
        _write_long(file, 0)
        file.write(data)        # write measured COMM chunk
        self.__headersize = self.__headersize + 14 + len(data)
        # the rest doesn't count as "headersize"
        file.write('SSND')
        self.__ssnd_length_pos = file.tell()
        _write_long(file, 8)
        _write_long(file, 0)
        _write_long(file, 0)
        self.__length = 0
        self.__initialized = 1
