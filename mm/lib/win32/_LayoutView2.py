# Experimental layout view for light region view

# editor features
import features

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

# atoi
import string

# win32 lib modules
import win32mu, components

# std mfc windows stuf
from pywinlib.mfc import window,object,docview,dialog
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

#
from SMILTreeWrite import fmtfloat

# units
from appcon import *

from GenFormView import GenFormView

class _LayoutView2(GenFormView):
	def __init__(self,doc,bgcolor=None):
		GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT_T1)
		
		self._layout = None
		self._mmcontext = None

		self.__ctrlNames=n=('RegionX','RegionY','RegionW','RegionH','RegionZ','ShowAllMedias')
		self.__listeners = {}
			
		i = 0
		self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_X); i=i+1
		self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Y); i=i+1
		self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_W); i=i+1
		self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_H); i=i+1
		self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Z); i=i+1
		self[n[i]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_SHOW_ALLMEDIAS); i=i+1
			
		# Initialize control objects whose command are activable as well from menu bar
		self[ATTRIBUTES]=components.Button(self,grinsRC.IDCMD_ATTRIBUTES)
		
		self._activecmds={}

		# set this to 0 to suppress region names
		self._showRegionNames = 1

		# set to true while updating controls due to darwing
		self._mouse_update = 0

		# layout component
		self._previousHandler = None
		self._layout = LayoutManager()

		# tree component
		self._treeComponent = TreeManager()
		
		# allow to valid the field with the return key
		self.lastModifyCtrlField = None
			
			
	# special initialization because previous control is not managed like any another component
	# allow to have a handle on previous component from an external module
	def getPreviousComponent(self):
		return self._layout

	# for now avoid to have one handler by dialog ctrl
	def getDialogComponent(self):
		return self

	# define a handler for callbacks fnc
	def setListener(self, ctrlName, listener):
		self.__listeners[ctrlName] = listener

	# remove the handler for callback fnc
	def removeListener(self, ctrlName):
		if self.__listeners.has_key(ctrlName):
			del self.__listeners[ctrlName]
			
	# tree component
	def getTreeComponent(self):
		return self._treeComponent

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
		self._layout.onInitialUpdate(self, rc, bgcolor)

		self._treeComponent.onInitialUpdate(self)
			
		# we have to notify layout if has capture
		self.HookMessage(self.onMouse,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onMouse,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouse,win32con.WM_MOUSEMOVE)

	#
	# setup the dialog control values
	#
	
	def fillSelecterCtrl(self, ctrlName, vList):
		# fill combos selecter
		if vList:
			self[ctrlName].resetcontent()
			for vname in vList:
				self[ctrlName].addstring(vname)
			self[ctrlName].setcursel(0)

	def fillMultiSelCtrl(self, ctrlName, vList):
		# fill combos selecter
		if vList:
			self[ctrlName].resetcontent()
			for vname in vList:
				self[ctrlName].addstring(0, vname)
#			self[ctrlName].setcursel(0)

	def setMultiSelecterCtrl(self, ctrlName, vItem, bValue):
		# for now
		self[ctrlName].sendmessage(win32con.LB_SETSEL, bValue, vItem)
		
	def setSelecterCtrl(self, ctrlName, value):
		self[ctrlName].setcursel(value)
		
	def setCheckCtrl(self, ctrlName, bValue):
		self[ctrlName].setcheck(bValue)

	def setFieldCtrl(self, ctrlName, sValue):
		self[ctrlName].settext(sValue)

	def enable(self, ctrlName, bValue):
		self[ctrlName].enable(bValue)
		
	#
	# end setup the dialog control values
	#

	def onMouse(self, params):
		if self._layout.hasCapture():
			self._layout.onNCLButton(params)

	# Sets the acceptable command list by delegating to its parent keeping a copy.
	def set_commandlist(self, list):
		GenFormView.set_commandlist(self, list)
		self.set_localcommandlist(list)
		
	def close(self):
		self.deactivate()
		GenFormView.close(self)
		
	# Sets the acceptable commands. 
	def set_localcommandlist(self,commandlist):
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

	# apply changement when the control lose the focus. As the 'KILLFOCUS' event may be called
	# too late, this method can be called by the high level code
	def flushChangement(self):
		if self.lastModifyCtrlField != None:
			value = self[self.lastModifyCtrlField].gettext()
			listener = self.__listeners.get(self.lastModifyCtrlField)
			if listener != None:
				listener.onFieldCtrl(self.lastModifyCtrlField, value)
			self.lastModifyCtrlField = None
			return

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

		if id==win32con.IDOK or nmsg == win32con.EN_KILLFOCUS:
			self.flushChangement()
			return
				
		# delegate combo box notifications to handler
		if nmsg==win32con.LBN_SELCHANGE:
			ctrlName = None
		
			# multi selection ctrl			
