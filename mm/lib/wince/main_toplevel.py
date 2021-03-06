__version__ = "$Id$"

import winkernel, winuser

from appcon import *

import main_window

from wince_preload import preload_list
preload_list_msg = 0

class Toplevel:
    def __init__(self):

        # timer handling
        self._timers = []
        self._timer_id = 0
        self._idles = {}
        self.__idleid = 0
        self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND

        # application's main window
        self._mainwnd = None

        #
        self._waiting = 0
        self._wait_cursor = winuser.LoadStandardCursor(wincon.IDC_WAIT)

    def close(self):
        pass

    def newdocument(self, cmifdoc, adornments = None, commandlist = None):
        if self._mainwnd is None:
            self._mainwnd = main_window.MainWnd(self)
            self._mainwnd.create()
        self._mainwnd.set_commandlist(commandlist, 'document')
        return self._mainwnd

    def createmainwnd(self, title = None, adornments = None, commandlist = None):
        if self._mainwnd is None:
            self._mainwnd = main_window.MainWnd(self)
            self._mainwnd.create()
        self._mainwnd.set_commandlist(commandlist, 'app')
        return self._mainwnd

    def getactivedocframe(self):
        return self._mainwnd

    def getmainwnd(self):
        if self._mainwnd is None:
            self._mainwnd = main_window.MainWnd(self)
            self._mainwnd.create()
        return self._mainwnd

    def serve_events(self,params=None):
        global preload_list, preload_list_msg
        if preload_list:
##             self._mainwnd.setStatusMsg('Loading module %s' % preload_list[0])
            try:
                __import__(preload_list[0])
            except:
                pass
            del preload_list[0]
        elif preload_list_msg == 0:
##             self._mainwnd.setStatusMsg('')
            self._mainwnd.setReady()
            preload_list_msg = 1

        self.setready()
        while self._timers:
            t = float(winkernel.GetTickCount())/TICKS_PER_SECOND
            sec, cb, tid = self._timers[0]
            sec = sec - (t - self._time)
            self._time = t
            if sec <= 0.002:
                del self._timers[0]
                apply(apply, cb)
            else:
                self._timers[0] = sec, cb, tid
                break
        self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND
        self.serve_timeslices()

    # Register a timer even
    def settimer(self, sec, cb):
        self._timer_id = self._timer_id + 1
        t0 = float(winkernel.GetTickCount())/TICKS_PER_SECOND
        if self._timers:
            t, a, i = self._timers[0]
            t = t - (t0 - self._time) # can become negative
            self._timers[0] = t, a, i
        self._time = t0
        t = 0
        for i in range(len(self._timers)):
            time0, dummy, tid = self._timers[i]
            if t + time0 > sec:
                self._timers[i] = (time0 - sec + t, dummy, tid)
                self._timers.insert(i, (sec - t, cb, self._timer_id))
                return self._timer_id
            t = t + time0
        self._timers.append((sec - t, cb, self._timer_id))
        return self._timer_id

    # Unregister a timer even
    def canceltimer(self, id):
        if id == None: return
        for i in range(len(self._timers)):
            t, cb, tid = self._timers[i]
            if tid == id:
                del self._timers[i]
                if i < len(self._timers):
                    tt, cb, tid = self._timers[i]
                    self._timers[i] = (tt + t, cb, tid)
                return
        raise 'unknown timer', id

    # Register for receiving timeslices
    def setidleproc(self, cb):
        self.__idleid = self.__idleid + 1
        self._idles[self.__idleid] = cb
        return self.__idleid

    # Register for receiving timeslices
    def cancelidleproc(self, id):
        del self._idles[id]

    # Dispatch timeslices
    def serve_timeslices(self):
        for onIdle in self._idles.values():
            onIdle()

    def setwaiting(self):
        if not self._waiting:
            if not self._mainwnd or not self._mainwnd._in_gapi_mode:
                winuser.SetCursor(self._wait_cursor)
                self._waiting = 1

    def setready(self):
        if self._waiting:
            winuser.SetCursor(0)
            self._waiting = 0
    #
    def register_embedded(self, event, func, arg):
        pass

    def unregister_embedded(event):
        pass
