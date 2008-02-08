__version__ = "$Id$"

import Transitions

# timer support
import windowinterface
import time

# for ddraw.error
import ddraw

# for Sleep
import winkernel

class TransitionEngine:
    def __init__(self, window, outtrans, runit, dict, cb):
        self.windows = [window,]
        self.outtrans = outtrans

        self.__duration = dict.get('dur', 1)
        self.__multiElement = dict.get('coordinated')
        self.__childrenClip = dict.get('clipBoundary', 'children') == 'children'

        self.__callback = cb

        trtype = dict.get('trtype', 'fade')
        subtype = dict.get('subtype')
        klass = Transitions.TransitionFactory(trtype, subtype)
        self.__transitiontype = klass(self, dict)

        self.__fiber_id = None
        self.__running = 0

        self.__startprogress = dict.get('startProgress', 0)
        self.__endprogress = dict.get('endProgress', 1)
        if self.__endprogress <= self.__startprogress:
            self.__transperiod = 0
            #raise AssertionError
        elif self.__duration <= 0:
            self.__transperiod = 0
            self.__startprogress = self.__endprogress
        else:
            self.__transperiod = float(self.__endprogress - self.__startprogress) / self.__duration

    def __del__(self):
        if self.__transitiontype:
            self.endtransition()
        del self._tosurf
        del self._tmp

    def begintransition(self):
        self.__createSurfaces()
        self.__running = 1
        self.__start = time.time()
        self.settransitionvalue(self.__startprogress)
        if self.__duration<=0.0:
            self.settransitionvalue(self.__endprogress)
        else:
            self.__register_for_timeslices()

    def endtransition(self):
        if not self.__transitiontype: return
        self.__unregister_for_timeslices()
        if self.__callback:
            apply(apply, self.__callback)
            self.__callback = None
        self.__transitiontype = None
        self.__running = 0
        wnd = self.windows[0]
        if wnd.is_closed():
            return
        else:
            # XXX: patch
            if self.outtrans and wnd._active_displist:
                wnd._active_displist.close()
        for win in self.windows:
            win._transition = None
            win._drawsurf = None
        wnd.update(wnd.getwindowpos())

    def settransitionvalue(self, value):
        if value<0.0 or value>1.0:
            raise AssertionError
        parameters = self.__transitiontype.computeparameters(value)

        # transition window
        # or parent window in multiElement transitions
        wnd = self.windows[0]
        if wnd.is_closed():
            return

        # assert that we paint the active surface the correct way
        # for each of the following cases:
        # 1. multiElement==true, childrenClip==true
        # 2. multiElement==true, childrenClip==false
        # 3. multiElement==false
        if self.__multiElement:
            if self.__childrenClip:
                # since children clipping will be done in wnd's paint method
                # do a normal painting on active surface
                wnd.paintOnDDS(self._tosurf, wnd)
            else:
                # do a normal painting on active surface
                wnd.paintOnDDS(self._tosurf, wnd)
        else:
            if self.outtrans:
                wnd._paintOnDDS(wnd._fromsurf, wnd._rect)
                wnd.updateBackDDS(self._tosurf, exclwnd=wnd)
            else:
                wnd.updateBackDDS(wnd._fromsurf, exclwnd=wnd)
                wnd._paintOnDDS(self._tosurf, wnd._rect)

        fromsurf =      wnd._fromsurf
        tosurf = self._tosurf
        tmpsurf  = self._tmp
        dstsurf  = wnd._drawsurf
        dstrgn = None

        self.__transitiontype.updatebitmap(parameters, tosurf, fromsurf, tmpsurf, dstsurf, dstrgn)
        wnd.update(wnd.getwindowpos())

    def join(self, window, ismaster, cb):
        # Join this (sub or super) window to an existing transition
        if ismaster:
            self.__callback = cb
            if self.isrunning():
                self.windows.insert(0, window)
                self.__createSurfaces()
            else:
                self.windows.insert(0, window)
        else:
            self.windows.append(window)

        x, y, w, h = self.windows[0]._rect
        self.__transitiontype.move_resize((0, 0, w, h))

    def _ismaster(self, wnd):
        return self.windows[0]==wnd

    def _isrunning(self):
        return self.__running

    def __createSurfaces(self):
        # transition window
        # or parent window in multiElement transitions
        wnd = self.windows[0]
        while 1:
            try:
                wnd._fromsurf = wnd.getBackDDS(exclwnd = wnd, dopaint = 1)
                # use getBackDDS instead of createDDS
                # just in case of an early repaint
                wnd._drawsurf = wnd.getBackDDS(exclwnd = wnd, dopaint = 0)
                self._tosurf = wnd.getBackDDS(exclwnd = wnd, dopaint = 0)
                self._tmp = wnd.getBackDDS(exclwnd = wnd, dopaint = 0)
            except ddraw.error, arg:
                print arg
                winkernel.Sleep(50)
            else:
                break

        # resize to this window
        x, y, w, h = wnd._rect
        self.__transitiontype.move_resize((0, 0, w, h))

    def __onIdle(self):
        if self.windows[0].is_closed():
            self.endtransition()
            return
        t_sec = time.time() - self.__start
        if t_sec>=self.__duration:
            try:
                self.settransitionvalue(self.__endprogress)
                self.endtransition()
            except ddraw.error, arg:
                print arg
        else:
            try:
                self.settransitionvalue(self.__startprogress + self.__transperiod * t_sec)
            except ddraw.error, arg:
                print arg


    def __register_for_timeslices(self):
        if not self.__fiber_id:
            self.__fiber_id = windowinterface.setidleproc(self.__onIdle)

    def __unregister_for_timeslices(self):
        if self.__fiber_id is not None:
            windowinterface.cancelidleproc(self.__fiber_id)
            self.__fiber_id = None


