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
		self._curcursor = 'arrow'

		# scaling
		self._xd_org, self._yd_org = 0, 0
		self._d2l = 1.0

		# wince menubar height
		self._menu_height = 26
		self._splash = None
		self._splash_pos = 0, 0
		self._ready = 0
		self._status_msg = 'Looading modules ...'
		self._progress = None

	def __getattr__(self, attr):
		if attr != '__dict__':
			o = self.__dict__.get('_obj_')
			if o is not None:
				return getattr(o, attr)
		raise AttributeError, attr

	def create(self):
		app = winuser.GetApplication()
		wnd = app.GetMainWnd()
		if not wnd:
			winuser.MessageBox('failed to attach to main wnd')
			return
		self.__dict__['_obj_'] = wnd
		self.HookMessage(self.OnClose, wincon.WM_CLOSE)
		self.HookMessage(self.OnPaint, wincon.WM_PAINT)
		self.HookMessage(self.OnTimer, wincon.WM_TIMER)
		self.HookMessage(self.OnCommand, wincon.WM_COMMAND)
		self.HookMessage(self.OnLButtonDown, wincon.WM_LBUTTONDOWN)
		self.HookMessage(self.OnLButtonUp, wincon.WM_LBUTTONUP)
		self.HookMessage(self.OnLButtonDblClk, wincon.WM_LBUTTONDBLCLK)
		self.HookMessage(self.OnMouseMove, wincon.WM_MOUSEMOVE)
		self._timer = self.SetTimer(1, 20)
		self.InvalidateRect()

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
##		print 'Cmd: id=%d usercmd=%s' % (cmdid, repr(cmd))
		if cmd:
			if cmd == usercmd.EXIT:
				self.OnClose(params)
			elif cmd == usercmd.OPEN or cmd == usercmd.OPENFILE:
				if self._ready:
					self.execute_cmd(cmd)
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
##		print 'OnLButtonDblClk %d %d' % lpt
		#winuser.MessageBox('OnLButtonDblClk %d %d' % lpt)

	# rem: we want to reuse this window
	def close(self):
		if self._viewport:
			viewport = self._viewport
			self._viewport = None
			viewport.close()
		self.redraw()

	def set_toggle(self, cmdcl, onoff):
##		print 'set_toggle',  cmdcl, onoff
		if cmdcl == usercmd.PLAY:
			pass

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
		sw, sh = self.LStoDS((width, height), round = 1)
		sx = max(0, (w - sw)/2)
		sy = max(0, (h - sh)/2)
		if 1: sx = max(sx, 2); sy = 2 # bias to top for now
		self._xd_org, self._yd_org = sx, sy
		
		# assume 'white' as default
		bgcolor = bgcolor or (255, 255, 255)

		# create and return viewport
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

	def LStoDS(self, sz, round = 0):
		wl, hl = sz
		sc = 1.0/self._d2l
		if round:
			return int(sc*wl+0.5), int(sc*hl+0.5)
		return sc*wl, sc*hl
	#
	# Offscreen painting
	# 
	def OnPaint(self, params):
		if self.__dict__['_obj_'] is None:
			return 0
		ps = self.BeginPaint()
		hdc, eraceBg, rcPaint  = ps[:3]
		dc = wingdi.CreateDCFromHandle(hdc)
		self.paintOn(dc)
		dc.Detach()
		self.EndPaint(ps)

	def paintOn(self, dc):
		if self._viewport is None or not self._ready:
			# show splash when no document is open
			self.paintSplash(dc)
			if self._status_msg:
				rc = self.getStatusRect()
				dc.DrawText(self._status_msg, rc)
		else:
			# blit offscreen bmp
			buf = self._viewport.getBackBuffer()
			if buf:
				device_org = self._xd_org, self._yd_org
				dc.SetViewportOrg(device_org)
				ltrb1 = dc.GetClipBox()
				bsize = w, h = buf.GetSize()
				ltrb2 = 0, 0, w, h
				ltrb = winstruct.rectAnd(ltrb1, ltrb2)
				if ltrb:
					ltrb = winstruct.inflate(ltrb, 2, 2)
					dcc = dc.CreateCompatibleDC()
					dcc.SetViewportOrg((0,0))
					oldbuf = dcc.SelectObject(buf)
					rgn = wingdi.CreateRectRgn(ltrb)
					dcc.SelectClipRgn(rgn)
					rgn.DeleteObject()
					self._viewport.paint(dcc)
					dc.BitBlt((0, 0), bsize, dcc, (0, 0), wincon.SRCCOPY)
					dcc.SelectObject(oldbuf)
					dcc.DeleteDC()
				dc.SetViewportOrg((0, 0))


	def update(self, rc = None):
		if self._viewport:
			if rc is None:
				rc = self._viewport.getwindowpos()
			rc = self.LRtoDR(rc, round = 1)
			self.InvalidateRect(winstruct.ltrb(rc), 0)
		else:
			self.InvalidateRect()

	def redraw(self):
		self.InvalidateRect()
		self.UpdateWindow()

	def show(self):
		self.redraw()

	def paintSplash(self, dc):
		if self._splash is None:
			filename = r'\Program Files\GRiNS\bin\wince\cesplash.bmp'
			import mediainterface
			self._splash = mediainterface.get_image(filename, dc)
			ws, hs = self._splash.GetSize()
			l, t, r, b = self.GetClientRect()
			w, h = r-l, b - t - self._menu_height
			self._splash_pos = (w-ws)/2, (h-hs)/2 - 24
		dcc = dc.CreateCompatibleDC()
		bmp = dcc.SelectObject(self._splash)
		dc.BitBlt(self._splash_pos, self._splash.GetSize(), dcc, (0, 0), wincon.SRCCOPY)
		dcc.SelectObject(bmp)
		dcc.DeleteDC()
	
	def getStatusRect(self):
		l, t, r, b = self.GetClientRect()
		y = self._splash_pos[1] + self._splash.GetSize()[1] + 16
		return l, y, r, y+24
		
	def setStatusMsg(self, msg):
		self._status_msg = msg
		rc = self.getStatusRect()
		self.InvalidateRect(rc)
		self.UpdateWindow()

	def setReady(self):
		self._ready = 1

	def CreateProgressBar(self):
		self._ready = 0
		self.redraw()
		wndclass = 'msctls_progress32'
		height = 16
		l, t, r, b = self.getStatusRect()
		l, t, r, b = l+16, b+4, r-16, b
		wnd = self.__dict__['_obj_']
		self._progress = winuser.CreateWindowEx(0, wndclass, '', 
			wincon.WS_VISIBLE | wincon.WS_BORDER , (l, t), (r-l, height), wnd, 0)
		self._progress.ShowWindow(wincon.SW_SHOW)
		self._progress.UpdateWindow()
		return self._progress

	def DestroyProgressBar(self):
		self._progress.DestroyWindow()
		self._progress = None
		self._status_msg = ''
		self._ready = 1
		self.redraw()
