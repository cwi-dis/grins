__version__ = "$Id$"


import MMAttrdefs
import string
import math
import svgpath
import re
from fmtfloat import round
import tokenizer

# units, messages
import windowinterface
from windowinterface import UNIT_MM, UNIT_SCREEN, UNIT_PXL

# conditional behaviors
import settings

# modules flags
basicAnimation  = 1
splineAnimation = settings.MODULES.get('SplineAnimation')
timeManipulations = settings.MODULES.get('TimeManipulations')

# debug flags
debug = 0
debugParser = 0

# animateMotion default origin
# assume origin in ('element', 'parent')
regionOrigin = 'parent' # smil20-profile (IE5.5 defaults to 'element')
mediaOrigin = 'parent' # smil20-profile


# An Animator represents an animate element at run time.
# An Animator entity implements interpolation taking into
# account the calc mode, the 'accumulate' attr and
# the time manipulations: speed, accelerate-decelerate and autoReverse
class Animator:
    def __init__(self, attr, domval, values, dur, mode='linear',
                    times=None, splines=None, accumulate='none', additive='replace'):
        self._attr = attr
        self._domval = domval
        self._dur = float(dur)
        self._mode = mode
        self._values = values
        self._times = times
        self._splines = splines
        self._accumulate = accumulate
        self._additive = additive

        # assertions
        assert( len(values) )
        assert( len(values)!=1 or mode == 'discrete' )
        assert( not times or len(times)==len(values) )
        assert( (not times or not splines) or len(splines)==len(times)-1)

        # set calc mode
        if mode=='discrete': self._inrepol = self._discrete
        elif mode=='paced': self._inrepol = self._paced
        elif mode=='spline': self._inrepol = self._spline
        else: self._inrepol = self._linear

        # return value convertion (for example int())
        self._convert = None
        self._range = None

        # construct boundaries of time intervals
        self._efftimes = []
        if not times:
            n = len(values)
            if mode == 'paced':
                # create intervals proportional to values
                # values may be not monotonic, so use segments:
                tl = 0.0
                for i in range(1,n):
                    tl = tl + self.distValues(values[i-1],values[i])
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
                        d = d + self.distValues(values[i-1],values[i])
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

        # repeat counter
        self._repeatCounter = 0

        # cashed acc value
        self._accValue = None

        # current values
        self._curvalue = None
        self._time = None

        # time manipulators
        self._speed = 1.0
        self._accelerate = 0.0
        self._decelerate = 0.0
        self._autoReverse = 0
        self._direction = 1

        # path origin
        self._origin = ""

        # composition context of this animator
        self._effectiveAnimator = None

        # transitionFilter
        self._trdict = None

    def getDOMValue(self):
        return self._domval

    def getAttrName(self):
        return self._attr

    def getTimeManipulatedDur(self):
        dur = self._dur
        if self._autoReverse:
            dur = 2*dur
        dur = dur/self._speed
        return dur

    # return the current local time in [0, dur]
    # after time manipulations
    def getLocalTime(self):
        return self._time

    # set local time to t and return value at t
    def getValue(self, t):
        # time manipulate transform
        t = self._transformTime(t)
        self._time = t

        # assert that t is in [0,dur)
        # i.e. assert end-point exclusive model
        if self._dur>0:
            if t<0 or t>self._dur or (t==self._dur and not self._autoReverse):
                raise AssertionError

        # compute interpolated value according to calcMode
        v = self._inrepol(t)

        # accumulate
        if self._accumulate=='sum' and self._accValue:
            v = self._accValue + v

        self._curvalue = v
        return v

    def getCurrValue(self):
        return self._curvalue

    # mainly for freeze and accumulate calculations
    def setToEnd(self):
        if self._dur <= 0: return
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

    # reset
    def restart(self):
        self._repeatCounter = 0
        self._accValue = None
        self._curvalue = None
        self._time = None

    def isAdditive(self):
        return self._additive=='sum'

    def isAccumulating(self):
        return self._accumulate=='sum'

    def isEffValueAnimator(self):
        return 0

    def addCurrValue(self, v):
        return self.addValues(v, self._curvalue)

    # redefine this method to override addition (for additive attributes)
    def addValues(self, v1, v2):
        return v1 + v2

    # redefine this method to override metrics (for paced mode)
    def distValues(self, v1, v2):
        return math.fabs(v2-v1)

    # t in [0, dur]
    def _getinterval(self, t):
        tl = self._efftimes
        n = len(tl)
        for i in range(n-1):
            if t >= tl[i] and t < tl[i+1]:
                return i, (t - tl[i]) / (tl[i+1] - tl[i])
        # t == dur
        if self._mode == 'discrete':
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

    # set legal attr values range
    def setRange(self, range):
        self._range = range

    # the following method will be called by the EffectiveAnimator
    # to clamp the results at the top of the animation stack to the legal range
    # before applying them to the presentation value
    def clamp(self, v):
        if not self._range:
            return v
        if v < self._range[0]: return self._range[0]
        elif v > self._range[1]:return self._range[1]
        else: return v

    # the following method will be called by the EffectiveAnimator
    # to convert final value
    def convert(self, v):
        if self._convert:
            v = self._convert(v)
        return v

    def _setAccumulate(self, acc):
        if acc not in ('none', 'sum'):
            print 'invalid accumulate value:',acc
            self._accumulate = 'none'
        else:
            self._accumulate = acc

    def setOrigin(self, origin):
        self._origin = origin

    def setRetunedValuesConverter(self, cvt):
        self._convert = cvt

    def setEffectiveAnimator(self, ea):
        self._effectiveAnimator = ea

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
    def __init__(self, attr, domval, value, dur):
        Animator.__init__(self, attr, domval, (value, ), dur, mode ='discrete')

###########################
# A special animator to manage to-only additive animate elements
class EffValueAnimator(Animator):
    def __init__(self, attr, domval, value, dur, mode='linear',
                    times=None, splines=None, accumulate='none', additive='replace'):
        Animator.__init__(self, attr, domval, (domval, value,), dur, mode,
                times, splines, accumulate, additive)
    def isEffValueAnimator(self):
        return 1
    def getValue(self, t):
        if not self._effectiveAnimator:
            return Animator.getValue(self, t)
        u, v = self._values[:2]
        u = self._effectiveAnimator.getcurrentbasevalue(self)
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
    def __init__(self, attr, domval, values, dur, mode='paced',
                    times=None, splines=None, accumulate='none', additive='replace'):
        self._path = RNPath(values)

        # pass to base the length parameters of values or path
        values = self._path.getLengthValues()

        Animator.__init__(self, attr, 0, values, dur, mode,
                times, splines, accumulate, additive)

        # time to paced interval convertion factor
        if dur>0:
            self._time2length = self._path.getLength()/dur
        else:
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

    def addValues(self, v1, v2):
        n = len(v1)
        r = []
        for i in range(n):
            r.append(v1[i]+v2[i])
        return tuple(r)

    def getDOMValue(self):
        return self._path.coords[0]

class IntTupleAnimator(FloatTupleAnimator):
    def convert(self, v):
        n = len(v)
        l = []
        for i in range(n):
            l.append(round(v[i]))
        return tuple(l)

class EffIntTupleAnimator(IntTupleAnimator):
    def __init__(self, attr, domval, value, dur, mode='linear',
                    times=None, splines=None, accumulate='none', additive='replace'):
        IntTupleAnimator.__init__(self, attr, domval, (domval, value,), dur, mode,
                times, splines, accumulate, additive)
    def isEffValueAnimator(self):
        return 1
    def getValue(self, t):
        if not self._effectiveAnimator:
            return IntTupleAnimator.getValue(self, t)
        u, v = self._path.coords[:2]
        u = self._effectiveAnimator.getcurrentbasevalue(self)
        self._path = RNPath((u,v))
        return IntTupleAnimator.getValue(self, t)

