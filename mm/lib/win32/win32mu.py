__version__ = "$Id$"


# Objects
# <draw functions>
# def SetCursor(strid):

from types import *
import win32ui, win32con, win32api
from win32modules import grinsRC

Sdk=win32ui.GetWin32Sdk()

####################################################
# Utilities that replace part of cmifex functionality
# and correct some of its drawbacks
# They radically correct the flashing problem (repeated paintings)
# by using the correct device context
# and clipping region returned by windows
# through BeginPaint. 

# We have indroduced Sdk Gdi objects because
# CPen,CBrush,... are not destroyed properly
# by win32ui

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
	pen=Sdk.CreatePen(win32con.PS_SOLID,0,RGB(rgb))
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

def DrawRectangle(dc,rc,rgb,st):
	if st == "d":
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

# replaces: cmifex.SetSiblings
def SetTransparent(wnd,enable):
	style = wnd.GetWindowLong(win32con.GWL_EXSTYLE)
	if enable:
		style = style | win32con.WS_EX_TRANSPARENT;
	else:
		style = style & ~win32con.WS_EX_TRANSPARENT;
	wnd.SetWindowLong(win32con.GWL_EXSTYLE,style)

# replaces: cmifex.DrawLines			
def DrawLines(dc,ll,rgb):
	pen=Sdk.CreatePen(win32con.PS_SOLID,0,RGB(rgb))
	oldpen=dc.SelectObjectFromHandle(pen)
	dc.Polyline(ll)
	dc.SelectObjectFromHandle(oldpen)
	Sdk.DeleteObject(pen)


class Point:
	def __init__(self,p=(0,0)):
		self.x=p[0];self.y=p[1]
	def tuple():
		return self.x,self.y

class Size:
	def __init__(self,s=(0,0)):
		self.cx=s[0];self.cy=s[1]
	def tuple():
		return self.cx,self.cy

class Rect:
	def __init__(self,r=(0,0,0,0)):
		self.left=r[0];self.top=r[1];
		self.right=r[2];self.bottom=r[3]
	def tuple(self):
		return self.left,self.top,self.right,self.bottom
	def pos_size_tuple(self):
		return self.left,self.top,self.right-self.left,self.bottom-self.top
	def width(self):
		return self.right-self.left
	def height(self):
		return self.bottom-self.top

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
		return win32api.LOWORD(self._lParam),win32api.HIWORD(self._lParam)
				
	def sizeType(self):
		return self._wParam
	def keyFlags(self):
		return self._wParam

	def minimized(self):
		if (self._wParam & win32con.SIZE_MINIMIZED):
			return 1
		return 0

	def cmdid(self): return self.LOWORD_wParam()
	
	def getcontrolid(self): return self.LOWORD_wParam()
	def getnmsg(self): return self.HIWORD_wParam()
	def gethandle(self): return self._lParam

	def __repr__(self):
		s='message=%d wparam=%d lparam=%d' % (self._message,self._wParam,self._lParam)
		return '<%s instance, %s>' % (self.__class__.__name__, s)
	


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

############## CURSORS

[ARROW, WAIT, HAND, START, G_HAND, U_STRECH,
D_STRECH, L_STRECH, R_STRECH, UL_STRECH, 
UR_STRECH, DR_STRECH, DL_STRECH, PUT] = range(14)

_win32Cursors = { 'hand':HAND, 'watch':WAIT, '':ARROW, 'start':START,
				'g_hand':G_HAND, 'ustrech':U_STRECH, 'dstrech':D_STRECH,
				'lstrech':L_STRECH, 'rstrech':R_STRECH, 'ulstrech':UL_STRECH,
				'urstrech':UR_STRECH, 'drstrech':DR_STRECH,
				'dlstrech':DL_STRECH, 'channel':PUT , ' ':ARROW}

_win32CursorsKeys = _win32Cursors.keys()

def SetCursor(strid):
	id=ARROW		
	if strid in _win32CursorsKeys:
		id=_win32Cursors[strid]
	App=(win32ui.GetAfx()).GetApp()
	if id==ARROW:
		cursor = App.LoadStandardCursor(win32con.IDC_ARROW)
	elif id==HAND:
		cursor = App.LoadCursor(grinsRC.IDC_POINT_HAND2)
	elif id==G_HAND:
		cursor = App.LoadCursor(grinsRC.IDC_GRAB_HAND2)
	elif id==U_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_U_STRECH)
	elif id==D_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_D_STRECH)
	elif id==L_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_L_STRECH)
	elif id==R_STRECH:
		cursor = App.LoaddCursor(grinsRC.IDC_R_STRECH)
	elif id==UL_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_UL_STRECH)
	elif id==UR_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_UR_STRECH)
	elif id==DR_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_RD_STRECH)
	elif id==DL_STRECH:
		cursor = App.LoadCursor(grinsRC.IDC_LD_STRECH)
	elif id==PUT:
		cursor = App.LoadCursor(grinsRC.IDC_PUT)
	elif id==WAIT:
		cursor = App.LoadCursor(grinsRC.IDC_WATCH2)
	elif id==START:
		cursor = App.LoadCursor(grinsRC.IDC_APPSTARTING)
	else: cursor = App.LoadStandardCursor(win32con.IDC_ARROW)
	(win32ui.GetWin32Sdk()).SetCursor(cursor);
	return cursor
