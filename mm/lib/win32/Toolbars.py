__version__ = "$Id$"

import math

import afxexttb
import afxres
import commctrl
import win32con
import win32mu
import win32ui
Sdk = win32ui.GetWin32Sdk()
Afx = win32ui.GetAfx()
from pywinlib.mfc import window

import usercmd
import usercmdui
import wndusercmd
import grinsRC
import DropTarget
import ToolbarTemplate
import settings
import features

import win32reg
import ToolbarState

# temporary:
SHOW_TOOLBAR_COMBO = 1
ID_TOOLBAR_COMBO = grinsRC._APS_NEXT_COMMAND_VALUE + 1000
TOOLBAR_COMBO_WIDTH = 144
TOOLBAR_COMBO_HEIGHT = 10*18 # drop down height

# Debug
from wndusercmd import TOOLBAR_GENERAL

# player panel support module
import winplayerdlg

DEFAULT_PLAYER_PANEL_ATTRIBUTES = []

# player panel mixin
class PanelMixin:
	def __init__(self):
		self._pbar = None
		self._pcmdid = usercmdui.usercmd2id(wndusercmd.PLAYER_PANEL)

	# attributes is a list of tuples describing player panel
	# see DEFAULT_PLAYER_PANEL_ATTRIBUTES for an example
	def createPanel(self, attributes=None):
		flag = 0
		if self._pbar:
			flag = self._pbar.IsWindowVisible()
			self.destroy()
		if attributes is None:
			attributes = DEFAULT_PLAYER_PANEL_ATTRIBUTES
		pbar = winplayerdlg.PlayerDlgBar()
		pbar.createWindow(self, attributes)
		self._pbar = pbar
		self.HookCommand(self.OnShowPanelCommand, self._pcmdid)
		self.HookCommandUpdate(self.OnUpdatePanelCommand, self._pcmdid)
		if flag: self._pbar.show()

	def OnShowPanelCommand(self, id, code):
		if id == self._pcmdid:
			flag = self._pbar.IsWindowVisible()
			if flag: self._pbar.hide()
			else: self._pbar.show()
	
	def OnUpdatePanelCommand(self, cmdui):
		if cmdui.m_nID == self._pcmdid:
			cmdui.Enable(1)
			cmdui.SetCheck(self._pbar.IsWindowVisible())
	
	def assertPanelVisible(self):
		if self._pbar:
			if not self._pbar.IsWindowVisible():
				self._pbar.show()

	def destroy(self):
		if self._pbar:
			self._pbar.DestroyWindow()
			self._pbar = None	

	def setOptions(self, optionsdict):
		if not self._pbar: return
		self._pbar.setOptions(optionsdict)

	def update(self):
		if self._pbar:
			self._pbar.eraseClose() 

	def updatePanelCmdUI(self):
		if self._pbar and self._pbar.IsWindowVisible():
			self._pbar.UpdateCmdUI()

# null player panel mixin
class NullPanelMixin:
	def __init__(self):
		self._pbar = None
	def createPanel(self, attributes=None):
		pass
	def destroy(self):
		pass
	def setOptions(self, optionsdict):
		pass
	def update(self):
		pass
	def assertPanelVisible(self):
		pass
	def updatePanelCmdUI(self):
		pass

# do not use player panel for player yet
if not features.editor:
	PanelMixin = NullPanelMixin

##############################
class ToolbarMixin(PanelMixin):

	def __init__(self):
		#
		# Toolbars. Indexed by PyCCmdUI identity, 
		# values are GRiNSToolbar instances.
		#
		self._bars = {}
		PanelMixin.__init__(self)

		#
		# Pulldown adornments. Indexed by pulldown name,
		# values are (valuelist, callback, initialvalue).
		# The callback dict is indexed by combo id, values
		# are (combo, callback)
		self._pulldowndict = {}
		self._pulldowncallbackdict = {}
		#
		for template in ToolbarTemplate.TOOLBARS:
			name, tp, state, command, barid, resid, candrag, buttonlist = template
			cmdid = usercmdui.usercmd2id(command)
			self._bars[cmdid] = None

	def _restoreToolbarState(self, usedefault = 0):
		if self.IsFirstTime() or usedefault:
			win32reg.register(ToolbarState.DefaultState)