#			if id == self['RegionList']._id:
#				ctrlName = 'RegionList'
#			if ctrlName != None:
#				self[ctrlName].callcb()
#				itemNumber = self[ctrlName].getselcount()
#				items = self[ctrlName].getselitems(itemNumber)
#				self._dialogHandler.onMultiSelCtrl(ctrlName, items)				
#				return
		
		if nmsg==win32con.BN_CLICKED:
			ctrlName = None
			
#			if id == self['ShowAllMedias']._id:
#				ctrlName = 'ShowAllMedias'
						
			if ctrlName != None:
				value = self[ctrlName].getcheck()
				listener = self.__listeners.get(self.lastModifyCtrlField)
				if listener != None:
					listener.onCheckCtrl(ctrlName, value)
				return 
		
			if ctrlName != None:
				listener = self.__listeners.get(self.lastModifyCtrlField)
				if listener != None:
					listener.onButtonClickCtrl(ctrlName)
				return

		if nmsg==win32con.EN_CHANGE:
			ctrlName = None
			
			if id == self['RegionX']._id:
				ctrlName = 'RegionX'
			elif id == self['RegionY']._id:
				ctrlName = 'RegionY'
			elif id == self['RegionW']._id:
				ctrlName = 'RegionW'
			elif id == self['RegionH']._id:
				ctrlName = 'RegionH'
			elif id == self['RegionZ']._id:
				ctrlName = 'RegionZ'
				
			if ctrlName != None:
				self.lastModifyCtrlField = ctrlName
				
			return
			
		# process rest
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)

	def showScale(self, scale):
		t=components.Static(self,grinsRC.IDC_LAYOUT_SCALE)
		t.attach_to_parent()
		str = fmtfloat(scale, prec=1)
		t.settext('scale 1 : %s' % str)

###########################
# tree component management
# the tree component is based on the PyCTreeCtrl python class, which is itself based
# on MFC CTreeCtrl class. So it's not a lightweight component as Button, List,
# that we manage in componenent module

