__version__ = "$Id$"

import string
import audio

class select:
    def __init__(self, rdr, rangelist):
        lastend = -1
        for begin, end in rangelist:
            if begin is None:
                begin = 0
            if lastend is None or lastend > begin:
                raise audio.Error, 'rangelist must be non-overlapping and sorted'
            if end is not None and end < begin:
                raise audio.Error, 'end must not be less than begin'
            lastbegin, lastend = begin, end
        self.__rdr = rdr
        self.__rangelist = rangelist
        self.__currange = 0
        self.__curframe = 0
        if rangelist:
            begin = rangelist[0][0]
            if begin:
                dummy, self.__curframe = rdr.readframes(begin)

    def getformat(self):
        return self.__rdr.getformat()

    def getframerate(self):
        return self.__rdr.getframerate()

    def readframes(self, nframes = -1):
        currange = self.__currange
        rangelist = self.__rangelist
        curframe = self.__curframe
        rdr = self.__rdr
        data = []               # data read
        read = 0                # # frames read
        while nframes != 0:
            if currange >= len(rangelist):
                break
            begin, end = rangelist[currange]
            if begin is None:
                begin = 0
            while curframe < begin:
                dummy, n = rdr.readframes(min(begin-curframe, 8192))
                if n == 0:
                    break
                curframe = curframe + n
            if end is None or end == 0 or \
               (nframes >= 0 and curframe + nframes <= end):
                # can read nframes
                n = nframes
            else:
                # can only read up to end
                n = end - curframe
            d, n = rdr.readframes(n)
            if n == 0:
                break
            data.append(d)
            read = read + n
            curframe = curframe + n
            if end is not None and end != 0 and curframe >= end:
                currange = currange + 1
            if nframes > 0:
                nframes = nframes - n
        self.__currange = currange
        self.__curframe = curframe
        return string.join(data, ''), read

    def rewind(self):
        self.__rdr.rewind()
        self.__currange = 0
        self.__curframe = 0
        dummy = self.readframes(0)

    def getpos(self):
        pos = self.__rdr.getpos()
        return self.__currange, self.__curframe, pos

    def setpos(self, (currange, curframe, pos)):
        self.__rdr.setpos(pos)
        self.__currange = currange
        self.__curframe = curframe

    def getnframes(self):
        currange = self.__currange
        rangelist = self.__rangelist
        curframe = end = self.__curframe
        rdr = self.__rdr
        nframes = rdr.getnframes()
        n = 0
        while 1:
            if currange >= len(rangelist):
                break
            begin, end = rangelist[currange]
            if begin is None:
                begin = 0
            if curframe < begin:
                nframes = nframes - begin + curframe
                curframe = begin
            if end is None or end == 0:
                n = n + nframes
                break
            else:
                n = n + end - curframe
            nframes = nframes - end + curframe
            curframe = end
            currange = currange + 1
        return n

    def getmarkers(self):
        markers = []
        diff = 0
        for id, pos, name in self.__rdr.getmarkers():
            lastend = 0
            for begin, end in self.__rangelist:
                if pos < (begin or 0):
                    # no point in continuing
                    break
                diff = diff + begin - lastend
                if end is None or end == 0 or pos < end:
                    markers.append((id, pos - diff, name))
                lastend = end
        return markers
