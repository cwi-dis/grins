# Experimental layout view for light region view

treeVersion = 0

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
		if treeVersion:
			GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT_T1)			
		else:
			if features.CUSTOM_REGIONS in features.feature_set:
				GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT3)
			else:
				GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT2)
		self._layout = None
		self._mmcontext = None

		if not treeVersion:
			# Initialize control objects
			# save them in directory: accessible directly from LayoutViewDialog class
			# note: if you modify the key names, you also have to modify them in LayoutViewDialog
			self.__ctrlNames=n=('ViewportSel','RegionSel','RegionX','RegionY',
							'RegionW','RegionH','RegionZ', 'ShowNames',
							'AsOutLine',
							'ShowRbg', 'SendBack', 'BringFront', 'MediaSel',
							'ViewportCheck','RegionCheck','MediaCheck','HideRegion','HideMedia')
			if features.CUSTOM_REGIONS in features.feature_set:
				n = n + ('NewRegion', 'DelRegion', 'NewView', 'ShowAllRegions')
			
			i = 0
			self[n[i]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_VIEWPORT_SEL); i=i+1
			self[n[i]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_REGION_SEL); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_X); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Y); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_W); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_H); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Z); i=i+1
			self[n[i]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_SHOW_NAMES); i=i+1
			self[n[i]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_AS_OUTLINE); i=i+1
			self[n[i]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_SHOW_RBG); i=i+1
			self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_SENDBACK); i=i+1
			self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_BRINGFRONT); i=i+1
			self[n[i]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_MEDIA_SEL); i=i+1
			self[n[i]]=components.RadioButton(self,grinsRC.IDC_LAYOUT_VIEWPORT_RADIO); i=i+1
			self[n[i]]=components.RadioButton(self,grinsRC.IDC_LAYOUT_REGION_RADIO); i=i+1
			self[n[i]]=components.RadioButton(self,grinsRC.IDC_LAYOUT_MEDIA_RADIO); i=i+1
			self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_HIDEREGION); i=i+1
			self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_HIDEMEDIA); i=i+1
			if features.CUSTOM_REGIONS in features.feature_set:
				self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_NEWREGION); i=i+1
				self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_DELREGION); i=i+1
				self[n[i]]=components.Button(self,grinsRC.IDC_LAYOUT_NEWVIEW); i=i+1
				self[n[i]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_SHOW_ALLREGIONS); i=i+1
		else:
			self.__ctrlNames=n=('RegionX','RegionY','RegionW','RegionH','RegionZ','ShowAllMedias')
			
			i = 0
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_X); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Y); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_W); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_H); i=i+1
			self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Z); i=i+1
			self[n[i]]=components.CheckButton(self,grinsRC.IDC_LAYOUT_SHOW_ALLMEDIAS); i=i+1
			
		if not treeVersion:
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

		if treeVersion:
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
	def setDialogHandler(self, handler):
		self._dialogHandler = handler

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

		# initialize the control tree
		if treeVersion:
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

		if id==win32con.IDOK or nmsg == win32con.EN_KILLFOCUS:
			if self.lastModifyCtrlField != None:
				value = self[self.lastModifyCtrlField].gettext()
				self._dialogHandler.onFieldCtrl(self.lastModifyCtrlField, value)
				self.lastModifyCtrlField = None
				return
				
		# delegate combo box notifications to handler
		if nmsg==win32con.LBN_SELCHANGE:
			ctrlName = None
		
			if not treeVersion:
				if id == self['ViewportSel']._id:
					ctrlName = 'ViewportSel'
				elif id == self['RegionSel']._id:
					ctrlName = 'RegionSel'
				elif id == self['MediaSel']._id:
					ctrlName = 'MediaSel'
				if ctrlName != None:
					self[ctrlName].callcb()
					value = self[ctrlName].getvalue()
					self._dialogHandler.onSelecterCtrl(ctrlName, value)				
					return

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
			
			if not treeVersion:
				if id == self['ShowNames']._id:
					ctrlName = 'ShowNames'
				elif id == self['AsOutLine']._id:
					ctrlName = 'AsOutLine'
				elif id == self['ShowRbg']._id:
					ctrlName = 'ShowRbg'
				elif id == self['ViewportCheck']._id:
					ctrlName = 'ViewportCheck'
				elif id == self['RegionCheck']._id:
					ctrlName = 'RegionCheck'
				elif id == self['MediaCheck']._id:
					ctrlName = 'MediaCheck'
				if ctrlName == None:
					if features.CUSTOM_REGIONS in features.feature_set:
						if id == self['ShowAllRegions']._id:
							ctrlName = 'ShowAllRegions'
			else:
				if id == self['ShowAllMedias']._id:
					ctrlName = 'ShowAllMedias'
						
			if ctrlName != None:
				value = self[ctrlName].getcheck()
				self._dialogHandler.onCheckCtrl(ctrlName, value)
				return 

			if not treeVersion:
				if id == self['SendBack']._id:
					ctrlName = 'SendBack'
				elif id == self['BringFront']._id:
					ctrlName = 'BringFront'
				elif id == self['HideRegion']._id:
					ctrlName = 'HideRegion'
				elif id == self['HideMedia']._id:
					ctrlName = 'HideMedia'
				if ctrlName == None:
					if features.CUSTOM_REGIONS in features.feature_set:
						if id == self['NewRegion']._id:
							ctrlName = 'NewRegion'
						elif id == self['DelRegion']._id:
							ctrlName = 'DelRegion'
						elif id == self['NewView']._id:
							ctrlName = 'NewView'
		
			if ctrlName != None:
				self._dialogHandler.onButtonClickCtrl(ctrlName)
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

	#
	# User input response from dialog controls
	# 

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
			if self._layout._selected == self._layout._viewport:
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


	#
	# Helpers for user input responses
	# 