class TreeManager:
	def __init__(self):
		self.__imageList = win32ui.CreateImageList(16, 16, 0, 10, 5)
		self.bitmapNameToId = {}
		self._listener = None

	def destroy(self):
		self.treeCtrl.removeExpandListener(self)
		self.treeCtrl.removeMultiSelListener(self)
		self.treeCtrl = None
		self.__imageList = None
		self.bitmapNameToId = None
		self._listener = None
	
	def setListener(self, listener):
		self._listener = listener

	def removeListener(self):
		self._listener = None

	def onInitialUpdate(self, parent):
		import TreeCtrl
		self.treeCtrl = TreeCtrl.TreeCtrl(parent, grinsRC.IDC_TREE1)
		self.treeCtrl.addMultiSelListener(self)
		self.treeCtrl.addExpandListener(self)

		# init the image list used in the tree
		self.__initImageList()

	def _loadbmp(self, idRes):
		import win32dialog
		return win32dialog.loadBitmapFromResId(idRes)

	def __addImage(self, bitmap):
		return self.__imageList.Add(bitmap.GetHandle(), 0)
		
	def __initImageList(self):
		# initialize
		import grinsRC

		# viewport
		bitmap = self._loadbmp(grinsRC.IDB_VIEWPORT)
		id = self.__addImage(bitmap)
		self.bitmapNameToId['viewport'] = id
		# region
		bitmap = self._loadbmp(grinsRC.IDB_REGION)
		id = self.__addImage(bitmap)
		self.bitmapNameToId['region'] = id
		# media nodes
		for name, idRes in [('image',grinsRC.IDB_IMAGE), ('sound',grinsRC.IDB_SOUND),
							('video',grinsRC.IDB_VIDEO), ('text',grinsRC.IDB_TEXT),
							('html',grinsRC.IDB_HTML),('brush',grinsRC.IDB_IMAGE)]:
			bitmap = self._loadbmp(idRes)
			id = self.__addImage(bitmap)
			self.bitmapNameToId[name] = id

		self.treeCtrl.SetImageList(self.__imageList, commctrl.LVSIL_NORMAL)

	def removeNode(self, item):
		self.treeCtrl.DeleteItem(item)
		
	def insertNode(self, parent, text, imageName, selectedImageName):
		iImage = self.bitmapNameToId.get(imageName)
		iSelectedImage = self.bitmapNameToId.get(selectedImageName)
		mask = int(commctrl.TVIF_TEXT|commctrl.TVIF_IMAGE|commctrl.TVIF_SELECTEDIMAGE)
		item = self.treeCtrl.InsertItem(mask,
						text, # text
						iImage, # iImage
						iSelectedImage, # iSelectedImage
						commctrl.TVIS_BOLD , # state
						0, #state mask
						None, #lParam
						parent, # parent
						commctrl.TVI_FIRST)
		return item

	def updateNode(self, item, text, imageName, selectedImageName):
		iImage = self.bitmapNameToId.get(imageName)
		iSelectedImage = self.bitmapNameToId.get(selectedImageName)
		self.treeCtrl.SetItemText(item, text)
		self.treeCtrl.SetItemImage(item, iImage, iSelectedImage)

	# ExpandBranch - Expands a branch completely
	def expandBranch(self, item):
		treeCtrl = self.treeCtrl
		if treeCtrl.ItemHasChildren(item):
			treeCtrl.Expand( item, commctrl.TVE_EXPAND )
			child = treeCtrl.GetChildItem(item)
			while child != None:
				self.expandBranch(child)
				# XXX find the right method
				try:
					child = treeCtrl.GetNextSiblingItem(child)
				except:
					child = None

	def expand(self, item):
		try:
			self.treeCtrl.Expand(item, commctrl.TVE_EXPAND)
		except:
			# if the node has no child, it's an error in windows
			pass
		
	def destroyAllNodes(self):								  		
		self.treeCtrl.DeleteAllItems()

	def selectNodeList(self, itemList):
		self.treeCtrl.SelectItemList(itemList)
		
#	def _onSelect(self, std, extra):
#		action, itemOld, itemNew, ptDrag = extra
#		# XXX the field number doesn't correspond with API documention ???
#		item, field2, field3, field4, field5, field6, field7, field8 = itemNew
#		if self._handler != None:
#			self._handler.onSelectTreeNodeCtrl(item)
	
	def OnMultiSelChanged(self):
		if self._listener != None:
			self._listener.onSelectTreeNodeCtrl(self.treeCtrl.getSelectedItems())

	def OnExpandChanged(self, item, isExpanded):
		if self._listener != None:
			self._listener.onExpandTreeNodeCtrl(item, isExpanded)
						 
###########################
debugPreview = 0

