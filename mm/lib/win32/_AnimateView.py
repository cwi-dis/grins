__version__ = "$Id$"

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()

# win32 lib modules
import win32mu, components

# GRiNS resource ids
import grinsRC

#
import win32window

#
from fmtfloat import fmtfloat

from GenFormView import GenFormView

class _AnimateView(GenFormView):
	def __init__(self,doc,bgcolor=None):
		GenFormView.__init__(self, doc, grinsRC.IDD_ANIMATE)	
		self._layout = LayoutManager()

		# org positions
		self.__orgctrlpos = {}

	# returning true will make frame resizeable
	def isResizeable(self):
		return 1

	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)

		# set normal size from frame to be 640x480
		flags, sw, minpos, maxpos, rcnorm = self.GetParent().GetWindowPlacement()
		l, t = rcnorm[:2]
		self.GetParent().SetWindowPlacement(flags, sw, minpos, maxpos, (l,t,640,480))

		# create layout window
		preview = components.Control(self, grinsRC.IDC_LAYOUT_PREVIEW)
		preview.attach_to_parent()
		l1,t1,r1,b1 = self.GetWindowRect()
		l2,t2,r2,b2 = preview.getwindowrect()
		rc = l2-l1, t2-t1-2, r2-l2, b2-t2
		bgcolor = (255, 255, 255)
		self._layout.onInitialUpdate(self, rc, bgcolor)
		
		# resizing
		self.saveOrgCtrlPos()
		self.resizeCtrls(r1-l1, b1-t1)
		self.HookMessage(self.OnSize, win32con.WM_SIZE)
			
		# we have to notify layout if has capture
		self.HookMessage(self.onMouse,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onMouse,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouse,win32con.WM_MOUSEMOVE)

		self.addZoomButtons()


		# XXX: test only code
		mdiframe = self.GetParent().GetMDIFrame()
		smildoc = mdiframe.getgrinsdoc()
		player = smildoc.player
		ctx = player.userplayroot.GetContext()
		mmviewport = ctx.getviewports()[0]
		attrdict = {}
		attrdict['transparent'] = 1
		w, h = mmviewport.getPxGeom()
		fit = mmviewport.GetAttrDef('fit','hidden')
		attrdict['wingeom'] = 0, 0, w, h
		attrdict['z'] = 0
		self._layout._viewport = Viewport('', self, attrdict, 1.0)

	def onMouse(self, params):
		if self._layout._drawContext.hasCapture():
			self._layout.onNCLButton(params)

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()

	def showScale(self, d2lscale):
		t=components.Static(self,grinsRC.IDC_LAYOUT_SCALE)
		t.attach_to_parent()
		str = fmtfloat(d2lscale, prec=1)
		t.settext('Scale 1 : %s' % str)

	#
	# Zoom in/out
	#
	def addZoomButtons(self):
		self._iconzoomin = win32ui.GetApp().LoadIcon(grinsRC.IDI_ZOOMIN)
		self._iconzoomout = win32ui.GetApp().LoadIcon(grinsRC.IDI_ZOOMOUT)
		self._bzoomin = components.Button(self, grinsRC.IDC_ZOOMIN)
		self._bzoomout = components.Button(self, grinsRC.IDC_ZOOMOUT)
		self._bzoomin.attach_to_parent()
		self._bzoomout.attach_to_parent()
		self._bzoomin.seticon(self._iconzoomin)
		self._bzoomout.seticon(self._iconzoomout)
		self._bzoomin.show()
		self._bzoomout.show()
		self._bzoomin.hookcommand(self, self.OnZoomIn)
		self._bzoomout.hookcommand(self, self.OnZoomOut)

	def OnZoomIn(self, id, params):
		self.zoomIn()

	def OnZoomOut(self, id, params):
		self.zoomOut()

	def zoomIn(self):
		d2lscale = self._layout.getDeviceToLogicalScale()
		d2lscale = d2lscale - 0.1
		if d2lscale < 0.1 : d2lscale = 0.1
		self._layout.setDeviceToLogicalScale(d2lscale)

	def zoomOut(self):
		d2lscale = self._layout.getDeviceToLogicalScale()
		d2lscale = d2lscale + 0.1
		if d2lscale>10.0: d2lscale = 10.0
		self._layout.setDeviceToLogicalScale(d2lscale)

	#
	# Focus adjustements
	#
	def addFocusCtrl(self):
		fctrl = components.Control(self, grinsRC.IDC_1)
		fctrl.attach_to_parent()
		fctrl.hookmessage(self.OnHilight, win32con.WM_SETFOCUS)
		fctrl.hookmessage(self.OnUnhilight, win32con.WM_KILLFOCUS)
		fctrl.hookmessage(self.OnPaneKey, win32con.WM_KEYDOWN)

	def OnHilight(self, params):
		self._layout.hilight(1)
					
	def OnUnhilight(self, params):
		focusReceiver =  params[2] 
		if focusReceiver != self._layout.GetSafeHwnd():
			self._layout.hilight(0)			

	def OnPaneKey(self, params):
		key = params[2]
		if key == win32con.VK_TAB: 
			self.GetParent().GetPane(0,0).GetTreeCtrl().SetFocus()
		else:
			self._layout.onKeyDown(params)
		return 0

	#
	# Reposition controls on size
	#
	def getCtrlIds(self):
		return (grinsRC.IDC_SLIDER1,)

	def resizeCtrls(self, w, h):
		# controls margin + posibly scrollbar
		cm = 48 

		lf, tf, rf, bf = self.GetWindowRect()

		# resize preview pane
		ll, tl, rl, bl = self._layout.GetWindowRect()
		wp = rf - ll - 20
		hp = bf - tl - cm
		newrc = 0, 0, wp, hp
		self._layout.SetWindowPos(self._layout.GetSafeHwnd(), newrc,
				win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)
		
		# resize controls
		ctrlIDs = self.getCtrlIds()
		flags = win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE
		for id in ctrlIDs:
			ctrl = components.Control(self,id)
			ctrl.attach_to_parent()
			l1,t1,r1,b1 = ctrl.getwindowrect()
			hc = b1-t1
			if hc<15: dh =12
			else: dh=8
			newrc = self.__orgctrlpos[id], tl-tf+hp+dh, r1-l1, b1-t1
			ctrl.setwindowpos(ctrl._hwnd, newrc, flags)

	def saveOrgCtrlPos(self):
		lf, tf, rf, bf = self.GetWindowRect()
		ctrlIDs = self.getCtrlIds()
		for id in ctrlIDs:
			ctrl = components.Control(self,id)
			ctrl.attach_to_parent()
			l1,t1,r1,b1 = ctrl.getwindowrect()
			self.__orgctrlpos[id] = l1-lf
		self.__orgctrlpos[-1] = self.GetClientRect()[2:]

	def OnSize(self, params):
		msg = win32mu.Win32Msg(params)
		w, h = msg.width(), msg.height()
		worg, horg = self.__orgctrlpos[-1]
		self.resizeCtrls(w, h)
		self.centerViewport()

	def centerViewport(self):
		if self._layout and self._layout._viewport:
			self._layout._viewport.center()

