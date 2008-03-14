__version__ = "$Id$"

from dev import Error
from format import *

import linuxaudiodev

class AudioDevLINUX:
    # default supported formats and frame rates
    __formats = {linear_8_mono_signed: linuxaudiodev.AFMT_S8,
                 linear_8_mono_excess: linuxaudiodev.AFMT_U8,
                 #ulaw_mono: linuxaudiodev.AFMT_MU_LAW,
                 #linear_16_mono_big_signed: linuxaudiodev.AFMT_S16_BE,
                 #linear_16_mono_big_excess: linuxaudiodev.AFMT_U16_BE,
                 linear_16_mono_little_signed: linuxaudiodev.AFMT_S16_LE,
                 linear_16_stereo_signed: linuxaudiodev.AFMT_S16_LE,
                 #linear_16_mono_little_excess: linuxaudiodev.AFMT_U16_LE,
                 }
    __rates = (8000, 11025, 16000, 22050, 32000, 44100, 48000)

    try:
        __port = linuxaudiodev.open('w')
    except linuxaudiodev.error:
        # can't open device, so keep the default
        pass
    else:
        # try if hardware supports CD quality
        try:
            __port.setparameters(44100, 16, 2, linuxaudiodev.AFMT_S16_LE)
        except linuxaudiodev.error:
            # CD quality not supported, use phone quality
            __formats = {linear_8_mono_signed:AudioDevLINUX.__formats[linear_8_mono_signed]}
            __rates = (8000,)
        # cleanup
        __port.close()
        del __port

    def __init__(self, fmt = None, qsize = None):
        self.__format = None
        self.__port = None
        self.__framerate = 0
        if fmt:
            self.setformat(fmt)

    def __del__(self):
        self.stop()

    def getformats(self):
        return self.__formats.keys()

    def getframerates(self):
        return self.__rates

    def setformat(self, fmt):
        if not self.__formats.has_key(fmt):
            raise Error, 'bad format'
        self.__format = fmt

    def getformat(self):
        return self.__format

    def setframerate(self, rate):
        if rate not in self.__rates:
            raise Error, 'bad output rate'
        self.__framerate = rate

    def getframerate(self):
        return self.__framerate

    def writeframes(self, data):
        if not self.__format or not self.__framerate:
            raise Error, 'params not specified'
        if not self.__port:
            self.__initport()
        self.__port.write(data)

    def wait(self):
        if not self.__port:
            return
        self.__port.flush()
        self.stop()

    def stop(self):
        port = self.__port
        if port:
            port.flush()
            port.close()
            self.__port = None

    def getfilled(self):
        if self.__port:
            return self.__port.obufcount()
        else:
            return 0

    def getfillable(self):
        inited = 0
        if not self.__port:
            self.__initport()
            inited = 1
        rv = self.__port.obuffree()
        if inited:
            self.__port.close()
            self.__port = None
        return rv

    def __initport(self):
        fmt = self.__format
        self.__port = linuxaudiodev.open('w')
        if not fmt or not self.__framerate:
            return

        bps = (fmt.getbps() + 7) & ~7
        try:
            self.__port.setparameters(self.__framerate, bps,
                                      fmt.getnchannels(),
                                      self.__formats[fmt])
        except linuxaudiodev.error:
            if fmt.getencoding() != 'linear' or \
               self.__framerate != 8000:
                raise Error, 'unsupported format'