class LayoutManager(window.Wnd, win32window.MSDrawContext):
	def __init__(self):
		window.Wnd.__init__(self, win32ui.CreateWnd())
		win32window.MSDrawContext.__init__(self)
		self._listener = None
		
	# allow to create a LayoutManager instance before the onInitialUpdate of dialog box
	def onInitialUpdate(self, parent, rc, bgcolor):
		# register dialog as listener
		win32window.MSDrawContext.addListener(self, self) 

		self._parent = parent
		self._bgcolor = bgcolor

		self._viewport = None
		
		self._device2logical = 1

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

		self.__initState()

	def __initState(self):
		# allow to know the last state about shape (selected, moving, resizing)
		self._selectedList = []
		self._isGeomChanging = 0
		self._wantDown = 0
		self._oldSelected = None
	
	def OnCreate(self, params):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		self.HookMessage(self.onLButtonDblClk,win32con.WM_LBUTTONDBLCLK)
		self.GetParent().HookMessage(self.onKeyDown, win32con.WM_KEYDOWN)

	def onKeyDown(self, params):
		key = params[2]
		dx, dy = 0, 0
		if key == win32con.VK_DOWN: dy = 1 
		elif key == win32con.VK_UP: dy = -1
		elif key == win32con.VK_RIGHT: dx = 1
		elif key == win32con.VK_LEFT: dx = -1
		if dx or dy:
			win32window.MSDrawContext.moveSelectionBy(self, dx, dy)
		return 1

	def OnDestroy(self, params):
		if self.__hsmallfont:
			Sdk.DeleteObject(self.__hsmallfont)

	#
	# win32window.MSDrawContext listener interface
	#
	
	def onDSelChanged(self, selections):
		self._selectedList = selections
		if self._listener != None:
			self._listener.onMultiSelChanged(selections)

	def onDSelMove(self, selections):
		self._isGeomChanging = 1
		self.onGeomChanging(selections)
			
	def onDSelResize(self, selection):
		self._isGeomChanging = 1
		self.onGeomChanging([selection])

	def onDSelProperties(self, selection): 
		if not selection: return
		selection.onProperties()

	# 
	# interface implementation: function called from an external module
	#

	def onGeomChanged(self, shapeList):
		if self._listener != None:
			self._listener.onGeomChanged(shapeList)		

	def onGeomChanging(self, shapeList):
		if self._listener != None:
			self._listener.onGeomChanging(shapeList)		

	# define a handler for the layout component
	def setListener(self, listener):
		self._listener = listener

	def removeListener(self):
		self._listener = None
		
	# create a new viewport
	def newViewport(self, attrdict, name):
		x,y,w, h = attrdict.get('wingeom')
		self._cycaption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
		self._device2logical = self.findDeviceToLogicalScale(w,h+self._cycaption)
		self._parent.showScale(self._device2logical)
		self.__initState()
		self._viewport = Viewport(name, self, attrdict, self._device2logical)
		win32window.MSDrawContext.reset(self)

		return self._viewport

	# selection of a list of nodes
	def selectNodeList(self, shapeList):
		self._selectedList = shapeList
		self.selectShapes(shapeList)			
	
	#
	# end implementation interface 
	#

	def __isInsideShapeList(self, selectedList, point):
		for selected in selectedList:
			if selected.inside(point):
				return 1
		return 0

	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		self._wantDown = 1
		self._sflags = flags
		self._spoint = point
		
		if not self.__isInsideShapeList(self._selectedList, point):
			self._wantDown = 0
			if debugPreview: print 'onLButtonDown: call MSDrawContext.onLButtonDown'
			win32window.MSDrawContext.onLButtonDown(self, flags, point)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		if self._wantDown:
			if debugPreview: print 'onLButtonUp: call MSDrawContext.onLButtonDown'
			win32window.MSDrawContext.onLButtonDown(self, self._sflags, self._spoint)
			self._wantDown = 0
		if debugPreview: print 'onLButtonUp: call MSDrawContext.onLButtonUp'
		win32window.MSDrawContext.onLButtonUp(self, flags, point)

		# update user events
		if self._isGeomChanging:
			if debugPreview: print 'onLButtonUp: call onGeomChanged'
			self.onGeomChanged(self._selectedList)
					
		self._isGeomChanging = 0
	
	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		if self._wantDown:
			if debugPreview: print 'onLButtonMove: call MSDrawContext.onLButtonDown'
			self._isGeomChanging = 1
			win32window.MSDrawContext.onLButtonDown(self, self._sflags, self._spoint)
			self._wantDown = 0
		win32window.MSDrawContext.onMouseMove(self, flags, point)

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		win32window.MSDrawContext.onLButtonDblClk(self, flags, point)

	def onNCLButton(self, params):
		win32window.MSDrawContext.onNCButton(self)

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

	def findDeviceToLogicalScale(self, wl, hl):
		wd, hd = self.GetClientRect()[2:]
		md = 32 # device margin
		xsc = wl/float(wd-md)
		ysc = hl/float(hd-md)
		if xsc>ysc: sc = xsc
		else: sc = ysc
		if sc<1.0: sc = 1
		return sc

	def getMouseTarget(self, point):
		if self._viewport:
			if not self._isGeomChanging:
				return self._viewport.getMouseTarget(point)
			else:
				# The shapes move. In this case, if the mouse hit a previous target
				# we have to keep the same, and not change of target (for a region/media child)
				for selected in self._selectedList:
					if selected.inside(point):
						return selected

				# Otherwise, choice another target according to the shape hierarchy.
				# the priority is the shape which are on the front
				return self._viewport.getMouseTarget(point)
		return None

	def update(self, rc=None):
		if rc:
			x, y, w, h = rc
			rc = x, y, x+w, y+h
		try:
			self.InvalidateRect(rc or self.GetClientRect())
		except:
			# XXX the winui may already destroyed !
			pass

	def getClipRgn(self, rel=None):
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn(self.GetClientRect())
		return rgn

	def OnEraseBkgnd(self,dc):
		return 1

	def paintOn(self, dc, rc=None):
		rc = l, t, r, b = self.GetClientRect()
		w, h = r - l, b - t

		# draw to offscreen bitmap for fast looking repaints
		dcc=dc.CreateCompatibleDC()

		bmp=win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc, w, h)
				
		dcc.OffsetViewportOrg((-l, -t))
		oldBitmap = dcc.SelectObject(bmp)

		rgn = self.getClipRgn()

		# background decoration on dcc
		dcc.FillSolidRect((0,0,w,h),win32mu.RGB(self._bgcolor or (255,255,255)))

		# draw objects on dcc
		if self._viewport:
			self._viewport.paintOn(dcc)
			dcc.SelectClipRgn(rgn)
			#self._viewport._drawcaption(dcc)
			self._viewport._draw3drect(dcc)
			self.drawTracker(dcc)

		# copy bitmap
		dc.SetViewportOrg((0, 0))
		dc.SetWindowOrg((0,0))
		dc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt((l, t),(w, h),dcc,(0, 0), win32con.SRCCOPY)

		# clean up (revisit this)
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC() # needed?
		del bmp

	def drawTracker(self, dc):
		for wnd in self._selections:
			if wnd != self._viewport:
				rgn = self._viewport.getClipRgn()
				dc.SelectClipRgn(rgn)
			nHandles = wnd.getDragHandleCount()		
			for ix in range(1,nHandles+1):
				x, y, w, h = wnd.getDragHandleRect(ix)
				dc.PatBlt((x, y), (w, h), win32con.DSTINVERT);

	#
	# Scaling support
	#
	def DPtoLP(self, pt):
		x, y = pt
		sc = self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5)

	def DRtoLR(self, rc):
		x, y, w, h = rc
		sc = self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5), int(sc*w+0.5), int(sc*h+0.5)

	def LPtoDP(self, pt):
		x, y = pt
		sc = 1.0/self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5)

	def LRtoDR(self, rc):
		x, y, w, h = rc
		sc = 1.0/self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5), int(sc*w+0.5), int(sc*h+0.5)


