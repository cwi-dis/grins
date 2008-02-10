__version__ = "$Id$"

import math
import string

class Animator:
    def __init__(self, timenode, attr, dict):
        self._timenode = timenode
        self._attr = attr
        self._calcMode = dict.get('calcMode')
        self._values = dict.get('values')
        self._times = dict.get('times')
        self._splines = dict.get('splines')
        self._accumulate = dict.get('accumulate')
        self._additive = dict.get('additive')

        # time manipulators
        self._speed, self._direction= 1.0, 1
        self._accelerate = 0.0
        self._decelerate = 0.0
        self._autoReverse = 0
        self._setSpeed(dict['speed'])
        self._setAccelerateDecelerate(dict['accelerate'], dict['decelerate'])
        self._setAutoReverse(dict['autoReverse'])

        self._dur = None # will be set by prepare
        self._efftimes = None

        # shortcuts
        mode = self._calcMode
        values, times, splines = self._values, self._times, self._splines

        # assertions
        assert len(values)>0, 'empty values'
        assert len(values)!=1 or mode == 'discrete', 'missing values'
        assert not times or len(times)==len(values), 'times vs values missmatch'
        assert (not times or not splines) or len(splines)==len(times)-1, 'times vs splines missmatch'

        # set calc mode
        if mode=='discrete': self._inrepol = self._discrete
        elif mode=='paced': self._inrepol = self._paced
        elif mode=='spline': self._inrepol = self._spline
        else: self._inrepol = self._linear

        # repeat counter
        self._repeatCounter = 0

        # cashed acc value
        self._accValue = None

        # current values
        self._curvalue = None
        self._time = None

        # path origin
        self._origin = ""

        # transitionFilter
        self._trdict = None

    # reset
    def reset(self):
        self._repeatCounter = 0
        self._accValue = None
        self._curvalue = None
        self._time = None
        self._dur = None

    def getTimeManipulatedDur(self, dur):
        if self._autoReverse: dur = 0.5*dur
        return dur*self._speed

    def prepareInterval(self, dur):
        if dur == 'indefinite':
            return
        assert dur>0, 'invalid element interval'
        self._dur = self.getTimeManipulatedDur(dur)

        mode = self._calcMode
        values, times = self._values, self._times

        # construct boundaries of time intervals
        self._efftimes = []
        if not times:
            n = len(values)
            if mode == 'paced':
                # create intervals proportional to values
                # values may be not monotonic, so use segments:
                tl = 0.0
                for i in range(1,n):
                    tl = tl + self._attr.distValues(values[i-1],values[i])
                if tl == 0.0:
                    tau = dur/float(n)
                    t = 0.0
                    for i in range(n):
                        self._efftimes.append(t)
                        t = t + tau
                else:
                    f = dur/tl
                    d = 0.0
                    self._efftimes.append(0)
                    for i in range(1,n-1):
                        d = d + self._attr.distValues(values[i-1],values[i])
                        self._efftimes.append(f*d)
                    self._efftimes.append(dur)
            elif mode == 'discrete':
                # for discrete mode n is the number of intervals
                tau = dur/float(n)
                t = 0.0
                for i in range(n):
                    self._efftimes.append(t)
                    t = t + tau
            else:
                # create uniform intervals
                if n <= 2:
                    self._efftimes = [0, dur]
                else:
                    tau = dur/float(n-1)
                    t = 0.0
                    for i in range(n):
                        self._efftimes.append(t)
                        t = t + tau
        else:
            # scale times to dur
            if mode=='discrete':
                self._efftimes = times
            else:
                self._efftimes = []
                for p in times:
                    self._efftimes.append(p*dur)

    # return the current local time in [0, dur]
    # after time manipulations
    def getLocalTime(self):
        return self._time

    # set local time to t and return value at t
    def getValue(self, t):
        if self._dur == 'indefinite':
            self._curvalue = self._values[0]
            return self._curvalue

        # time manipulate transform
        t = self._transformTime(t)
        self._time = t

        # assert that t is in [0,dur)
        # i.e. assert end-point exclusive model
        if self._dur>0:
            if t<0 or t>self._dur or (t==self._dur and not self._autoReverse):
                print 't=',t, 'dur=', self._dur
                raise AssertionError

        # compute interpolated value according to calcMode
        v = self._inrepol(t)

        # accumulate
        if self._accumulate=='sum' and self._accValue:
            v = self._accValue + v

        self._curvalue = v
        return v

    def getCurrValue(self):
        t = self._timenode.getSimpleTime()
        if self._timenode.isFrozen() and t == self._dur:
            self.setToEnd()
        else:
            self.getValue(t)
        return self._curvalue

    # mainly for freeze and accumulate calculations
    def setToEnd(self):
        if self._dur == 'indefinite':
            self._curvalue = self._values[0]
            return self._curvalue

        # set local time to end
        if self._autoReverse:t = 0
        else: t = self._dur
        self._time = t

        # compute interpolated value according to calcMode
        v = self._inrepol(t)

        # set current value taking into account accumulate
        self._repeatCounter = self._repeatCounter + 1
        if self._accumulate=='sum':
            if self._repeatCounter == 1:
                self._accValue = v
            else:
                self._accValue = self.addValues(self._accValue, v)
            self._curvalue = self._accValue
        else:
            self._curvalue = v
        return self._curvalue

    def isAdditive(self):
        return self._additive=='sum'

    def isAccumulating(self):
        return self._accumulate=='sum'

    def isEffValueAnimator(self):
        return 0

    # t in [0, dur]
    def _getinterval(self, t):
        tl = self._efftimes
        n = len(tl)
        for i in range(n-1):
            if t >= tl[i] and t < tl[i+1]:
                return i, (t - tl[i]) / (tl[i+1] - tl[i])
        # t == dur
        if self._calcMode == 'discrete':
            return n-1, 1.0
        return n-2, 1.0

    def _discrete(self, t):
        n = len(self._values)
        if n==1: return self._values[0]
        ix, pdt = self._getinterval(t)
        return self._values[ix]

    def _linear(self, t):
        vl = self._values
        dur = self._dur
        n = len(vl)
        if dur>0 and t==dur:
            return vl[n-1]
        elif t==0 or n==1:
            return vl[0]
        ix, pdt = self._getinterval(t)
        return vl[ix] + (vl[ix+1]-vl[ix])*pdt

    def _paced(self, t):
        # since intervals are proportional to values
        # by construction, linear results to paced
        return self._linear(t)

    def _spline(self, t):
        vl = self._values
        dur = self._dur
        el = self._splines
        if t==dur:
            return vl[len(vl)-1]
        elif t==0:
            return vl[0]
        ix, pdt = self._getinterval(t)
        return vl[ix] + (vl[ix+1]-vl[ix])*self.bezier(pdt, el[ix])

    def _setAccumulate(self, acc):
        if acc not in ('none', 'sum'):
            print 'invalid accumulate value:',acc
            self._accumulate = 'none'
        else:
            self._accumulate = acc

    def setOrigin(self, origin):
        self._origin = origin

    def setTransition(self, dict):
        self._trdict = dict

    def _setAutoReverse(self,f):
        if f: self._autoReverse = 1
        else: self._autoReverse = 0

    def _setAccelerateDecelerate(self, a, b):
        if a <0.0 or b<0.0:
            print 'invalid accelerate/decelerate values'
        a = math.fabs(a)
        b = math.fabs(b)
        s = a + b
        if s==0:
            self._accelerate = 0
            self._decelerate = 0
        elif s>1.0:
            print 'invalid accelerate/decelerate values'
            self._accelerate = a / s
            self._decelerate = b / s
        else:
            self._accelerate = a
            self._decelerate = b

    # can be called two times
    # one to set speed attribute and
    # two to set implicit speed from the container
    def _setSpeed(self,s):
        if s == 0:
            print 'invalid zero speed value'
            s = 1.0
        self._speed = self._speed * math.fabs(s)
        self._direction = 1
        if self._speed<0.0:
            self._direction = -1

    def _transformTime(self, t):
        # first apply time scaling
        if self._speed!=1.0:
            t = self._applySpeed(t)

        # then t mod dur
        if self._autoReverse:
            t = self._applyAutoReverse(t)

        # then speed direction
        if self._direction<0:
            t = self._applyReflect(t)

        # apply acc/dec for t is [0,dur]
        if (self._accelerate+self._decelerate)>0.0:
            t = self._applyAccelerateDecelerate(t)

        return t

    # t in [0,dur]
    # to preserve duration max speed m should be:
    # d = accTriangle + constRectangle + decTriangle = a*d*m/2 + (d-b*d-a*d)*m + b*d*m/2
    # therefore max speed m = 1 / (1 - a/2 - b/2)
    def _applyAccelerateDecelerate(self, t):
        if t<0 or t>self._dur:
            raise AssertionError
        a = self._accelerate
        b = self._decelerate
        d = self._dur
        ad = a*d
        bd = b*d
        t2 = t*t
        dt2 = (d-t)*(d-t)
        m = 1.0/(1.0 - 0.5*a - 0.5*b)
        if t>=0 and t<=ad:
            tp = 0.5*m*t2/ad
        elif t>=a*d and t<=(d-bd):
            tp = 0.5*m*ad + (t-ad)*m
        elif t>=(d-bd) and t<=d:
            tp = d - 0.5*m*dt2/bd
        if tp<0 or tp>d:
            raise AssertionError
        return tp

    # t in [0,2*dur]
    def _applyAutoReverse(self, t):
        if t<0 or t>2.0*self._dur:
            raise AssertionError
        if t > self._dur:
            return self._dur - (t - self._dur)
        else:
            return t

    def _applySpeed(self, t):
        return self._speed*t

    # t in [0, dur]
    def _applyReflect(self, t):
        return self._dur - t

    #
    # temporary parametric form
    #
    def bezier(self, t, e = (0,0,1,1)):
        res = 20
        step = 1.0/float(res)
        s = 0.0
        for i in range(res+1):
            sc = 1.0-s
            b = 3.0*sc*sc*s
            c = 3.0*sc*s*s
            d = s*s*s
            tp = b*e[0] + c*e[2] + d
            if tp >= t:
                return b*e[1] + c*e[3] + d
            s = s + step

