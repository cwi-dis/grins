# Experimental layout view for light region view

# std win32 modules
import win32ui, win32con, win32api

# win32 lib modules
import win32mu, components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# UserCmds
from usercmd import *
from usercmdui import *

# GRiNS resource ids
import grinsRC


# draw toolkit
import DrawTk

# we need win32window.Window 
# for coordinates transformations
# and other services
import win32window

# units
from appcon import *

from GenFormView import GenFormView

class _LayoutView2(GenFormView):
	def __init__(self,doc,bgcolor=None):
		GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT2)	
		
		# Initialize control objects
		# save them in directory: accessible directly from LayoutViewDialog class
		# note: if you modify the key names, you also have to modify them in LayoutViewDialog
		self.__ctrlNames=n=('ViewportSel','RegionSel','RegionX','RegionY','RegionW','RegionH','RegionZ')
		self[n[0]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_VIEWPORT_SEL)
		self[n[1]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_REGION_SEL)
		self[n[2]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_X)
		self[n[3]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Y)
		self[n[4]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_W)
		self[n[5]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_H)
		self[n[6]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Z)

		# Initialize control objects whose command are activable as well from menu bar
		self[ATTRIBUTES]=components.Button(self,grinsRC.IDC_LAYOUT_PROPERTIES)
		
		self._activecmds={}

	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		# enable all lists
		for name in self.__ctrlNames:	
			self.EnableCmd(name,1)

		# create layout window
		preview = components.Control(self, grinsRC.IDC_LAYOUT_PREVIEW)
		preview.attach_to_parent()
		l1,t1,r1,b1 = self.GetWindowRect()
		l2,t2,r2,b2 = preview.getwindowrect()
		rc = l2-l1, t2-t1, r2-l2, b2-t2
		bgcolor = (255, 255, 255)
		self._drawwnd = LayoutWnd(self, rc, bgcolor)
	
	# Sets the acceptable commands. 
	def set_commandlist(self,commandlist):
		frame=self.GetParent()
		contextcmds=self._activecmds
		for cl in self.keys():
			# only menu bar commands
			if type(cl)!=type(''):
				self.EnableCmd(cl,0)
		contextcmds.clear()
		if not commandlist: return
		for cmd in commandlist:
			if cmd.__class__== CLOSE_WINDOW:continue
			id=self[cmd.__class__]._id
			self.EnableCmd(cmd.__class__,1)
			contextcmds[id]=cmd

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		
		# delegate combo box notifications
		for name in self.__ctrlNames:	
			if id==self[name]._id:
				self.OnComboBoxCmd(id,nmsg)
				return

		# process rest
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)

	# Response to a selection change of the listbox 
	def OnComboBoxCmd(self,id,code):
		if code==win32con.LBN_SELCHANGE:
			for s in self._ctrlNames:
				if self[s]._id==id:
					self[s].callcb()
					break


class LayoutWnd(window.Wnd, win32window.Window, DrawTk.DrawLayer):
	def __init__(self, parent, rc, bgcolor):
		window.Wnd.__init__(self, win32ui.CreateWnd())
		win32window.Window.__init__(self)
		DrawTk.DrawLayer.__init__(self)

		self._parent = parent
		self._rect = rc
		self._bgcolor = bgcolor
		self._active_displist = None
		
		self.create(None, rc, UNIT_PXL)

		Afx=win32ui.GetAfx()
		Sdk=win32ui.GetWin32Sdk()
		brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(bgcolor),0)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		icon=0
		clstyle=win32con.CS_DBLCLKS
		style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS
		exstyle = 0
		title = '' 
		strclass=Afx.RegisterWndClass(clstyle, cursor, brush, icon)
		self.CreateWindowEx(exstyle,strclass, title, style,
			(rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]),parent,0)
		self.ShowWindow(win32con.SW_SHOW)
		self.UpdateWindow()

	def OnCreate(self, params):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		
		# initialize DrawTk.DrawLayer
		self.SetRelCoordRef(self)
		self.SetLayoutMode(0)
		self.SetBRect(self.GetClientRect())
		self.SetCRect(self.GetClientRect())
		self.SetUnits(UNIT_PXL)

	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		self.paintOn(dc)
		self.EndPaint(paintStruct)

	def paintOn(self, dc):
		self.DrawObjLayer(dc)


