__version__ = "$Id$"

import winuser, wincon, wingdi

from appcon import *
from WMEVENTS import *

import winstruct

import usercmd, usercmdui
import usercmdinterface

class MainWnd(usercmdinterface.UserCmdInterface):
	def __init__(self, toplevel):
		self.__have_menu = 1
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
		self._status_msg = 'Loading modules ...'
		self._progress = None

		# player state
		self.__playerstate = None
		
		# using GAPI flag
		self._in_gapi_mode = 0

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
		self.HookMessage(self.OnKeyDown, wincon.WM_KEYDOWN)
		self.set_commandlist(None, 'document')
		self.set_commandlist(None, 'pview_')
		self._timer = self.SetTimer(1, 20)
		self.loadSplash()
		self.InvalidateRect()

	# application exit hook
	def OnClose(self, params):
		# application exit
		if self._timer:
			self.KillTimer(self._timer)
			self._timer = 0
		if self._in_gapi_mode:
			self.EnableGAPI(0)
		self.execute_cmd(usercmd.EXIT)
			
	def destroy(self):
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
			elif cmd == usercmd.CLOSE:
				self.execute_cmd(cmd)
				self.set_commandlist(None, 'document')
				self.set_commandlist(None, 'pview_')
			elif cmd == usercmd.CHOOSESKIN:
				self.execute_cmd(cmd)
			else:
				self.execute_cmd(cmd)
			self.loadSplash()
			return 
		for cbd in self._dyncmds.values():
			if cbd.has_key(cmdid):
				apply(apply, cbd[cmdid])
				return

	def set_commandlist(self, commandlist, context):
		self._activecmds[context] = {}
		if commandlist:
			for cmd in 	commandlist:
				self._activecmds[context][cmd.__class__] = cmd

		# enable/disable 'app' commands
		if context == 'app':
			entries = [usercmd.OPEN, usercmd.EXIT, usercmd.CHOOSESKIN]
			for cmdcl in entries:
				id = usercmdui.usercmd2id(cmdcl)
				self.EnableMenuItem(0, id, self._activecmds[context].has_key(cmdcl))

		# enable/disable 'document' commands
		if context == 'document':
			entries = [usercmd.CLOSE,]
			for cmdcl in entries:
				id = usercmdui.usercmd2id(cmdcl)
				self.EnableMenuItem(0, id, self._activecmds[context].has_key(cmdcl))
		
		# enable/disable playback commands
		if context == 'pview_':
			entries = [usercmd.PLAY, usercmd.PAUSE, usercmd.STOP,]
			for cmdcl in entries:
				id = usercmdui.usercmd2id(cmdcl)
				self.EnableMenuItem(1, id, self._activecmds[context].has_key(cmdcl))
					
	def HideMenu(self):
		if not self.__have_menu:
			return
		try:
			hmenu = self.HideMenuBar()
		except:
			# no menu
			pass
		self.__have_menu = 0

	def ShowMenu(self):
		if self.__have_menu:
			return
		try:
			hmenu = self.ShowMenuBar()
		except:
			# no menu
			pass
		self.__have_menu = 1

	def EnableMenuItem(self, submenu_index, id, enabled):
		if not self.__have_menu:
			return
		try:
			hmenu = self.GetMenuHandle()
		except:
			# no menu
			self.__have_menu = 0
			return
		menu = winuser.CreateMenuFromHandle(hmenu)
		submenu = menu.wce_GetSubMenu(submenu_index)
		if enabled:
			flags = wincon.MF_BYCOMMAND | wincon.MF_ENABLED
		else:
			flags = wincon.MF_BYCOMMAND | wincon.MF_GRAYED
		submenu.EnableMenuItem(id, flags)				

	def CheckMenuItem(self, submenu_index, id, checked):
		if not self.__have_menu:
			return
		try:
			hmenu = self.GetMenuHandle()
		except:
			# no menu
			self.__have_menu = 0
			return
		menu = winuser.CreateMenuFromHandle(hmenu)
		submenu = menu.wce_GetSubMenu(submenu_index)
		if checked:
			flags = wincon.MF_BYCOMMAND | wincon.MF_CHECKED
		else:
			flags = wincon.MF_BYCOMMAND | wincon.MF_UNCHECKED
		submenu.CheckMenuItem(id, flags)				
					
	def setplayerstate(self, state):
		import Player
		self.__playerstate = state
		submenu = 1
		id_play = usercmdui.usercmd2id(usercmd.PLAY)
		id_pause = usercmdui.usercmd2id(usercmd.PAUSE)
		id_stop = usercmdui.usercmd2id(usercmd.STOP)
		if state == Player.PLAYING:
			self.EnableMenuItem(submenu, id_play, 0)
			self.EnableMenuItem(submenu, id_pause, 1)
			self.EnableMenuItem(submenu, id_stop, 1)
			self.CheckMenuItem(submenu, id_pause, 0)
		elif state == Player.PAUSING:
			self.EnableMenuItem(submenu, id_play, 1)
			self.EnableMenuItem(submenu, id_pause, 1)
			self.EnableMenuItem(submenu, id_stop, 1)
			self.CheckMenuItem(submenu, id_pause, 1)
		elif state == Player.STOPPED:
			self.CheckMenuItem(submenu, id_pause, 0)
			self.EnableMenuItem(submenu, id_play, 1)
			self.EnableMenuItem(submenu, id_pause, 0)
			self.EnableMenuItem(submenu, id_stop, 0)
		else:
			self.CheckMenuItem(submenu, id_pause, 0)
			self.EnableMenuItem(submenu, id_play, 0)
			self.EnableMenuItem(submenu, id_pause, 0)
			self.EnableMenuItem(submenu, id_stop, 0)

	def set_toggle(self, cmdcl, onoff):
		if cmdcl in (usercmd.PLAY, usercmd.PAUSE, usercmd.STOP):
			# managed by setplayerstate
			return 
		hmenu = self.GetMenuHandle()
		menu = winuser.CreateMenuFromHandle(hmenu)
		flags = wincon.MF_BYCOMMAND
		if onoff: flags = flags | wincon.MF_CHECKED
		else: flags = flags | wincon.MF_UNCHECKED
		id = usercmdui.usercmd2id(cmdcl)
		# submenu = menu.wce_GetSubMenu(index)
		# submenu.CheckMenuItem(id, flags)
			
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

	__keymap = {
		wincon.VK_RETURN: 'center',
		wincon.VK_LEFT: 'left',
		wincon.VK_UP: 'up',
		wincon.VK_DOWN: 'down',
		wincon.VK_RIGHT: 'right',
		}
	def OnKeyDown(self, params):
		if self.__keymap.has_key(params[2]):
			self._viewport.onKeyboardEvent(self.__keymap[params[2]], KeyboardInput)

	# rem: we want to reuse this window
	def close(self):
		if self._viewport:
			viewport = self._viewport
			self._viewport = None
			viewport.close()
		self.redraw()

	def newViewport(self, width, height, units, bgcolor):
		l, t, r, b = self.GetClientRect()
		stderr_height = 0 # for debug
		w, h = r-l, b-t-self._menu_height-stderr_height
		we, he = w-4, h-4

		xs, ys = width/float(we), height/float(he)
		
		# assume fit = 'meet' if viewport can not fit
		scale = max(xs, ys)