##			self.PositionForFirstTime()
##			if self._pbar:
##				self._pbar.show()
##			return
		try:
			self.LoadBarState("GRiNSToolBars")
			PanelMixin.update(self)
		except:
			print "_restoreToolbarState: Could not load bar state, setting default"
##			for bar in self._bars.values():
##				self.ShowControlBar(bar,1,0)
##				bar.RedrawWindow()

	def IsFirstTime(self):
		return win32ui.GetProfileVal('GRiNSToolBars-Summary', 'Bars', -1) == -1

	def PositionForFirstTime(self):
		y = 10000
		for bar in self._bars.values():
			self.DockControlBar(bar, afxres.AFX_IDW_DOCKBAR_TOP)
			self.RecalcLayout()
			y = min(y, bar.GetWindowRect()[1])
		i = 0
		for bar in self._bars.values():
			self.DockControlBar(bar, afxres.AFX_IDW_DOCKBAR_TOP, (i, y, i, y))
			self.RecalcLayout()
			i = i + 1
		self.RecalcLayout()

	def OnClose(self):
		self.SaveBarState("GRiNSToolBars")

	def CreateToolbars(self):
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		self._lastbar = None
		for template in ToolbarTemplate.TOOLBARS:
			self._setToolbarFromTemplate(template)
		PanelMixin.createPanel(self)
		self._lastbar = None
		self._recalcPulldownEnable()
		self._restoreToolbarState()
		self.RecalcLayout()

	def DestroyToolbars(self):
		for bar in self._bars.values():
##			if hasattr(bar,'DestroyWindow'):
##				bar.DestroyWindow()
			bar.destroy()
		self._bars = {}
		self._pulldowndict = {}
		self._pulldowncallbackdict = {}

	def ShowToolbars(self, flag):
		# Show/hide all toolbars. Jack thinks this isn't needed
		# anymore.
		if flag:
			# XXX This is wrong, it shows *all* bars!
			for bar in self._bars.values():
				bar.ShowWindow(win32con.SW_SHOW)
				self.ShowControlBar(bar,1,0)
				bar.RedrawWindow()
			PanelMixin.assertPanelVisible(self)
		else:
			for bar in self._bars.values():
				bar.ShowWindow(win32con.SW_HIDE)

	def OnCreate(self, createStruct):
		for id in self._bars.keys():
			self.HookCommand(self.OnShowToolbarCommand, id)
			self.HookCommandUpdate(self.OnUpdateToolbarCommand, id)

	def OnShowToolbarCommand(self, id, code):
		barid = id
		bar = self._bars[barid]
		flag = not bar.IsWindowVisible()
		if flag:
##			self.ShowControlBar(bar,1,0)
##			bar.RedrawWindow()
			bar.show()
		else:
##			self.ShowControlBar(bar,0,0)
			bar.hide()

	def OnUpdateToolbarCommand(self, cmdui):
		barid = cmdui.m_nID
		bar = self._bars[barid]
		cmdui.Enable(1)
		cmdui.SetCheck(bar.IsWindowVisible())

	def _setToolbarFromTemplate(self, template):
		# First count number of buttons
		name, tp, state, command, barid, resid, candrag, buttonlist = template

		# Create the toolbar
		cmdid = usercmdui.usercmd2id(command)
		if resid<=0: return
		bar = GRiNSToolbar(self, name, barid, resid, candrag)
		self._bars[cmdid] = bar
		self.DockControlBar(bar)