# for now manage only on listener in the same time
# it should be enough
class UserEventMng:
	def __init__(self):
		self.listener = None

	def setListener(self, listener):
		self.listener = listener

	def removeListener(self, listener):
		self.listener = None
		
	def onProperties(self):
			self.listener.onProperties()
			
###########################

class Viewport(win32window.Window, UserEventMng):
	def __init__(self, name, context, attrdict, scale):
		self._attrdict = attrdict
		self._name = name
		self._ctx = context
		win32window.Window.__init__(self)
		UserEventMng.__init__(self)
		self.setDeviceToLogicalScale(scale)

		self._cycaption = 0 #win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
		self._cycaptionlog = 0 # int(self._device2logical*self._cycaption+0.5)
		x, y, w, h = attrdict.get('wingeom')
		self._rc = (x, y, w, h)
		units = attrdict.get('units')
		z = 0
		transparent = attrdict.get('transparent')
		bgcolor = attrdict.get('bgcolor')
		if transparent == None:
			if bgcolor != None:
				transparent = 0
			else:
				transparent = 1
		self.create(None, self._rc, units, z, transparent, bgcolor)

		# adjust some variables
		self._topwindow = self

		# disp list of this window
		# use shortcut instead of render 
		self._active_displist = self.newdisplaylist()

		# XXX: test
		#filename = r'D:\ufs\mmdocuments\smil2time\FLC-Cream.jpg'
		#self.setImage(filename, fit='fill')

		self._showname = 1
		self._scale  = scale

	# overide the default newdisplaylist method defined in win32window
	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return win32window._ResizeableDisplayList(self, bgcolor)

	# 
	# interface implementation: function called from an external module
	#

	# return the current geometry
	def getGeom(self):
		return self._rectb
	
	# add a sub region	
	def addRegion(self, attrdict, name):
		rgn = Region(self, name, self._ctx, attrdict, self._scale)
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
			self._ctx.selectShapes(self._ctx._selectedList)

		# remove the link with the parent
		for ind in range(len(self._subwindows)):
			if self._subwindows[ind] is region:
				del self._subwindows[ind]
				break
					
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
		
	def setImage(self, filename, fit, mediadisplayrect = None):
		if self._active_displist != None:
			self._active_displist.newimage(filename, fit, mediadisplayrect)
	#
	#  end interface implementation
	#
 	