###########################
# 'animateColor'  element animator
class ColorAnimator(IntTupleAnimator):
    def __init__(self, attr, domval, value, dur, mode='linear',
                    times=None, splines=None, accumulate='none', additive='replace'):
        IntTupleAnimator.__init__(self, attr, domval, value, dur, mode,
                times, splines, accumulate, additive)
    def clamp(self, v):
        n = len(v)
        r = []
        for i in range(n):
            if v[i]<0: r.append(0)
            elif v[i]>255: r.append(255)
            else: r.append(v[i])
        return tuple(r)


class EffColorAnimator(EffIntTupleAnimator):
    def __init__(self, attr, domval, value, dur, mode='linear',
                    times=None, splines=None, accumulate='none', additive='replace'):
        EffIntTupleAnimator.__init__(self, attr, domval, value, dur, mode,
                times, splines, accumulate, additive)
    def isEffValueAnimator(self):
        return 1
    def clamp(self, v):
        n = len(v)
        r = []
        for i in range(n):
            if v[i]<0: r.append(0)
            elif v[i]>255: r.append(255)
            else: r.append(v[i])
        return tuple(r)

###########################
# 'animateMotion' element animator
class MotionAnimator(Animator):
    def __init__(self, attr, domval, path, dur, mode='paced',
                    times=None, splines=None, accumulate='none', additive='replace'):
        self._path = path

        # pass to base the length parameters of values or path
        values = path.getLengthValues()

        Animator.__init__(self, attr, 0, values, dur, mode,
                times, splines, accumulate, additive)

        # time to paced interval convertion factor
        if dur <= 0:
            self._time2length = 0
        else:
            self._time2length = path.getLength()/dur

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

    def convert(self, v):
        x, y = v.real, v.imag
        return round(x), round(y)

    def getDOMValue(self):
        x, y = self._path.getPointAtLength(0)
        return complex(0,0)

class EffMotionAnimator(Animator):
    def __init__(self, attr, domval, value, dur, mode='paced',
                    times=None, splines=None, accumulate='none', additive='replace'):
        x, y = value
        value = complex(x,y)
        Animator.__init__(self, attr, domval, (domval, value,), dur, mode,
                times, splines, accumulate, additive)

    def isEffValueAnimator(self):
        return 1

    def getValue(self, t):
        if not self._effectiveAnimator:
            return Animator.getValue(self, t)
        u, v = self._values[:2]
        u = self._effectiveAnimator.getcurrentbasevalue(self)
        self._values = u, v
        return Animator.getValue(self, t)

    def convert(self, v):
        x, y = v.real, v.imag
        return round(x), round(y)

    def distValues(self, v1, v2):
        x1, y1 = v1.real, v1.imag
        x2, y2 = v2.real, v2.imag
        dx = x2 - x1;dy=y2-y1
        return math.sqrt(dx*dx+dy*dy)

class DiscreteMotionAnimator(Animator):
    def __init__(self, attr, domval, value, dur, mode='paced',
                    times=None, splines=None, accumulate='none', additive='replace'):
        x, y = value
        value = complex(x,y)
        Animator.__init__(self, attr, domval, (value,), dur, mode,
                times, splines, accumulate, additive)

    def convert(self, v):
        x, y = v.real, v.imag
        return round(x), round(y)

    def distValues(self, v1, v2):
        x1, y1 = v1.real, v1.imag
        x2, y2 = v2.real, v2.imag
        dx = x2 - x1;dy=y2-y1
        return math.sqrt(dx*dx+dy*dy)

class SetMotionAnimator(Animator):
    def __init__(self, attr, domval, value, dur):
        Animator.__init__(self, attr, domval, (value, ), dur, mode ='discrete')

    def convert(self, v):
        x, y = v.real, v.imag
        return round(x), round(y)

###########################
# An EffectiveAnimator is responsible to combine properly
# all animations of the same attribute and the base value
# to give the final display value.
# This is the entity that knows and keeps the attr display value
# taking into account all animations and the dom value.
# Implements animations composition semantics
#       'additive' attribute + priorities
#  and is an entity at a higher level than animators (and thus channels).

