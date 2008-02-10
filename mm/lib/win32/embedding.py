__version__ = "$Id$"

import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import GenWnd
import usercmd, usercmdui
from WMEVENTS import *
import urlcache

import string

from licparser import *

WM_USER_OPEN = win32con.WM_USER+1
WM_USER_CLOSE = win32con.WM_USER+2
WM_USER_PLAY = win32con.WM_USER+3
WM_USER_STOP = win32con.WM_USER+4
WM_USER_PAUSE = win32con.WM_USER+5
WM_USER_GETSTATUS = win32con.WM_USER+6
WM_USER_SETHWND = win32con.WM_USER+7
WM_USER_UPDATE = win32con.WM_USER+8
WM_USER_MOUSE_CLICKED  = win32con.WM_USER+9
WM_USER_MOUSE_MOVED  = win32con.WM_USER+10
WM_USER_SETPOS = win32con.WM_USER+11
WM_USER_SETSPEED = win32con.WM_USER+12
WM_USER_SELWND = win32con.WM_USER+13

STOPPED, PAUSING, PLAYING = range(3)
UNKNOWN = -1

class ListenerWnd(GenWnd.GenWnd):
    def __init__(self, toplevel):
        GenWnd.GenWnd.__init__(self)
        self._toplevel = toplevel
        self.create()
        self._docmap = {}
        self._slidermap = {}
        self._focuswnd = None
        self._haslicense = 0
        from __main__ import commodule
        commodule.SetPyListener(self)

        self.HookMessage(self.OnOpen, WM_USER_OPEN)
        self.HookMessage(self.OnClose, WM_USER_CLOSE)
        self.HookMessage(self.OnPlay, WM_USER_PLAY)
        self.HookMessage(self.OnStop, WM_USER_STOP)
        self.HookMessage(self.OnPause, WM_USER_PAUSE)
        self.HookMessage(self.OnSetWindow, WM_USER_SETHWND)
        self.HookMessage(self.OnUpdate, WM_USER_UPDATE)
        self.HookMessage(self.OnMouseClicked, WM_USER_MOUSE_CLICKED)
        self.HookMessage(self.OnMouseMoved, WM_USER_MOUSE_MOVED)
        self.HookMessage(self.OnSetPos, WM_USER_SETPOS)
        self.HookMessage(self.OnSetSpeed, WM_USER_SETSPEED)
        self.HookMessage(self.OnSelWnd, WM_USER_SELWND)

    def OnDestroy(self, params):
        pass

    def GetPermission(self, licensestr):
        import features
        if hasattr(features, 'license_features_needed') and features.license_features_needed:
            user = ''
            organization = 'WGBH Educational Foundation'
            license_features_needed = list(features.license_features_needed)
            if 'embeddedplayer' not in license_features_needed:
                license_features_needed.append('embeddedplayer')
            self.license = License(license_features_needed, licensestr, user, organization)
            if not self.license.msg:
                self._haslicense = 1
        else:
            self._haslicense = 1
        return self._haslicense

    def OnOpen(self, params):
        if not self._haslicense:
            return
        # lParam (params[3]) is a pointer to a c-string
        filename = Sdk.GetWMString(params[3])
        event = 'OnOpen'
        self._toplevel._peerdocid = params[2]
        try:
            func, arg = self._toplevel.get_embedded(event)
            func(arg, self, event, filename)
            frame = self._toplevel.get_most_recent_docframe()
            if frame is not None:
                self._docmap[params[2]] = frame
        except:
            pass
        self._toplevel._peerdocid = 0
        frame = self._docmap.get(params[2])
        if frame:
            cmifdoc = frame._cmifdoc
            if cmifdoc:
                self._slidermap[params[2]] = SliderPeer(cmifdoc, params[2])

    def OnClose(self, params):
        id = params[2]
        frame = self._docmap.get(id)
        if frame:
            frame.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.CLOSE].id)
        del self._docmap[id]
        del self._slidermap[id]

    def OnPlay(self, params):
        frame = self._docmap.get(params[2])
        if frame:
            id = usercmdui.usercmd2id(usercmd.PLAY)
            frame.OnUserCmd(id, 0)

    def OnStop(self, params):
        frame = self._docmap.get(params[2])
        if frame:
            id = usercmdui.usercmd2id(usercmd.STOP)
            frame.OnUserCmd(id, 0)

    def OnPause(self, params):
        frame = self._docmap.get(params[2])
        if frame:
            id = usercmdui.usercmd2id(usercmd.PAUSE)
            frame.OnUserCmd(id, 0)

    def OnSetWindow(self, params):
        frame = self._docmap.get(params[2])
        data = Sdk.GetWMString(params[3])
        data = string.split(data, ' ')
        if len(data)!=2: return
        wndid = string.atoi(data[0])
        hwnd = string.atoi(data[1])
        if frame: frame.setEmbeddedHwnd(wndid, hwnd)

    def OnUpdate(self, params):
        frame = self._docmap.get(params[2])
        if frame:
            for wnd in frame._peerviewports.values():
                wnd.update()

    def OnSelWnd(self, params):
        frame = self._docmap.get(params[2])
        wndid = params[3]
        if frame:
            self._focuswnd = frame.getEmbeddedWnd(wndid)

    def OnMouseClicked(self, params):
        frame = self._docmap.get(params[2])
        if frame and self._focuswnd:
            x, y = win32api.LOWORD(params[3]),win32api.HIWORD(params[3])
            self._focuswnd.onMouseEvent((x,y),Mouse0Press)
            self._focuswnd.onMouseEvent((x,y),Mouse0Release)

    def OnMouseMoved(self, params):
        frame = self._docmap.get(params[2])
        if frame and self._focuswnd:
            x, y = win32api.LOWORD(params[3]),win32api.HIWORD(params[3])
            self._focuswnd.onMouseMoveEvent((x,y))

    def OnSetPos(self, params):
        pos = 0.001*params[3]
        slider = self._slidermap.get(params[2])
        if slider:
            slider.setPos(pos)

    def OnSetSpeed(self, params):
        frame = self._docmap.get(params[2])
        if frame:
            speed = 0.001*params[3]
            slider = self._slidermap.get(params[2])
            if slider:
                slider.setSpeed(speed)

    def GetPos(self, id):
        slider = self._slidermap.get(id)
        if slider:
            return int(1000*slider.getPos())
        return 0

    def GetMediaFrameRate(self, id, rurl):
        slider = self._slidermap.get(id)
        if slider:
            return slider.GetMediaFrameRate(rurl)
        return 20

    def GetState(self, id):
        slider = self._slidermap.get(id)
        if slider:
            return slider.getState()
        return 0