################################################
import winlayout

LayoutManagerBase = winlayout.LayoutScrollOsWnd
LayoutManagerDrawContext = winlayout.MSDrawContext

class LayoutManager(LayoutManagerBase):
	def __init__(self):
		LayoutManagerBase.__init__(self, LayoutManagerDrawContext())
		self._drawContext.addListener(self)
		self._drawContext.setShapeContainer(self)

		self._listener = None
		self._viewport = None
		self._hasfocus = 0
	
		self._popup = None

		self._selectedList = []

		# decor
		self._blackBrush = Sdk.CreateBrush(win32con.BS_SOLID, 0, 0)
		self._selPen = Sdk.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(0,0,255))
		self._selPenDot = Sdk.CreatePen(win32con.PS_DOT, 1, win32api.RGB(0,0,255))

		self.selInc = 0
			
	# allow to create a LayoutManager instance before the onInitialUpdate of dialog box
	def onInitialUpdate(self, parent, rc, bgcolor):
		self.createWindow(parent, rc, bgcolor, (0, 0, 1280, 1024))

	def OnCreate(self, cs):
		LayoutManagerBase.OnCreate(self, cs)
		self.HookMessage(self.onKeyDown, win32con.WM_KEYDOWN)
		self.HookMessage(self.OnSetFocus,win32con.WM_SETFOCUS)
		self.HookMessage(self.OnKillFocus,win32con.WM_KILLFOCUS)

		# popup menu
		self.HookMessage(self.OnRButtonDown, win32con.WM_RBUTTONDOWN)
	
	def OnDestroy(self, params):
		LayoutManagerBase.OnDestroy(self, params)
		if self._blackBrush:
			Sdk.DeleteObject(self._blackBrush)
			self._blackBrush = 0
		if self._selPen:
			Sdk.DeleteObject(self._selPen)
			self._selPen = 0
		if self._selPenDot:
			Sdk.DeleteObject(self._selPenDot)
			self._selPenDot = 0
					
	#
	#  Scaling related
	#
	def setDeviceToLogicalScale(self, d2lscale):
		self._device2logical = d2lscale
		if self._viewport:
			self._viewport.setDeviceToLogicalScale(d2lscale)
		self._parent.showScale(d2lscale)
		self.updateCanvasSize() 
		self.InvalidateRect(self.GetClientRect())

	def getDeviceToLogicalScale(self):
		return self._device2logical

	def findDeviceToLogicalScale(self, wl, hl):
		wd, hd = self.GetClientRect()[2:]
		md = 32 # device margin
		xsc = wl/float(wd-md)
		ysc = hl/float(hd-md)
		if xsc>ysc: sc = xsc
		else: sc = ysc
		if sc<1.0: sc = 1
		return sc
	

	#  OnRButtonDown popup menu
	def OnRButtonDown(self, params):
		# simulate a left click to select the object
		self.onLButtonDown(params)
		self.onLButtonUp(params)
					
		msg = win32mu.Win32Msg(params)
		point = msg.pos()
		flags = msg._wParam
		point = self.ClientToScreen(point)
		flags = win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_LEFTBUTTON

		if self._popup:
			# xxx to improve
			self._popup.TrackPopupMenu(point, flags, self.GetParent().GetParent().GetMDIFrame())

	#
	#  popup menu
	#
	def setpopup(self, menutemplate):
		if self._popup:
			self._popup.DestroyMenu()
			self._popup = None
		if menutemplate != None:
			import win32menu
			popup = win32menu.Menu('popup')
			popup.create_popup_from_menubar_spec_list(menutemplate, usercmd2id)
			self._popup = popup
		else:
			self._popup = None
	
	#
	#  Painting
	#

	# win32window context update callback
	# rc is in win32window coordinates (N)
	def update(self, rc=None):
		if rc:
			x, y, w, h = rc
			rc = x, y, x+w, y+h
			# convert N (natural) coordinates to D (device)
			rc = self.NRtoDR(rc)
		try:
			self.InvalidateRect(rc or self.GetClientRect())
		except:
			# os window not alive
			pass

	# called by base class OnDraw or OnPaint
	def paintOn(self, dc):
		# fill background
		lc, tc, rc, bc = dc.GetClipBox()
		dc.FillSolidRect((lc, tc, rc, bc), win32mu.RGB(self._bgcolor or (255,255,255)))

		# draw objects on dc
		if self._viewport:
			self._viewport._draw3drect(dc, self._hasfocus)
			self._viewport.paintOn(dc)
			self.drawTracker(dc)

	def drawTracker(self, dc):
		v = self._viewport
		xv, yv, wv, hv = v.LRtoDR(v.getwindowpos(), round=1)
		ltrbv = xv, yv, xv+wv, yv+hv

		for wnd in self._drawContext._selections:
			rc = wnd.LRtoDR(wnd.getwindowpos(), round=1)
			l, t, r, b = wnd.ltrb(rc)

			hsave = dc.SaveDC()
			dc.ExcludeClipRect(ltrbv)
			oldpen = dc.SelectObjectFromHandle(self._selPenDot)
			win32mu.DrawRectanglePath(dc, (l, t, r-1, b-1))
			dc.SelectObjectFromHandle(oldpen)
			dc.RestoreDC(hsave)

			hsave = dc.SaveDC()
			dc.IntersectClipRect(ltrbv)
			oldpen = dc.SelectObjectFromHandle(self._selPen)
			win32mu.DrawRectanglePath(dc, (l, t, r-1, b-1))
			dc.SelectObjectFromHandle(oldpen)
			dc.RestoreDC(hsave)

			nHandles = wnd.getDragHandleCount()		
			for ix in range(1,nHandles+1):
				x, y, w, h = wnd.getDragHandleRect(ix)
				dc.FillSolidRect((x, y, x+w, y+h), win32api.RGB(255,127,80))
				dc.FrameRectFromHandle((x, y, x+w, y+h), self._blackBrush)

	def hilight(self, f):
		self._hasfocus = f
		self.InvalidateRect(self.GetClientRect())	

	def OnSetFocus(self, params):
		self.hilight(1)

	def OnKillFocus(self, f):
		self.hilight(0)


