import math

import afxexttb
import afxres
import commctrl
import win32con
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
import ToolbarTemplate
import settings

# temporary:
SHOW_TOOLBAR_COMBO = 1
ID_TOOLBAR_COMBO = grinsRC._APS_NEXT_COMMAND_VALUE + 1000
TOOLBAR_COMBO_WIDTH = 144
TOOLBAR_COMBO_HEIGHT = 10*18 # drop down height

# Debug
from wndusercmd import TOOLBAR_GENERAL

class ToolbarMixin:

	def __init__(self):
		#
		# Toolbars. Indexed by PyCCmdUI identity, 
		# values are GRiNSToolbar instances.
		#
		self._bars = {}
		#
		# Pulldown adornments. Indexed by pulldown name,
		# values are (valuelist, callback, initialvalue).
		# The callback dict is indexed by combo id, values
		# are (combo, callback)
		self._pulldowndict = {}
		self._pulldowncallbackdict = {}
		#
		for template in ToolbarTemplate.TOOLBARS:
			name, command, barid, resid, buttonlist = template
			cmdid = usercmdui.class2ui[command].id
			self._bars[cmdid] = None

	def _restoreToolbarState(self):
		try:
			self.LoadBarState("GRiNSToolBars")
		except:
			print "_restoreToolbarState: Could not load bar state, setting default"
			for bar in self._bars.values():
				self.ShowControlBar(bar,1,0)
				bar.RedrawWindow()

	def OnClose(self):
		self.SaveBarState("GRiNSToolBars")

	def CreateToolbars(self):
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		for template in ToolbarTemplate.TOOLBARS:
			self._setToolbarFromTemplate(template)
		self._recalcPulldownEnable()
		self._restoreToolbarState()
		self.RecalcLayout()

	def DestroyToolbars(self):
		for bar in self._bars.values():
			bar.DestroyWindow()
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
			self.ShowControlBar(bar,1,0)
			bar.RedrawWindow()
		else:
			self.ShowControlBar(bar,0,0)

	def OnUpdateToolbarCommand(self, cmdui):
		barid = cmdui.m_nID
		bar = self._bars[barid]
		cmdui.Enable(1)
		cmdui.SetCheck(bar.IsWindowVisible())

	def _setToolbarFromTemplate(self, template):
		# First count number of buttons
		name, command, barid, resid, buttonlist = template

		# Create the toolbar
		cmdid = usercmdui.class2ui[command].id
		bar = GRiNSToolbar(self, name, barid, resid, 0)
		self._bars[cmdid] = bar
		self.DockControlBar(bar)

		# Initialize it
		nbuttons = len(buttonlist)
		bar.SetButtons(nbuttons)
		buttonindex = 0
		for button in buttonlist:
			if button.type == 'button':
				id = usercmdui.class2ui[button.cmdid].id
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

	def setToolbarPulldowns(self, pulldowndict):
		self._pulldowndict = pulldowndict
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
		# shortcut for GRiNS private clipboard format
		self.CF_TOOL = Sdk.RegisterClipboardFormat('Tool')
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

	def hookMessages(self):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)

	def onLButtonDown(self, params):
		if self._enableToolDrag:
			msgpos=win32mu.Win32Msg(params).pos()
			self._dragging = msgpos
		return 1 # continue normal processing

	def onLButtonUp(self, params):
		if self._enableToolDrag:
			if self._dragging: 
				self._dragging = None
		return 1 # continue normal processing
	
	def onMouseMove(self, params):
		if self._enableToolDrag and self._dragging:
			xp, yp = self._dragging
			x, y =win32mu.Win32Msg(params).pos()
			if math.fabs(xp-x)>4 or math.fabs(yp-y)>4:
				str='%d %d' % (xp, yp)
				# start drag and drop
				self.DoDragDrop(self.CF_TOOL, str)
				self._dragging = None
				self.ReleaseCapture()
		return 1 # continue normal processing