##		self._d2l = max(1.0, scale)

		# center scaled viewport
		sw, sh = self.LStoDS((width, height), round = 1)
		sx = max(0, (w - sw)/2)
		sy = max(0, (h - sh)/2)
		if 1: sx = max(sx, 2); sy = 2 # bias to top for now
##		self._xd_org, self._yd_org = sx, sy
		
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

	def loadSplash(self):
		filename = r'\Program Files\GRiNS\cesplash.bmp'
		import settings
		skin = settings.get('skin')
		if skin:
			import parseskin, MMurl
			try:
				dict = parseskin.parsegskin(MMurl.urlopen(skin))
				if dict.has_key('image'):
					filename = MMurl.urlretrieve(MMurl.basejoin(skin, dict['image']))[0]
			except parseskin.error, msg:
				settings.nonsaved_user_settings['skin'] = ''
				from windowinterface import showmessage
				showmessage(msg)
			except:
				settings.set('skin', '')
				from windowinterface import showmessage
				showmessage('Error reading skin')
			else:
				if dict.has_key('image'):
					self.HideMenu()
					self._menu_height = 0
		dc = wingdi.GetDesktopDC()
		try:
			self._splash = wingdi.CreateDIBSurfaceFromFile(dc, filename)
		except wingdi.error, arg:
			self._splash = None
			ws, hs = 240, 144
		else:
			ws, hs = self._splash.GetSize()			
		dc.DeleteDC()
		l, t, r, b = self.GetClientRect()
		w, h = r-l, b - t - self._menu_height
		self._splash_pos = max(0, (w-ws)/2), max(0, (h-hs)/2 - 24)

	def paintSplash(self, dc):
		if self._splash is not None:
			dcc = dc.CreateCompatibleDC()
			bmp = dcc.SelectObject(self._splash)
			dc.BitBlt(self._splash_pos, self._splash.GetSize(), dcc, (0, 0), wincon.SRCCOPY)
			dcc.SelectObject(bmp)
			dcc.DeleteDC()
	
	def getStatusRect(self):
		l, t, r, b = self.GetClientRect()
		y = self._splash_pos[1]
		if self._splash is not None:
			y = y + self._splash.GetSize()[1]
		y = min(y, b-44)
		return l, y, r, y+24
		
	def setStatusMsg(self, msg):
		if not msg:
			import version
			msg = version.version
		self._status_msg = msg
		rc = self.getStatusRect()
		self.InvalidateRect(rc)
		self.UpdateWindow()

	def setReady(self):
		self.setStatusMsg('')
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
	
	def EnableGAPI(self, flag):
		import winmm
		if flag:
			if not self._in_gapi_mode:
				self._toplevel.setready()
				winmm.GXOpenDisplay(self.GetSafeHwnd())
				self._in_gapi_mode = 1
		else:
			if self._in_gapi_mode:
				winmm.GXCloseDisplay()
				self._in_gapi_mode = 0