#	def createRegions(self):
		# create the regions of this viewport
#		parentNode = self._ctx._viewports
#		self.__createRegions(self, parentNode, self._scale)

	def getwindowpos(self, rel=None):
		return self._rectb

	def update(self, rc=None):
		self._ctx.update(rc)

	def pop(self, poptop=1):
		pass
	
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
		x, y, w, h = self.LRtoDR(self.getwindowpos())
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		return rgn
		
	def paintOn(self, dc, rc=None):
		x, y, w, h = self.LRtoDR(self.getwindowpos())
		ltrb = l, t, r, b = x, y, x+w, y+h

		rgn = self.getClipRgn()
		dc.SelectClipRgn(rgn)

		x0, y0 = dc.SetWindowOrg((-l,-t))
		if self._active_displist:
			self._active_displist._render(dc, rc)
		dc.SetWindowOrg((x0,y0))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc, rc)

	def _draw3drect(self, dc):
		x, y, w, h = self.LRtoDR(self.getwindowpos())
		l, t, r, b = x, y-self._cycaption, x+w, y+h
		l, t, r, b = l-3, t-3, r+2, b+2
		c1, c2 = 220, 150
		for i in range(3):
			dc.Draw3dRect((l,t,r,b),win32api.RGB(c1, c1, c1), win32api.RGB(c2, c2, c2))
			c1, c2 = c1-15, c2-15
			l, t, r, b = l+1, t+1, r-1, b-1

	def _drawcaption(self, dc):
		x, y, w, h = self.LRtoDR(self.getwindowpos())
		l, t, r, b = x, y, x+w, y+h
		dc.FillSolidRect((l,t-self._cycaption,r, t) ,win32mu.RGB((128, 128, 255)))
		dc.SetBkMode(win32con.TRANSPARENT)
		dc.SetTextAlign(win32con.TA_BOTTOM)
		clr_org=dc.SetTextColor(win32api.RGB(255,255,255))
		dc.TextOut(l+4,t-2,self._name)
		dc.SetTextColor(clr_org)

	def invalidateDragHandles(self):
		x, y, w, h  = self.LRtoDR(self.getwindowpos())
		delta = 4
		x = x-delta
		y = y-delta - self._cycaption
		w = w+2*delta
		h = h+2*delta + self._cycaption
		self.update((x, y, w, h))
				
