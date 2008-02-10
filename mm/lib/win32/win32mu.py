__version__ = "$Id$"

# @win32doc|win32mu
# This module contain simple class utilities
# and function utilities that simplify
# the process of working with win32 structures
# The classes defined here are:
#       Point: (x,y)
#       Size: (cx,cy)
#       Rect : (left,top,right,bottom)
#       SizeRect: (x,y,width,height)
#       Win32Msg: cracks win32 messages into meaningful parts
#       CreateStruct: simplifies win32 CREATESTRUCT manipulation

import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()

####################################################
# General Class Utilities and Functions


class Point:
    def __init__(self,p=(0,0)):
        self.x=p[0];self.y=p[1]
    def tuple(self):
        return self.x,self.y
    def iseq(self,other):
        return self.x==other.x and self.y==other.y
    def subtr(pt1,pt2):
        return Point(((pt1.x-pt2.x),(pt1.y-pt2.y)))

class Size:
    def __init__(self,s=(0,0)):
        self.cx=s[0];self.cy=s[1]
    def tuple():
        return self.cx,self.cy

class Rect:
    def __init__(self,r=(0,0,0,0)):
        self.left=r[0];self.top=r[1]
        self.right=r[2];self.bottom=r[3]
    def ltrb_tuple(self):
        return self.left,self.top,self.right,self.bottom
    def xywh_tuple(self):
        return self.left,self.top,self.right-self.left,self.bottom-self.top
    def round(self):
        if self.left<1:self.left=0
        if self.top<1:self.top=0
        self.left=int(self.left+0.5);self.top=int(self.top+0.5)
        self.right=int(self.right+0.5);self.bottom=int(self.bottom+0.5)

    def pos(self):
        return (self.left,self.top)
    def rb_pos(self):
        return (self.right,self.bottom)
    def size(self):
        return (self.right-self.left,self.bottom-self.top)
    def width(self):
        return self.right-self.left
    def height(self):
        return self.bottom-self.top
    def setRect(self,l,t,r,b):
        self.left=l;self.top=t;
        self.right=r;self.bottom=b
    def setToRect(self,other):
        self.left=other.left;self.top=other.top
        self.right=other.right;self.bottom=other.bottom

    def normalizeRect(self):
        if self.right<self.left:
            self.right, self.left = self.left, self.right
        if self.bottom<self.top:
            self.top, self.bottom = self.bottom, self.top
        if self.right==self.left:
            self.right=self.right+1
        if self.bottom==self.top:
            self.bottom=self.bottom+1

    def isRectEmpty(self):
        if self.right==self.left or self.bottom==self.top:
            return 1
        return 0
    def intersect(rc1,rc2):
        rc,ans= Sdk.IntersectRect(rc1.ltrb_tuple(),rc2.ltrb_tuple())
        return ans
    def moveByPt(self,pt):
        self.left=self.left+pt.x
        self.right=self.right+pt.x
        self.top=self.top+pt.y
        self.bottom=self.bottom+pt.y
    def iseq(self,other):
        if (self.left==other.left and self.right==other.right and
                self.top==other.top and self.bottom==other.bottom):
            return 1
        return 0
    def inflateRect(self,cx,cy):
        self.left=self.left-cx
        self.right=self.right+cx
        self.top=self.top-cy
        self.bottom=self.bottom+cy

    def isPtInRect(self,point):
        if (point.x >= self.left and point.x < self.right and
                point.y >= self.top and point.y < self.bottom):
            return 1
        return 0

    def getvertices(self):
        return Point((self.left,self.top)),Point((self.right,self.top)),\
                Point((self.left,self.bottom)),Point((self.right,self.bottom))

    def isPtInRectEq(self,point):
        if (point.x >= self.left and point.x <= self.right and
                point.y >= self.top and point.y <= self.bottom):
            return 1
        return 0

    def isRectIn(self,rc):
        v=rc.getvertices()
        for p in v:
            if not self.isPtInRectEq(p):
                return 0
        return 1

    # borrow cmifwnd's _prepare_image but very much simplified
    def adjustSize(self, size):
        xsize, ysize = size
        x,y,r,b=self.left,self.top,self.right,self.bottom
        width, height=r-x,b-y

        scale = min(float(width)/xsize, float(height)/ysize)

        w=xsize
        h=ysize
        if scale != 1:
            w = int(xsize * scale + .5)
            h = int(ysize * scale + .5)

        x, y = x + (width - w) / 2, y + (height - h) / 2
        return 0, 0, x, y, w, h, (0,0,xsize,ysize)