###########################
# 'set' element animator
class SetAnimator(Animator):
    def __init__(self, timenode, attr, dict):
        dict['calcMode'] = 'discrete' # assert
        assert len(dict.get('values'))==1, 'invalid set element values'
        Animator.__init__(self, timenode, attr, dict)

###########################
# A special animator to manage to-only additive animate elements
class EffValueAnimator(Animator):
    def isEffValueAnimator(self):
        return 1
    def getValue(self, t):
        if not self._attr:
            return Animator.getValue(self, t)
        u, v = self._values[:2]
        u = self._attr.getPresentValue(below=self)
        self._values = u, v
        return Animator.getValue(self, t)


###########################
class RNPath:
    def __init__(self, coords):
        self.coords = coords
        self.params = [0,]
        n = len(coords)
        assert n, 'empty values'
        self.length = 0.0
        for i in range(1,n):
            self.length = self.length + self.dist(coords[i-1], coords[i])
            self.params.append(self.length)

    def getLength(self):
        return self.length

    def getLengthValues(self):
        return tuple(self.params)

    def getPointAtLength(self, s):
        n = len(self.coords)
        if n==1: return self.coords[0]
        if s<=0: return self.coords[0]
        elif s>= self.length:
            return self.coords[n-1]
        d = 0.0
        ptp = self.coords[0]
        for i in range(1,n):
            pt = self.coords[i]
            ds = self.dist(pt, ptp)
            if s>=d and s <= (d + ds):
                f = (s-d)/ds
                pt = self.line(ptp, pt, f)
                break
            d = d + ds
            ptp=pt
        return pt

    def line(self, pt1, pt2, t):
        n = len(pt1)
        r = []
        for i in range(n):
            r.append(pt1[i] + t*(pt2[i]-pt1[i]))
        return tuple(r)

    def dist(self, pt1, pt2):
        n = len(pt1)
        d2 = 0.0
        for i in range(n):
            dq = pt2[i]-pt1[i]
            d2 = d2 + dq*dq
        return math.sqrt(d2)