class EffectiveAnimator:
    def __init__(self, context, targnode, attr, domval):
        self.__context = context
        self.__node = targnode
        self.__attr = attr
        self.__domval = domval

        self.__animators = []

        self.__chan = None
        self.__currvalue = None

        # keep target type for exceptions
        if targnode.getClassName() in ('Region', 'Viewport'):
            self.__tag = 'region'
        else:
            if targnode.GetType() == 'anchor': # area
                self.__tag = 'area'
            else:
                self.__tag = 'subregion'

        # we need a temporary instance of the
        # last animator removed from self.__animators
        self.__lastanimator = None

        # helper variables
        self.__layout = None
        self.__subChannels = []

    def getDOMValue(self):
        return self.__domval

    def getAttrName(self):
        return self.__attr

    def getCurrValue(self):
        return self.__currvalue

    def getTargetNode(self):
        return self.__node

    def getCssObj(self, mmobj):
        resolver = self.__context.getCssResolver()
        return resolver.getCssObj(mmobj)

    def getCssAttr(self, mmobj, name):
        return self.getCssObj(mmobj).getRawAttr(name)

    def getPxGeom(self, mmobj):
        return self.getCssObj(mmobj).getPxGeom()

    def onAnimateBegin(self, targChan, animator):
        for a in self.__animators:
            if id(a) == id(animator):
                self.__animators.remove(animator)
        self.__animators.append(animator)
        animator.setEffectiveAnimator(self)
        if not self.__chan:
            self.__chan = targChan
        if self.__attr == 'transition':
            self.__begintransition(animator)
        if debug: print 'adding animator', animator

    def onAnimateEnd(self, targChan, animator, update=1):
        self.__animators.remove(animator)
        if debug: print 'removing animator',animator
        if not self.__animators:
            self.__lastanimator = animator
        if update: self.update(targChan)
        self.__lastanimator = None
        if self.__attr == 'transition':
            self.__endtransition()

    # compute and apply animations composite effect
    # this method is a notification from some animator
    # or some other knowledgeable entity that something has changed
    def update(self, targChan):
        if not self.__chan:
            self.__chan = targChan

        cv = self.__domval
        for a in self.__animators:
            if a.isAdditive() and not a.isEffValueAnimator():
                cv = a.addCurrValue(cv)
            else:
                cv = a.getCurrValue()

        # keep a copy
        self.__currvalue = cv

        # convert and clamp display value
        displayValue = cv
        a = None
        if self.__animators:
            a = self.__animators[0]
        elif self.__lastanimator:
            a = self.__lastanimator
        if a:
            displayValue = a.convert(displayValue)
            displayValue = a.clamp(displayValue)

        # update presentation value

        # handle regions and areas separately
        if self.__tag == 'region':
            self.__updateregion(displayValue)
            return
        elif self.__tag == 'area':
            self.__updatearea(displayValue)
            return
        elif self.__attr == 'transition':
            self.__settransitionvalue(displayValue)
            return
        elif self.__attr in ('top','left','width','height','right','bottom','position', 'z', 'bgcolor'):
            self.__updatesubregion(displayValue)
            return

        # normal proccessing
        self.__node.SetPresentationAttr(self.__attr, displayValue)

        # notify/update display value if we have a channel
        if self.__chan:
            self.__chan.updateattr(self.__node, self.__attr, displayValue)
            if debug:
                if cv == self.__domval:
                    print 'update',self.__attr,'of channel',self.__chan._name,'to',displayValue,'(domvalue)'
                else:
                    print 'update',self.__attr,'of channel',self.__chan._name,'to',displayValue
        elif debug:
            name = MMAttrdefs.getattr(self.__node, 'name')
            if cv == self.__domval:
                print 'update',self.__attr,'of node',name,'to',displayValue,'(domvalue)'
            else:
                print 'update',self.__attr,'of node',name,'to',displayValue


    def __getLayoutChannel(self, name):
        from Channel import channels
        for chan in channels:
            type = chan._attrdict.get('type')
            if type == 'layout' and chan._name == name:
                return chan

    def __appendSubChannels(self, region, childs):
        from Channel import channels
        for chan in channels:
            base_window = chan._attrdict.get('base_window')
            if base_window == region._name:
                childs.append(chan)
                self.__appendSubChannels(chan, childs)

    # update region attributes display value
    def __updateregion(self, value):
        attr = self.__attr
        ch = self.__node
        regionname = ch.name

        # locate region and its contents (once)
        if not self.__layout:
            self.__layout = self.__getLayoutChannel(regionname)
            self.__appendSubChannels(self.__layout, self.__subChannels)
        if not self.__layout:
            return

        region = self.__layout._attrdict

        if attr == 'position':
            # origin is 'parent'
            cssregion = self.getCssObj(region)
            cssregion.move(value)
            cssregion.updateTree()
            coords = cssregion.getPxGeom()
            fit = cssregion.getFit()
            if self.__layout.window:
                self.__layout.window.updatecoordinates(coords, UNIT_PXL, fit, None)
            for subch in self.__subChannels:
                if subch._attrdict.get('type') == 'layout':
                    cssreg = self.getCssObj(subch._attrdict)
                    if subch.window:
                        subch.window.updatecoordinates(cssreg.getPxGeom(), UNIT_PXL, cssreg.getFit(), None)
                elif subch._armed_node:
                    node = subch._armed_node
                    csssubreg = self.getCssObj(node)
                    cssmedia = csssubreg.media
                    if subch.window:
                        subch.window.updatecoordinates(csssubreg.getPxGeom(), UNIT_PXL, csssubreg.getFit(), cssmedia.getPxGeom())

        elif attr in ('left','top','width','height','right','bottom'):
            cssregion = self.getCssObj(region)
            cssregion.changeRawAttr(attr, value)
            cssregion.updateTree()
            coords = cssregion.getPxGeom()
            fit = cssregion.getFit()
            if self.__layout.window:
                self.__layout.window.updatecoordinates(coords, UNIT_PXL, fit, None)
            for subch in self.__subChannels:
                if subch._attrdict.get('type') == 'layout':
                    cssreg = self.getCssObj(subch._attrdict)
                    if subch.window:
                        subch.window.updatecoordinates(cssreg.getPxGeom(), UNIT_PXL, cssreg.getFit(), None)
                elif subch._armed_node:
                    node = subch._armed_node
                    csssubreg = self.getCssObj(node)
                    cssmedia = csssubreg.media
                    if subch.window:
                        subch.window.updatecoordinates(csssubreg.getPxGeom(), UNIT_PXL, csssubreg.getFit(), cssmedia.getPxGeom())

        elif attr=='z':
            if self.__layout.window:
                self.__layout.window.updatezindex(value)
            region.SetPresentationAttr(attr, value)

        elif attr=='bgcolor':
            if self.__layout.window:
                self.__layout.window.updatebgcolor(value)
            for subch in self.__subChannels:
                # check for inherited attr
                if not subch._attrdict.get('bgcolor') and subch.window:
                    subch.window.updatebgcolor(value)
            region.SetPresentationAttr(attr, value)

        elif attr=='soundLevel':
            for subch in self.__subChannels:
                if hasattr(subch,'updatesoundlevel'):
                    subch.updatesoundlevel(value)
            region.SetPresentationAttr(attr, value)
        else:
            print 'update',attr,'of region',regionname,'to',value,'(unsupported)'

        if debug:
            print 'update',attr,'of region',regionname,'to',value


    # update area attributes display value
    def __updatearea(self, value):
        attr = self.__attr
        node = self.__node
        name = node.attrdict.get('name')
        # notify/update display value if we have a channel
        if self.__chan:
            if self.__chan._played_anchor2button.has_key(name):
                button = self.__chan._played_anchor2button[name]
                if attr == 'coords':
                    button.updatecoordinates(value)
            if debug:
                print 'update area',self.__attr,'of channel',self.__chan._name,'to',value
        elif debug:
            name = MMAttrdefs.getattr(self.__node, 'name')
            print 'update area',self.__attr,'of node',name,'to',value


    def __updatesubregion(self, value):
        if not self.__chan:
            return
        chan = self.__chan

        if self.__attr == 'position':
            # 19/3/2001: according to a recent resolution of the working group:
            # subregion is what is moved
            # default origin is parent left top corner
            csssubregion = self.getCssObj(self.__node)
            csssubregion.move(value)
            csssubregion.updateTree()
            coords = csssubregion.getPxGeom()
            fit = csssubregion.getFit()
            mediacoords = None
            if csssubregion.media:
                csssubregion.media.update()
                mediacoords = csssubregion.media.getPxGeom()
            if chan.window:
                chan.window.updatecoordinates(coords, UNIT_PXL, fit, mediacoords)

        elif self.__attr in ('left','top','width','height','right','bottom'):
            csssubregion = self.getCssObj(self.__node)
            csssubregion.changeRawAttr(self.__attr, value)
            csssubregion.updateTree()
            coords = csssubregion.getPxGeom()
            fit = csssubregion.getFit()
            mediacoords = None
            if csssubregion.media:
                csssubregion.media.update()
                mediacoords = csssubregion.media.getPxGeom()
            if chan.window:
                chan.window.updatecoordinates(coords, UNIT_PXL, fit, mediacoords)

        elif self.__attr=='bgcolor':
            if chan.window:
                chan.window.updatebgcolor(value)

        elif self.__attr=='z':
            if chan.window:
                chan.window.updatezindex(value)

        if debug:
            print 'update',self.__attr,'of channel',self.__chan._name,'to',value

    def __begintransition(self, anim):
        if self.__chan and self.__chan.window:
            self.__chan.window.begintransition(anim._trdict['mode']=='out', 0, anim._trdict, None)
        if debug: print 'begintransition', anim._trdict

    def __endtransition(self):
        if self.__chan and self.__chan.window:
            self.__chan.window.endtransition()
        if debug: print 'endtransition'

    def __settransitionvalue(self, value):
        if debug: print 'settransitionvalue', value
        if self.__chan and self.__chan.window:
            self.__chan.window.settransitionvalue(value)

    def getcurrentbasevalue(self, animator=None):
        cv = self.__domval
        for a in self.__animators:
            if animator and id(a) == id(animator):
                break
            if a.isAdditive() and not a.isEffValueAnimator():
                cv = a.addCurrValue(cv)
            else:
                cv = a.getCurrValue()
        return cv


###########################
# AnimateContext is an EffectiveAnimator repository
# We need a well-known repository so that we can find EffectiveAnimators
# from Animators (channel) context.
# Implements also operations that apply to all EffectiveAnimator objects
# and is a document level entity.