###########################

class Viewport(win32window.Window):
	def __init__(self, name, context, attrdict, d2lscale):
		self._attrdict = attrdict
		self._name = name
		self._ctx = context
		win32window.Window.__init__(self)
		self._uidx, self._uidy = 64, 64
		self.setDeviceToLogicalScale(d2lscale)

		self._cycaption = 0 #win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
		self._cycaptionlog = 0 # int(self._device2logical*self._cycaption+0.5)

		x, y, w, h = attrdict.get('wingeom')
		units = attrdict.get('units')
		z = 0
		transparent = attrdict.get('transparent')
		bgcolor = attrdict.get('bgcolor')
		if transparent == None:
			if bgcolor != None:
				transparent = 0
			else:
				transparent = 1


		self.create(None, (self._uidx, self._uidy, w, h), units, z, transparent, bgcolor)
		self.setDeviceToLogicalScale(d2lscale)

		# adjust some variables
		self._topwindow = self

		# disp list of this window
		# use shortcut instead of render 
		self._active_displist = self.newdisplaylist()

		self.center()
		self._showname = 1

	def center(self):
		x, y, w, h = self._rectb
		layout = self._ctx._layout
		vw, vh = layout.GetClientRect()[2:]
		vw, vh = self.DPtoLP((vw, vh))
		x = (vw - w)/2
		y = (vh - h)/2
		if x<8: x=8
		if y<8: y=8
		self._rectb = x, y, w, h

	# overide the default newdisplaylist method defined in win32window
	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return win32window._ResizeableDisplayList(self, bgcolor)

	def close(self):
		if self._active_displist:
			self._active_displist.close()

	# 
	# interface implementation: function called from an external module
	#

	# return the current geometry
	def getGeom(self):
		x, y, w, h = self._rectb
		return 0, 0, int(w+0.5), int(h+0.5)
	
	# add a sub region	
	def addRegion(self, attrdict, name):
		rgn = Region(self, name, self._ctx, attrdict, self._device2logical)
		return rgn

	# remove a sub region
	def removeRegion(self, region):
		# update the selection
		selectChanged = 0
		for ind in range(len(self._ctx._selectedList)):
			if self._ctx._selectedList[ind] is region:
				del self._ctx._selectedList[ind]
				selectChanged = 1
				break
		if selectChanged:
			self._ctx._drawContext.selectShapes(self._ctx._selectedList)

		# remove the link with the parent
		for ind in range(len(self._subwindows)):
			if self._subwindows[ind] is region:
				del self._subwindows[ind]
				break

		# do not forget to close region
		# important resources like images will not be freed 
		region.close()
					
	def setAttrdict(self, attrdict):
		# print 'setAttrdict', attrdict
		newBgcolor = attrdict.get('bgcolor')
		oldBgcolor = self._attrdict.get('bgcolor')
		newGeom = attrdict.get('wingeom')
		oldGeom = self._attrdict.get('wingeom')
		self._attrdict = attrdict

		if oldGeom != newGeom:
			self.updatecoordinates(newGeom, units=UNIT_PXL)			
		if newBgcolor != oldBgcolor:
			if newBgcolor != None:
				self.updatebgcolor(newBgcolor)

		self._ctx.update()

	# shape content. may be replaced by displaylist ???
	def showName(self, bv):
		self._showname = bv
		self._ctx.update()
	
	def hasmedia(self):
		return 0 # ignore trace image
				
	def setImage(self, filename, fit, mediadisplayrect = None):
		if self._active_displist != None:
			self._active_displist.newimage(filename, fit, mediadisplayrect)
	#
	#  end interface implementation
	#
	
