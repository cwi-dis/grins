__version__ = "$Id$"

import winkernel

import MainWnd

from appcon import *

class _Toplevel:
    def __init__(self):
        # timer handling
        self._timers = []
        self._timer_id = 0
        self._idles = {}
        self.__idleid = 0
        self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND

        self._frame = None

    def close(self):
        if self._frame:
            self._frame.close()
            self._frame = None

    def newdocument(self, cmifdoc, adornments=None, commandlist=None):
        if self._frame is None:
            self._frame = MainWnd.MainWnd()
            self._frame.create()
            self._frame.set_commandlist(commandlist, 'document')
        return self._frame

    def createmainwnd(self, title = None, adornments = None, commandlist = None):
        if self._frame is None:
            self._frame = MainWnd.MainWnd()
            self._frame.create()
            self._frame.set_commandlist(commandlist, 'app')
        return self._frame

    def getactivedocframe(self):
        return self._frame

    def getmainwnd(self):
        if self._frame is None:
            self._frame = MainWnd.MainWnd()
            self._frame.create()
        return self._frame

    def serve_events(self,params=None):
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

    def _image_size(self, filename, grinsdoc):
        from win32ig import win32ig
        img = win32ig.load(filename)
        return win32ig.size(img)[:2]

    def _image_handle(self, filename, grinsdoc):
        from win32ig import win32ig
        return win32ig.load(filename)

    #
    def register_embedded(self, event, func, arg):
        if event == 'OnOpen':
            self.__onOpenEvent = func, arg

    def unregister_embedded(event):
        self.__onOpenEvent = None


# url parsing
import MMurl, urlparse

import winuser

def shell_execute(url,verb='open', showmsg=1):
    utype, host, path, params, query, fragment = urlparse.urlparse(url)
    islocal = (not utype or utype == 'file') and (not host or host == 'localhost')
    if islocal:
        filename=MMurl.url2pathname(path)
        if not os.path.isabs(filename):
            filename=os.path.join(os.getcwd(),filename)
            filename=os.path.normpath(filename)
        if not os.path.exists(filename):
            if os.path.exists(filename+'.lnk'):
                filename = filename + '.lnk'
            else:
                rv = win32con.IDCANCEL
                if verb == 'edit':
                    rv = winuser.MessageBox(filename+': not found.\nCreate?',
                             '', win32con.MB_OKCANCEL)
                if rv == win32con.IDCANCEL:
                    return -1
                try:
                    open(filename, 'w').close()
                except:
                    pass
        url=filename
    rc,msg = winuser.ShellExecute(0, verb, url, None, "", win32con.SW_SHOW)
    if rc<=32:
        if showmsg:
            winuser.MessageBox('Explorer cannot '+ verb +' '+url+':\n'+msg,'GRiNS')
        return rc
    return 0

class htmlwindow:
    def __init__(self,url):
        self.goto_url(url)
    def goto_url(self,url):
        shell_execute(url,'open')
    def close(self):pass
    def is_closed(self):return 1