#	def _selectViewport(self, name):
#		self._layout.setViewport(name)
#		rgnList = self._layout.getRegions(name)
#		self['RegionSel'].resetcontent()
#		i = 0
#		for reg in rgnList:
#			self['RegionSel'].addstring(reg)
#			self._region2ix[reg] = i
#			i = i + 1
#		if rgnList:
#			self['RegionSel'].setcursel(0)
#			self._selectRegion(rgnList[0])
#			self['RegionSel'].callcb()
				
#	def _selectRegion(self, name):
#		region = self._layout.getRegion(name)
#		if region:
#			self._layout.selectRegion(name)
#			self.onShapeChange(region)
			
#	def onProperties(self, shape):
#		if not shape: return
#		r, g, b = shape._bgcolor or (255, 255, 255)
#		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self)
#		if dlg.DoModal() == win32con.IDOK:
#			newcol = dlg.GetColor()
#			rgb = win32ui.GetWin32Sdk().GetRGBValues(newcol)
#			shape.updatebgcolor(rgb)
#			self._layout.update()

###########################
# tree component management
# the tree component is based on the PyCTreeCtrl python class, which is itself based
# on MFC CTreeCtrl class. So it's not a lightweight component as Button, List,
# that we manage in componenent module

class TreeManager:
	def __init__(self):
		self.__imageList = win32ui.CreateImageList(16, 16, 0, 10, 5)
		self.bitmapNameToId = {}
		self._handler = None

	def setHandler(self, handler):
		self._handler = handler
		
	def onInitialUpdate(self, parent):
		# get the tree control form the dialog box ressource
		import win32con, win32ui
		Sdk=win32ui.GetWin32Sdk()
		parentHwnd = parent.GetSafeHwnd()
		self.treeCtrl = parent.GetDlgItem(grinsRC.IDC_TREE1)

		# init the image list used in the tree
		self.__initImageList()

		# hook messages
		parent.HookNotify(self._onSelect,commctrl.TVN_SELCHANGED)

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
							('html',grinsRC.IDB_HTML)]:
			bitmap = self._loadbmp(idRes)
			id = self.__addImage(bitmap)
			self.bitmapNameToId[name] = id

		self.treeCtrl.SetImageList(self.__imageList, commctrl.LVSIL_NORMAL)

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

	def destroyAllNodes(self):								  		
		self.treeCtrl.DeleteAllItems()

	def selectNode(self, item):
		self.treeCtrl.SelectItem(item)
		
	def _onSelect(self, std, extra):
		action, itemOld, itemNew, ptDrag = extra
		# XXX the field number doesn't correspond with API documention ???
		item, field2, field3, field4, field5, field6, field7, field8 = itemNew
		if self._handler != None:
			self._handler.onSelectTreeNodeCtrl(item)
		