class AnimateContext:
    def __init__(self, player=None, node=None):
        self._player = player
        self._effAnimators = {}
        self._id2key = {}
        if player:
            self._root = player.root
            ctx=player.context
        elif node:
            self._root = node.GetRoot()
            ctx=node.GetContext()
        self._ctx = ctx
        self._cssResolver = ctx.newCssResolver(self._root)
        self._cssDomResolver = None # will be created if needed

    def reset(self):
        del self._id2key
        del self._effAnimators
        self._effAnimators = {}
        self._id2key = {}
        self._cssResolver = None
        self._cssDomResolver = None

    def getEffectiveAnimator(self, targnode, targattr, domval):
        key = "n%d-%s" % (id(targnode), targattr)
        if self._effAnimators.has_key(key):
            return self._effAnimators[key]
        else:
            ea = EffectiveAnimator(self, targnode, targattr, domval)
            self._effAnimators[key] = ea
            self._id2key[id(ea)] = key
            return ea

    def removeEffectiveAnimator(self, ea):
        eaid = id(ea)
        if self._id2key.has_key(eaid):
            key = self._id2key[eaid]
            if debug: print 'removing eff animator', key
            del self._effAnimators[key]
            del self._id2key[eaid]

    def getCssResolver(self):
        if not self._cssResolver:
            self._cssResolver = self._ctx.newCssResolver(self._root)
        return self._cssResolver

    def getDOMCssResolver(self):
        if not self._cssDomResolver:
            self._cssDomResolver = self._ctx.newCssResolver(self._root)
        return self._cssDomResolver

    def getAbsPos(self, mmobj):
        resolver = self.getDOMCssResolver()
        region = resolver.getCssObj(mmobj)
        return region.getAbsPos()

    def getParentAbsPos(self, mmobj):
        resolver = self.getDOMCssResolver()
        region = resolver.getCssObj(mmobj)
        if region.container:
            return region.container.getAbsPos()
        return 0, 0

    def getNodePosRelToParent(self, mmobj):
        resolver = self.getDOMCssResolver()
        region = resolver.getCssObj(mmobj)
        if region.media:
            x, y = region.media.getAbsPos()
        else:
            x, y = region.getAbsPos()
        xp, yp = 0, 0
        if region.container.container:
            region = region.container.container
            xp, yp = region.getAbsPos()
        return x-xp, y-yp

###########################

additivetypes = ['int', 'float', 'color', 'position', 'inttuple', 'floattuple']
alltypes = ['string',] + additivetypes

animatetypes = ['invalid', 'values', 'from-to', 'from-by', 'to', 'by']

# Animation syntax and semantics parser
class AnimateElementParser:
    def __init__(self, anim, ctx, sctx = None):
        self.__anim = anim                      # the animate element node
        self.__elementTag = anim.attrdict['atag']
        self.__attrname = ''            # target attribute name
        self.__attrtype = ''            # in alltypes (see above)
        self.__domval = None            # document attribute value
        self.__refval = None            # attribute reference value for percent
        self.__target = None            # target node
        self.__targettype = None        # target type in ('region', 'subregion', 'area')
        self.__hasValidTarget = 0       # valid target node and attribute

        self.__grinsattrname = ''       # grins internal target attribute name
        self.__animtype = 'invalid'     # in animatetypes (see above)
        self.__isadditive = 0

        self.__animateContext = ctx # animate context
        self.__sctx = sctx      # Scheduler Context
        self.__mmtarget = None # the MM object target of animateMotion (used for absolute coords)

        if not basicAnimation:
            return

        ############################
        # Locate target node

        # for some elements not represented by nodes (region, area, transition)
        # create a virtual node
        # once target found (self.__target)
        # set its grins-type (self.__targettype in ('subregion', 'region', 'area') )

        if anim.targetnode is None:
            te = MMAttrdefs.getattr(anim, 'targetElement')
            if te:
                anim.targetnode = anim.GetRoot().GetChildByName(te)
                if not anim.targetnode:
                    anim.targetnode = anim.GetContext().getchannel(te)
            else:
                anim.targetnode = anim.GetParent()

        if anim.targetnode is None:
            # missing target node
            te = MMAttrdefs.getattr(anim, 'targetElement')
            print 'Failed to locate target element', te
            print '\t',self
            return

        self.__target = anim.targetnode

        if self.__target.getClassName() in ('Region', 'Viewport'):
            self.__targettype = 'region'
        else:
            if self.__target.GetType() == 'anchor': # area
                self.__targettype = 'area'
            else:
                self.__targettype = 'subregion'


        # verify
        if debugParser:
            print self.__elementTag, self.__target, self.__targettype


        ########################################
        # Locate target attribute, its DOM value and type

        # do we have a valid target attribute?
        self.__hasValidTarget = self.__checkTarget()

        self.__isadditive = self.__attrtype in additivetypes

        # verify
        if debugParser:
            print self.__grinsattrname, self.__attrname, self.__domval, self.__attrtype


        ########################################
        # find animation type i.e. one of
        # ['invalid', 'values', 'from-to', 'from-by', 'to', 'by']

        self.__animtype = self.__getAnimationType()
        if self.__animtype == 'invalid' and self.__elementTag!='transitionFilter':
            print 'Syntax error: Invalid animation values'
            print '\t',self

        # verify
        if debugParser:
            print 'animation type: ', self.__animtype

        ########################################
        # Read enumeration attributes

        # additive has the default value 'replace' see SMIL.py
        self.__additive = MMAttrdefs.getattr(anim, 'additive')
        if self.__additive == 'sum' and not self.__isadditive:
            print 'Warning: additive attribute will be ignored. The target attribute does not support additive animation.'
            self.__additive = 'replace'

        # for 'by-only animation' force: additive = 'sum'
        if self.__animtype == 'by' and self.__isadditive:
            self.__additive = 'sum' # XXX guess by sjoerd

        # accumulate has the default value 'none' see SMIL.py
        self.__accumulate = MMAttrdefs.getattr(anim, 'accumulate')
        if self.__accumulate == 'sum' and not self.__isadditive:
            print 'Warning: accumulate attribute will be ignored. The target attribute does not support additive animation.'
            self.__accumulate = 'none'

        # calcMode has the default value 'paced' for animateMotion
        # end 'linear' for all the other cases
        self.__calcMode = MMAttrdefs.getattr(anim, 'calcMode')
        if not splineAnimation and self.__calcMode == 'spline':
            print 'Warning: Module SplineAnimation is disabled'
            print '\t',self
            self.__calcMode = None
        if not self.__calcMode:
            if self.__elementTag == 'animateMotion':
                self.__calcMode = 'paced'
            else:
                self.__calcMode = 'linear'


        ########################################
        # Read time manipulation attributes
        # speed="1" is a no-op, and speed="-1" means play backwards
        # This speed is relative to parent.
        # The context absolute speed is set elsewhere.
        self.__speed = MMAttrdefs.getattr(anim, 'speed')
        if self.__speed==0.0: # not allowed
            self.__speed=1.0
        self.__accelerate = max(0, MMAttrdefs.getattr(anim, 'accelerate'))
        self.__decelerate = max(0, MMAttrdefs.getattr(anim, 'decelerate'))
        dt =  self.__accelerate + self.__decelerate
        if dt>1.0:
            # accelerate is clamped to 1 and decelerate=1-accelerate
##             self.__accelerate = min(self.__accelerate, 1.0)
##             self.__decelerate = 1.0 - self.__accelerate
            self.__accelerate = self.__decelerate = 0
        self.__autoReverse = MMAttrdefs.getattr(anim, 'autoReverse')

        if not timeManipulations and \
                (self.__speed!=1.0 or self.__accelerate or self.__decelerate or self.__autoReverse):
            print 'Warning: Module TimeManipulations is disabled'
            print '\t',self
            self.__speed = 1.0
            self.__accelerate = self.__decelerate = 0
            self.__autoReverse = 0