############################
import FrameRate

class SliderPeer:
    def __init__(self, smildoc, peerid):
        self.__smildoc = smildoc
        self.__peerid = peerid
        player = smildoc.player
        root = player.userplayroot
        ctx = root.GetContext()
        self.ctx = ctx

        # indefinite: -1, unresolved: 0, else: >0
        #fulldur = root.calcfullduration(None)

        t0, t1, t2, downloadlag, begindelay = root.GetTimes('virtual')
        fulldur = t1-t0

        # find doc media
        self.media = []
        self.findMedia(root, self.media)
        framerate = self.findFrameRate()

        # update peer for dur and first video/audio frameRate
        try:
            from __main__ import commodule
            if peerid:
                commodule.AdviceSetDur(peerid, fulldur)
                commodule.AdviceSetFrameRate(peerid, framerate)
        except: pass
        self.updateposcallback = player.setstarttime
        self.timefunction = player.scheduler.timefunc
        self.canusetimefunction = player.isplaying
        self.getstatefunction = player.getstate
        self.__updatepeer = 1

    def GetMediaFrameRate(self, rurl):
        url = self.ctx.findurl(rurl)
        mtype = urlcache.mimetype(url)
        if mtype:
            mt = mtype.split('/')
            return FrameRate.GetFrameRate(url, mt[0], mt[1])
        return -1

    # set player pos
    def setPos(self, pos):
        self.__updatepeer = 0
        self.updateposcallback(pos)
        self.__updatepeer = 1

    def getPos(self):
        if self.canusetimefunction and\
                self.canusetimefunction() and self.timefunction:
            return self.timefunction()
        return 0

    def getState(self):
        return self.getstatefunction()

    # set player speed
    def setSpeed(self, speed):
        self.__updatepeer = 0
        pass # setspeed
        self.__updatepeer = 1

    def findMedia(self, node, media):
        import MMTypes
        nt = node.GetType()
        if nt == 'ext':
            url = node.GetRawAttr('file')
            if url:
                media.append(url)
        if nt in MMTypes.interiortypes:
            for child in node.GetChildren():
                self.findMedia(child, media)

    def findFrameRate(self):
        for rurl in self.media:
            url = self.ctx.findurl(rurl)
            mtype = urlcache.mimetype(url)
            if mtype:
                mt = mtype.split('/')
                if mt[0] == 'video':
                    cache = urlcache.urlcache[url]
                    rate = cache.get('framerate')
                    if rate is not None:
                        rate = FrameRate.GetFrameRate(url, mt[0], mt[1])
                        cache['framerate'] = rate
                    return rate
        for rurl in self.media:
            url = self.ctx.findurl(rurl)
            mtype = urlcache.mimetype(url)
            if mtype:
                mt = mtype.split('/')
                if mt[0] == 'audio':
                    cache = urlcache.urlcache[url]
                    rate = cache.get('framerate')
                    if rate is not None:
                        rate = FrameRate.GetFrameRate(url, mt[0], mt[1])
                        cache['framerate'] = rate
                    return rate
        return 20

