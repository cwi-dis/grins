__version__ = "$Id$"

# BitBlitter base classes for machine-independent transition classes.
# See comment at the beginning of Transitions for an explanation of the overall
# architecture.
from Carbon import Qd
from Carbon import QuickDraw

class BlitterClass:
    SHOW_UNIMPLEMENTED_TRANSITION_NAME=1

    def __init__(self, engine, dict):
        pass

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        """Called by the engine when the parameters have changed and the
        destination bitmap has to be recomputed. Also called for other redraw reasons."""
        Qd.CopyBits(src1, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
        if self.SHOW_UNIMPLEMENTED_TRANSITION_NAME:
            x0, y0, x1, y1 = self.ltrb
            Qd.MoveTo(x0, y0)
            Qd.LineTo(x1, y1)
            Qd.MoveTo(x0, y1)
            Qd.LineTo(x1, y0)
            Qd.MoveTo(x0, (y0+y1)/2)
            Qd.DrawString("%s %s"%(self.dict.get('trtype', '???'), self.dict.get('subtype', '')))

    def needtmpbitmap(self):
        """Return true if this blitter needs the temporary bitmap."""
        return 0

    def _convertrect(self, ltrb):
        """Convert an lrtb-style rectangle to the local convention"""
        return ltrb

class R1R2BlitterClass(BlitterClass):
    """parameter is 2 rects, first copy rect2 from src2, then rect1 from src1"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        rect1, rect2 = parameters
        rect1 = self._convertrect(rect1)
        rect2 = self._convertrect(rect2)
        Qd.CopyBits(src2, dst, rect2, rect2, QuickDraw.srcCopy, dstrgn)
        Qd.CopyBits(src1, dst, rect1, rect1, QuickDraw.srcCopy, dstrgn)

class R1R2R3R4BlitterClass(BlitterClass):
    """Parameter is 4 rects. Copy src1[rect1] to rect2, src2[rect3] to rect4"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        srcrect1, dstrect1, srcrect2, dstrect2 = parameters
        Qd.CopyBits(src2, dst, srcrect2, dstrect2, QuickDraw.srcCopy, dstrgn)
        Qd.CopyBits(src1, dst, srcrect1, dstrect1, QuickDraw.srcCopy, dstrgn)

class R1R2OverlapBlitterClass(BlitterClass):
    """Like R1R2BlitterClass but rects may overlap, so copy via the temp bitmap"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        rect1, rect2 = parameters
        Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, dstrgn)
        Qd.CopyBits(src1, tmp, rect1, rect1, QuickDraw.srcCopy, dstrgn)
        Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)

    def needtmpbitmap(self):
        return 1

class RlistR2OverlapBlitterClass(BlitterClass):
    """Like R1R2OverlapBlitterClass, but first item is a list of rects"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        rectlist, rect2 = parameters
        Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, None)
        x0, y0, x1, y1 = self.ltrb
        rgn = Qd.NewRgn()
        for rect in rectlist:
            rgn2 = Qd.NewRgn()
            Qd.RectRgn(rgn2, rect)
            Qd.UnionRgn(rgn, rgn2, rgn)
            Qd.DisposeRgn(rgn2)
        Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, rgn)
        Qd.DisposeRgn(rgn)
        Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)

    def needtmpbitmap(self):
        return 1

def _mkpoly(pointlist):
    poly = Qd.OpenPoly()
    apply(Qd.MoveTo, pointlist[-1])
    for x, y in pointlist:
        Qd.LineTo(x, y)
    Qd.ClosePoly(poly)
    return poly

def _mkpolyrgn(pointlist):
    rgn = Qd.NewRgn()
    Qd.OpenRgn()
    apply(Qd.MoveTo, pointlist[-1])
    for x, y in pointlist:
        Qd.LineTo(x, y)
    Qd.CloseRgn(rgn)
    return rgn

class PolyR2OverlapBlitterClass(BlitterClass):
    """Like R1R2OverlapBlitterClass, but first item is a polygon (list of points)"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        pointlist, rect2 = parameters
        Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, None)
        if pointlist:
            rgn = _mkpolyrgn(pointlist)
            Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, rgn)
            Qd.DisposeRgn(rgn)
        Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)

    def needtmpbitmap(self):
        return 1

class PolylistR2OverlapBlitterClass(BlitterClass):
    """Like PolyR2OverlapBlitterClass, but first item is a list of polygons"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        pointlist, rect2 = parameters
        Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, None)
        if pointlist:
            rgn = _mkpolyrgn(pointlist[0])
            for pl in pointlist[1:]:
                newrgn = _mkpolyrgn(pl)
                Qd.UnionRgn(rgn, newrgn, rgn)
                Qd.DisposeRgn(newrgn)
            Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, rgn)
            Qd.DisposeRgn(rgn)
        Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)

    def needtmpbitmap(self):
        return 1

class FadeBlitterClass(BlitterClass):
    """Parameter is float in range 0..1, use this as blend value"""

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        value = parameters
        rgb = int(value*0xffff), int(value*0xffff), int(value*0xffff)
        Qd.OpColor(rgb)
        Qd.CopyBits(src2, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
        Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.blend, dstrgn)
        Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)

    def needtmpbitmap(self):
        return 1