##		self._DockControlBarNextPosition(bar)

		# Initialize it
		nbuttons = len(buttonlist)
		bar.SetButtons(nbuttons)
		buttonindex = 0
		for button in buttonlist:
			if button.type == 'button':
				id = usercmdui.usercmd2id(button.cmdid)
				bar.SetButtonInfo(buttonindex, id,
					afxexttb.TBBS_BUTTON, button.arg)
			elif button.type == 'separator':
				bar.SetButtonInfo(buttonindex, afxexttb.ID_SEPARATOR,
					afxexttb.TBBS_SEPARATOR, button.width)
			elif button.type == 'pulldown':
				self._createPulldown(bar, buttonindex, button.name)
			else:
				raise 'Unknown toolbar item type', button.type
			buttonindex = buttonindex+1
##		self.ShowControlBar(self._bars[barid],1,0)
##		self._bars[barid].RedrawWindow()

	def _DockControlBarNextPosition(self, bar):
		# Dock a control bar in the next position available at the top of
		# the window. This trick obtained from the MSDN toolbar example code.
		if not self._lastbar:
			self.DockControlBar(bar, afxres.AFX_IDW_DOCKBAR_TOP)
			self._lastbar = bar
			return
		self.RecalcLayout()
		l, t, r, b = self._lastbar.GetWindowRect()
		rect = (l+1, t, r+1, b)
		self.DockControlBar(bar, afxres.AFX_IDW_DOCKBAR_TOP, rect)
		self._lastbar = bar

	def setToolbarPulldowns(self, pulldowndict):
		if pulldowndict == self._pulldowndict:
#			print 'It is the same!'
			return
		self._pulldowndict = pulldowndict
		PanelMixin.setOptions(self, pulldowndict)
		self._recalcPulldownEnable()

	def _recalcPulldownEnable(self):
		# Loop over the bars and their pulldowns and set
		# the correct list and enable/disable
		self._pulldowncallbackdict = {}
		for bar in self._bars.values():
			if not bar:
				continue
			for name, pulldown in bar._toolbarCombos.items():
				pulldowninit = self._pulldowndict.get(name, None)
				self._recalcSinglePulldown(pulldown, name, pulldowninit)

	def _recalcSinglePulldown(self, combo, name, init):
		combo.resetcontent()
		if not init:
			# Disable.
			combo.addstring(name)
			combo.setcursel(0)
			combo.enable(0)
		else:
			# Enable.
			values, callback, initvalue = init
			for v in values:
				combo.addstring(v)
			combo.setcursel(values.index(initvalue))
			combo.enable(1)
			id = combo._id
			self._pulldowncallbackdict[id] = (combo, callback)

	def _createPulldown(self, bar, index, name):
		# the return object is a components.ComboBox
		global ID_TOOLBAR_COMBO
		tbcb = self.createToolBarCombo(bar, index, ID_TOOLBAR_COMBO, TOOLBAR_COMBO_WIDTH, TOOLBAR_COMBO_HEIGHT, self.onToolbarCombo)
		ID_TOOLBAR_COMBO = ID_TOOLBAR_COMBO + 1
		bar._toolbarCombos[name] = tbcb
		tbcb.addstring(name)
		tbcb.setcursel(0)
		tbcb.enable(0)

	def createToolBarCombo(self, bar, index, ctrlid, width, ddheight, responseCb=None):
		bar.SetButtonInfo(index, ctrlid, afxexttb.TBBS_SEPARATOR, width)
		l, t, r, b = bar.GetItemRect(index)
		b = b + ddheight
		rc = l, t, r-l, b-t
		import components
		ctrl = components.ComboBox(bar,ctrlid)
		ctrl.create(components.COMBOBOX(), rc)
		if responseCb:
			self.HookCommand(responseCb,ctrlid)
		
		# set combo box font
		lf = {'name':'', 'pitch and family':win32con.FF_SWISS,'charset':win32con.ANSI_CHARSET}
		d = Sdk.EnumFontFamiliesEx(lf)
		logfont = None
		if d.has_key('Tahoma'): # win2k
			logfont = {'name':'Tahoma', 'height': 11, 'weight': win32con.FW_MEDIUM, 'charset':win32con.ANSI_CHARSET}
		elif d.has_key('Microsoft Sans Serif'): # not win2k
			logfont = {'name':'Microsoft Sans Serif', 'height': 11, 'weight': win32con.FW_MEDIUM, 'charset':win32con.ANSI_CHARSET}
		if logfont:
			ctrl.setfont(logfont)

		return ctrl

	def onToolbarCombo(self, id, code):
		if code==win32con.CBN_SELCHANGE:
			tbcb, cb = self._pulldowncallbackdict.get(id, (None, None))
			if not cb or not tbcb:
				print 'No callback for pulldown:', id
				return
			if type(cb) == type(()):
				apply(cb[0], (cb[1], tbcb.getvalue()))
			else:
				cb(tbcb.getvalue())