class FloatTupleAnimator(Animator):
    def __init__(self, timenode, attr, dict):
        self._path = RNPath(dict.get('values'))
        self._time2length = 1
        dict['values'] = self._path.getLengthValues()
        Animator.__init__(self, timenode, attr, dict)

    def prepareInterval(self, dur):
        Animator.prepareInterval(self, dur)
        if self._dur != 'indefinite':
            self._time2length = self._path.getLength()/self._dur

    def reset(self):
        Animator.reset(self)
        self._time2length = 1

    def _paced(self, t):
        return self._path.getPointAtLength(t*self._time2length)

    def _linear(self, t):
        lv = Animator._linear(self, t)
        return self._path.getPointAtLength(lv)

    def _spline(self, t):
        lv = Animator._spline(self, t)
        return self._path.getPointAtLength(lv)

    def _discrete(self, t):
        lv = Animator._discrete(self, t)
        return self._path.getPointAtLength(lv)

class IntTupleAnimator(FloatTupleAnimator):
    pass

class EffIntTupleAnimator(IntTupleAnimator):
    def isEffValueAnimator(self):
        return 1
    def getValue(self, t):
        if not self._attr:
            return IntTupleAnimator.getValue(self, t)
        u, v = self._path.coords[:2]
        u = self._attr.getPresentValue(below=self)
        self._path = RNPath((u,v))
        return IntTupleAnimator.getValue(self, t)

