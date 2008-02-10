__version__ = "$Id$"

# BitBlitter base classes for machine-independent transition classes.
# See comment at the beginning of Transitions for an explanation of the overall
# architecture.

class BlitterClass:
    SHOW_UNIMPLEMENTED_TRANSITION_NAME=1

    def __init__(self, engine, dict):
        pass

    def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
        """Called by the engine when the parameters have changed and the
        destination bitmap has to be recomputed. Also called for other redraw reasons."""
        pass

    def needtmpbitmap(self):
        """Return true if this blitter needs the temporary bitmap."""
        return 0

    def _convertrect(self, ltrb):
        """Convert an lrtb-style rectangle to the local convention"""
        return ltrb

class R1R2BlitterClass(BlitterClass):
    """parameter is 2 rects, first copy rect2 from src2, then rect1 from src1"""
    pass

class R1R2R3R4BlitterClass(BlitterClass):
    """Parameter is 4 rects. Copy src1[rect1] to rect2, src2[rect3] to rect4"""
    pass

class R1R2OverlapBlitterClass(BlitterClass):
    """Like R1R2BlitterClass but rects may overlap, so copy via the temp bitmap"""
    pass

class RlistR2OverlapBlitterClass(BlitterClass):
    """Like R1R2OverlapBlitterClass, but first item is a list of rects"""
    pass

class PolyR2OverlapBlitterClass(BlitterClass):
    """Like R1R2OverlapBlitterClass, but first item is a polygon (list of points)"""
    pass

class PolylistR2OverlapBlitterClass(BlitterClass):
    """Like PolyR2OverlapBlitterClass, but first item is a list of polygons"""
    pass

class FadeBlitterClass(BlitterClass):
    """Parameter is float in range 0..1, use this as blend value"""
    pass
