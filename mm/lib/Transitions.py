__version__ = "$Id$"

# Machine-independent part of transitions.
#
# This module creates a number of transition classes. Each transition class
# consists of a machine-dependent base class that handles a specific type of bitblit and
# a subclass (declared here) that does the actual computation.
#
# This module also contains the factory function that handles creating the
# classes.
#
# These transition classes are driven by a machine dependent module that knows
# how to obtain the parameters that that bitblitters want from the windowinterface
# objects.
#
# XXX To be done: drawing color outlines if wanted
# XXX To be done: implementing more than the default subtype for each transition

import math

TAN_PI_DIV_3 = math.tan(math.pi/3)

from TransitionBitBlit import BlitterClass, R1R2BlitterClass, R1R2OverlapBlitterClass, \
        RlistR2OverlapBlitterClass, PolyR2OverlapBlitterClass, PolylistR2OverlapBlitterClass, \
        R1R2R3R4BlitterClass, FadeBlitterClass

class TransitionClass:

    def __init__(self, engine, dict):
        # Initialize a transition. Engine is our machine-dependent engine (not
        # used here but the blitter may want it) and dict is the MMNode transition
        # object
        # This is funky but it works: we know that our subclasses will inherit
        # some for of BlitterClass.
        BlitterClass.__init__(self, engine, dict)
        self.ltrb = (0, 0, 0, 0)
        self.dict = dict

    def move_resize(self, ltrb):
        # Called by the engine whenever the windowinterface code has resized
        # or moved the window, or when a new window has joined the transition.
        # Can be overridden by subclasses.
        self.ltrb = ltrb

    def computeparameters(self, value):
        # Compute a set of parameters (understandable to our blitter) that fully
        # describe the state the display should be in. The engine is responsible for
        # comparing this to the previous set and not doing an update if not needed.
        return None


class NullTransition(TransitionClass, BlitterClass):
    pass

class BarWipeTransition(TransitionClass, R1R2BlitterClass):
    # Reveal the new image by sweeping a divider line from left to right

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        if self.dict.get('subtype','leftToRight') == 'leftToRight':
            if self.dict.get('direction','forward') == 'forward':
                # left-to-right
                xpixels = int(value*(x1-x0)+0.5)
                xcur = x0+xpixels
                return ((x0, y0, xcur, y1), (xcur, y0, x1, y1))
            else:
                # right-to-left
                xpixels = int(value*(x1-x0)+0.5)
                xcur = x1-xpixels
                return ((xcur, y0, x1, y1), (x0, y0, xcur, y1))
        else:
            if self.dict.get('direction','forward') == 'forward':
                # top-to-bottom
                ypixels = int(value*(y1-y0)+0.5)
                ycur = y0+ypixels
                return ((x0, y0, x1, ycur), (x0, ycur, x1, y1))
            else:
                # bottom-to-top
                ypixels = int(value*(y1-y0)+0.5)
                ycur = y1-ypixels
                return ((x0, ycur, x1, y1), (x0, y0, x1, ycur))

class BoxWipeTransition(TransitionClass, R1R2OverlapBlitterClass):
    # Reveal the new image by an expanding box

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        # Assume left-to-right
        xpixels = int(value*(x1-x0)+0.5)
        ypixels = int(value*(y1-y0)+0.5)
        xcur = x0+xpixels
        ycur = y0+ypixels
        return ((x0, y0, xcur, ycur), (x0, y0, x1, y1))

class FourBoxWipeTransition(TransitionClass, RlistR2OverlapBlitterClass):
    # Reveal the new image by 4 boxes growing from the corners to the center

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        ymid = (y0+y1)/2
        xpixels = int(value*(xmid-x0)+0.5)
        ypixels = int(value*(ymid-y0)+0.5)
        boxes = (
                (x0, y0, x0+xpixels, y0+ypixels),
                (x1-xpixels, y0, x1, y0+ypixels),
                (x0, y1-ypixels, x0+xpixels, y1),
                (x1-xpixels, y1-ypixels, x1, y1))
        return (boxes, (x0, y0, x1, y1))

class BarnDoorWipeTransition(TransitionClass, R1R2OverlapBlitterClass):
    # Reveal the new image by sweeping two divier lines from the center outward

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        xpixels = int(value*(xmid-x0)+0.5)
        return ((xmid-xpixels, y0, xmid+xpixels, y1), (x0, y0, x1, y1))

class DiagonalWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by sweeping a diagonal divider line

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xwidth = (x1-x0)
        xmin = x0 - 2*xwidth
        xcur = xmin + int(value*2*xwidth)
        poly = (
                (xcur, y0),
                (xcur+2*xwidth, y0),
                (xcur+xwidth, y1),
                (xcur, y1))
        return poly, self.ltrb

class MiscDiagonalWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by two diagonals moving from the center out

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        width = (x1-x0)
        height = (y1-y0)
        xleft = x0 + value * width
        xright = x1 - value * width
        ytop = y0 + value * height
        ybot = y1 - value * height
        poly = (
                (x0, ybot),
                (x0, y1),
                (xleft, y1),
                (x1, ytop),
                (x1, y0),
                (xright, y0))
        return poly, self.ltrb

class VeeWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by sweeping a V shape down

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        width = (x1-x0)
        height = (y1-y0)
        if value <= 0.5:
            xleft = int(xmid-value*width)
            xright = int(xmid+value*width)
            ybot = int(y0+value*height)
            poly = (
                    (xleft, y0),
                    (xright, y0),
                    (xmid, ybot))
        else:
            ytop = int(y0+2*(value-0.5)*height)
            ybot = ytop + height/2
            poly = (
                    (x0, y0),
                    (x1, y0),
                    (x1, ytop),
                    (xmid, ybot),
                    (x0, ytop))
        return poly, self.ltrb

class BarnVeeWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by sweeping a V shape outward

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        width = (x1-x0)
        height = (y1-y0)
        xleft = int(x0 + 0.5*value*width)
        xright = int(x1 - 0.5*value*width)
        xmidleft = int(xmid - 0.5*value*width)
        xmidright = int(xmid + 0.5*value*width)
        ytop = int(y0 + value*height)
        ybot = int(y1 - value*height)
        poly = (
                (x0, y0),
                (xleft, y0),
                (xmid, ybot),
                (xright, y0),
                (x1, y0),
                (x1, ytop),
                (xmidright, y1),
                (xmidleft, y1),
                (x0, ytop))
        return poly, self.ltrb

class ZigZagWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by sweeping a zigzag divider line

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xwidth = (x1-x0)
        yzig = (y1-y0)/8
        xzig = xwidth/8
        xmin = x0 - (xwidth + xzig)
        xcur = xmin + int(value*(xwidth+xzig))
        poly = (
                (xcur, y0),
                (xcur+xwidth, y0),
                (xcur+xwidth+xzig, y0+1*yzig),
                (xcur+xwidth, y0+2*yzig),
                (xcur+xwidth+xzig, y0+3*yzig),
                (xcur+xwidth, y0+4*yzig),
                (xcur+xwidth+xzig, y1-3*yzig),
                (xcur+xwidth, y1-2*yzig),
                (xcur+xwidth+xzig, y1-1*yzig),
                (xcur+xwidth, y1),
                (xcur, y1))
        return poly, self.ltrb

class BarnZigZagWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by sweeping a zigzag divider lines from the center out

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xwidth = (x1-x0)
        xmid = (x0+x1)/2
        yzig = (y1-y0)/8
        xzig = xwidth/8
        displacement = int(value*(xwidth/2 + xzig))
        xleft = xmid - displacement
        xright = xmid + displacement
        poly = (
                (xleft, y0),
                (xleft+xzig, y0+1*yzig),
                (xleft, y0+2*yzig),
                (xleft+xzig, y0+3*yzig),
                (xleft, y0+4*yzig),
                (xleft+xzig, y1-3*yzig),
                (xleft, y1-2*yzig),
                (xleft+xzig, y1-1*yzig),
                (xleft, y1),
                (xright, y1),
                (xright+xzig, y1-1*yzig),
                (xright, y1-2*yzig),
                (xright+xzig, y1-3*yzig),
                (xright, y0+4*yzig),
                (xright+xzig, y0+3*yzig),
                (xright, y0+2*yzig),
                (xright+xzig, y0+1*yzig),
                (xright, y0))
        return poly, self.ltrb

class DiagonalWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by sweeping a diagonal divider line

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xwidth = (x1-x0)
        xmin = x0 - 2*xwidth
        xcur = xmin + int(value*2*xwidth)
        poly = (
                (xcur, y0),
                (xcur+2*xwidth, y0),
                (xcur+xwidth, y1),
                (xcur, y1))
        return poly, self.ltrb

class BowTieWipeTransition(TransitionClass, PolylistR2OverlapBlitterClass):
    # Reveal the new image by sweeping bowtie

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        ymid = (y0+y1)/2
        width = (x1-x0)
        height = (y1-y0)
        if value <= 0.5:
            xleft = xmid - int(value*width)
            xright = xmid + int(value*width)
            ytop = y0 + int(value*height)
            ybot = y1 - int(value*height)
            poly1 = ((xleft, y0), (xright, y0), (xmid, ytop))
            poly2 = ((xleft, y1), (xright, y1), (xmid, ybot))
            return (poly1, poly2), self.ltrb
        else:
            value = value - 0.5
            xleft = xmid - int(value*width)
            xright = xmid + int(value*width)
            ytop = y0 + int(value*height)
            ybot = y1 - int(value*height)
            poly = (
                    (x0, y0),
                    (x0, ytop),
                    (xleft, ymid),
                    (x0, ybot),
                    (x0, y1),
                    (x1, y1),
                    (x1, ybot),
                    (xright, ymid),
                    (x1, ytop),
                    (x1, y0))
            return (poly,), self.ltrb

class DoubleSweepWipeTransition(TransitionClass, PolylistR2OverlapBlitterClass):
    # Reveal the image by two rotating bars, mid-top and mid-bottom

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        width = (x1-x0)
        height = (y1-y0)
        if value <= 0.5:
            ydist = int(2*value*height)
            poly1 = (
                    (xmid, y0),
                    (x1, y0),
                    (x1, y0+ydist))
            poly2 = (
                    (xmid, y1),
                    (x0, y1),
                    (x0, y1-ydist))
        else:
            xdist = int((value-0.5)*width)
            poly1 = (
                    (xmid, y0),
                    (x1, y0),
                    (x1, y1),
                    (x1-xdist, y1))
            poly2 = (
                    (xmid, y1),
                    (x0, y1),
                    (x0, y0),
                    (x0+xdist, y0))
        return (poly1, poly2), self.ltrb

class SaloonDoorWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the image by two rotating bars, topleft and topright

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        width = (x1-x0)
        height = (y1-y0)
        if value <= 0.5:
            ydist = int(2*value*height)
            poly = (
                    (x0, y0),
                    (x1, y0),
                    (xmid, ydist))
        else:
            xdist = int((value-0.5)*width)
            poly = (
                    (x0, y0),
                    (x1, y0),
                    (xmid+xdist, y1),
                    (xmid-xdist, y1))
        return poly, self.ltrb


class WindShieldWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the image by two rotating bars from midhicenter and midlowcenter

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = (x0+x1)/2
        height = (y1-y0)
        ymidlo = int(y0+height/3.0)
        ymid = int(y0+height/2.0)
        ymidhi = int(y1-height/3.0)
        width = (x1-x0)
        if value <= 0.2:
            xdist = int(5*value*width/2)
            poly = (
                    (xmid, ymidlo),
                    (xmid+xdist, ymid),
                    (xmid, ymidhi))
        elif value <= 0.4:
            ydist = int(5*(value-0.2)*height/2)
            poly = (
                    (xmid, ymidlo),
                    (x1, ymid-ydist),
                    (x1, ymid+ydist),
                    (xmid, ymidhi))
        elif value <= 0.6:
            xdist = int(5*(value-0.4)*width)
            poly = (
                    (xmid, ymidlo),
                    (x1-xdist, y0),
                    (x1, y0),
                    (x1, y1),
                    (x1-xdist, y1),
                    (xmid, ymidhi))
        elif value <= 0.8:
            ydist = int(5*(value-0.6)*height/2)
            poly = (
                    (xmid, ymidlo),
                    (x0, y0+ydist),
                    (x0, y0),
                    (x1, y0),
                    (x1, y1),
                    (x0, y1),
                    (x0, y1-ydist),
                    (xmid, ymidhi))
        else:
            xdist = int(5*(value-0.8)*width/2)
            poly = (
                    (xmid, ymidlo),
                    (x0+xdist, ymid),
                    (x0, ymid),
                    (x0, y0),
                    (x1, y0),
                    (x1, y1),
                    (x0, y1),
                    (x0, ymid),
                    (x0+xdist, ymid))
        return poly, self.ltrb


## class TriangleWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
##     # Reveal the new image by a triangle growing from the center outward
##
##     def __init__(self, engine, dict):
##         TransitionClass.__init__(self, engine, dict)
##         self._recomputetop()
##
##     def move_resize(self, ltrb):
##         TransitionClass.move_resize(self, ltrb)
##         self._recomputetop()
##
##     def _recomputetop(self):
##         x0, y0, x1, y1 = self.ltrb
##         self.xmid = (x0+x1)/2
##         self.ymid = (y0+y1)/2
##         # XXXX This fails for narrow high windows, I think.
##         ytop = y1 + int(TAN_PI_DIV_3*(self.xmid-x0))
##         self.range = ytop-self.ymid
##
##     def computeparameters(self, value):
##         totop = int(value*self.range)
##         ytop = self.ymid - totop
##         ybot = self.ymid + totop/2
##         height = ybot - ytop
##         base_div_2 = height / TAN_PI_DIV_3
##         xleft = int(self.xmid - base_div_2)
##         xright = int(self.xmid + base_div_2)
##         points = (
##             (xleft, ybot),
##             (self.xmid, ytop),
##             (xright, ybot))
##         return points, self.ltrb

class _ShapeWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Helper baseclass for wipes with growing regular polygons

    def __init__(self, engine, dict):
        TransitionClass.__init__(self, engine, dict)
        self._recomputetop()

    def move_resize(self, ltrb):
        TransitionClass.move_resize(self, ltrb)
        self._recomputetop()

    def _recomputetop(self):
        x0, y0, x1, y1 = self.ltrb
        self.xmid = (x0+x1)/2
        self.ymid = (y0+y1)/2
        # We are done interior circle is as big as our diagonal...
        self.innerradius = math.sqrt((self.xmid-x0)*(self.xmid-x0)+(self.ymid-y0)*(self.ymid-y0))
        # ...but the cornerpoints lie on the exterior circle
        inner_to_outer = 1/math.cos(0.5*(self._NPOINTS-2)*math.pi/self._NPOINTS)
##         inner_to_outer = 1/math.cos(0.5*math.pi-0.5*(self._NPOINTS-2)*math.pi/self._NPOINTS)
        self.range = self.innerradius*inner_to_outer

    def computeparameters(self, value):
        radius = int(value*self.range)
        points = []
        for i in range(self._NPOINTS):
            angle = self._FIRSTANGLE + (2*math.pi*i)/self._NPOINTS
            x = math.cos(angle)*radius
            y = math.sin(angle)*radius
            points.append((self.xmid+x, self.ymid-y))
        return tuple(points), self.ltrb

class TriangleWipeTransition(_ShapeWipeTransition):
    _FIRSTANGLE=math.pi/2
    _NPOINTS=3

class PentagonWipeTransition(_ShapeWipeTransition):
    _FIRSTANGLE=math.pi/2
    _NPOINTS=5

class HexagonWipeTransition(_ShapeWipeTransition):
    _FIRSTANGLE=math.pi/2
    _NPOINTS=6

class EllipseWipeTransition(_ShapeWipeTransition):
    _FIRSTANGLE=0
    _NPOINTS=32