class SizeRect:
    def __init__(self,r=(0,0,0,0)):
        self.x=r[0];self.y=r[1];
        self.width=r[2];self.height=r[3]
        return self.x,self.y,self.width,self.height

class Win32Msg:
    def __init__(self,params):
        self._hwnd,self._message,self._wParam,self._lParam,self._time,self._pt=params
    def LOWORD_wParam(self):
        return win32api.LOWORD(self._wParam)
    def HIWORD_wParam(self):
        return win32api.HIWORD(self._wParam)
    def LOWORD_lParam(self):
        return win32api.LOWORD(self._lParam)
    def HIWORD_lParam(self):
        return win32api.HIWORD(self._lParam)

    def loword(self):
        return win32api.LOWORD(self._lParam)
    def hiword(self):
        return win32api.HIWORD(self._lParam)

    def width(self):
        return win32api.LOWORD(self._lParam)
    def height(self):
        return win32api.HIWORD(self._lParam)

    def hpos(self):
        return win32api.LOWORD(self._lParam)
    def vpos(self):
        return win32api.HIWORD(self._lParam)
    def pos(self):
        return (win32api.LOWORD(self._lParam),win32api.HIWORD(self._lParam))

    def sizeType(self):
        return self._wParam
    def keyFlags(self):
        return self._wParam

    def minimized(self):
        if (self._wParam & win32con.SIZE_MINIMIZED):
            return 1
        return 0
    def maximized(self):
        if (self._wParam & win32con.SIZE_MAXIMIZED):
            return 1
        return 0

    def cmdid(self): return self.LOWORD_wParam()

    def getcontrolid(self): return self.LOWORD_wParam()
    def getnmsg(self): return self.HIWORD_wParam()
    def gethandle(self): return self._lParam

    def nmhdr(self): return Sdk.CrackNMHDR(self._lParam)

    def __repr__(self):
        s='message=%d wparam=%d lparam=%d' % (self._message,self._wParam,self._lParam)
        return '<%s instance, %s>' % (self.__class__.__name__, s)

class Win32NotifyMsg:
    def __init__(self, std, extra, ctrltype=None):
        self.hwndFrom, self.idFrom, self.code = std
        if ctrltype == 'tree':
            self.action, self.itemOld, self.itemNew, self.pt = extra
        elif ctrltype == 'list':
            self.row, self.col, self.state = extra[:3]

class CreateStruct:
    def __init__(self,csd):
        self.CreateParams=csd[0]
        self.hInstance=csd[1]
        self.hMenu=csd[2]
        self.hwndParent=csd[3]
        self.cy,self.cx,self.y,self.x=csd[4]
        self.style=csd[5]
        self.NameId=csd[6]
        self.ClassId=csd[7]
        self.ExStyle=csd[8]
    def to_csd(self):
        return (self.CreateParams,self.hInstance,
                self.hMenu,self.hwndParent,
                (self.cy,self.cx,self.y,self.x),
                self.style,self.NameId,self.ClassId,self.ExStyle)
    def pos(self):
        return self.x,self.y
    def size(self):
        return self.cx,self.cy

def PtInRect(rc,pt):
    rc=Rect(rc);pt=Point(pt)
    if rc.left<=pt.x and pt.x<rc.right and rc.top<=pt.y and pt.y<rc.bottom:
        return 1
    return 0


def roundi(x):
    if x < 0:
        return roundi(x + 1024) - 1024
    return int(x + 0.5)

def UInt16ToInt(x):
    if x & 0x8000:
        return x | 0xffff0000
    else:
        return x

