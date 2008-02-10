__version__ = "$Id$"

from dev import Error
from format import *

import al

class AudioDevSGI:
    __frameratedict = {
            48000: al.RATE_48000,
            44100: al.RATE_44100,
            32000: al.RATE_32000,
            22050: al.RATE_22050,
            16000: al.RATE_16000,
            11025: al.RATE_11025,
             8000: al.RATE_8000,
            }

    __nchannelsdict = {
            1: al.MONO,
            2: al.STEREO,
            }

    __sampwidthdict = {
            1: al.SAMPLE_8,
            2: al.SAMPLE_16,
            3: al.SAMPLE_24,
            }

    __formats = (linear_8_mono_signed,
                 linear_16_mono_big,
                 linear_8_stereo_signed,
                 linear_16_stereo_big)

    def __init__(self, fmt = None, qsize = None):
        self.__format = None
        self.__framerate = 0
        self.__params = [al.OUTPUT_RATE, 0]
        self.__oldparams = []
        self.__port = None
        self.__config = al.newconfig()
        if fmt:
            self.setformat(fmt)
        if qsize and hasattr(al, 'OpenPort'):
            # only set queuesize on modern systems :-(
            self.__config.setqueuesize(qsize)

    def __del__(self):
        self.stop()

    def getformats(self):
        return self.__formats

    def getframerates(self):
        return tuple(self.__frameratedict.keys())

    def setformat(self, fmt):
        if fmt not in self.__formats:
            raise Error, 'bad format'
        self.__format = fmt
        c = self.__config
        width = (fmt.getbps() + 7) / 8
        width = self.__sampwidthdict[width]
        c.setwidth(width)
        nchannels = fmt.getnchannels()
        self.__nchannels = nchannels
        nchannels = self.__nchannelsdict[nchannels]
        c.setchannels(nchannels)

    def getformat(self):
        return self.__format

    def setframerate(self, rate):
        try:
            cooked = self.__frameratedict[rate]
        except KeyError:
            raise Error, 'bad output rate'
        else:
            self.__params[1] = cooked
            self.__framerate = rate

    def getframerate(self):
        return self.__framerate

    def writeframes(self, data):
        if not self.__format or not self.__params[1]:
            raise Error, 'params not specified'
        if not self.__port:
            self.__port = al.openport('Python', 'w', self.__config)
            self.__oldparams = self.__params[:]
            al.getparams(al.DEFAULT_DEVICE, self.__oldparams)
            al.setparams(al.DEFAULT_DEVICE, self.__params)
        self.__port.writesamps(data)

    def wait(self):
        if not self.__port:
            return
        import time
        while self.__port.getfilled() > 0:
            time.sleep(0.1)
        self.stop()

    def stop(self):
        if self.__port:
            self.__port.closeport()
            self.__port = None
        if self.__oldparams:
            al.setparams(al.DEFAULT_DEVICE, self.__oldparams)
            self.__oldparams = []

    def getfilled(self):
        if self.__port:
            return self.__port.getfilled() / self.__nchannels
        else:
            return 0

    def getfillable(self):
        if self.__port:
            return self.__port.getfillable()
        else:
            return self.__config.getqueuesize()
