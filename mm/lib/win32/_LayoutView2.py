# Experimental layout view for light region view

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()

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
		self._layout = None
		self._context = None

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

		self._regions = {}

	def setContext(self, ctx):
		self._context = ctx

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
		self._layout = LayoutManager(self, rc, bgcolor)
		self._layout.setMMNodeContext(self._context)

		# fill combos
		vpList = self._layout.getViewports()
		for vpname in vpList:
			self['ViewportSel'].addstring(vpname)
		if vpList:
			self['ViewportSel'].setcursel(0)
			self.selectViewport(vpList[0])

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
	def OnCmd(self, params):
		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		
		# delegate combo box notifications
		if nmsg==win32con.LBN_SELCHANGE:
			if id == self['ViewportSel']._id:
				self.onViewportSelChange()	
			elif id == self['RegionSel']._id:
				self.onRegionSelChange()
			return

		# process rest
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)


	def onViewportSelChange(self):
		vpname = self['ViewportSel'].getvalue()
		self.selectViewport(vpname)
			
	def onRegionSelChange(self):
		rgnname = self['RegionSel'].getvalue()
		self.selectRegion(rgnname)

	def selectViewport(self, name):
		self._layout.setViewport(name)
		rgnList = self._layout.getRegions(name)
		self['RegionSel'].resetcontent()
		for reg in rgnList:
			self['RegionSel'].addstring(reg)
		if rgnList:
			self['RegionSel'].setcursel(0)
			self.selectRegion(rgnList[0])
	
	def selectRegion(self, name):
		region = self._layout.getRegion(name)
		if region:
			self._layout.selectRegion(name)
			self.onShapeChange(region)
			
	def onShapeChange(self, shape):
		if shape is None: return
		if id(shape)==id(self._layout._viewport): return
		rc = shape._rectb
		i = 0
		for name in ('RegionX','RegionY','RegionW','RegionH'):
			self[name].settext('%d' % rc[i])
			i = i +1
		self['RegionZ'].settext('%d' % shape._z)

###########################

class LayoutManager(window.Wnd, win32window.DrawContext):
	def __init__(self, parent, rc, bgcolor):
		window.Wnd.__init__(self, win32ui.CreateWnd())
		win32window.DrawContext.__init__(self)
		
		# register dialog as listener
		win32window.DrawContext.addListener(self, parent) 

		self._parent = parent
		self._bgcolor = bgcolor

		self._context = None
		self.__viewports = {}
		self._viewport = None
		
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

	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		win32window.DrawContext.onLButtonDown(self, flags, point)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		win32window.DrawContext.onLButtonUp(self, flags, point)
	
	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		win32window.DrawContext.onMouseMove(self, flags, point)

	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		
		self.paintOn(dc)
		
		# paint frame decoration
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(self.GetClientRect(),br)
		Sdk.DeleteObject(br)

		self.EndPaint(paintStruct)
	
	def setMMNodeContext(self, ctx):
		self._context = ctx
		self.__buildRegions()
	
	def getViewports(self):
		return self.__viewports.keys()

	def getRegions(self, vpname):
		return self.__viewports[vpname]

	def getRegion(self, name):
		if self._viewport:
			return self._viewport.getRegion(name)
		return None

	def selectRegion(self, name):
		if self._viewport:
			self._selected = self._viewport.getRegion(name)
		else:
			self._selected = None
		self.InvalidateRect(self.GetClientRect())
					
	def getChannel(self, name):
		return self._context.channeldict[name]

	def setViewport(self, name):
		mmchan = self.getChannel(name)
		self._viewport = Viewport(name, self, mmchan.attrdict)
		win32window.DrawContext.reset(self)
		self.InvalidateRect(self.GetClientRect())

	def getMouseTarget(self, point):
		if self._viewport:
			return self._viewport.getMouseTarget(point)
		return None

	def update(self, rc=None):
		if rc:
			x, y, w, h = rc
			rc = x, y, x+w, y+h
		self.InvalidateRect(rc or self.GetClientRect())

	def paintOn(self, dc, rc=None):
		rc = l, t, r, b = self.GetClientRect()
		
		# draw to offscreen bitmap for fast looking repaints
		dcc=dc.CreateCompatibleDC()

		bmp=win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc, r-l, b-t)
		
		#self.OnPrepareDC(dcc)
		
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-l, -t))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((l % 8, t % 8))
		dcc.IntersectClipRect(rc)

		
		# background decoration on dcc
		dcc.FillSolidRect(rc,win32mu.RGB(self._bgcolor or (255,255,255)))

		# draw objects on dcc
		if self._viewport:
			self._viewport.paintOn(dcc)
			self.drawTracker(dcc)

		# copy bitmap
		dc.SetViewportOrg((0, 0))
		dc.SetWindowOrg((0,0))
		dc.SetMapMode(win32con.MM_TEXT)
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt((l, t),(r-l, b-t),dcc,(0, 0), win32con.SRCCOPY)

		# clean up (revisit this)
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC() # needed?
		del bmp

	def drawTracker(self, dc):
		if not self._selected: return
		wnd = self._selected
		nHandles = wnd.getDragHandleCount()		
		for ix in range(1,nHandles+1):
			x, y, w, h = wnd.getDragHandleRect(ix)
			dc.PatBlt((x, y), (w, h), win32con.DSTINVERT);

	# brude force, will be improved
	def __buildRegions(self):
		d = {}
		for chan in self._context.channels:
			if chan.attrdict.get('type')=='layout':
				if chan.attrdict.has_key('base_window'):
					d[chan.name] = chan.attrdict['base_window']
				else:
					d[chan.name] = None
					self.__viewports[chan.name] = []
		for child, parent in d.items():
			if parent:
				while parent:
					p = d[parent]
					if p is None:
						self.__viewports[parent].append(child)
					parent = p


