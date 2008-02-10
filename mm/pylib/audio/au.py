__version__ = "$Id$"

import audio
from format import *

_AUDIO_FILE_ENCODING_MULAW_8 = 1
_AUDIO_FILE_ENCODING_LINEAR_8 = 2
_AUDIO_FILE_ENCODING_LINEAR_16 = 3
_AUDIO_FILE_ENCODING_LINEAR_24 = 4
_AUDIO_FILE_ENCODING_LINEAR_32 = 5
_AUDIO_FILE_ENCODING_FLOAT = 6
_AUDIO_FILE_ENCODING_DOUBLE = 7
_AUDIO_FILE_ENCODING_ADPCM_G721 = 23
_AUDIO_FILE_ENCODING_ADPCM_G722 = 24
_AUDIO_FILE_ENCODING_ADPCM_G723_3 = 25
_AUDIO_FILE_ENCODING_ADPCM_G723_5 = 26
_AUDIO_FILE_ENCODING_ALAW_8 = 27

_AUDIO_UNKNOWN_SIZE = 0xFFFFFFFFL       # ((unsigned)(~0))

def _read_ulong(file):
    x = 0L
    for i in range(4):
        byte = file.read(1)
        if byte == '':
            raise EOFError
        x = x*256 + ord(byte)
    return x

def _read_long(file):
    x = 0L
    for i in range(4):
        byte = file.read(1)
        if byte == '':
            raise EOFError
        x = x*256 + ord(byte)
    if x >= 0x80000000L:
        x = x - 0x100000000L
    return int(x)

class reader:
    def __init__(self, file):
        if type(file) == type(''):
            self.__filename = file # only needed for __repr__
            self.__file = file = open(file, 'rb')
        else:
            self.__filename = '<unknown filename>'
            self.__file = file
        self.__framesread = 0
        magic = file.read(4)
        if magic != '.snd':
            raise audio.Error, 'not a AU file'
        self.__hdr_size = _read_ulong(file)
        if self.__hdr_size < 24:
            raise audio.Error, 'header size too small'
        if self.__hdr_size > 100:
            raise audio.Error, 'header size rediculously large'
        data_size = _read_long(file)
        encoding = _read_long(file)
        self.__framerate = _read_long(file)
        nchannels = _read_long(file)
        if nchannels < 1 or nchannels > 2:
            raise audio.Error, 'Unsupported format'
        if encoding == _AUDIO_FILE_ENCODING_MULAW_8:
            if nchannels == 1:
                self.__format = ulaw_mono
            else:
                self.__format = ulaw_stereo
            self.__nframes = data_size / nchannels
        elif encoding == _AUDIO_FILE_ENCODING_LINEAR_8:
            if nchannels == 1:
                self.__format = linear_8_mono_signed
            else:
                self.__format = linear_8_stereo_signed
            self.__nframes = data_size / nchannels
        elif encoding == _AUDIO_FILE_ENCODING_LINEAR_16:
            if nchannels == 1:
                self.__format = linear_16_mono_big
            else:
                self.__format = linear_16_stereo_big
            self.__nframes = data_size / nchannels / 2
        else:
            raise audio.Error, 'Unsupported format'
        if data_size < 0:
            self.__nframes = -1
        if self.__hdr_size > 24:
            dummy = file.read(self.__hdr_size - 24)

    def __repr__(self):
        return '<AUreader instance, file=%s, format=%s, framerate=%d>' % (self.__filename, `self.__format`, self.__framerate)

    def getformat(self):
        return self.__format

    def getnframes(self):
        return self.__nframes - self.__framesread

    def getframerate(self):
        return self.__framerate

    def readframes(self, nframes = -1):
        fmt = self.__format
        if nframes >= 0:
            nbytes = (nframes / fmt.getfpb()) * fmt.getblocksize()
        else:
            nbytes = -1
        data = self.__file.read(nbytes)
        nframes = len(data) * fmt.getfpb() / fmt.getblocksize()
        self.__framesread = self.__framesread + nframes
        return data, nframes

    def rewind(self):
        self.__file.seek(self.__hdr_size)
        self.__framesread = 0

    def getpos(self):
        return self.__file.tell(), self.__framesread

    def setpos(self, (pos, framesread)):
        self.__file.seek(pos)
        self.__framesread = framesread

    def getmarkers(self):
        return []