class StarWipeTransition(_ShapeWipeTransition):
    _FIRSTANGLE=math.pi/2
    _SUBTYPES = {
            'fourPoint': 4,
            'fivePoint': 5,
            'sixPoint': 6,
            }

    def __init__(self, engine, dict):
        self._NPOINTS = self._SUBTYPES.get(dict.get('subtype','fourPoint'), 4)
        _ShapeWipeTransition.__init__(self, engine, dict)

    def _recomputetop(self):
        _ShapeWipeTransition._recomputetop(self)
        self.range = self.range*1.5

    def computeparameters(self, value):
        radius = int(value*self.range)
        iradius = int(value*self.innerradius)
##         print value, radius, iradius
        points = []
        for i in range(self._NPOINTS):
            angle = self._FIRSTANGLE + (2*math.pi*i)/self._NPOINTS
            x = math.cos(angle)*radius
            y = math.sin(angle)*radius
            points.append((self.xmid+x, self.ymid-y))
            angle = self._FIRSTANGLE + (2*math.pi*(i+0.5))/self._NPOINTS
            x = math.cos(angle)*iradius
            y = math.sin(angle)*iradius
            points.append((self.xmid+x, self.ymid-y))
        return tuple(points), self.ltrb


class RoundRectWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    _NPOINTS=16

    def __init__(self, engine, dict):
        TransitionClass.__init__(self, engine, dict)
        self._recomputetop()

    def move_resize(self, ltrb):
        TransitionClass.move_resize(self, ltrb)
        self._recomputetop()

    def _recomputetop(self):
        x0, y0, x1, y1 = self.ltrb
        self.xmid = (x0+x1)/2
        self.ymid = (y0+y1)/2
        innerradius = math.sqrt((self.xmid-x0)*(self.xmid-x0)+(self.ymid-y0)*(self.ymid-y0))
        self.range = innerradius

    def computeparameters(self, value):
        radius = value*self.range
        r4 = radius*radius*radius*radius
        radius = int(radius)
        if not radius:
            return (), self.ltrb
        xmin = self.xmid - radius
        points = []
        for i in range(self._NPOINTS+1):
            x = xmin + i*radius*2/self._NPOINTS
            xp = float(x - self.xmid)
            xp4 = xp*xp*xp*xp
            y = self.ymid + int(math.sqrt(math.sqrt(r4-xp4)))
            points.append((x, y))
        for i in range(self._NPOINTS+1):
            x = xmin + (self._NPOINTS-i)*radius*2/self._NPOINTS
            xp = float(x - self.xmid)
            xp4 = xp*xp*xp*xp
            y = self.ymid - int(math.sqrt(math.sqrt(r4-xp4)))
            points.append((x, y))
        return tuple(points), self.ltrb

class EyeWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    _NPOINTS=16

    def __init__(self, engine, dict):
        TransitionClass.__init__(self, engine, dict)
        self._recomputetop()

    def move_resize(self, ltrb):
        TransitionClass.move_resize(self, ltrb)
        self._recomputetop()

    def _recomputetop(self):
        x0, y0, x1, y1 = self.ltrb
        self.xmid = (x0+x1)/2
        self.ymid = (y0+y1)/2
        innerradius = math.sqrt((self.xmid-x0)*(self.xmid-x0)+(self.ymid-y0)*(self.ymid-y0))
        self.range = innerradius*2

    def computeparameters(self, value):
        radius = value*self.range
        r2 = radius*radius
        radius = int(radius)
        if not radius:
            return (), self.ltrb
        xmin = self.xmid - radius
        points = []
        for i in range(self._NPOINTS+1):
            x = xmin + i*radius*2/self._NPOINTS
            xp = float(x - self.xmid)
            xp2 = xp*xp
            y = self.ymid + int(math.sqrt(r2-xp2)/2)
            points.append((x, y))
        for i in range(self._NPOINTS+1):
            x = xmin + (self._NPOINTS-i)*radius*2/self._NPOINTS
            xp = float(x - self.xmid)
            xp2 = xp*xp
            y = self.ymid - int(math.sqrt(r2-xp2)/2)
            points.append((x, y))
        return tuple(points), self.ltrb

class ArrowHeadWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
    # Reveal the new image by an arrowhead growing from the center outward

    def __init__(self, engine, dict):
        TransitionClass.__init__(self, engine, dict)
        self._recomputetop()

    def move_resize(self, ltrb):
        TransitionClass.move_resize(self, ltrb)
        self._recomputetop()

    def _recomputetop(self):
        x0, y0, x1, y1 = self.ltrb
        self.xmid = (x0+x1)/2
        self.ymid = (y0+y1)/2
        # XXXX This fails for narrow high windows, I think.
        ytop = y1 + int(TAN_PI_DIV_3*(self.xmid-x0))
        self.range = ytop-self.ymid

    def computeparameters(self, value):
        totop = int(value*self.range)
        ytop = self.ymid - totop
        ybot = self.ymid + totop/2
        ybotmid = self.ymid + totop/4
        height = ybot - ytop
        base_div_2 = height / TAN_PI_DIV_3
        xleft = int(self.xmid - base_div_2)
        xright = int(self.xmid + base_div_2)
        points = (
                (xleft, ybot),
                (self.xmid, ytop),
                (xright, ybot),
                (self.xmid, ybotmid))
        return points, self.ltrb