###########################
class LayoutManager(window.Wnd, win32window.DrawContext):
	def __init__(self):
		window.Wnd.__init__(self, win32ui.CreateWnd())
		win32window.DrawContext.__init__(self)
		
	# allow to create a LayoutManager instance before the onInitialUpdate of dialog box
	def onInitialUpdate(self, parent, rc, bgcolor):
		# register dialog as listener
		win32window.DrawContext.addListener(self, self) 

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
		self._selected = None
		self._isGeomChanging = 0
		self._wantDown = 0
		self._oldSelected = None
	
	def OnCreate(self, params):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		self.HookMessage(self.onLButtonDblClk,win32con.WM_LBUTTONDBLCLK)
		
	def OnDestroy(self, params):
		if self.__hsmallfont:
			Sdk.DeleteObject(self.__hsmallfont)


	#
	# win32window.DrawContext listener interface
	# 
	def onShapeChange(self, shape):
		if shape is None:
			# update user events
			if self._oldSelected != None:
				self._mouse_update = 1
				self._oldSelected.onUnselected()
				
			self._selected = None
			self._isGeomChanging = 0
						
			self._mouse_update = 0
			return

		self._mouse_update = 1
		rc = shape._rectb		
		if shape._rc != rc:
			self._isGeomChanging = 1
			shape.onGeomChanging(rc)
			shape._rc = rc
		elif not self._isGeomChanging:
			if self._oldSelected != shape:
				self._oldSelected = shape
				shape.onSelected()
						
		self._selected = shape
		self._mouse_update = 0

	def onProperties(self, shape):
		if not shape: return

		shape.onProperties()

	# 
	# interface implementation: function called from an external module
	#


	# define a handler for the layout component
	def setHandler(self, handler):
		self._Handler = handler
			
	# create a new viewport
	def newViewport(self, attrdict, name):
		x,y,w, h = attrdict.get('wingeom')
		self._cycaption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
		self._device2logical = self.findDeviceToLogicalScale(w,h+self._cycaption)
		self._parent.showScale(self._device2logical)
		self.__initState()
		self._viewport = Viewport(name, self, attrdict, self._device2logical)
		win32window.DrawContext.reset(self)

		return self._viewport
			
	#
	# end implementation interface 
	#
		
	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		self._wantDown = 1
		self._sflags = flags
		self._spoint = point
		self._oldSelected = self._selected
		if self._selected != None:
			if not self._selected.inside(point):
				self._wantDown = 0
				win32window.DrawContext.onLButtonDown(self, flags, point)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		if self._wantDown:
			if not self._isGeomChanging:
				win32window.DrawContext.onLButtonDown(self, self._sflags, self._spoint)
				self._wantDown = 0
		win32window.DrawContext.onLButtonUp(self, flags, point)

		# update user events
		if self._selected:
			if self._isGeomChanging:
					self._selected.onGeomChanged(self._selected._rectb)
					
		self._isGeomChanging = 0
	
	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		if self._wantDown:
			if not self._isGeomChanging:
				self._isGeomChanging = 1
				win32window.DrawContext.onLButtonDown(self, self._sflags, self._spoint)
				self._wantDown = 0
		win32window.DrawContext.onMouseMove(self, flags, point)

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLP(point)
		win32window.DrawContext.onLButtonDblClk(self, flags, point)

	def onNCLButton(self, params):
		win32window.DrawContext.onNCButton(self)

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
				if self._selected != None:
					if self._selected.inside(point):
						return self._selected
					
				self._viewport.getMouseTarget(point)
		return None

	def update(self, rc=None):
		if rc:
			x, y, w, h = rc
			rc = x, y, x+w, y+h
		try:
			self.InvalidateRect(rc or self.GetClientRect())
		except:
			print '_LayoutView2: LayoutManager.update: unexpected error ?'

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

	def selectRequest(self, node):
		self._selected = node
		self.update()

	def unselectRequest(self, node):
		self._selected = None
		self.update()
		
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

	def addListener(self, listener):
		self.listener = listener

	def removeListener(self, listener):
		self.listener = None
		
	def onSelected(self):
		if self.listener != None:
			self.listener.onSelected()

	def onUnselected(self):
		if self.listener != None:
			self.listener.onUnselected()

	def onGeomChanging(self, geom):
		if self.listener != None:
			self.listener.onGeomChanging(geom)		

	def onGeomChanged(self, geom):
		if self.listener != None:
			self.listener.onGeomChanged(geom)		

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

		self._showname = 1
		self._scale  = scale
	# 
	# interface implementation: function called from an external module
	#

	# add a sub region	
	def addRegion(self, attrdict, name):
		rgn = Region(self, name, self._ctx, attrdict, self._scale)
		return rgn

	# remove a sub region
	def removeRegion(self, region):
		if self._ctx._selected is region:
			region.unselect()
		ind = 0
		for w in self._subwindows:
			if w == region:
				del self._subwindows[ind]
				break
			ind = ind+1
				
	def select(self):
		self._ctx.select(self)


	def unselect(self):
		self._ctx.unselectRequest(self)
	
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
		
	def setImage(self, handle, image, fit):
		print 'setImage on viewport: not implemented yet'

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
		if self._bgcolor:
			dc.FillSolidRect(ltrb,win32mu.RGB(self._bgcolor))

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

	# add a sub region
	def addRegion(self, attrdict, name):
		rgn = Region(self, name, self._ctx, attrdict, self._scale)
		return rgn

	# remove a sub region
	def removeRegion(self, region):
		if self._ctx._selected is region:
			region.unselect()
		ind = 0
		for w in self._subwindows:
			if w == region:
				del self._subwindows[ind]
				break
			ind = ind+1

	def select(self):
		self._ctx.selectRequest(self)

	def unselect(self):
		self._ctx.unselectRequest(self)

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

	def setImage(self, filename, fit):
		if self._active_displist != None:
			self._active_displist.newimage(filename, fit)

	# 
	# end interface implementation
	#