##     def __repr__(self):
##         import SMILTreeWrite
##         return SMILTreeWrite.WriteBareString(self.__anim)

    # this is the main service method of this class
    # returns an appropriate animator or None
    def getAnimator(self):
        if not basicAnimation:
            return None

        if not self.__hasValidTarget:
            return None

        if self.__elementTag=='transitionFilter':
            return self.__getTransitionFilterAnimator()

        if self.__animtype == 'invalid':
            return None

        ################
        # set element
        if self.__elementTag=='set':
            return self.__getSetAnimator()

        # a discrete to animation or a to animation of a non addidive attribute is equivalent to set
        if self.__animtype == 'to' and not self.__isadditive:
            return self.__getSetAnimator()

        ################
        # shortcuts
        attr = self.__grinsattrname
        domval = self.__domval
        accumulate = self.__accumulate
        additive = self.__additive
        mode = self.__calcMode
        dur = self.getDuration()

        # check for keyTimes, keySplines
        if not splineAnimation or mode == 'paced':
            # ignore times and splines for 'paced' animation
            times = splines = ()
        else:
            times = self.__getInterpolationKeyTimes()
            splines = self.__getInterpolationKeySplines()

        ################
        # to-only animation for additive attributes
        # needs always special handling
        if self.__animtype == 'to' and self.__isadditive:
            anim = None
            if mode == 'discrete':
                if self.__attrtype == 'int':
                    v = string.atoi(self.getTo())
                    anim = Animator(attr, domval, (v,), dur, mode, times, splines, accumulate, additive)
                    anim.setRetunedValuesConverter(round)
                elif self.__attrtype == 'float':
                    v = string.atof(self.getTo())
                    anim = Animator(attr, domval, (v,), dur, mode, times, splines, accumulate, additive)
                elif self.__attrtype == 'color':
                    values = self.__getColorValues()
                    anim = ColorAnimator(attr, domval, (values,), dur, mode, times, splines, accumulate, additive)
                elif self.__attrtype == 'position':
                    coords = self.__getNumPairInterpolationValues()
                    if coords:
                        anim = DiscreteMotionAnimator(attr, domval, coords, dur, mode, times, splines, accumulate, additive)
                elif self.__attrtype == 'inttuple':
                    coords = self.__getNumTupleInterpolationValues()
                    anim = IntTupleAnimator(attr, domval, (coords,), dur, mode, times, splines, accumulate, additive)
            else:
                if self.__attrtype == 'int':
                    v = string.atoi(self.getTo())
                    anim = EffValueAnimator(attr, domval, v, dur, mode, times, splines, accumulate, additive)
                    anim.setRetunedValuesConverter(round)
                elif self.__attrtype == 'float':
                    v = string.atof(self.getTo())
                    anim = EffValueAnimator(attr, domval, v, dur, mode, times, splines, accumulate, additive)
                elif self.__attrtype == 'color':
                    values = self.__getColorValues()
                    if values:
                        anim = EffColorAnimator(attr, domval, values, dur, mode, times, splines, accumulate, additive)
                elif self.__attrtype == 'position':
                    coords = self.__getNumPairInterpolationValues()
                    if coords:
                        anim = EffMotionAnimator(attr, domval, coords, dur, mode, times, splines, accumulate, additive)
                elif self.__attrtype == 'inttuple':
                    coords = self.__getNumTupleInterpolationValues()
                    anim = EffIntTupleAnimator(attr, domval, coords, dur, mode, times, splines, accumulate, additive)
            if anim:
                self.__setTimeManipulators(anim)
            return anim

        ################
        # by-only animation for additive attributes
        # like normal 'values' type except that the attribute must be additive
        if self.__animtype == 'by':
            if not self.__isadditive:
                return None
            anim = None
            if self.__attrtype == 'int':
                values = self.__getNumInterpolationValues()
                if mode == 'discrete': values = values[1:]
                anim = Animator(attr, domval, values, dur, mode, times, splines, accumulate, additive='sum')
                anim.setRetunedValuesConverter(round)
            elif self.__attrtype == 'float':
                values = self.__getNumInterpolationValues()
                if mode == 'discrete': values = values[1:]
                anim = Animator(attr, domval, values, dur, mode, times, splines, accumulate, additive='sum')
            elif self.__attrtype == 'color':
                values = self.__getColorValues()
                if mode == 'discrete': values = values[1:]
                anim = ColorAnimator(attr, domval, values, dur, mode, times, splines, accumulate, additive='sum')
            elif self.__attrtype == 'position':
                if mode == 'discrete':
                    coords = self.__getNumPairInterpolationValues()
                    if coords:
                        anim = DiscreteMotionAnimator(attr, domval, coords[1], dur, mode, times, splines, accumulate, additive='sum')
                else:
                    path = svgpath.Path()
                    coords = self.__getNumPairInterpolationValues()
                    if coords:
                        path.constructFromPoints(coords)
                        anim = MotionAnimator(attr, domval, path, dur, mode, times, splines, accumulate, additive='sum')
            if anim:
                self.__setTimeManipulators(anim)
            return anim

        ################
        # animateColor or attrtype=='color'
        if self.__elementTag == 'animateColor' or self.__attrtype=='color':
            values = self.__getColorValues()
            if not self.__checkValues(values, times, splines, mode):
                return None
            anim = ColorAnimator(attr, domval, values, dur, mode, times, splines, accumulate, additive)
            self.__setTimeManipulators(anim)
            return anim

        ################
        # animateMotion  (or attrtype=='position')
        if self.__elementTag=='animateMotion' or self.__attrtype=='position':
            strpath = ''
            if splineAnimation:
                strpath = MMAttrdefs.getattr(self.__anim, 'path')
            path = svgpath.Path()
            if strpath:
                path.constructFromSVGPathString(strpath)
                if not self.isAdditive():
                    path = self.translateToDefault(path=path)
            else:
                coords = self.__getNumPairInterpolationValues()
                if not self.isAdditive():
                    coords = self.translateToDefault(coords=coords)
                path.constructFromPoints(coords)
            if path.getLength():
                anim = MotionAnimator(attr, domval, path, dur, mode, times, splines,
                        accumulate, additive)
                self.__setTimeManipulators(anim)
                return anim
            return None

        ################
        # animate

        # 4. Return an animator based on the attr type
        if debug: print 'Guessing animator for attribute',`self.__attrname`,'(', self.__attrtype,')'
        anim = None
        if self.__attrtype == 'int':
            values = self.__getNumInterpolationValues()
            if not self.__checkValues(values, times, splines, mode):
                return None
            anim = Animator(attr, domval, values, dur, mode, times, splines,
                    accumulate, additive)
            anim.setRetunedValuesConverter(round)

        elif self.__attrtype == 'float':
            values = self.__getNumInterpolationValues()
            if not self.__checkValues(values, times, splines, mode):
                return None
            anim = Animator(attr, domval, values, dur, mode, times, splines,
                    accumulate, additive)

        elif self.__attrtype == 'string' or self.__attrtype == 'enum' or self.__attrtype == 'bool':
            mode = 'discrete' # override calc mode
            values = self.__getAlphaInterpolationValues()
            if not self.__checkValues(values, times, splines, mode):
                return None
            anim = Animator(attr, domval, values, dur, mode, times, splines,
                    accumulate, additive)

        elif self.__attrtype == 'inttuple':
            values = self.__getNumTupleInterpolationValues()
            if not self.__checkValues(values, times, splines, mode):
                return None
            anim = IntTupleAnimator(attr, domval, values, dur, mode, times, splines,
                    accumulate, additive)

        elif self.__attrtype == 'floattuple':
            values = self.__getNumTupleInterpolationValues()
            if not self.__checkValues(values, times, splines, mode):
                return None
            anim = FloatTupleAnimator(attr, domval, values, dur, mode, times, splines,
                    accumulate, additive)
        if anim:
            self.__setTimeManipulators(anim)
        return anim

    # return an animator for the 'set' animate element
    def __getSetAnimator(self):
        if not basicAnimation:
            return None

        if not self.__hasValidTarget:
            return None

        attr = self.__attrname
        domval = self.__domval

        value = self.getTo()
        if value==None or value=='':
            print 'set element without attribute to'
            return None

        dur = self.getDuration()

        anim = None

        if self.__attrtype == 'int':
            value = string.atoi(value)
            anim = SetAnimator(attr, domval, value, dur)
            anim.setRetunedValuesConverter(round)

        elif self.__attrtype == 'float':
            value = string.atof(value)
            anim = SetAnimator(attr, domval, value, dur)

        elif self.__attrtype == 'string' or self.__attrtype == 'enum' or self.__attrtype == 'bool':
            anim = SetAnimator(attr, domval, value, dur)

        elif self.__attrtype == 'inttuple':
            value = self.__split(value)
            value = map(string.atoi, value)
            anim = SetAnimator(attr, domval, value, dur)

        elif self.__attrtype == 'position':
            x, y = self.__getNumPair(value)
            if not self.isAdditive():
                x, y = self.translateToDefault(coords=((x,y),))[0]
            anim = SetMotionAnimator(attr, domval, complex(x, y), dur)

        elif self.__attrtype == 'color':
            value = self.__convert_color(value)
            anim = SetAnimator(attr, domval, value, dur)

        elif self.__attrtype == 'floattuple':
            value = self.__splitf(value)
            anim = SetAnimator(attr, domval, value, dur)

        if anim:
            self.__setTimeManipulators(anim)

        return anim

    def __getTransitionFilterAnimator(self):
        if not basicAnimation:
            return None

        if not self.__hasValidTarget:
            return None

        # shortcuts
        attr = self.__grinsattrname
        accumulate = self.__accumulate
        additive = self.__additive
        calcmode = self.__calcMode
        dur = self.getDuration()

        # get transition attrs
        trtype = MMAttrdefs.getattr(self.__anim, 'trtype')
        trsubtype = MMAttrdefs.getattr(self.__anim, 'subtype')
        trmode = MMAttrdefs.getattr(self.__anim, 'mode')

        # check for keyTimes, keySplines
        if not splineAnimation or calcmode == 'paced':
            # ignore times and splines for 'paced' animation
            times = splines = ()
        else:
            times = self.__getInterpolationKeyTimes()
            splines = self.__getInterpolationKeySplines()

        if self.__animtype == 'invalid':
            if trmode=='in':
                values = (0, 1)
                self.__domval = 1
            else:
                values = (1, 0)
                self.__domval = 0
        else:
            values = self.__getNumInterpolationValues()
            self.__domval = values[len(values)-1]
        anim = Animator(attr, self.__domval, values, dur, calcmode, times, splines, accumulate, additive)
        self.__setTimeManipulators(anim)
        anim.setRange((0.0,1.0))

        dict = {'trtype':trtype, 'subtype':trsubtype, 'mode':trmode}
        anim.setTransition(dict)

        return anim

    def getAttrName(self):
        return self.__attrname

    def getGrinsAttrName(self):
        return self.__grinsattrname

    def getDOMValue(self):
        return self.__domval

    def getDuration(self):
        dur = self.__anim.calcfullduration(self.__sctx, ignoreloop = 1, useend = 1)
        # force first value display (fulfil: use f(0) if duration is undefined)
        if dur is None or dur < 0:
            dur=0
        return dur

    def getFrom(self):
        return MMAttrdefs.getattr(self.__anim, 'from')

    def getTo(self):
        return MMAttrdefs.getattr(self.__anim, 'to')

    def getBy(self):
        return MMAttrdefs.getattr(self.__anim, 'by')

    def getValues(self):
        return MMAttrdefs.getattr(self.__anim, 'values')

    def getPath(self):
        return MMAttrdefs.getattr(self.__anim, 'path')

    def getOrigin(self):
        return MMAttrdefs.getattr(self.__anim, 'origin')

    def getKeyTimes(self):
        return MMAttrdefs.getattr(self.__anim, 'keyTimes')

    def getKeySplines(self):
        return MMAttrdefs.getattr(self.__anim, 'keySplines')

    def getTargetNode(self):
        return self.__target

    def isPositionAnimation(self):
        return self.__elementTag=='animateMotion' or self.__attrtype=='position'

    def getAnimationType(self):
        return self.__animtype

    def isAdditive(self):
        return self.__additive == 'sum'

    #
    #  Translate coordinates
    #
    def translateTo(self, pt, coords, path):
        dx, dy = pt
        if coords:
            tcoords = []
            for x, y in coords:
                tcoords.append((x+dx, y+dy))
            return tuple(tcoords)
        elif path:
            path.translate(dx, dy)
            return path

    # origin in ('default', 'layout', 'parent', 'topLayout')
    def translateToDefault(self, coords=None, path=None):
        # set default origin
        origin = self.getOrigin()
        if self.__targettype == 'region':
            if not origin or origin=='default':
                origin = regionOrigin
        elif self.__targettype == 'subregion':
            if not origin or origin=='default':
                origin = mediaOrigin

        # translate region coordiantes to  internal 'parent'
        if self.__targettype == 'region':

            if origin == 'parent':
                pass

            elif origin == 'layout':
                # coordinates of layout with respect to parent
                x, y = self.__domval.real, self.__domval.imag
                return self.translateTo((x, y), coords, path)

            elif origin == 'topLayout':
                # coordinates of topLayout with respect to parent
                x, y = self.__animateContext.getParentAbsPos(self.__mmtarget)
                return self.translateTo((-x, -y), coords, path)

                return self.translateTo((x, y), coords, path)

        # translate media coordinates to internal 'parent'
        elif self.__targettype == 'subregion':

            if origin == 'parent':
                pass

            elif origin == 'layout':
                x, y = self.__domval.real, self.__domval.imag
                return self.translateTo((x, y), coords, path)

            elif origin == 'topLayout':
                x, y = self.__animateContext.getParentAbsPos(self.__mmtarget)
                return self.translateTo((-x, -y), coords, path)

        if coords: return coords
        elif path: return path

    #
    # The following 3 translate methods are used by SMILTreeWriteXhtmlSmil
    #
    def toDOMOriginPosAttr(self, attr):
        val = MMAttrdefs.getattr(self.__anim, attr)
        if not val: return val
        cl = tokenizer.splitlist(val, delims = ' ,')
        if len(cl)>1:
            try:
                x, y = string.atoi(cl[0]), string.atoi(cl[1])
            except:
                return '0, 0'
        dx, dy = self.__domval.real, self.__domval.imag
        x = x - dx
        y = y - dy
        return '%d, %d' % (x, y)

    # transform pos values to coordinates with the dom value as origin
    def toDOMOriginPosValues(self):
        values = MMAttrdefs.getattr(self.__anim, 'values')
        if not values: return values
        dx, dy = self.__domval.real, self.__domval.imag
        strcoord = string.split(values,';')
        retstr = ''
        for str in strcoord:
            x, y = self.__getNumPair(str)
            x = x - dx
            y = y - dy
            retstr = retstr + '%d, %d;' % (x, y)
        if retstr:
            return retstr[:-1]
        return values

    def toDOMOriginPath(self):
        strpath = MMAttrdefs.getattr(self.__anim, 'path')
        if not strpath: return strpath
        dx, dy = self.__domval.real, self.__domval.imag
        path = svgpath.Path()
        path.constructFromSVGPathString(strpath)
        path.translate(-dx, -dy)
        return repr(path)


    # Translate methods for SMILTreeWriteXhtmlSmil
    def convertColorValue(self, value):
        if value is None or value.find('rgb') < 0:
            return value
        return self.__convert_color_rs(value)
    def convertColorValues(self, values):
        if not values or values.find('rgb') < 0:
            return values
        try:
            return ';'.join(map(self.__convert_color_rs, string.split(values,';')))
        except ValueError:
            return values

    # set time manipulators to the animator
    def __setTimeManipulators(self, anim):
        if self.__autoReverse:
            anim._setAutoReverse(1)
        if (self.__accelerate+self.__decelerate)>0.0:
            anim._setAccelerateDecelerate(self.__accelerate, self.__decelerate)
        if self.__speed!=1.0:
            anim._setSpeed(self.__speed)

    def __checkValues(self, values, times, splines, mode):
        try:
            assert( len(values) )
            assert( len(values)!=1 or mode == 'discrete' )
            assert( not times or len(times)==len(values) )
            assert( (not times or not splines) or len(splines)==len(times)-1)
        except:
            return 0
        return 1

    # check that we have a valid target attribute
    # get its DOM value and type
    # this method sets:
    # self.__attrname and its grins alias self.__grinsattrname
    # self.__attrtype, self.__domval
    # returns 1 on success and 0 on failure
    def __checkTarget(self):

        # Manage animateMotion first
        # animateMotion has an implicit attributeName (position)

        # for animate motion the implicit target attribute
        # is region.position or node.position
        if self.__elementTag=='animateMotion':
            self.__grinsattrname = self.__attrname = 'position'
            self.__attrtype = 'position'
            rc = None
            if self.__targettype == 'subregion':
                try:
                    rc = self.__target.getPxGeom()
                except:
                    rc = None
                self.__mmtarget = self.__target
            elif self.__targettype == 'region':
                ch = self.__target
                try:
                    rc = ch.getPxGeom()
                except:
                    rc = None
                self.__mmtarget = ch
            if rc:
                x, y, w, h = rc
                self.__domval = complex(x, y)
                return 1
            return 0

        # transitionFilter
        if self.__elementTag=='transitionFilter':
            self.__grinsattrname = self.__attrname = 'transition'
            self.__attrtype = 'float'
            rc = None
            if self.__targettype == 'subregion':
                self.__mmtarget = self.__target
                self.__domval = 0
                return 1
            elif self.__targettype == 'region':
                self.__mmtarget = self.__target
                self.__domval = 0
                return 1
            return 0

        # For all other animate elements we must have an explicit attributeName
        # else its a syntax error
        self.__attrname = MMAttrdefs.getattr(self.__anim, 'attributeName')
        if not self.__attrname:
            print 'failed to get attributeName'
            print '\t',self
            return 0

        # we have an attributeName
        # is it valid?

        if self.__attrname in ('left', 'top', 'width', 'height','right','bottom'):
            attr = self.__grinsattrname = self.__attrname
            self.__attrtype = 'int'
            rc = rcref = None
            if self.__targettype == 'subregion':
                try:
                    rc = self.__target.getPxGeom()
                except:
                    rc = None
                try:
                    channel = self.__target.GetChannel()
                    region = channel.GetLayoutChannel()
                    rcref = region.getPxGeom()
                except:
                    rcref = rc
            elif self.__targettype == 'region':
                ch = self.__target
                try:
                    rc = ch.getPxGeom()
                except:
                    rc = None
                try:
                    rcref = ch.GetParent().getPxGeom()
                    if rcref and len(rcref) == 2:
                        w, h = rcref
                        rcref = 0, 0, w, h
                except:
                    rcref = rc
            if rc:
                if attr == 'left':
                    v = rc[0]
                    vref = rcref[0]
                elif attr=='top':
                    v = rc[1]
                    vref = rcref[1]
                elif attr == 'right':
                    v = rc[0] + rc[2]
                    vref = rcref[0] + rcref[2]
                elif attr == 'bottom':
                    v = rc[1] + rc[3]
                    vref = rcref[1] + rcref[3]
                elif attr == 'width':
                    v = rc[2]
                    vref = rcref[2]
                elif attr == 'height':
                    v = rc[3]
                    vref = rcref[3]
                self.__domval = v
                self.__refval = vref
                return 1
            return 0

        if self.__attrname == 'backgroundColor':
            self.__grinsattrname = 'bgcolor'
            self.__attrtype = 'color'
            if self.__targettype == 'region':
                ch = self.__target
                self.__domval = ch.get('bgcolor')
                if not self.__domval:
                    self.__domval = 0, 0, 0
                return 1
            elif self.__targettype == 'subregion':
                self.__domval = self.__target.attrdict.get('bgcolor')
                if not self.__domval:
                    self.__domval = 0, 0, 0
                return 1
            return 0

        if self.__attrname == 'z-index':
            self.__grinsattrname = 'z'
            self.__attrtype = 'int'
            if self.__targettype == 'region':
                ch = self.__target
                self.__domval = ch.get('z')
                return 1
            elif self.__targettype == 'subregion':
                self.__domval = self.__target.attrdict.get('z')
                return 1
            return 0

        if self.__attrname == 'soundLevel':
            self.__grinsattrname = 'soundLevel'
            self.__attrtype = 'float'
            if self.__targettype == 'region':
                ch = self.__target
                self.__domval = ch.get('soundLevel', 1.0)
                self.__refval = 1.0
                return 1
            return 0

        if self.__attrname=='coords':
            self.__grinsattrname = 'coords'
            self.__attrtype = 'inttuple' # SMIL20: should be managed as 'string'
            d = self.__target.attrdict
            if d.has_key('coords'):
                coords = d['coords']
                # use grins convention
                shape, coords = coords[0], coords[1:]
                self.__domval = coords
            else:
                self.__domval = 0, 0, 0, 0
            return 1

        if self.__attrname == 'color':
            self.__grinsattrname = 'fgcolor'
            self.__attrtype = 'color'
            self.__domval = MMAttrdefs.getattr(self.__target, 'fgcolor')
            return 1

        self.__domval = MMAttrdefs.getattr(self.__target, self.__attrname)
        self.__grinsattrname = self.__attrname # low probability to be true
        self.__attrtype = MMAttrdefs.getattrtype(self.__attrname)

        if self.__domval==None:
            print 'Failed to get original DOM value for attr',self.__attrname,'from node',self.__target
            print '\t',self
            return 0

        return 1

    def __getAnimationType(self):
        if self.getValues() or self.getPath():
            return 'values'

        v1 = self.getFrom()
        v2 = self.getTo()
        dv = self.getBy()

        # if we don't have 'values' then 'to' or 'by' must be given
        if not v2 and not dv:
            return 'invalid'

        if v1:
            if v2:
                return 'from-to'
            elif dv:
                return 'from-by'
        else:
            if v2:
                return 'to'
            elif dv:
                return 'by'

        return 'invalid'


    # return list of interpolation values
    def __getNumInterpolationValues(self):
        # if 'values' are given ignore 'from/to/by'
        values =  self.getValues()
        if values:
            try:
                sl = string.split(values,';')
                vl = []
                for s in sl:
                    if s:
                        vl.append(self.safeatof(s))
                return tuple(vl)
            except ValueError:
                return ()

        if self.__animtype == 'from-to':
            return self.safeatof(self.getFrom()), self.safeatof(self.getTo())
        elif self.__animtype == 'from-by':
            v1 = self.safeatof(self.getFrom())
            dv = self.safeatof(self.getBy())
            return v1, v1+dv
        elif self.__animtype == 'to':
            return  self.safeatof(self.getTo())
        elif self.__animtype == 'by':
            return 0, self.safeatof(self.getBy())
        return ()

    def __getNumPair(self, v):
        if not v: return None
        if type(v) == type(complex(0,0)):
            return v.real, v.imag
        v = v.strip()
        if v[:1] == '(' and v[-1:] == ')':
            v = v[1:-1].strip()
        vl = self.__split(v)
        if len(vl)==2:
            x, y = vl
            return self.safeatof(x), self.safeatof(y)
        else:
            return None

    # return list of interpolation numeric pairs
    def __getNumPairInterpolationValues(self):
        # if 'values' are given ignore 'from/to/by'
        values =  self.getValues()
        if values:
            strcoord = string.split(values,';')
            coords = []
            for str in strcoord:
                if str:
                    pt = self.__getNumPair(str)
                    if pt != None:
                        coords.append(pt)
            return tuple(coords)
        if self.__animtype == 'from-to':
            v1 = self.__getNumPair(self.getFrom())
            v2 = self.__getNumPair(self.getTo())
            if v1 is None or v2 is None:
                return ()
            return v1, v2
        elif self.__animtype == 'from-by':
            v1 = self.__getNumPair(self.getFrom())
            dv = self.__getNumPair(self.getBy())
            if v1 is None or dv is None:
                return ()
            return v1, (v1[0]+dv[0], v1[1]+dv[1])
        elif self.__animtype == 'to':
            v = self.__getNumPair(self.getTo())
            if v is None: v = 0, 0
            return  v
        elif self.__animtype == 'by':
            v = self.__getNumPair(self.getBy())
            if v is None: v = 0, 0
            return (0, 0), v
        return ()

    # return list of interpolation numeric tuples
    def __getNumTupleInterpolationValues(self):
        # if 'values' are given ignore 'from/to/by'
        values =  self.getValues()
        if values:
            strcoord = string.split(values,';')
            L = []
            for str in strcoord:
                t = self.__splitf(str)
                if t!=None:
                    L.append(t)
            return tuple(L)

        if self.__animtype == 'from-to':
            return self.__splitf(self.getFrom()), self.__splitf(self.getTo())
        elif self.__animtype == 'from-by':
            v1 = self.__splitf(self.getFrom())
            dv = self.__splitf(self.getBy())
            ts = []
            for i in range(len(dv)):
                ts.append(v1[i]+dv[i])
            return v1, tuple(ts)
        elif self.__animtype == 'to':
            return  self.__splitf(self.getTo())
        elif self.__animtype == 'by':
            dv = self.__splitf(self.getBy())
            tz = []
            for i in range(len(dv)):
                tz.append(0)
            return tuple(tz), dv
        return ()


    # return list of interpolation strings
    def __getAlphaInterpolationValues(self):
        # if values are given ignore from/to/by
        if self.__animtype == 'values':
            values =  self.getValues()
            if values:
                return string.split(values,';')
        elif self.__animtype == 'from-to':
            return self.getFrom(), self.getTo()
        elif self.__animtype == 'from-by':
            return ()
        elif self.__animtype == 'to':
            return  self.getTo()
        elif self.__animtype == 'by':
            return ()
        return ()


    def __convert_color(self, val):
        from colors import convert_color, error
        try:
            return convert_color(val, system = 0, extend = 1)
        except error, msg:
            return 0, 0, 0

    def __convert_color_rs(self, val):
        from colors import rcolors
        val = self.__convert_color(val)
        if rcolors.has_key(val):
            return rcolors[val]
        else:
            return '#%02x%02x%02x' % val

    def __getColorValues(self):
        values =  self.getValues()
        if values:
            try:
                return tuple(map(self.__convert_color, string.split(values,';')))
            except ValueError:
                return ()

        if self.__animtype == 'from-to':
            return self.__convert_color(self.getFrom()),self.__convert_color(self.getTo())
        elif self.__animtype == 'from-by':
            v1 = self.__convert_color(self.getFrom())
            dv = self.__convert_color(self.getBy())
            return v1, (v1[0]+dv[0], v1[1]+dv[1], v1[2]+dv[2])
        elif self.__animtype == 'to':
            return  self.__convert_color(self.getTo())
        elif self.__animtype == 'by':
            dv = self.__convert_color(self.getBy())
            return (0, 0, 0), dv
        return ()

    # len of interpolation list values
    # len == 0 is a syntax error
    # len == 1 and mode != 'discrete' is a syntax error
    def __countInterpolationValues(self):
        values =  self.getValues()
        if values:
            l = string.split(values,';')
            return len(l)

        n = 0
        v1 = self.getFrom()
        if v1: n = n + 1
        elif self.__calcMode != 'discrete': n = n + 1

        v2 = self.getTo()
        dv = self.getBy()
        if v2 or dv: n = n + 1
        return n

    # return keyTimes or an empty list on failure
    def __getInterpolationKeyTimes(self):
        keyTimes = self.getKeyTimes()
        if not keyTimes: return []

        # len of values must be equal to len of keyTimes
        lvl = self.__countInterpolationValues()
        if  lvl != len(keyTimes):
            print 'values vs times mismatch'
            return []

        last = keyTimes[-1]
        if self.__calcMode !='discrete':
            # normalize keyTimes
            if last<=0.0:
                print 'invalid keyTimes'
                return []
            if last!=1.0:
                tl = []
                for t in keyTimes:
                    tl.append(t/last)
                keyTimes = tl

        # heuristics to cover proportions in 'discrete' mode
        dur = self.getDuration()
        if self.__calcMode =='discrete' and last<=1.0 and dur>0:
            # unnormalize
            tl = []
            for t in keyTimes:
                tl.append(t*dur)
            keyTimes = tl

        # check boundary constraints
        first = keyTimes[0]
        last = keyTimes[-1]
        if self.__calcMode == 'linear' or self.__calcMode == 'spline':
            if first!=0.0 or last!=1.0:
                print 'keyTimes range error'
                return []
        elif self.__calcMode == 'discrete':
            if first!=0.0:
                print 'not zero start keyTime'
                return []
        elif self.__calcMode == 'paced':
            print 'ignoring keyTimes for paced mode'
            return []

        # values should be increasing
        for i in  range(1,len(keyTimes)):
            if keyTimes[i] < keyTimes[i-1]:
                print 'keyTimes order mismatch'
                return []
        return keyTimes

    # return keySplines or an empty list on failure
    def __getInterpolationKeySplines(self):
        keySplines = self.getKeySplines()
        if not keySplines: return ()
        if self.__calcMode != 'spline':
            print 'splines while not in spline calc mode'
            return []
        sl = string.split(keySplines,';')

        # there must be one fewer sets of control points
        # the keySplines attribute than there are keyTimes.
        # This semantic (the duration is divided into n-1 even periods)
        # applies as well when the keySplines attribute is specified, but keyTimes is not
        keyTimes = self.getKeyTimes()
        if keyTimes:
            if len(sl) != len(keyTimes)-1:
                print 'intervals vs splines mismatch'
                return []

        rl = []
        for e in sl:
            vl = self.__split(e)
            if len(vl)==4:
                x1, y1, x2, y2 = map(string.atof, vl)
            else:
                print 'splines syntax error'
            if x1<0.0 or x1>1.0 or x2<0.0 or x2>1.0 or y1<0.0 or y1>1.0 or y2<0.0 or y2>1.0:
                print 'splines syntax error'
            rl.append((x1, y1, x2, y2))
        return rl

    def safeatof(self, s):
        if s and s[-1]=='%':
            if self.__refval and (type(self.__refval) == type(1.0) or type(self.__refval) == type(1)):
                return self.__refval*0.01*string.atof(s[:-1])
            return 0.01*string.atof(s[:-1])
        else:
            return string.atof(s)

    def __splitf(self, arg, f=None):
        if not f: f = self.safeatof
        if type(arg) == type(''):
            arg = self.__split(arg)
        try:
            return map(f, arg)
        except:
            return arg

    def __split(self, str):
        if type(str) == type(''):
            return tokenizer.splitlist(str, delims = ' \t\r\n,')
        return str
