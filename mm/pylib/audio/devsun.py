__version__ = "$Id$"

from dev import Error
from format import *

import sunaudiodev, SUNAUDIODEV

class AudioDevSUN:
    # default supported formats and frame rates
    __formats = (ulaw_mono,
                 ulaw_stereo,
                 linear_16_mono_big,
                 linear_16_stereo_big)
    __rates = (8000, 11025, 16000, 22050, 32000, 44100, 48000)

    # see if we can determine whether we have to restrict ourselves
    try:
        __port = sunaudiodev.open('w')
    except sunaudiodev.error:
        # can't open device, so keep the default
        pass
    else:
        # try if hardware supports CD quality
        __info = __port.getinfo()
        __info.o_sample_rate = 44100
        __info.o_channels = 2
        __info.o_encoding = SUNAUDIODEV.ENCODING_LINEAR
        __info.o_precision = 16
        try:
            __port.setinfo(__info)
        except sunaudiodev.error:
            # CD quality not supported, use phone quality
            __formats = (ulaw_mono,)
            __rates = (8000,)
        # cleanup
        __port.close()
        del __port, __info

    def __init__(self, fmt = None, qsize = None):
        self.__format = None
        self.__port = None
        self.__framerate = 0
        if fmt:
            self.setformat(fmt)

    def __del__(self):
        self.stop()

    def getformats(self):
        return self.__formats

    def getframerates(self):
        return self.__rates

    def setformat(self, fmt):
        if fmt not in self.__formats:
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
        self.__port.drain()
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
        port = self.__port
        info = port.getinfo()
        fact = info.o_precision * info.o_channels / 8
        val = info.o_buffer_size / fact - port.obufcount()
        if inited:
            port.close()
            self.__port = None
        return val

    def __initport(self):
        fmt = self.__format
        self.__port = sunaudiodev.open('w')
        if not fmt or not self.__framerate:
            return
        info = self.__port.getinfo()
        info.o_sample_rate = self.__framerate
        info.o_channels = fmt.getnchannels()
        if fmt.getencoding() == 'u-law':
            info.o_encoding = SUNAUDIODEV.ENCODING_ULAW
            info.o_precision = 8
        else:
            info.o_precision = (fmt.getbps() + 7) & ~7
            info.o_encoding = SUNAUDIODEV.ENCODING_LINEAR
        try:
            self.__port.setinfo(info)
        except sunaudiodev.error:
            if fmt.getencoding() != 'u-law' or \
               self.__framerate != 8000:
                raise Error, 'unsupported format'
