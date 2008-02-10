__version__ = "$Id$"

import struct

class BitBuffer:
    def __init__(self, fp):
        self.__fp = fp
        self.initbits()

    def close(self):
        if self.__fp is not None:
            self.__fp.close()
        self.__fp = None

    def __del__(self):
        self.close()

    def initbits(self):
        self.__bitpos = 0
        self.__bitbuf = 0

    def getbits(self, n):
        # get n bits from the stream
        v = 0
        while 1:
            s = n - self.__bitpos
            if s > 0:
                # consume the entire buffer
                v = v | (self.__bitbuf << s)
                n = n - self.__bitpos
                # get the next byte
                self.initbits()
                self.__bitbuf = ord(self.__fp.read(1))
                self.__bitpos = 8
            else:
                # consume a portion of the buffer
                v = v | (self.__bitbuf >> -s)
                self.__bitpos = self.__bitpos - n
                self.__bitbuf = self.__bitbuf & (0xFF >> (8 - self.__bitpos)) # mask off the consumed bits
                return v

    def getsbits(self, n):
        # get the number as an unsigned value
        v = self.getbits(n)
        # is the number negative?
        if v & (1 << (n - 1)):
            # yes, extend the sign
            v = v | (-1 << n)
        return v

    def getword(self):
        self.initbits()
        return struct.unpack('<h', self.__fp.read(2))[0]

    def getdword(self):
        self.initbits()
        return struct.unpack('<l', self.__fp.read(4))[0]

def swfparser(url, fp):
    # first 4 bytes have already been read
    info = {}
    bb = BitBuffer(fp)
    filelength = bb.getdword()
    if filelength < 21:
        print '%s: file size too short (%d)' % (url, filelength)
        return info
    nbits = bb.getbits(5)
    xmin = bb.getbits(nbits)
    xmax = bb.getbits(nbits)
    ymin = bb.getbits(nbits)
    ymax = bb.getbits(nbits)
    info['width'] = (xmax - xmin) / 20
    info['height'] = (ymax - ymin) / 20
    framerate = float(bb.getword()) / 256
    framecount = bb.getword()
    info['duration'] = framecount / framerate
    return info