class IrisWipeTransition(TransitionClass, R1R2OverlapBlitterClass):
    # Reveal the new image by a square growing from the center outward

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        xmid = int((x0+x1+0.5)/2)
        ymid = int((y0+y1+0.5)/2)
        xc0 = int((x0+(1-value)*(xmid-x0))+0.5)
        yc0 = int((y0+(1-value)*(ymid-y0))+0.5)
        xc1 = int((xmid+value*(x1-xmid))+0.5)
        yc1 = int((ymid+value*(y1-ymid))+0.5)
        return ((xc0, yc0, xc1, yc1), (x0, y0, x1, y1))

class _RadialTransitionClass(TransitionClass, PolylistR2OverlapBlitterClass):
    # Generic subclass for radial transitions. Our angle system has 0 is up, 90 degrees is left.

    def __init__(self, engine, dict):
        TransitionClass.__init__(self, engine, dict)
        self._recomputeangles()

    def move_resize(self, ltrb):
        TransitionClass.move_resize(self, ltrb)
        self._recomputeangles()

    def _recomputeangles(self):
        x0, y0, x1, y1 = self.ltrb
        self.xmid = (x0+x1)/2.0
        self.ymid = (y0+y1)/2.0
        self.xradius = (x1-x0)/2.0
        self.yradius = (y1-y0)/2.0
        # Note: second arg to atan2 is reversed because 0,0 is topleft in our
        # coordinate system (as oposed to botleft in math coordinate system)
        self.angle_topleft = math.atan2(self.yradius, -self.xradius)
        self.angle_topright = math.atan2(self.yradius, self.xradius)
        self.angle_botleft = math.atan2(-self.yradius, -self.xradius)
        self.angle_botright = math.atan2(-self.yradius, self.xradius)
##         print 'DBG: topleft', self.angle_topleft * 180 / math.pi
##         print 'DBG: topright', self.angle_topright * 180 / math.pi
##         print 'DBG: botleft', self.angle_botleft * 180 / math.pi
##         print 'DBG: botright', self.angle_botright * 180 / math.pi
##         print 'xradius, yradius', self.xradius, self.yradius

    def _angle2edge(self, angle):
        # First normalize to range -pi..pi
        while angle < -math.pi:
            angle = angle + 2*math.pi
        while angle >= math.pi:
            angle = angle - 2*math.pi
        # Next find the edge on which our point lies
        if angle >= self.angle_topright and angle <= math.pi / 2:
            edge = 0
        elif angle <= self.angle_topright and angle >= self.angle_botright:
            edge = 1
        elif angle >= self.angle_botleft and angle <= self.angle_botright:
            edge = 2
        elif angle >= self.angle_topleft or angle <= self.angle_botleft:
            edge = 3
        elif angle >= math.pi / 2 and angle <= self.angle_topleft:
            edge = 4
        else:
            raise 'Impossible angle', angle
        x0, y0, x1, y1 = self.ltrb
        if edge == 0 or edge == 4:
            x = int(self.xmid + (1/math.tan(angle))*self.xradius + 0.5)
            y = y0
        elif edge == 1:
            x = x1
            y = int(self.ymid - math.tan(angle)*self.yradius + 0.5)
        elif edge == 2:
            x = int(self.xmid - (1/math.tan(angle))*self.xradius + 0.5)
            y = y1
        elif edge == 3:
            x = x0
            y = int(self.ymid + math.tan(angle)*self.yradius + 0.5)
        else:
            raise 'impossible edge', edge
##         print 'angle2edge', angle * 180 / math.pi, edge, (x, y)
        return edge, (x, y)

    def _angle2poly(self, angle, clockwise=1):
        x0, y0, x1, y1 = self.ltrb
        xm = self.xmid
        ym = self.ymid
        edge, point = self._angle2edge(angle)
        if clockwise:
            if edge == 0:
                return ( (xm, ym), (xm, y0), point)
            if edge == 1:
                return ( (xm, ym), (xm, y0), (x1, y0), point)
            elif edge == 2:
                return ( (xm, ym), (xm, y0), (x1, y0), (x1, y1), point)
            elif edge == 3:
                return ( (xm, ym), (xm, y0), (x1, y0), (x1, y1), (x0, y1), point)
            elif edge == 4:
                return ( (xm, ym), (xm, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0), point)
        else:
            if edge == 4:
                return ( (xm, ym), (xm, y0), point)
            if edge == 3:
                return ( (xm, ym), (xm, y0), (x0, y0), point)
            elif edge == 2:
                return ( (xm, ym), (xm, y0), (x0, y0), (x0, y1), point)
            elif edge == 1:
                return ( (xm, ym), (xm, y0), (x0, y0), (x0, y1), (x1, y1), point)
            elif edge == 0:
                return ( (xm, ym), (xm, y0), (x0, y0), (x0, y1), (x1, y1), (x1, y0), point)
        raise 'impossible edge/clockwise', (edge, clockwise)

class ClockWipeTransition(_RadialTransitionClass):
    # A clockwise radial reveal from the center

    def computeparameters(self, value):
        angle = math.pi/2 - (value*2*math.pi)
        poly = self._angle2poly(angle, clockwise=1)
        return (poly,), self.ltrb

class PinWheelWipeTransition(_RadialTransitionClass):
    # Two clockwise radials from the center, one from top one from bottom

    def computeparameters(self, value):
        angle = math.pi/2 - (value*math.pi)
        poly1 = self._angle2poly(angle, clockwise=1)
        poly2 = []
        for x, y in poly1:
            x = 2*self.xmid-x
            y = 2*self.ymid-y
            poly2.append((x, y))
        return (poly1,tuple(poly2)), self.ltrb

