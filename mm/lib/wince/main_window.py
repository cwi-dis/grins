__version__ = "$Id$"

import winuser, wincon, wingdi

from appcon import *
from WMEVENTS import *

import winstruct

import usercmd, usercmdui
import usercmdinterface

class MainWnd(usercmdinterface.UserCmdInterface):
	def __init__(self, toplevel):
		usercmdinterface.UserCmdInterface.__init__(self)
		self.__dict__['_obj_'] = None
		self._toplevel = toplevel
		self._timer = 0

		self._viewport = None

		# scaling
		self._xd_org, self._yd_org = 0, 0
		self._d2l = 1.0

		# wince menubar height
		self._menu_height = 26

	def __getattr__(self, attr):
		try:	
			if attr != '__dict__':
				o = self.__dict__['_obj_']
				if o:
					return getattr(o, attr)
		except KeyError:
			pass
		raise AttributeError, attr

	def create(self):
		app = winuser.GetApplication()
		wnd = app.GetMainWnd()
		if not wnd:
			winuser.MessageBox('failed to attach to main wnd')
			return
		self.__dict__['_obj_'] = wnd
		self._timer = self.SetTimer(1, 100)
		self.HookMessage(self.OnClose, wincon.WM_CLOSE)
		self.HookMessage(self.OnPaint, wincon.WM_PAINT)
		self.HookMessage(self.OnTimer, wincon.WM_TIMER)
		self.HookMessage(self.OnCommand, wincon.WM_COMMAND)
		self.HookMessage(self.OnLButtonDown, wincon.WM_LBUTTONDOWN)
		self.HookMessage(self.OnLButtonUp, wincon.WM_LBUTTONUP)
		self.HookMessage(self.OnLButtonDblClk, wincon.WM_LBUTTONDBLCLK)
		self.HookMessage(self.OnMouseMove, wincon.WM_MOUSEMOVE)

	# application exit hook
	def OnClose(self, params):
		# application exit
		if self._timer:
			self.KillTimer(self._timer)
			self._timer = 0
		self.execute_cmd(usercmd.EXIT)
		app = winuser.GetApplication()
		app.SetMainWnd(None)
		wnd = self.__dict__['_obj_']
		self.__dict__['_obj_'] = None
		wnd.DestroyWindow()
			
	def OnTimer(self, params):
		self._toplevel.serve_events(params)
	
	def OnCommand(self, params):
		cmdid = winstruct.winmsg(params).id()
		cmd = usercmdui.id2usercmd(cmdid)
		print 'Cmd: id=%d usercmd=%s' % (cmdid, repr(cmd))
		if cmd:
			if cmd == usercmd.EXIT:
				self.OnClose(params)
			else:
				self.execute_cmd(cmd)
			return 
		for cbd in self._dyncmds.values():
			if cbd.has_key(cmdid):
				apply(apply, cbd[cmdid])
				return

	def OnLButtonDown(self, params):
		msg = winstruct.winmsg(params)
		pt = msg.pos()
		if self._viewport:
			lpt = self.DPtoLP(pt)
			self._viewport.onMouseEvent(lpt, Mouse0Press)
		#print 'OnLButtonDown %d %d' % pt

	def OnLButtonUp(self, params):
		msg = winstruct.winmsg(params)
		pt = msg.pos()
		if self._viewport:
			lpt = self.DPtoLP(pt)
			self._viewport.onMouseEvent(lpt, Mouse0Release)
		#print 'OnLButtonUp %d %d' % pt

	# for CE is posted when the stylus moves while the tip is down
	def OnMouseMove(self, params):
		msg = winstruct.winmsg(params)
		pt = msg.pos()
		if self._viewport:
			lpt = self.DPtoLP(pt)
			self._viewport.onMouseMove(lpt)
		#print 'OnMouseMove %d %d' % pt

	def OnLButtonDblClk(self, params):
		msg = winstruct.winmsg(params)
		pt = msg.pos()
		lpt = self.DPtoLP(pt)
		print 'OnLButtonDblClk %d %d' % lpt

	# rem: we want to reuse this window
	def close(self):
		if self._viewport:
			viewport = self._viewport
			self._viewport = None
			viewport.close()

	def newViewport(self, width, height, units, bgcolor):
		l, t, r, b = self.GetClientRect()
		stderr_height = 0 # for debug
		w, h = r-l, b-t-self._menu_height-stderr_height
		we, he = w-4, h-4

		xs, ys = width/float(we), height/float(he)
		
		# assume fit = 'meet' if viewport can not fit
		scale = max(xs, ys)
		self._d2l = max(1.0, scale)

		# center scaled viewport
		sw, sh = self.LPtoDP((width, height), round=1)
		sx = max(0, (w - sw)/2)
		sy = max(0, (h - sh)/2)
		if 1: sx = max(sx, 2); sy = 2 # bias to top for now
		self._xd_org, self._yd_org = sx, sy
		
		# assume 'white' as default
		bgcolor = bgcolor or (255, 255, 255)

		# create and return viewport
		
		if 0:
			# dummy test
			import dummy_layout
			self._viewport = dummy_layout.Viewport(self, (0, 0, width, height), bgcolor)
		else:
			# gdi test
			import gdi_layout
			self._viewport = gdi_layout.Viewport(self, (0, 0, width, height), bgcolor)
		
		return self._viewport

	#
	# Scaling support
	# parameters: xd_org, yd_org, d2l
	#
	def DPtoLP(self, pt):
		xd, yd = pt
		sc = self._d2l
		return sc*(xd - self._xd_org), sc*(yd - self._yd_org)

	def DRtoLR(self, rc):
		xd, yd, wd, hd = rc
		sc = self._d2l
		return sc*(xd - self._xd_org), sc*(yd - self._yd_org), sc*wd, sc*hd

	def LPtoDP(self, pt, round=0):
		xl, yl = pt
		sc = 1.0/self._d2l
		if round:
			return self._xd_org + int(sc*xl+0.5), self._yd_org + int(sc*yl+0.5)
		return self._xd_org + sc*xl, self._yd_org + sc*yl

	def LRtoDR(self, rc, round=0):
		xl, yl, wl, hl = rc
		sc = 1.0/self._d2l
		if round:
			return self._xd_org + int(sc*xl+0.5), self._yd_org + int(sc*yl+0.5), int(sc*wl+0.5), int(sc*hl+0.5)
		return self._xd_org + sc*xl, self._yd_org + sc*yl, sc*wl, sc*hl

	#
	# Offscreen painting
	# 
	def OnPaint(self, params):
		if self._obj_ is None:
			return 0
		ps = self.BeginPaint()
		hdc, eraceBg, rcPaint  = ps[:3]
		dc = wingdi.CreateDCFromHandle(hdc)
		if self._viewport is None:
			# show splash when no document is open
			l, t, r, b = self.GetClientRect()
			rc = l, t, r, b - self._menu_height
			dc.DrawText('Oratrix GRiNS Player', rc)
		else:
			# blit offscreen bmp
			dcc = dc.CreateCompatibleDC()
			bmp = self._viewport.getBmp()
			if bmp:
				oldbmp = dcc.SelectObject(bmp)
				rc = self._viewport.getwindowpos()
				dc.StretchBlt(self.LRtoDR(rc, round=1), dcc, rc, wincon.SRCCOPY)
				dcc.SelectObject(oldbmp)
			dcc.DeleteDC()

		dc.Detach()
		self.EndPaint(ps)

	def createBmp(self, w, h):
		hdc = self.GetDC()
		dc = wingdi.CreateDCFromHandle(hdc)
		bmp = dc.CreateCompatibleBitmap(w, h)
		self.ReleaseDC(dc.Detach())
		return bmp

	def update(self):
		if self._viewport:
			rc = self._viewport.getwindowpos()
			self.InvalidateRect(self.LRtoDR(rc))
		else:
			self.InvalidateRect()
