# Experimental layout view for light region view

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

# atoi
import string

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
		self.__ctrlNames=n=('ViewportSel','RegionSel','RegionX','RegionY','RegionW','RegionH','RegionZ', 'BgColor', 'ShowNames')
		self[n[0]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_VIEWPORT_SEL)
		self[n[1]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_REGION_SEL)
		self[n[2]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_X)
		self[n[3]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Y)
		self[n[4]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_W)
		self[n[5]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_H)
		self[n[6]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Z)
		self[n[7]]=components.Button(self,grinsRC.IDC_LAYOUT_BACKGROUND)
		self[n[8]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_SHOW_NAMES)

		# Initialize control objects whose command are activable as well from menu bar
		self[ATTRIBUTES]=components.Button(self,grinsRC.IDCMD_ATTRIBUTES)
		
		self._activecmds={}

		# set this to 0 to suppress region names
		self._showRegionNames = 1

		# region name : list index
		self._region2ix = {}

		# set to true while updating controls due to darwing
		self._mouse_update = 0

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

		# update show names check box 
		self['ShowNames'].setcheck(self._showRegionNames)

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
			if not self.has_key(cmd.__class__):continue
			id=self[cmd.__class__]._id
			self.EnableCmd(cmd.__class__,1)
			contextcmds[id]=cmd

	#
	# User input dispatch method 
	# i.e response to WM_COMMAND
	# 
	def OnCmd(self, params):
		if self._mouse_update: return

		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		
		# delegate combo box notifications
		if nmsg==win32con.LBN_SELCHANGE:
			if id == self['ViewportSel']._id:
				self['ViewportSel'].callcb()
				self.onViewportSelChange()	
			elif id == self['RegionSel']._id:
				self['RegionSel'].callcb()
				self.onRegionSelChange()
			return
		
		if id == self['ShowNames']._id:
			if nmsg==win32con.BN_CLICKED:
				self.onShowRegionNames()
			return 

		for name in ('RegionX','RegionY','RegionW','RegionH'):
			if id==self[name]._id:
				if nmsg==win32con.EN_CHANGE:
					self.onEditCoordinates()
				return
		if id==self['RegionZ']._id:
			if nmsg==win32con.EN_CHANGE:
				self.onEditZorder()
			return

		if id==self['BgColor']._id:
			self.onBgColor()
			return
			
		# process rest
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)


	#
	# User input response from dialog controls
	# 
	def onViewportSelChange(self):
		vpname = self['ViewportSel'].getvalue()
		self.selectViewport(vpname)
			
	def onRegionSelChange(self):
		rgnname = self['RegionSel'].getvalue()
		self.selectRegion(rgnname)

	def onShowRegionNames(self):
		self._showRegionNames = self['ShowNames'].getcheck()
		self._layout._viewport.showNames(self._showRegionNames)
		self._layout.update()

	def onEditCoordinates(self):
		name = self['RegionSel'].getvalue()
		region = self._layout.getRegion(name)
		if not region:
			if self._layout._selected == self._layout._viewport:
				region = self._layout._viewport
			else:
				return
		rc = self['RegionX'].gettext(),self['RegionY'].gettext(), self['RegionW'].gettext(), self['RegionH'].gettext()
		try:
			coordinates = tuple(map(string.atoi,rc))
		except ValueError:
			return
		else:
			if len(coordinates)==4 and coordinates[2]!=0 and coordinates[3]!=0:
				region.updatecoordinates(coordinates, units=UNIT_PXL)
				self._layout.update()

	def onEditZorder(self):
		name = self['RegionSel'].getvalue()
		region = self._layout.getRegion(name)
		if not region:
			if self._layout.selected == self._layout._viewport:
				region = self._layout._viewport
			else:
				return
		strz = self['RegionZ'].gettext()
		try:
			z = string.atoi(strz)
		except string.atoi_error:
			return
		else:
			if z>=0:
				region.updatezindex(z)
				self._layout.update()

	def onBgColor(self):
		name = self['RegionSel'].getvalue()
		region = self._layout.getRegion(name)
		if not region: return
		r, g, b = region._bgcolor or (255, 255, 255)
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self)
		if dlg.DoModal() == win32con.IDOK:
			newcol = dlg.GetColor()
			rgb = win32ui.GetWin32Sdk().GetRGBValues(newcol)
			region.updatebgcolor(rgb)
			self._layout.update()


	#
	# Helpers for user input responses
	# 
	def selectViewport(self, name):
		self._layout.setViewport(name)
		rgnList = self._layout.getRegions(name)
		self['RegionSel'].resetcontent()
		i = 0
		for reg in rgnList:
			self['RegionSel'].addstring(reg)
			self._region2ix[reg] = i
			i = i + 1
		if rgnList:
			self['RegionSel'].setcursel(0)
			self.selectRegion(rgnList[0])
				
	def selectRegion(self, name):
		region = self._layout.getRegion(name)
		if region:
			self._layout.selectRegion(name)
			self.onShapeChange(region)
			
	#
	# win32window.DrawContext listener interface
	# 
	def onShapeChange(self, shape):
		if shape is None:
			for name in ('RegionX','RegionY','RegionW','RegionH'):
				self[name].settext('')
			self._mouse_update = 1
			self['RegionZ'].settext('')
			self['RegionSel'].setcursel(-1)
			self['BgColor'].enable(0)
			self._mouse_update = 0
			return
		rc = shape._rectb
		i = 0
		self._mouse_update = 1
		for name in ('RegionX','RegionY','RegionW','RegionH'):
			self[name].settext('%d' % rc[i])
			i = i +1
		self['RegionZ'].settext('%d' % shape._z)
		if id(shape)!=id(self._layout._viewport):
			self['RegionSel'].setcursel(self._region2ix[shape._name])
		else:
			self['RegionSel'].setcursel(-1)
		self['BgColor'].enable(1)
		self._mouse_update = 0

	def onProperties(self, shape):
		if not shape: return
		r, g, b = shape._bgcolor or (255, 255, 255)
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self)
		if dlg.DoModal() == win32con.IDOK:
			newcol = dlg.GetColor()
			rgb = win32ui.GetWin32Sdk().GetRGBValues(newcol)
			shape.updatebgcolor(rgb)
			self._layout.update()

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
		
		fd = {'name':'Arial','height':10,'weight':700}
		self.__hsmallfont = Sdk.CreateFontIndirect(fd)		

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
		self.HookMessage(self.onLButtonDblClk,win32con.WM_LBUTTONDBLCLK)

	def OnDestroy(self, params):
		if self.__hsmallfont:
			Sdk.DeleteObject(self.__hsmallfont)

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

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		win32window.DrawContext.onLButtonDblClk(self, flags, point)

	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		
		hf = dc.SelectObjectFromHandle(self.__hsmallfont)
		dc.SetBkMode(win32con.TRANSPARENT)

		self.paintOn(dc)
		
		dc.SelectObjectFromHandle(hf)
		
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

	def getClipRgn(self, rel=None):
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn(self.GetClientRect())
		return rgn

	def OnEraseBkgnd(self,dc):
		return 1

	def paintOn(self, dc, rc=None):
		rc = l, t, r, b = self.GetClientRect()

		# draw to offscreen bitmap for fast looking repaints
		dcc=dc.CreateCompatibleDC()

		bmp=win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc, r-l, b-t)
				
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-l, -t))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((l % 8, t % 8))
		dcc.IntersectClipRect(rc)

		rgn = self.getClipRgn()

		# background decoration on dcc
		dcc.FillSolidRect(rc,win32mu.RGB(self._bgcolor or (255,255,255)))

		# draw objects on dcc
		if self._viewport:
			self._viewport.paintOn(dcc)
			dcc.SelectClipRgn(rgn)
			self._viewport._draw3drect(dcc)
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
		if wnd != self._viewport:
			rgn = self._viewport.getClipRgn()
			dc.SelectClipRgn(rgn)
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

	def __setSmallFont(self, dc):
		self.__hfont_org = dc.SelectObjectFromHandle(self.__hsmallfont)

	def __restoreFont(self, dc):
		if self.__hfont_org:
			dc.SelectObjectFromHandle(self._hfont_org)


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

		self._showname = 1

		self._regions = {}
		self.__createRegions(name, ctx._context)

	def getRegion(self, name):
		return self._regions.get(name)
			
	def getwindowpos(self, rel=None):
		return self._rectb

	def update(self, rc=None):
		self._ctx.update(rc)

	def showNames(self, bv):
		for w in self._subwindows:
			w.showNames(bv)
		self._showname = bv
		
	def getMouseTarget(self, point):
		for w in self._subwindows:
			if w.inside(point):
				return w
		if self.inside(point):
			return self
		return None
	
	def getClipRgn(self, rel=None):
		x, y, w, h = self._rectb
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		return rgn
		
	def paintOn(self, dc, rc=None):
		x, y, w, h = self.getwindowpos()
		ltrb = l, t, r, b = x, y, x+w, y+h

		rgn = self.getClipRgn()
		dc.SelectClipRgn(rgn)
		if self._bgcolor:
			dc.FillSolidRect(ltrb,win32mu.RGB(self._bgcolor))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc, rc)

	def _draw3drect(self, dc):
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
		self._showname = 1
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

		rgn = self.getClipRgn()

		dc.SelectClipRgn(rgn)
		if self._bgcolor: # not self._transparent
			dc.FillSolidRect(ltrb,win32mu.RGB(self._bgcolor))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc)

		dc.SelectClipRgn(rgn)
		if self._showname:
			dc.DrawText(self._name, ltrb, win32con.DT_SINGLELINE|win32con.DT_CENTER|win32con.DT_VCENTER)

		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(ltrb,br)
		Sdk.DeleteObject(br)

	def getClipRgn(self, rel=None):
		x, y, w, h = self.getwindowpos(rel);
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		if rel==self: return rgn
		prgn = self._parent.getClipRgn(rel)
		rgn.CombineRgn(rgn,prgn,win32con.RGN_AND)
		prgn.DeleteObject()
		return rgn

	def showNames(self, bv):
		for w in self._subwindows:
			w.showNames(bv)
		self._showname = bv