class FanWipeTransition(_RadialTransitionClass):
    # Two radials from the top, one CW one CCW

    def computeparameters(self, value):
        angle1 = math.pi/2 - (value*math.pi)
        poly1 = self._angle2poly(angle1, clockwise=1)
        angle2 = math.pi/2 + (value*math.pi)
        poly2 = self._angle2poly(angle2, clockwise=0)
        return (poly1,poly2), self.ltrb

class DoubleFanWipeTransition(_RadialTransitionClass):
    # Two radials from the top, one CW one CCW

    def computeparameters(self, value):
        angle1 = math.pi/2 - (value*math.pi/2)
        poly1 = self._angle2poly(angle1, clockwise=1)
        angle2 = math.pi/2 + (value*math.pi/2)
        poly2 = self._angle2poly(angle2, clockwise=0)
        poly3 = []
        for x, y in poly1:
            y = 2*self.ymid-y
            poly3.append((x, y))
        poly4 = []
        for x, y in poly2:
            y = 2*self.ymid-y
            poly4.append((x, y))
        return (poly1, poly2, tuple(poly3), tuple(poly4)), self.ltrb

class _MatrixTransitionClass(TransitionClass, RlistR2OverlapBlitterClass):
    # Generic subclass for all the matrix transitions

    def __init__(self, engine, dict):
        TransitionClass.__init__(self, engine, dict)
## XXXX It seems this is _not_ the intention of horzRepeat and vertRepeat
##         hr = dict.get('horzRepeat', 0)+1
##         vr = dict.get('vertRepeat', 0)+1
        hr = 8
        vr = 8
        self.hsteps = hr
        self.vsteps = vr
        self._recomputeboundaries()

    def _recomputeboundaries(self):
        x0, y0, x1, y1 = self.ltrb
        self.hboundaries = []
        self.vboundaries = []
        hr = self.hsteps
        vr = self.vsteps
        for i in range(hr+1):
            self.hboundaries.append(x0 + int((x1-x0)*float(i)/hr + 0.5))
        for i in range(vr+1):
            self.vboundaries.append(y0 + int((y1-y0)*float(i)/vr + 0.5))

    def move_resize(self, ltrb):
        TransitionClass.move_resize(self, ltrb)
        self._recomputeboundaries()

class SingleSweepWipeTransition(_MatrixTransitionClass):
    # Reveal the new images by sweeping over the matrix left-to-right, top-to-botton

    def computeparameters(self, value):
        index = int(value*self.hsteps*self.vsteps)
        hindex = index % self.hsteps
        vindex = index / self.hsteps
        x0, y0, x1, y1 = self.ltrb
        rectlist = []
        for i in range(vindex):
            rect = (x0, self.vboundaries[i], x1, self.vboundaries[i+1])
            rectlist.append(rect)
        if hindex:
            ylasttop = self.vboundaries[vindex]
            ylastbottom = self.vboundaries[vindex+1]
            for i in range(hindex):
                rect = (self.hboundaries[i], ylasttop, self.hboundaries[i+1], ylastbottom)
                rectlist.append(rect)
        return rectlist, self.ltrb

class SnakeWipeTransition(_MatrixTransitionClass):
    # Reveal the new image by sweeping left-to-right, then on the next line right-to-left, etc

    def computeparameters(self, value):
        index = int(value*self.hsteps*self.vsteps)
        hindex = index % self.hsteps
        vindex = index / self.hsteps
        x0, y0, x1, y1 = self.ltrb
        rectlist = []
        for i in range(vindex):
            rect = (x0, self.vboundaries[i], x1, self.vboundaries[i+1])
            rectlist.append(rect)
        if hindex:
            ylasttop = self.vboundaries[vindex]
            ylastbottom = self.vboundaries[vindex+1]
            for i in range(hindex):
                if vindex % 2:
                    idx = self.hsteps-i-1
                else:
                    idx = i
                rect = (self.hboundaries[idx], ylasttop, self.hboundaries[idx+1], ylastbottom)
                rectlist.append(rect)
        return rectlist, self.ltrb

class ParallelSnakesWipeTransition(_MatrixTransitionClass):
    # Reveal the new image by sweeping left-to-right, then on the next line right-to-left, etc
    # And the same from bottom up

    def computeparameters(self, value):
        index = int(0.5*value*self.hsteps*self.vsteps+0.5)
        hindex = index % self.hsteps
        vindex = index / self.hsteps
        x0, y0, x1, y1 = self.ltrb
        rectlist = []
        for i in range(vindex):
            rect = (x0, self.vboundaries[i], x1, self.vboundaries[i+1])
            rectlist.append(rect)
            rect = (x0, self.vboundaries[self.vsteps-i-1], x1, self.vboundaries[self.vsteps-i])
            rectlist.append(rect)
        if hindex:
            ylasttop = self.vboundaries[vindex]
            ylastbottom = self.vboundaries[vindex+1]
            ydowntop = self.vboundaries[self.vsteps-vindex-1]
            ydownbottom = self.vboundaries[self.vsteps-vindex]
            for i in range(hindex):
                if vindex % 2:
                    idx = self.hsteps-i-1
                else:
                    idx = i
                rect = (self.hboundaries[idx], ylasttop, self.hboundaries[idx+1], ylastbottom)
                rectlist.append(rect)
                rect = (self.hboundaries[idx], ydowntop, self.hboundaries[idx+1], ydownbottom)
                rectlist.append(rect)
        return rectlist, self.ltrb