###########################

class Region(win32window.Window, UserEventMng):
	def __init__(self, parent, name, context, attrdict, scale):
		self._name = name
		self._attrdict = attrdict
		self._showname = 1
		self._ctx = context		
		self._scale  = scale

		win32window.Window.__init__(self)
		UserEventMng.__init__(self)
		self.setDeviceToLogicalScale(scale)

		self._rc = x, y, w, h = attrdict.get('wingeom')
		units = attrdict.get('units')
		z = attrdict.get('z')
		transparent = attrdict.get('transparent')
		bgcolor = attrdict.get('bgcolor')
		if transparent == None:
			if bgcolor != None:
				transparent = 0
			else:
				transparent = 1
		self.create(parent, self._rc, units, z, transparent, bgcolor)
		
		# disp list of this window
		# use shortcut instead of render 
		self._active_displist = self.newdisplaylist()

		# allow to determinate if the region is moving
		self._isMoving = 0
		
		# allow to determinate if the region is resizing
		self._isResizing = 0

	# overide the default newdisplaylist method defined in win32window
	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return win32window._ResizeableDisplayList(self, bgcolor)
	
	def paintOn(self, dc, rc=None):
		ltrb = l, t, r, b = self.ltrb(self.LRtoDR(self.getwindowpos()))

		rgn = self.getClipRgn()

		dc.SelectClipRgn(rgn)

		x0, y0 = dc.SetWindowOrg((-l,-t))
		if self._active_displist:
			self._active_displist._render(dc, None)
		dc.SetWindowOrg((x0,y0))

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc)

		dc.SelectClipRgn(rgn)
		if self._showname:
			dc.SetBkMode(win32con.TRANSPARENT)
			dc.DrawText(self._name, ltrb, win32con.DT_SINGLELINE|win32con.DT_CENTER|win32con.DT_VCENTER)

		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(ltrb,br)
		Sdk.DeleteObject(br)

	def getClipRgn(self, rel=None):
		x, y, w, h = self.LRtoDR(self.getwindowpos())
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		if rel==self: return rgn
		prgn = self._parent.getClipRgn(rel)
		rgn.CombineRgn(rgn,prgn,win32con.RGN_AND)
		prgn.DeleteObject()
		return rgn

	def getMouseTarget(self, point):
		for w in self._subwindows:
			target = w.getMouseTarget(point)
			if target:
				return target
		if self.inside(point):
			return self
		return None

	# 
	# interface implementation: function called from an external module
	#

	# return the current geometry
	def getGeom(self):
		return self._rectb

	# add a sub region
	def addRegion(self, attrdict, name):
		rgn = Region(self, name, self._ctx, attrdict, self._scale)
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
			self._ctx.selectShapes(self._ctx._selectedList)

		# remove the link with the parent
		for ind in range(len(self._subwindows)):
			if self._subwindows[ind] is region:
				del self._subwindows[ind]
				break

	def setAttrdict(self, attrdict):
		newBgcolor = attrdict.get('bgcolor')
		oldBgcolor = self._attrdict.get('bgcolor')
		newGeom = attrdict.get('wingeom')
		oldGeom = self._attrdict.get('wingeom')
		newZ = attrdict.get('z')
		oldZ = self._attrdict.get('z')
		self._attrdict = attrdict

		if oldGeom != newGeom:
			self.updatecoordinates(newGeom, units=UNIT_PXL)
		if newBgcolor != oldBgcolor:
			if newBgcolor != None:
				self.updatebgcolor(newBgcolor)
		if newZ != oldZ:
			self.updatezindex(newZ)

		self._ctx.update()

	# shape content. may be replaced by displaylist ???
	def showName(self, bv):
		self._showname = bv
		self._ctx.update()

	def setImage(self, filename, fit, mediadisplayrect = None):
		if self._active_displist != None:
			self._active_displist.newimage(filename, fit, mediadisplayrect)

	# 
	# end interface implementation
	#


