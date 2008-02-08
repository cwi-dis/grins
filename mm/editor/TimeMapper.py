__version__ = "$Id$"

# TimeMapper maps times to pixels and the reverse.

Error = 'TimeMapper.Error'

CONSISTENT_TIME_MAPPING=0
DEBUG=0

class TimeMapper:
    def __init__(self, min_pxl_per_sec):
        self.collecting = 1
        self.dependencies = []
        self.collisions = []
        self.collisiondict = {}
        self.stalldict = {}
        self.markerdict = {}    # map interesting pixels to times
        self.minpos = {}
        self.offset = 0
        self.width = 0
        self.range = 0, 0
        self.min_pxl_per_sec = min_pxl_per_sec

    def setoffset(self, offset, width):
        # we're given pixels from offset to offset+width
        # recalculate mapping so that collisions stay same
        # size but between collisions we give proportinately
        # more/fewer pixels to times
        assert type(offset) is type(0)
        assert type(width) is type(0)
        if __debug__:
            if DEBUG: print 'setoffset',offset,width
        coll = 0
        for pxl in self.collisiondict.values():
            coll = coll + pxl
        if width > coll:
            width = width - coll
            r0, r1 = self.range
            numpxl = r1 - r0 - coll
            factor = float(width) / numpxl
            coll = r0
            off = offset - r0
            for t in self.times:
                self.minpos[t] = int((self.minpos[t] - coll) * factor + .5) + coll + off
                coll = coll + self.collisiondict[t]
            if __debug__:
                if DEBUG:
                    print 'MINPOS'
                    for t in self.times:
                        print (t, self.minpos[t])
                    print 'RANGES'
                    for t in self.times:
                        print t, self.minpos[t], self.collisiondict[t], self.minpos[t] + self.collisiondict[t]
                    print self.minpos
            self.range = self.minpos[self.times[0]], self.minpos[self.times[-1]] + self.collisiondict[self.times[-1]]
        else:
            # not enough pixels given to fit collisions,
            # must scale everything.
            self.offset = offset
            self.width = width

    def adddependency(self, t0, t1, minpixeldistance, node):
        assert type(minpixeldistance) is type(0)
        if not self.collecting:
            raise Error, 'Adding dependency while not collecting data anymore'
        if __debug__:
            if DEBUG: print 'adddependency',t0,t1,minpixeldistance,node
        self.dependencies.append((t1, t0, minpixeldistance))
        self.collisiondict[t0] = 0
        self.collisiondict[t1] = 0

    def addmarker(self, time):
        if self.collecting:
            # when we're collecting, store the exact specified time
            if not self.collisiondict.has_key(time):
                self.collisiondict[time] = 0
            return
        # not collecting anymore
        # add value to markerdict for later use in pixel2time
        # make sure the time we store is the central time of the pixel
        px = self.interptime2pixel(time)
        self.markerdict[px] = self.pixel2time(px)[0]

    def addcollision(self, time, minpixeldistance):
        assert type(minpixeldistance) is type(0)
        if not self.collecting:
            raise Error, 'Adding collision while not collecting data anymore'
        if __debug__:
            if DEBUG: print 'addcollision',time,minpixeldistance
        self.collisions.append((time, minpixeldistance))
        self.collisiondict[time] = 0

    def addstalltime(self, time, stalltime, stalltype='stall'):
        if not self.collecting:
            raise Error, 'Adding stilltime while not collecting data anymore'
        if __debug__:
            if DEBUG: print 'addstalltime',time,stalltime,stalltype
        oldstalltime, oldstalltype = self.stalldict.get(time, (0, None))
        stalltime = oldstalltime + stalltime
        # XXXX Adding is not correct for different types of stalls
        # XXXX We should take the worst of stalltype and oldstalltype
        self.stalldict[time] = stalltime, stalltype
        self.collisiondict[time] = 0

    def calculate(self, realtime=0):
        min_pixels_per_second = self.min_pxl_per_sec
        if not self.collecting:
            raise Error, 'Calculate called while not collecting data'
        if __debug__:
            if DEBUG: print 'calculate',realtime,min_pixels_per_second
        self.collecting = 0
        self.dependencies.sort()
        if __debug__:
            if DEBUG:
                print 'DEPENDENCIES'
                for item in self.dependencies:
                    print item
                print 'COLLISIONS'
                self.collisions.sort()
                for item in self.collisions:
                    print item
                print 'STALLS'
                for item in self.stalldict.items():
                    print item
        for time, pixels in self.collisions:
            oldpixels = self.collisiondict[time]
            if pixels > oldpixels:
                self.collisiondict[time] = pixels
        self.times = self.collisiondict.keys()
        self.times.sort()
        if realtime and min_pixels_per_second == 0:
            for t1, t0, pixels in self.dependencies:
                if t1 > t0 and pixels/(t1-t0) > min_pixels_per_second:
                    min_pixels_per_second = pixels/(t1-t0)