class InlineTransitionEngine:
    def __init__(self, window, outtrans, runit, dict, cb):
        self.window = window
        self.outtrans = outtrans
        self.dict = dict
        self.cb = cb

        trtype = dict.get('trtype')
        subtype = dict.get('subtype')
        klass = Transitions.TransitionFactory(trtype, subtype)
        self.__transitiontype = klass(self, self.dict)

        self.__running = 0
        self._lastvalue = None

    def __del__(self):
        if self.__transitiontype:
            self.endtransition()

    def begintransition(self):
        self.__createSurfaces()
        self.__running = 1
        self._lastvalue = None

    def endtransition(self):
        if not self.__transitiontype: return
        self.__transitiontype = None
        self.__running = 0
        wnd = self.window
        if wnd.is_closed():
            return
        wnd._transition = None
        wnd._drawsurf = None
        wnd.update(wnd.getwindowpos())

    def settransitionvalue(self, value):
        if value<0.0 or value>1.0:
            raise AssertionError, 'settransitionvalue out of range %d', value

        # transition window
        wnd = self.window
        if wnd.is_closed():
            return

        if self._lastvalue == value:
            wnd.update(wnd.getwindowpos())
            return
        self._lastvalue = value

        # hack until i find the bug
        if value == 1.0:
            if self.outtrans:
                wnd.updateBackDDS(wnd._drawsurf, exclwnd=wnd)
            else:
                wnd._paintOnDDS(wnd._drawsurf, wnd._rect)
            wnd.update(wnd.getwindowpos())
            return
        elif value==0.0:
            if self.outtrans:
                wnd._paintOnDDS(wnd._drawsurf, wnd._rect)
            else:
                wnd.updateBackDDS(wnd._drawsurf, exclwnd=wnd)
            wnd.update(wnd.getwindowpos())
            return

        # normal processing
        parameters = self.__transitiontype.computeparameters(value)
        if self.outtrans:
            wnd._paintOnDDS(wnd._fromsurf, wnd._rect)
            wnd.updateBackDDS(self._tosurf, exclwnd=wnd)
        else:
            wnd.updateBackDDS(wnd._fromsurf, exclwnd=wnd)
            wnd._paintOnDDS(self._tosurf, wnd._rect)

        fromsurf =      wnd._fromsurf
        tosurf = self._tosurf
        tmpsurf  = self._tmp
        dstsurf  = wnd._drawsurf
        dstrgn = None

        self.__transitiontype.updatebitmap(parameters, tosurf, fromsurf, tmpsurf, dstsurf, dstrgn)
        wnd.update(wnd.getwindowpos())


    def _ismaster(self, wnd):
        return self.window==wnd

    def _isrunning(self):
        return self.__running

    def __createSurfaces(self):
        # transition window
        # or parent window in multiElement transitions
        wnd = self.window
        while 1:
            try:
                # use getBackDDS instead of createDDS
                # just in case of an early repaint
                wnd._fromsurf = wnd.getBackDDS(dopaint = 1)
                wnd._drawsurf = wnd.getBackDDS(dopaint = 0)
                self._tosurf = wnd.getBackDDS(dopaint = 0)
                self._tmp = wnd.getBackDDS(dopaint = 0)
            except ddraw.error, arg:
                print arg
                winkernel.Sleep(50)
            else:
                break

        # resize to this window
        x, y, w, h = wnd._rect
        self.__transitiontype.move_resize((0, 0, w, h))
