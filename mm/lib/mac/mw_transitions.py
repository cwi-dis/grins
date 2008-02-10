__version__ = "$Id$"

import time
from Carbon import Qd
from Carbon import QuickDraw
import mw_globals
import Transitions

class TransitionEngine:
    def __init__(self, window, inout, runit, dict, cb):
        dur = dict.get('dur', 1)
        self.exclude_first_window = 0
        # if this is a coordinated transition with clipBoundary==children we should not
        # include the parent in the clip.
        if dict.get('coordinated') and dict.get('clipBoundary', 'children') == 'children':
            self.exclude_first_window = 1
        self.windows = [window]
        self.outtransition = inout
        self.starttime = time.time()    # Correct?
        self.duration = dur
        self.running = runit
        self.value = 0
        trtype = dict.get('trtype', 'fade')
        subtype = dict.get('subtype')
        self.__callback = cb
        klass = Transitions.TransitionFactory(trtype, subtype)
        self.transitiontype = klass(self, dict)
        self.dstrgn = None
        self.verbatimrgn = None
        self.move_resize()
        self.currentparameters = None

##         self.reverse = (dict['direction'] == 'reverse')
        self.reverse = 0
        if not self.reverse:
            self.startprogress = dict.get('startProgress', 0)
            self.endprogress = dict.get('endProgress', 1)
        else:
            self.startprogress = 1.0 - dict.get('endProgress', 1)
            self.endprogress = 1.0 - dict.get('startProgress', 0)
        # Now recompute starttime and "duration" based on these values
        if self.endprogress != self.startprogress:
            self.duration = self.duration / (self.endprogress-self.startprogress)
        self.starttime = self.starttime - (self.startprogress*self.duration)


        self.__idleid = mw_globals.toplevel.setidleproc(self._idleproc)

    def join(self, window, ismaster, cb):
        """Join this (sub or super) window to an existing transition"""
        if ismaster:
            self.windows.insert(0, window)
            self.__callback = cb
        else:
            self.windows.append(window)
        self.move_resize()

    def endtransition(self):
        """Called by upper layer (window) to tear down the transition"""
        if self.windows != None:
            # Show final result (saves us a redraw in window code)
            self.value = 1.0
            self._doredraw(0)
            # Tear down our datastructures
            mw_globals.toplevel.cancelidleproc(self.__idleid)
            self.windows = None
            self.transitiontype = None
            if self.__callback:
                apply(apply, self.__callback)
                self.__callback = None

    def need_tmp_wid(self):
        return self.transitiontype.needtmpbitmap()

    def move_resize(self):
        """Internal: recompute the region and rect on which this transition operates"""
        if self.dstrgn:
            Qd.DisposeRgn(self.dstrgn)
        if self.verbatimrgn:
            Qd.DisposeRgn(self.verbatimrgn)
        exclude_first_window = self.exclude_first_window
        x0, y0, x1, y1 = self.windows[0].qdrect()
        self.dstrgn = Qd.NewRgn()
        for w in self.windows:
            rect = w.qdrect()
            newrgn = w._mac_getclip()
            if exclude_first_window:
                exclude_first_window = 0
                self.verbatimrgn = Qd.NewRgn()
                Qd.CopyRgn(newrgn, self.verbatimrgn)
            else:
                Qd.UnionRgn(self.dstrgn, newrgn, self.dstrgn)
            nx0, ny0, nx1, ny1 = rect
            if nx0 < x0:
                x0 = nx0
            if ny0 < y0:
                y0 = ny0
            if nx1 > x1:
                x1 = nx1
            if ny1 > y1:
                y1 = ny1
        # We still subtract our children (there may be transparent windows in there)
        if self.verbatimrgn:
            Qd.DiffRgn(self.verbatimrgn, self.dstrgn, self.verbatimrgn)
        self.ltrb = (x0, y0, x1, y1)
        self.transitiontype.move_resize(self.ltrb)

    def ismaster(self, window):
        return window == self.windows[0]

    def isouttransition(self):
        return self.outtransition

    def _idleproc(self):
        """Called in the event loop to optionally do a recompute"""
        self.changed(0)

    def changed(self, mustredraw=1):
        """Called by upper layer when it wants the destination bitmap recalculated. If
        mustredraw is true we should do the recalc even if the transition hasn't advanced."""
        if self.running:
            self.value = float(time.time() - self.starttime) / self.duration
            if self.value >= self.endprogress:
                self._cleanup()
                return
        self._doredraw(mustredraw)

    def settransitionvalue(self, value):
        """Called by uppoer layer when it has a new percentage value"""
        self.value = value
        self._doredraw()

    def _cleanup(self):
        """Internal function called when our time is up. Ask the upper layer (window)
        to tear us down"""
        wcopy = self.windows[:]
        for w in wcopy:
            w.endtransition()

    def _doredraw(self, mustredraw):
        """Internal: do the actual computation, iff anything has changed since last time"""
        oldparameters = self.currentparameters
        self.currentparameters = self.transitiontype.computeparameters(self.value)
        if self.currentparameters == oldparameters and not mustredraw:
            return
        # All windows in the transition share their bitmaps, so we can pick any of them
        w = self.windows[0]
        dst = w._mac_getoswindowpixmap(mw_globals.BM_ONSCREEN)
        src_active = w._mac_getoswindowpixmap(mw_globals.BM_DRAWING)
        src_passive = w._mac_getoswindowpixmap(mw_globals.BM_PASSIVE)
        tmp = w._mac_getoswindowpixmap(mw_globals.BM_TEMP)
        if self.outtransition:
            src_old = src_active
            src_new = src_passive
        else:
            src_old = src_passive
            src_new = src_active
        w._mac_setwin(mw_globals.BM_ONSCREEN)
        Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
        Qd.RGBForeColor((0, 0, 0))
        self.transitiontype.updatebitmap(self.currentparameters, src_new, src_old, tmp, dst,
                self.dstrgn)
        if self.verbatimrgn:
            Qd.CopyBits(src_active, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, self.verbatimrgn)
