__version__ = "$Id$"

from format import *
import convert
import audioop
import string

class merge:
    def __init__(self, *args):
        self.__readers = []
        self.__mapreaders = []
        self.__port = None
        self.__framerate = 0
        self.__format = None
        for arg in args:
            if type(arg) is type(()):
                apply(self.merge, arg)
            else:
                self.merge(arg)

    def add(self, rdr, callback = None):
        if self.__readers:
            nrdr = convert.convert(rdr, (self.__format,),
                                   (self.__framerate,))
        else:
            nrdr = convert.convert(rdr, (linear_8_mono_signed,
                                         linear_8_stereo_signed,
                                         linear_16_mono,
                                         linear_16_stereo))
            self.__framerate = nrdr.getframerate()
            self.__format = nrdr.getformat()
        self.__readers.append((nrdr, callback))
        self.__mapreaders.append((rdr, nrdr))

    def delete(self, rdr):
        # find the mapping and delete it
        for i in range(len(self.__mapreaders)):
            if rdr is self.__mapreaders[i][0]:
                rdr = self.__mapreaders[i][1]
                del self.__mapreaders[i]
                break
        # find the mapped reader and delete it
        for i in range(len(self.__readers)):
            if rdr is self.__readers[i][0]:
                del self.__readers[i]
                return

    def readframes(self, nframes = -1):
        stretches = []
        counts = []
        width = self.__format.getbps() / 8
        for i in range(len(self.__readers)):
            rdr, cb = self.__readers[i]
            data, nf = rdr.readframes(nframes)
            if not data:
                # got to the end of this one
                self.__readers[i] = rdr, None
                if cb:
                    apply(cb[0], cb[1])
                continue
            newstretches = []
            newcounts = []
            for i in range(len(counts)):
                mixed = stretches[i]
                count = counts[i]
                if data:
                    minlen = min(len(data), len(mixed))
                    data0 = data[:minlen]
                    data = data[minlen:]
                    mixed0 = mixed[:minlen]
                    mixed = mixed[minlen:]
                    newstretches.append(audioop.add(mixed0, data0, width))
                    newcounts.append(count + 1)
                if mixed:
                    newstretches.append(mixed)
                    newcounts.append(count)
            newstretches.append(data)
            newcounts.append(1)
            stretches = newstretches
            counts = newcounts
        data = string.joinfields(stretches, '')
        return data, len(data) / (width * self.__format.getnchannels())

    def getformat(self):
        return self.__format

    def getnframes(self):
        nframes = 0
        for (rdr, cb) in self.__readers:
            n = rdr.getnframes()
            nframes = max(n, nframes)
        return nframes

    def getframerate(self):
        return self.__framerate

    def rewind(self):
        for (rdr, cb) in self.__readers:
            rdr.rewind()

    def getpos(self):
        positions = []
        for (rdr, cb) in self.__readers:
            positions.append((rdr, rdr.getpos()))
        return positions

    def setpos(self, pos):
        for (rdr, p) in pos:
            # only set pos of readers that weren't deleted
            for i in range(len(self.__readers)):
                if self.__readers[i][0] == rdr:
                    rdr.setpos(p)
                    break