#	def createRegions(self):
		# create the regions of this viewport
#		parentNode = self._ctx._viewports
#		self.__createRegions(self, parentNode, self._device2logical)

	def getwindowpos(self, rel=None):
		x, y, w, h = self._rectb
		return int(x+0.5), int(y+0.5), int(w+0.5), int(h+0.5)

	def update(self, rc=None):
		self._ctx.update(rc)

	def pop(self, poptop=1):
		pass
	
	# override win32window.Window method
	def setDeviceToLogicalScale(self, d2lscale):
		win32window.Window.setDeviceToLogicalScale(self, d2lscale)
		self.center()

	def insideCaption(self, point):
		x, y, w, h = self.getwindowpos()
		l, t, r, b = x, y-self._cycaptionlog, x+w, y
		xp, yp = point
		if xp>=l and xp<r and yp>=t and yp<b:
			return 1
		return 0
		
	def getMouseTarget(self, point):
		for w in self._subwindows:
			target = w.getMouseTarget(point)
			if target:
				return target
		if self.inside(point) or self.insideCaption(point):
			return self
		return None
	
	def getClipRgn(self, rel=None):
		x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		return rgn
		
	def paintOn(self, dc, rc=None):
		x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
		ltrb = l, t, r, b = x, y, x+w, y+h

		hsave = dc.SaveDC()
		dc.IntersectClipRect(ltrb)

		x0, y0 = dc.SetWindowOrg((-l,-t))
		if self._active_displist:
			self._active_displist._render(dc, rc)
		dc.SetWindowOrg((x0,y0))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc, rc)

		dc.RestoreDC(hsave)

	def _draw3drect(self, dc, hilight=0):
		hsave = dc.SaveDC()
		x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
		l, t, r, b = x, y-self._cycaption, x+w, y+h
		l, t, r, b = l-3, t-3, r+2, b+2
		c1, c2 = 180, 100
		if hilight:
			c1, c2 = 220, 150
		for i in range(3):
			if hilight:
				dc.Draw3dRect((l,t,r,b),win32api.RGB(c1, c1, 0), win32api.RGB(c2, c2, 0))
			else:
				dc.Draw3dRect((l,t,r,b),win32api.RGB(c1, c1, c1), win32api.RGB(c2, c2, c2))
			c1, c2 = c1-15, c2-15
			l, t, r, b = l+1, t+1, r-1, b-1
		dc.RestoreDC(hsave)

	def _drawcaption(self, dc):
		x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
		l, t, r, b = x, y, x+w, y+h
		dc.FillSolidRect((l,t-self._cycaption,r, t) ,win32mu.RGB((128, 128, 255)))
		dc.SetBkMode(win32con.TRANSPARENT)
		dc.SetTextAlign(win32con.TA_BOTTOM)
		clr_org=dc.SetTextColor(win32api.RGB(255,255,255))
		dc.TextOut(l+4,t-2,self._name)
		dc.SetTextColor(clr_org)