##             min_pixels_per_second = int(min_pixels_per_second+0.5)
        elif min_pixels_per_second == 0:
            min_pixels_per_second = 2
        # Jack added this back in:
        min_pixels_per_second = int(min_pixels_per_second+0.5)
        if __debug__:
            if DEBUG: print 'min pxl per sec:',min_pixels_per_second
        for time, (stalltime, stalltype) in self.stalldict.items():
            stallpixels = int(stalltime * min_pixels_per_second +0.5)
            if stallpixels > self.collisiondict[time]:
                self.collisiondict[time] = stallpixels
        minpos = 0
        prev_t = self.times[0]
        for t in self.times:
            if t != prev_t: # for times[0] don't add the dependency
                if realtime:
                    self.dependencies.append((t, prev_t, int((t-prev_t)*min_pixels_per_second + 0.5)))
                else:
                    self.dependencies.append((t, prev_t, min_pixels_per_second))
##             minpos = minpos + (t-prev_t) * min_pixels_per_second
            self.minpos[t] = minpos
            minpos = minpos + self.collisiondict[t] + 1
            prev_t = t
        self.dependencies.sort()
        if __debug__:
            if DEBUG:
                print 'MINPOS'
                for t in self.times:
                    print (t, self.minpos[t])
                print 'DEPENDENCIES NOW'
                for item in self.dependencies:
                    print item
##         pushover = {}
        for t1, t0, pixels in self.dependencies:
            t0maxpos = self.minpos[t0] + self.collisiondict[t0]
            t1minpos = t0maxpos + pixels
            if t1minpos > self.minpos[t1]:
                self.minpos[t1] = t1minpos
