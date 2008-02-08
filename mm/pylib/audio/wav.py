__version__ = "$Id$"

import audio
from format import *
from chunk import Chunk

_WAVE_FORMAT_PCM = 0x0001
_IBM_FORMAT_MULAW = 0x0101
_IBM_FORMAT_ALAW = 0x0102
_IBM_FORMAT_ADPCM = 0x0103

class reader:
    def __init__(self, file):
        if type(file) == type(''):
            self.__filename = file # only needed for __repr__
            self.__file = file = open(file, 'rb')
        else:
            self.__filename = '<unknown filename>'
            self.__file = file
        self.__soundpos = 0
        self.__framesread = 0
        self.__data_chunk = None
        self.__chunk = None
        self.__format = None
        # start parsing
        self.__file = file = Chunk(file, bigendian = 0)
        if file.getname() != 'RIFF':
            raise audio.Error, 'file does not start with RIFF id'
        if file.read(4) != 'WAVE':
            raise audio.Error, 'not a WAVE file'

    def __repr__(self):
        if self.__format is None:
            return '<WAVreader instance, file=%s, unknown format>' % self.__filename
        return '<WAVreader instance, file=%s, format=%s, framerate=%d>' % (self.__filename, `self.__format`, self.__framerate)

    def __read_until(self, name):
        if self.__chunk is not None:
            self.__chunk.skip()
        while 1:
            try:
                chunk = Chunk(self.__file, bigendian = 0)
            except EOFError:
                raise audio.Error, 'chunk %s not found' % name
            else:
                self.__chunk = chunk
            chunkname = chunk.getname()
            if chunkname == 'fmt ':
                self.__read_fmt_chunk(chunk)
            elif chunkname == 'data':
                self.__read_data_chunk(chunk)
            if name == chunkname:
                return
            chunk.skip()

    def __read_fmt_chunk(self, chunk):
        from struct import unpack
        wFormatTag, nchannels, self.__framerate, dwAvgBytesPerSec, wBlockAlign = unpack('<hhllh', chunk.read(14))
        if nchannels < 1 or nchannels > 2:
            raise audio.Error, 'Unsupported format'
        if wFormatTag == _WAVE_FORMAT_PCM:
            bps = unpack('<h', chunk.read(2))[0]
            if bps > 16:
                raise audio.Error, 'Unsupported format'
            if bps <= 8:
                if nchannels == 1:
                    self.__format = linear_8_mono_excess
                elif nchannels == 2:
                    self.__format = linear_8_stereo_excess
            elif bps <= 16:
                self.__encoding = 'linear'
                if nchannels == 1:
                    self.__format = linear_16_mono_little
                elif nchannels == 2:
                    self.__format = linear_16_stereo_little
        else:
            raise audio.Error, 'unknown WAVE format'

    def __read_data_chunk(self, chunk):
        if self.__format is None:
            raise audio.Error, 'data chunk before fmt chunk'
        self.__data_chunk = chunk
        fmt = self.__format
        self.__nframes = chunk.getsize() * fmt.getfpb() / fmt.getblocksize()
        self.__data_curpos = self.getpos()

    def getformat(self):
        if self.__format is None:
            self.__read_until('fmt ')
        return self.__format

    def getnframes(self):
        if self.__format is None:
            self.__read_until('fmt ')
        if self.__data_chunk is None:
            self.__read_until('data')
        return self.__nframes

    def getframerate(self):
        if self.__format is None:
            self.__read_until('fmt ')
        return self.__framerate

    def readframes(self, nframes = -1):
        if self.__format is None:
            self.__read_until('fmt ')
        if self.__data_chunk is None:
            self.__read_until('data')
        if self.__chunk is not self.__data_chunk:
            self.__chunk = self.__data_chunk
            self.__data_chunk.setpos(self.__data_curpos)
        fmt = self.__format
        if nframes >= 0:
            nbytes = (nframes / fmt.getfpb()) * fmt.getblocksize()
        else:
            nbytes = -1
        data = self.__data_chunk.read(nbytes)
        nframes = len(data) * fmt.getfpb() / fmt.getblocksize()
        self.__framesread = self.__framesread + nframes
        self.__data_curpos = self.getpos()
        return data, nframes

    def rewind(self):
        self.__data_chunk.seek(0)
        self.__framesread = 0
        self.__data_curpos = self.getpos()
        self.__chunk = self.__data_chunk

    def getpos(self):
        if self.__data_chunk is None:
            self.__read_until('data')
        return self.__data_chunk.tell(), self.__framesread

    def setpos(self, (pos, framesread)):
        self.__data_chunk.seek(pos)
        self.__framesread = framesread

    def getmarkers(self):
        return []