###########################

class Viewport(win32window.Window):
	def __init__(self, name, ctx, dict):
		self._name = name
		self._ctx = ctx
		win32window.Window.__init__(self)

		w, h = dict.get('winsize')
		rc = (8, 8, w, h)
		units = dict.get('units')
		z = 0
		transparent = dict.get('transparent')
		bgcolor = dict.get('bgcolor')
		self.create(None, rc, units, z, transparent, bgcolor)

		# adjust some variables
		self._topwindow = self

		self._regions = {}
		self.__createRegions(name, ctx._context)

	def getRegion(self, name):
		return self._regions.get(name)
			
	def getwindowpos(self, rel=None):
		return self._rectb

	def update(self, rc=None):
		self._ctx.update(rc)

	def getMouseTarget(self, point):
		for w in self._subwindows:
			if w.inside(point):
				return w
		if self.inside(point):
			return self
		return None
		
	def paintOn(self, dc, rc=None):
		x, y, w, h = self.getwindowpos()
		l, t, r, b = x, y, x+w, y+h
		if self._bgcolor:
			dc.FillSolidRect((l, t, r, b),win32mu.RGB(self._bgcolor))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc, rc)

		self.__draw3drect(dc)

	def __draw3drect(self, dc):
		x, y, w, h = self.getwindowpos()
		l, t, r, b = x, y, x+w, y+h
		l, t, r, b = l-3, t-3, r+2, b+2
		c1, c2 = 220, 150
		for i in range(3):
			dc.Draw3dRect((l,t,r,b),win32api.RGB(c1, c1, c1), win32api.RGB(c2, c2, c2))
			c1, c2 = c1-15, c2-15
			l, t, r, b = l+1, t+1, r-1, b-1

	# return true for regions rgnName belonging to viewport vpName
	def __isViewportRegion(self, rgnName, vpName, pardict):
		while 1:
			rgnName = pardict[rgnName]
			if rgnName is None: return 0
			elif rgnName==vpName: return 1
	
	# brude force, will be improved
	def __createRegions(self, name, ctx):
		d = {}
		for chan in ctx.channels:
			if chan.attrdict.get('type')=='layout':
				if chan.attrdict.has_key('base_window'):
					d[chan.name] = chan.attrdict['base_window']
				else:
					d[chan.name] = None
		
		dr = self._regions
		for chan in ctx.channels:
			if chan.attrdict.get('type')=='layout' and self.__isViewportRegion(chan.name, name, d):
				dr[chan.name] =  Region(chan.name, ctx, chan.attrdict)
		
		# do init with parents
		for rgnName, region in dr.items():
			parRgnName = d[rgnName]
			if parRgnName == name:
				parRegion = self
			else:
				parRegion = dr[parRgnName]
			region._do_init(parRegion)


###########################

class Region(win32window.Window):
	def __init__(self, name, ctx, dict):
		self._name = name
		self._ctx = ctx
		self._dict = dict
		win32window.Window.__init__(self)

	def _do_init(self, parent):
		dict = self._dict
		rc = x, y, w, h = dict.get('base_winoff')
		units = dict.get('units')
		z = dict.get('z')
		transparent = dict.get('transparent')
		bgcolor = dict.get('bgcolor')
		self.create(parent, rc, units, z, transparent, bgcolor)

	def paintOn(self, dc, rc=None):
		ltrb = self.ltrb(self.getwindowpos())
		if 	not self._transparent and self._bgcolor:
			dc.FillSolidRect(ltrb,win32mu.RGB(self._bgcolor))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc)

		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(ltrb,br)
		Sdk.DeleteObject(br)