class Pen:
    def __init__(self,style=win32con.PS_INSIDEFRAME,size=Size((1,1)),color=(0,0,0)):
        self._style=style
        self._size=size
        self._color=color

class Brush:
    def __init__(self,style=win32con.BS_SOLID,color=(192, 192, 192),hash=win32con.HS_HORIZONTAL):
        self._style=style
        self._hash=hash
        self._color=color

def RGB(l):
    return win32api.RGB(l[0],l[1],l[2])

def DrawLine(dc,l,rgb=(0,0,0),width=1,style=win32con.PS_SOLID):
    pen=Sdk.CreatePen(style,width,RGB(rgb))
    oldpen=dc.SelectObjectFromHandle(pen)
    dc.MoveTo(l[:2])
    dc.LineTo(l[2:])
    dc.SelectObjectFromHandle(oldpen)
    Sdk.DeleteObject(pen)

def FillPolygon(dc,pts,rgb):
    br=Sdk.CreateBrush(win32con.BS_SOLID,RGB(rgb),0)
##     pen=Sdk.CreatePen(win32con.PS_SOLID,0,RGB(rgb))
    pen=Sdk.CreatePen(win32con.PS_NULL,0,RGB(rgb))
    oldpen=dc.SelectObjectFromHandle(pen)
    oldbr=dc.SelectObjectFromHandle(br)
    pm = dc.SetPolyFillMode(win32con.WINDING);
    dc.Polygon(pts);
    dc.SetPolyFillMode(pm);
    dc.SelectObjectFromHandle(oldpen)
    dc.SelectObjectFromHandle(oldbr)
    Sdk.DeleteObject(pen)
    Sdk.DeleteObject(br)


def DrawRectanglePath(dc,rc):
    dc.MoveTo((rc[0],rc[1]))
    dc.LineTo((rc[2],rc[1]))
    dc.LineTo((rc[2],rc[3]))
    dc.LineTo((rc[0],rc[3]))
    dc.LineTo((rc[0],rc[1]))


def RectanglePath(dc, rc, rop=win32con.R2_NOTXORPEN, pens=win32con.BS_SOLID, penw=0, penc=win32api.RGB(0,0,0)):
    oldrop=dc.SetROP2(rop)
    pen=Sdk.CreatePen(pens,penw,penc)
    oldpen=dc.SelectObjectFromHandle(pen)
    DrawRectanglePath(dc,rc)
    dc.SelectObjectFromHandle(oldpen)
    Sdk.DeleteObject(pen)
    dc.SetROP2(oldrop);

def FrameRect(dc,rc,rgb):
    br=Sdk.CreateBrush(win32con.BS_SOLID,RGB(rgb),0)
    dc.FrameRectFromHandle(rc,br)
    Sdk.DeleteObject(br)

def DrawRectangle(dc,rc,rgb,st='f'):
    if st == 'd':
        pen=Sdk.CreatePen(win32con.PS_SOLID,0,win32api.RGB(0,0,0))
        oldpen=dc.SelectObjectFromHandle(pen)
        DrawRectanglePath(dc,rc)
        dc.SelectObjectFromHandle(oldpen)
        Sdk.DeleteObject(pen)
    else:
        br=Sdk.CreateBrush(win32con.BS_SOLID,RGB(rgb),0)
        dc.FrameRectFromHandle(rc,br)
        Sdk.DeleteObject(br)

def DrawWndRectangle(wnd,rc,rgb,st):
    dc=wnd.GetDC()
    DrawRectangle(dc,rc,rgb,st)
    wnd.ReleaseDC(dc)

def SetTransparent(wnd,enable):
    style = wnd.GetWindowLong(win32con.GWL_EXSTYLE)
    if enable:
        style = style | win32con.WS_EX_TRANSPARENT;
    else:
        style = style & ~win32con.WS_EX_TRANSPARENT;
    wnd.SetWindowLong(win32con.GWL_EXSTYLE,style)