class SpiralWipeTransition(_MatrixTransitionClass):
    # Reveal the new image by spiralling over the matrix

    def _recomputeboundaries(self):
        _MatrixTransitionClass._recomputeboundaries(self)
        self._xy_to_step = []
        xmax = self.hsteps-1
        ymax = self.vsteps-1
        ymax = 7
        xinc = 1
        yinc = 1
        x = 0
        y = 0
        skipfirstxmaxdecrement = 1
        while xmax >= 0 or ymax >= 0:
            for i in range(xmax):
                self._xy_to_step.append((x, y))
                x = x + xinc
            xinc = -xinc
            if skipfirstxmaxdecrement:
                skipfirstxmaxdecrement = 0
            else:
                xmax = xmax - 1
            for i in range(ymax):
                self._xy_to_step.append((x, y))
                y = y + yinc
            yinc = -yinc
            ymax = ymax - 1
        x = x - 1
        self._xy_to_step.append((x, y))
        self._xy_to_step.append((x, y))

    def computeparameters(self, value):
        index = int(value*self.hsteps*self.vsteps+0.5)
        rectlist = []
        for i in range(index):
            x, y = self._xy_to_step[i]
            rect = (self.hboundaries[x], self.vboundaries[y],
                            self.hboundaries[x+1], self.vboundaries[y+1])
            rectlist.append(rect)
        return rectlist, self.ltrb

class BoxSnakesWipeTransition(_MatrixTransitionClass):
    # Reveal the new image by spiralling over the matrix twice, top and bottom symmetric

    def _recomputeboundaries(self):
        _MatrixTransitionClass._recomputeboundaries(self)
        self._xy_to_step = []
        xmax = self.hsteps-1
        ymax = self.vsteps/2-1
        xinc = 1
        yinc = 1
        x = 0
        y = 0
        skipfirstxmaxdecrement = 1
        while xmax >= 0 or ymax >= 0:
            for i in range(xmax):
                self._xy_to_step.append((x, y))
                self._xy_to_step.append((x, self.vsteps-y-1))
                x = x + xinc
            xinc = -xinc
            if skipfirstxmaxdecrement:
                skipfirstxmaxdecrement = 0
            else:
                xmax = xmax - 1
            for i in range(ymax):
                self._xy_to_step.append((x, y))
                self._xy_to_step.append((x, self.vsteps-y-1))
                y = y + yinc
            yinc = -yinc
            ymax = ymax - 1
        x = x - 1
        self._xy_to_step.append((x, y))
        self._xy_to_step.append((x, self.vsteps-y-1))
        self._xy_to_step.append((x, y))
        self._xy_to_step.append((x, self.vsteps-y-1))

    def computeparameters(self, value):
        index = int(value*self.hsteps*self.vsteps+0.5)
        rectlist = []
        for i in range(index):
            x, y = self._xy_to_step[i]
            rect = (self.hboundaries[x], self.vboundaries[y],
                            self.hboundaries[x+1], self.vboundaries[y+1])
            rectlist.append(rect)
        return rectlist, self.ltrb

class WaterfallWipeTransition(_MatrixTransitionClass):
    # Reveal the new image by a waterfall-like pattern over the matrix

    def computeparameters(self, value):
        totalsteps = self.hsteps + 2*(self.vsteps-1)
        curstep = int(value*totalsteps+0.5)
        rectlist = []
        startstep = 0
        for x in range(self.hsteps):
            thismaxy = min(self.vsteps, curstep-startstep)
            for y in range(thismaxy):
                rect = (self.hboundaries[x], self.vboundaries[y],
                        self.hboundaries[x+1], self.vboundaries[y+1])
                rectlist.append(rect)
            startstep = startstep + 2
        return rectlist, self.ltrb

class PushWipeTransition(TransitionClass, R1R2R3R4BlitterClass):
    # Push in the new image, pushing out the old one

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        # Assume left-to-right
        xpixels = int(value*(x1-x0)+0.5)
        return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1),
                        (x0, y0, x1-xpixels, y1), (x0+xpixels, y0, x1, y1) )

class SlideWipeTransition(TransitionClass, R1R2R3R4BlitterClass):
    # Slide the new image over the old one

    def computeparameters(self, value):
        x0, y0, x1, y1 = self.ltrb
        # Assume left-to-right
        xpixels = int(value*(x1-x0)+0.5)
        return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1),
                        (x0+xpixels, y0, x1, y1), (x0+xpixels, y0, x1, y1))

class FadeTransition(TransitionClass, FadeBlitterClass):
    # Fade the old image to the new one

    def computeparameters(self, value):
        return value

