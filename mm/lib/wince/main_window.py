__version__ = "$Id$"

import winuser, wincon, wingdi

import winstruct

from appcon import *

import usercmdui
import usercmdinterface

class MainWnd(usercmdinterface.UserCmdInterface):
	def __init__(self, toplevel):
		usercmdinterface.UserCmdInterface.__init__(self)
		self.__dict__['_obj_'] = None
		self._toplevel = toplevel
		self._timer = 0

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
		self.HookMessage(self.OnLButtonDblClk, wincon.WM_LBUTTONDBLCLK)

	def OnClose(self, params):
		# application exit
		if self._timer:
			self.KillTimer(self._timer)
			self._timer = 0
		app = winuser.GetApplication()
		app.SetMainWnd(None)
		self.DestroyWindow()
		self.__dict__['_obj_'] = None
			
	def OnTimer(self, params):
		self._toplevel.serve_events(params)
	
	def OnCommand(self, params):
		cmdid = winstruct.winmsg(params).id()
		cmd = usercmdui.id2usercmd(cmdid)
		winuser.MessageBox('On Command id=%d usercmd=%s' % (cmdid, repr(cmd)))
		if cmd:
			self.execute_cmd(cmd)
			return 
		for cbd in self._dyncmds.values():
			if cbd.has_key(cmdid):
				apply(apply, cbd[cmdid])
				return
	
	def OnLButtonDblClk(self, params):
		msg = winstruct.winmsg(params)
		print 'OnLButtonDblClk %d %d' % msg.pos()

	def OnPaint(self, params):
		if self._obj_ is None:
			return 0
		ps = self.BeginPaint()
		hdc = ps[0]
		dc = wingdi.CreateDCFromHandle(hdc)
		rc = self.GetClientRect()
		dc.DrawText('Oratrix GRiNS Player', rc)
		self.EndPaint(ps)

	# we want to reuse this
	def close(self):
		pass