##             if t1minpos > self.minpos[t1] + pushover.get(t1, 0):
##                 pushover[t1] = t1minpos - self.minpos[t1]
##         curpush = 0
##         for time in self.times:
##             curpush = curpush + pushover.get(time, 0)
##             self.minpos[time] = self.minpos[time] + curpush
        if __debug__:
            if DEBUG:
                print 'MINPOS'
                for t in self.times:
                    print (t, self.minpos[t])
                print 'RANGES'
                for t in self.times:
                    print t, self.minpos[t], self.collisiondict[t], self.minpos[t] + self.collisiondict[t]
                print self.minpos
        self.range = self.minpos[self.times[0]], self.minpos[self.times[-1]] + self.collisiondict[self.times[-1]]
        if realtime:
            return min_pixels_per_second
        else:
            return 0

    def pixel2time(self, pxl):
        assert type(pxl) is type(0)
        if self.collecting:
            raise Error, 'pixel2time called while still collecting data'
        if self.markerdict.has_key(pxl):
            # hit a marker that was added after the mapper was finalized
            # do as if it is an exact value
            return self.markerdict[pxl], 1
        if self.width == 0:
            pos = pxl - self.offset
        else:
            pos = (pxl - self.offset) * float(self.range[1] - self.range[0]) / self.width
        lasttime = lastpos = None
        for tm in self.times:
            mp = self.minpos[tm]
            cd = self.collisiondict[tm]
            if mp == pxl:
                # Note by Jack: I added this "if" but I don't
                # fully understand the code below...
                return tm, 1
            if pos < mp:
                if lasttime is not None:
                    # need to interpolate
                    # "perfect" interpolation, but
                    # this gives way too many
                    # decimal places
                    time = lasttime + float(pos - lastpos) * (tm - lasttime) / float(mp - lastpos)
                    # "resolution" of time, i.e. #seconds per pixel
                    resolution = (tm - lasttime) / float(mp - lastpos)
                    # normalize to value between 1
                    # (inclusive) and 10 (not
                    # inclusive)
                    # fac is factor with which to
                    # multiply, div is factor by
                    # which to divide (one or both
                    # will be 1)
                    fac = div = 1
                    while resolution >= 10:
                        resolution = resolution / 10
                        fac = fac * 10
                    while resolution < 1:
                        resolution = resolution * 10
                        div = div * 10
                    # normalized and truncated time
                    # this is truncated with last digit == 0
                    xtime = int(time * div / (fac * 10)) * 10
                    # try different last digits to
                    # find a "nice" one that will
                    # result in the correct pixel
                    # value (order is important)
                    for off in (0,10,5,2,4,6,8,1,3,7,9):
                        t = (xtime + off) * fac / float(div)
                        if self.interptime2pixel(t) == pxl:
                            return t, 0
                    # didn't find any, use fallback mechanism
                    time = int(time * div / fac + .5) * fac / float(div)
                    return time, 0
                # before left edge
                # extrapolate first interval to the left
                for tm2 in self.times: # find first time that's different
                    if tm2 != tm:
                        # extrapolate
                        return tm + (pos - mp) * (tm2 - tm) / float(self.minpos[tm2] - mp), 0
                # no multiple times, use pixel == second
                return tm + (pos - mp), 0
            if mp <= pos <= mp + cd:
                # inside "grey area": time is exact
                return tm, 1
            lastpos = mp + cd
            lasttime = tm
        # beyond right edge
        # extrapolate last interval to the right
        times = self.times[:]
        times.reverse()
        for tm2 in times:
            if tm2 != tm:
                return tm + (pos - mp) * (tm2 - tm) / float(self.minpos[tm2] - mp), 0
        return tm + (pos - mp), 0

    def __pixel2pixel(self, pos):
        assert type(pos) is type(0)
        if self.width == 0:
            return pos
        return int(pos / float(self.range[1] - self.range[0]) * self.width + self.offset + .5)

    def time2pixel(self, time, align='left'):
        # Return either the leftmost or rightmost pixel for a given
        # time, which must be known
        if self.collecting:
            raise Error, 'time2pixel called while still collecting data'
        if not self.minpos.has_key(time):
            if __debug__: print 'Warning: TimeMapper: Interpolating time', time
            return self.interptime2pixel(time)
        pos = self.minpos[time]
        if align == 'right':
            pos = pos + self.collisiondict[time]
        if __debug__:
            if DEBUG: print 'time2pixel',time,align,'->',pos,self.__pixel2pixel(pos)
        return self.__pixel2pixel(pos)

    def interptime2pixel(self, time, align='left'):
        # Return a pixel position for any time value, possibly interpolating
        if self.collecting:
            raise Error, 'time2pixel called while still collecting data'
        if self.minpos.has_key(time):
            pos = self.minpos[time]
            if align == 'right':
                pos = pos + self.collisiondict[time]
            return self.__pixel2pixel(pos)
        if time < self.times[0]:
            # See whether this is the preload special case
            stall_t0, dummy = self.stalldict.get(self.times[0], (0, None))
            aftertime = self.times[0]
            beforetime = aftertime - stall_t0
            if time >= beforetime:
                factor = (float(time)-beforetime) / (aftertime-beforetime)
                beforepos = self.minpos[aftertime]
                afterpos = self.minpos[aftertime]+self.collisiondict[aftertime]
                width = afterpos - beforepos
                return self.__pixel2pixel(int(beforepos + factor*width + 0.5))
        if time < self.times[0]:
            return self.__pixel2pixel(self.minpos[self.times[0]])
        if time > self.times[-1]:
            return self.__pixel2pixel(self.minpos[self.times[-1]])
        i = 1
        while self.times[i] < time:
            i = i + 1
        beforetime = self.times[i-1]
        aftertime = self.times[i]
        factor = (float(time)-beforetime) / (aftertime-beforetime)
        beforepos = self.minpos[beforetime] + self.collisiondict[beforetime]
        afterpos = self.minpos[aftertime]
        width = afterpos - beforepos
        return self.__pixel2pixel(int(beforepos + factor*width + 0.5))

    def gettimesegments(self, range=None):
        # Return a list of (time, leftpixel, rightpixel) tuples
        rv = []
        for t in self.times:
            if range and (t < range[0] or t > range[1]):
                continue
            rv.append((t, self.__pixel2pixel(self.minpos[t]), self.__pixel2pixel(self.minpos[t] + self.collisiondict[t])))
        return rv

    def getstall(self, time):
        return self.stalldict.get(time, (0, None))

    def getallstalls(self):
        return self.stalldict.items()