TRANSITIONDICT = {
        ("barWipe", "leftToRight") : BarWipeTransition,
        ("barWipe", "topToBottom") : BarWipeTransition,
        ("barWipe", None) : BarWipeTransition,
        ("boxWipe", "topLeft") : BoxWipeTransition,
        ("boxWipe", None) : BoxWipeTransition,
        ("fourBoxWipe", "cornersIn") : FourBoxWipeTransition,
        ("fourBoxWipe", None) : FourBoxWipeTransition,
        ("barnDoorWipe", "vertical") : BarnDoorWipeTransition,
        ("barnDoorWipe", None) : BarnDoorWipeTransition,
        ("diagonalWipe", "topLeft") : DiagonalWipeTransition,
        ("diagonalWipe", None) : DiagonalWipeTransition,
        ("bowTieWipe", "vertical") : BowTieWipeTransition,
        ("bowTieWipe", None) : BowTieWipeTransition,
        ("miscDiagonalWipe", "doubleBarnDoor") : MiscDiagonalWipeTransition,
        ("miscDiagonalWipe", None) : MiscDiagonalWipeTransition,
        ("veeWipe", "down") : VeeWipeTransition,
        ("veeWipe", None) : VeeWipeTransition,
        ("barnVeeWipe", "down") : BarnVeeWipeTransition,
        ("barnVeeWipe", None) : BarnVeeWipeTransition,
        ("zigZagWipe", "leftToRight") : ZigZagWipeTransition,
        ("zigZagWipe", None) : ZigZagWipeTransition,
        ("barnZigZagWipe", "vertical") : BarnZigZagWipeTransition,
        ("barnZigZagWipe", None) : BarnZigZagWipeTransition,
        ("irisWipe", "rectangle") : IrisWipeTransition,
        ("irisWipe", None) : IrisWipeTransition,
        ("triangleWipe", "up") : TriangleWipeTransition,
        ("triangleWipe", None) : TriangleWipeTransition,
        ("arrowHeadWipe", "up") : ArrowHeadWipeTransition,
        ("arrowHeadWipe", None) : ArrowHeadWipeTransition,
        ("pentagonWipe", "up") : PentagonWipeTransition,
        ("pentagonWipe", None) : PentagonWipeTransition,
        ("hexagonWipe", "up") : HexagonWipeTransition,
        ("hexagonWipe", None) : HexagonWipeTransition,
        ("ellipseWipe", "circle") : EllipseWipeTransition,
        ("ellipseWipe", None) : EllipseWipeTransition,
        ("eyeWipe", "horizontal") : EyeWipeTransition,
        ("eyeWipe", None) : EyeWipeTransition,
        ("roundRectWipe", "horizontal") : RoundRectWipeTransition,
        ("roundRectWipe", None) : RoundRectWipeTransition,
        ("starWipe", "fourPoint") : StarWipeTransition,
        ("starWipe", "fivePoint") : StarWipeTransition,
        ("starWipe", "sixPoint") : StarWipeTransition,
        ("starWipe", None) : StarWipeTransition,
##     ("miscShapeWipe", "heart") : MiscShapeWipe,
##     ("miscShapeWipe", None) : MiscShapeWipe,
        ("clockWipe", "clockwiseTwelve") : ClockWipeTransition,
        ("clockWipe", None) : ClockWipeTransition,
        ("pinWheelWipe", "twoBladeVertical") : PinWheelWipeTransition,
        ("pinWheelWipe", None) : PinWheelWipeTransition,
        ("singleSweepWipe", "clockwiseTop") : SingleSweepWipeTransition,
        ("singleSweepWipe", None) : SingleSweepWipeTransition,
        ("fanWipe", "centerTop") : FanWipeTransition,
        ("fanWipe", None) : FanWipeTransition,
        ("doubleFanWipe", "fanOutVertical") : DoubleFanWipeTransition,
        ("doubleFanWipe", None) : DoubleFanWipeTransition,
        ("doubleSweepWipe", "parallelVertical") : DoubleSweepWipeTransition,
        ("doubleSweepWipe", None) : DoubleSweepWipeTransition,
        ("saloonDoorWipe", "top") : SaloonDoorWipeTransition,
        ("saloonDoorWipe", None) : SaloonDoorWipeTransition,
        ("windshieldWipe", "right") : WindShieldWipeTransition,
        ("windshieldWipe", None) : WindShieldWipeTransition,
        ("snakeWipe", "topLeftHorizontal") : SnakeWipeTransition,
        ("snakeWipe", None) : SnakeWipeTransition,
        ("spiralWipe", "topLeftClockwise") : SpiralWipeTransition,
        ("spiralWipe", None) : SpiralWipeTransition,
        ("parallelSnakesWipe", "verticalTopSame") : ParallelSnakesWipeTransition,
        ("parallelSnakesWipe", None) : ParallelSnakesWipeTransition,
        ("boxSnakesWipe", "twoBoxTop") : BoxSnakesWipeTransition,
        ("boxSnakesWipe", None) : BoxSnakesWipeTransition,
        ("waterfallWipe", "verticalLeft") : WaterfallWipeTransition,
        ("waterfallWipe", None) : WaterfallWipeTransition,
        ("pushWipe", "fromLeft") : PushWipeTransition,
        ("pushWipe", None) : PushWipeTransition,
        ("slideWipe", "fromLeft") : SlideWipeTransition,
        ("slideWipe", None) : SlideWipeTransition,
        ("fade", "crossfade") : FadeTransition,
        ("fade", None) : FadeTransition,
        ("audioVisualFade", "crossfade") : FadeTransition,
        ("audioVisualFade", None) : FadeTransition,
}

def TransitionFactory(trtype, subtype):
    # Return the class that implements this transition.
    if TRANSITIONDICT.has_key((trtype, subtype)):
        return TRANSITIONDICT[(trtype, subtype)]
    if TRANSITIONDICT.has_key((trtype, None)):
        return TRANSITIONDICT[(trtype, None)]
    return NullTransition

def IsImplemented(dict):
    trtype = dict['trtype']
    subtype = dict.get('subtype')
    return TRANSITIONDICT.has_key((trtype, subtype))