class GRiNSToolbar(window.Wnd):
	def __init__(self, parent, name, barid, resid, enabledrag):
		CBRS_GRIPPER = 0x00400000   # Missing from afxres.py
		style = (win32con.WS_CHILD |
			win32con.WS_VISIBLE |
			afxres.CBRS_TOP |
			afxres.CBRS_TOOLTIPS|
			afxres.CBRS_FLYBY|
			afxres.CBRS_SIZE_DYNAMIC|
			CBRS_GRIPPER)
		wndToolBar = win32ui.CreateToolBar(parent,style,barid)
		wndToolBar.LoadToolBar(resid)
		wndToolBar.EnableDocking(afxres.CBRS_ALIGN_ANY)
		wndToolBar.SetWindowText(name)
		wndToolBar.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
		window.Wnd.__init__(self,wndToolBar)

		# enable/disable tools draging
		self._enableToolDrag = enabledrag
		if self._enableToolDrag:
			self.hookMessages()
			self._dragging = None
		#
		# Dropdown combos in this toolbar. Indexed by dropdown name
		# (found in ToolbarTemplate and in the windowinterface.newdocument
		# adornments).
		# Values are comboobjects.
		#
		self._toolbarCombos = {}
		self.name = name
		self.parent = parent

	def destroy(self):
		if hasattr(self, 'DestroyWindow'):
			self.DestroyWindow()
		del self.parent

	def show(self):
		self.parent.ShowControlBar(self, 1, 0)
		self.RedrawWindow()

	def hide(self):
		self.parent.ShowControlBar(self, 0, 0)

	def hookMessages(self):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)

	def onLButtonDown(self, params):
		if self._enableToolDrag:
			msgpos=win32mu.Win32Msg(params).pos()
			self._dragging = self._findcommand(msgpos)
			self._dragpos = msgpos
		return 1 # continue normal processing

	def onLButtonUp(self, params):
		if self._enableToolDrag:
			if self._dragging: 
				self._dragging = None
		return 1 # continue normal processing
	
	def onMouseMove(self, params):
		if self._enableToolDrag and self._dragging:
			x, y =win32mu.Win32Msg(params).pos()
			xp, yp = self._dragpos
			if math.fabs(xp-x)>4 or math.fabs(yp-y)>4:
				str=`self._dragging`
				# start drag and drop. Not much use
				# in using DropTarget.EncodeDragData here
				# because it wants the usercmd and we already
				# have the cmdid here.
				self.DoDragDrop(DropTarget.CF_TOOL, str)
				self._dragging = None
				self.ReleaseCapture()
		return 1 # continue normal processing

	def _findcommand(self, (x, y)):
		# Find the usercmd for a given toolbar x/y position
		i = 0
		while 1:
			# First find the item by looping over the rects
			rect = self.GetItemRect(i)
			if rect == (0, 0, 0, 0):
				# Assume this is the last one
				return None
			l, t, r, b = rect
			if l <= x < r and t <= y < b:
				# Found it. Get the windows-command-id
				id = self.GetItemID(i)
				return id
			i = i+1