def DrawLines(dc,ll,rgb):
    pen=Sdk.CreatePen(win32con.PS_SOLID,0,RGB(rgb))
    oldpen=dc.SelectObjectFromHandle(pen)
    dc.Polyline(ll)
    dc.SelectObjectFromHandle(oldpen)
    Sdk.DeleteObject(pen)


################################## Print Screen to Bitmap

try:
    from sysmetrics import scr_width_pxl,scr_height_pxl
    SCR=Rect((0,0,scr_width_pxl,scr_height_pxl))
except:
    SCR=Rect((0,0,640,480))

# Limits rectangle in screen
def GetVisible(rct):
    rc=Rect(rct)
    if rc.left<0:rc.left=0
    if rc.top<0:rc.top=0
    if rc.right>SCR.right:rc.right=SCR.right
    if rc.bottom>SCR.bottom:rc.bottom=SCR.bottom
    return rc

# Creates a bitmap copying the screen
def ScreenToBitmap(rct):
    hdcscr=Sdk.CreateDC('DISPLAY')
    dcscr=win32ui.CreateDCFromHandle(hdcscr)
    #dcmem=win32ui.CreateDC()
    dcmem=dcsrc.CreateCompatibleDC()
    rc=GetVisible(rct)
    bmp=win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dcscr,rc.width(),rc.height())
    old=dcmem.SelectObject(bmp)
    dcmem.BitBlt((0,0),rc.size(),dcscr,rc.pos(),win32con.SRCCOPY)
    bmp=dcmem.SelectObject(old)
    dcscr.DeleteDC()
    dcmem.DeleteDC()
    return bmp

def BitBltBmp(dc,bmp,rc_dst):
    #dcmem=win32ui.CreateDC()
    dcmem=dc.CreateCompatibleDC()
    old=dcmem.SelectObject(bmp)
    pt_dst=(rc_dst[0],rc_dst[1])
    sz_dst=(rc_dst[2]-rc_dst[0],rc_dst[3]-rc_dst[1])
    dc.BitBlt(pt_dst,sz_dst,dcmem,(0,0),win32con.SRCCOPY)
    dcmem.SelectObject(old)
    dcmem.DeleteDC()

def StretchBltBmp(dc,bmp,rc_dst):
    #dcmem=win32ui.CreateDC()
    dcmem=dc.CreateCompatibleDC()
    old=dcmem.SelectObject(bmp)
    pt_dst=(rc_dst[0],rc_dst[1])
    sz_dst=(rc_dst[2]-rc_dst[0],rc_dst[3]-rc_dst[1])
    pt_src=(0,0)
    sz_src=bmp.GetSize()
    dc.StretchBlt(pt_dst,sz_dst,dcmem,pt_src,sz_src,win32con.SRCCOPY)
    dcmem.SelectObject(old)
    dcmem.DeleteDC()

def BitBltBmpFramed(dc,bmp,rc_dst):
    BitBltBmp(dc,bmp,rc_dst)
    br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)
    dc.FrameRectFromHandle(rc_dst,br)
    Sdk.DeleteObject(br)

def WndToBmp(wnd):
    rc=wnd.GetWindowRect()
    return ScreenToBitmap(rc)

################################### DlgTemplate
from Font import findfont

class DlgTemplate:
    def __init__(self,id):
        self._templ=win32ui.LoadDialogResource(id)
        #print self._templ
        self._header=self._templ[0]
        self._dlg_rc=self._header[1]
        if len(self._header)>4:
            pointsize=self._header[4][0]
            fontname=self._header[4][1]
            font=findfont(fontname, pointsize)
            self._cx = font._tm['tmAveCharWidth']+1
            self._cy = font._tm['tmHeight']
        else:
            print 'Extented dialog templates (DIALOGEX) not supported. Check dialog with id',id

    # dlg units should be computed from dialog font
    def getRect(self):
        if len(self._header)>4:
            l,t,r,b=self._dlg_rc
            cx,cy=self._cx,self._cy
            return Rect(((l*cx+2)/4,(t*cy+4)/8,(r*cx+2)/4,(b*cy+4)/8))
        else:
            return None