###########################
# 'animateColor'  element animator
class ColorAnimator(IntTupleAnimator):
    pass

class EffColorAnimator(EffIntTupleAnimator):
    pass

###########################
# 'animateMotion' element animator
class MotionAnimator(Animator):
    def __init__(self, timenode, attr, dict):
        self._path = dict.get('path')
        self._totlen = self._path.getLength()
        self._time2length = 1
        self._currlen = 0
        self._currangle = 0
        self.tftype = 'translate'
        self.rotate = dict.get('rotate')
        dict['values'] = self._path.getLengthValues()
        Animator.__init__(self, timenode, attr, dict)

    def prepareInterval(self, dur):
        Animator.prepareInterval(self, dur)
        if self._dur == 'indefinite':
            self._time2length = 1
        else:
            self._time2length = self._totlen/self._dur

    def reset(self):
        Animator.reset(self)
        self._time2length = 1
        self._currlen = 0

    def _paced(self, t):
        self._currlen = t*self._time2length
        return self._path.getPointAtLength(self._currlen)

    def _linear(self, t):
        self._currlen = Animator._linear(self, t)
        return self._path.getPointAtLength(self._currlen)

    def _spline(self, t):
        self._currlen = Animator._spline(self, t)
        return self._path.getPointAtLength(self._currlen)

    def _discrete(self, t):
        self._currlen = Animator._discrete(self, t)
        return self._path.getPointAtLength(self._currlen)

    def getCurrTransform(self):
        z = self.getCurrValue()
        x, y = z.real, z.imag # old convention
        if self.rotate is not None:
            if self.rotate in ('auto', 'auto-reverse'):
                zp = self._path.getPointAtLength(self._currlen+0.01*self._totlen)
                xp, yp = zp.real, zp.imag
                if math.fabs(xp-x)>0.0000001:
                    angle = math.atan((yp-y)/(xp-x))
                else:
                    if self._currangle>0: angle =  0.5*math.pi
                    else: angle =  -0.5*math.pi
                self._currangle = angle
                if self.rotate == 'auto-reverse':
                    angle = angle + math.pi
                return [(self.tftype, [x, y,]), ('rotate', [angle,])]
            else:
                return [(self.tftype, [x, y,]), ('rotate', [self.rotate,])]
        return [(self.tftype, [x, y,]),]

class EffMotionAnimator(Animator):
    def isEffValueAnimator(self):
        return 1

    def getValue(self, t):
        if not self._attr:
            return Animator.getValue(self, t)
        u, v = self._values[:2]
        u = self._attr.getPresentValue(below=self)
        self._values = u, v
        return Animator.getValue(self, t)


###########################
class TransformAnimator(Animator):
    def __init__(self, timenode, attr, dict):
        Animator.__init__(self, timenode, attr, dict)
        self.tftype = dict.get('type')

    def getCurrTransform(self):
        return [(self.tftype, [self.getCurrValue(),]),]

class VectorTransformAnimator(FloatTupleAnimator):
    def __init__(self, timenode, attr, dict):
        FloatTupleAnimator.__init__(self, timenode, attr, dict)
        self.tftype = dict.get('type')

    def getCurrTransform(self):
        vl = self.getCurrValue()
        arg = []
        for val in vl: arg.append(val)
        return [(self.tftype, arg),]