############################
import win32window
import ddraw
from pywinlib.mfc import window
from appcon import *
import win32mu
import grinsRC

class EmbeddedWnd(win32window.DDWndLayer):
    def __init__(self, wnd, w, h, units, bgcolor, title='', peerdocid=0):
        self._cmdframe = wnd
        self._peerwnd = wnd
        self._smildoc = wnd.getgrinsdoc()
        self._rect = 0, 0, w, h
        self._title = title
        self._peerdocid = peerdocid
        try:
            from __main__ import commodule
            if peerdocid:
                commodule.AdviceNewPeerWnd(peerdocid, id(self), w, h, title)
        except: pass
        self._viewport = win32window.Viewport(self, 0, 0, w, h, bgcolor)
        win32window.DDWndLayer.__init__(self, self, bgcolor)
        self.createBackDDLayer(w, h, wnd.GetSafeHwnd())
        self.settitle(title)

    def setPeerDocID(self, peerdocid):
        self._peerdocid = peerdocid
        x, y, w, h = self._rect
        try:
            from __main__ import commodule
            if peerdocid:
                commodule.AdviceNewPeerWnd(peerdocid, id(self), w, h, self._title)
        except: pass

    def setPeerWindow(self, hwnd):
        if Sdk.IsWindow(hwnd):
            self.createPrimaryDDLayer(hwnd)
            self._peerwnd = window.Wnd(win32ui.CreateWindowFromHandle(hwnd))
            self.settitle(self._title)
            self.update()

    def settitle(self,title):
        if not title: return
        import MMurl
        title=MMurl.unquote(title)
        self._title=title

    def getgrinsdoc(self):
        return self._smildoc

    #
    # paint
    #
    def update(self, rc=None, exclwnd=None):
        if not self._ddraw or not self._frontBuffer or not self._backBuffer:
            return
        if self._frontBuffer.IsLost():
            if not self._frontBuffer.Restore():
                # we can't do anything for this
                # system is busy with video memory
                #self.InvalidateRect(self.GetClientRect())
                return
        if self._backBuffer.IsLost():
            if not self._backBuffer.Restore():
                # and for this either
                # system should be out of memory
                #self.InvalidateRect(self.GetClientRect())
                return

        # do we have anything to update?
        if rc and (rc[2]==0 or rc[3]==0):
            return

        self.paint(rc, exclwnd)

        if rc is None:
            x, y, w, h = self._viewport._rect
            rcBack = x, y, x+w, y+h
        else:
            rc = self.rectAnd(rc, self._viewport._rect)
            rcBack = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]

        rcFront = self.getContextOsWnd().ClientToScreen(rcBack)
        try:
            self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
        except ddraw.error, arg:
            print 'EmbeddedWnd.update', arg

    def paint(self, rc=None, exclwnd=None):
        if rc is None:
            x, y, w, h = self._viewport._rect
            rcPaint = x, y, x+w, y+h
        else:
            rc = self.rectAnd(rc, self._viewport._rect)
            rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]

        try:
            self._backBuffer.BltFill(rcPaint, self._ddbgcolor)
        except ddraw.error, arg:
            print 'EmbeddedWnd.paint',arg
            return

        if self._viewport:
            self._viewport.paint(rc, exclwnd)


    def getRGBBitCount(self):
        return self._pxlfmt[0]

    def getPixelFormat(self):
        returnself._pxlfmt

    def getDirectDraw(self):
        return self._ddraw

    def getContextOsWnd(self):
        return self._peerwnd

    def pop(self, poptop=1):
        pass

    def getwindowpos(self):
        return self._viewport._rect

    def closeViewport(self, viewport):
        try:
            from __main__ import commodule
            if self._peerdocid:
                commodule.AdviceClosePeerWnd(self._peerdocid, id(self))
        except: pass
        self._viewport = None
        del viewport
        self.destroyDDLayer()

    def getDrawBuffer(self):
        return self._backBuffer

    def updateMouseCursor(self):
        pass

    def imgAddDocRef(self, file):
        self._cmdframe.imgAddDocRef(file)

    def CreateSurface(self, w, h):
        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w,h)
        dds = self._ddraw.CreateSurface(ddsd)
        dds.BltFill((0, 0, w, h), self._ddbgcolor)
        return dds

    def ltrb(self, xywh):
        x,y,w,h = xywh
        return x, y, x+w, y+h

    def xywh(self, ltrb):
        l,t,r,b = ltrb
        return l, t, r-l, b-t

    def rectAnd(self, rc1, rc2):
        # until we make calcs
        import win32ui
        rc, ans= win32ui.GetWin32Sdk().IntersectRect(self.ltrb(rc1),self.ltrb(rc2))
        if ans:
            return self.xywh(rc)
        return 0, 0, 0, 0

    #
    # Mouse input
    #
    def onMouseEvent(self, point, ev, params=None):
        return  self._viewport.onMouseEvent(point, ev)

    def onMouseMoveEvent(self, point):
        return  self._viewport.onMouseMove(0, point)

    def setcursor(self, strid):
        try:
            from __main__ import commodule
            if self._peerdocid:
                commodule.AdviceSetCursor(self._peerdocid, strid)
        except:
            pass

    #
    # OS windows
    #
    def setClientRect(self, w, h):
        l1, t1, r1, b1 = self.GetWindowRect()
        l2, t2, r2, b2 = self.GetClientRect()
        dxe = dye = 0
        #if (self._exstyle & WS_EX_CLIENTEDGE):
        #       dxe = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
        #       dye = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
        wi = (r1-l1) - (r2-l2)
        wp = w + wi + dxe
        hi = (b1-t1) - (b2-t2)
        hp = h + hi + dye
        flags=win32con.SWP_NOMOVE | win32con.SWP_NOZORDER
        self.SetWindowPos(0, (0,0,wp,hp), flags)

    def createOsWnd(self, rect, color, title='Viewport'):
        brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(color),0)
        cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
        icon=Afx.GetApp().LoadIcon(grinsRC.IDR_GRINSED)
        clstyle=win32con.CS_DBLCLKS
        style=win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
        exstyle = 0
        strclass=Afx.RegisterWndClass(clstyle,cursor,brush,icon)
        self.CreateWindowEx(exstyle,strclass,title,style,
                self.ltrb(rect), None, 0)
        self.ShowWindow(win32con.SW_SHOW)

class showmessage:
    def __init__(self, text, mtype = 'message', grab = 1, callback = None,
                 cancelCallback = None, name = 'message',
                 title = 'Ambulant', parent = None, identity = None):
        self._res = win32con.IDOK
        if callback and self._res==win32con.IDOK:
            apply(apply,callback)
        elif cancelCallback and self._res==win32con.IDCANCEL:
            apply(apply,cancelCallback)

# Shows a question to the user and returns the response
def showquestion(text, parent = None):
    return 0

class ProgressDialog:
    def __init__(self, *args):
        pass
    def set(self, *args):
        pass

# Displays a message and requests from the user to select Yes or No or Cancel
def GetYesNoCancel(prompt,parent=None,title='Ambulant'):
    return 1

# Displays a message and requests from the user to select OK or Cancel
def GetOKCancel(prompt,parent=None,title='Ambulant'):
    return 0

# Displays a message and requests from the user to select Yes or Cancel
def GetYesNo(prompt,parent=None,title='Ambulant'):
    return 0
