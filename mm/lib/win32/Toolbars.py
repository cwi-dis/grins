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

# temporary:
SHOW_TOOLBAR_COMBO = 1
ID_TOOLBAR_COMBO = grinsRC._APS_NEXT_COMMAND_VALUE + 1000
TOOLBAR_COMBO_WIDTH = 144
TOOLBAR_COMBO_HEIGHT = 10*18 # drop down height

# Debug
from wndusercmd import TOOLBAR_GENERAL

class ToolbarMixin:

	def __init__(self):
		self.__bars = {}
		for template in ToolbarTemplate.TOOLBARS:
			name, command, resid, buttonlist = template
			barid = usercmdui.class2ui[command].id
			self.__bars[barid] = None

	def CreateToolbars(self):
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		barid = usercmdui.class2ui[TOOLBAR_GENERAL].id

		self.__bars[barid]=GRiNSToolbar(self)
		self.DockControlBar(self.__bars[barid])
		if 0:
			self.setPlayerToolbar()
			self.LoadAccelTable(grinsRC.IDR_GRINS)
		else:
			self.setEditorFrameToolbar()
			self.LoadAccelTable(grinsRC.IDR_GRINSED)

	def DestroyToolbars(self):
		for bar in self.__bars.values():
			bar.DestroyWindow()
		self.__bars = {}

	def ShowToolbars(self, flag):
		# Show/hide all toolbars. Jack thinks this isn't needed
		# anymore.
		if flag:
			# XXX This is wrong, it shows *all* bars!
			for bar in self.__bars.values():
				bar.ShowWindow(win32con.SW_SHOW)
				self.ShowControlBar(bar,1,0)
				bar.RedrawWindow()
		else:
			for bar in self.__bars.values():
				bar.ShowWindow(win32con.SW_HIDE)

	def OnCreate(self, createStruct):
		for id in self.__bars.keys():
			self.HookCommand(self.OnShowToolbarCommand, id)
			self.HookCommandUpdate(self.OnUpdateToolbarCommand, id)

	def OnShowToolbarCommand(self, id, code):
		barid = id
		bar = self.__bars[barid]
		flag = not bar.IsWindowVisible()
		if flag:
			self.ShowControlBar(bar,1,0)
			bar.RedrawWindow()
		else:
			self.ShowControlBar(bar,0,0)

	def OnUpdateToolbarCommand(self, cmdui):
		barid = cmdui.m_nID
		bar = self.__bars[barid]
		cmdui.Enable(1)
		cmdui.SetCheck(bar.IsWindowVisible())

	def _setToolbarFromTemplate(self, template):
		# First count number of buttons
		name, command, resid, buttonlist = template
		barid = usercmdui.class2ui[command].id
		bar = self.__bars[barid]
		nbuttons = len(buttonlist)
		if buttonlist and buttonlist[-1].type == 'pulldown':
			nbuttons = nbuttons - 1
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
				pass
			else:
				raise 'Unknown toolbar item type', button.type
			buttonindex = buttonindex+1
		return nbuttons

			
	# Set the editor toolbar to the state without a document
	def setEditorFrameToolbar(self):
		self._setToolbarFromTemplate(ToolbarTemplate.FRAME_TEMPLATE)
		barid = usercmdui.class2ui[TOOLBAR_GENERAL].id
		self.ShowControlBar(self.__bars[barid],1,0)
		self.__bars[barid].RedrawWindow()


	# Set the editor toolbar to the state with a document
	def setEditorDocumentToolbar(self, adornments):
		num_buttons = self._setToolbarFromTemplate(ToolbarTemplate.GENERAL_TEMPLATE)
		barid = usercmdui.class2ui[TOOLBAR_GENERAL].id
		bar = self.__bars[barid]
		if adornments.has_key('pulldown'):
			index = num_buttons
			for list, cb, init in adornments['pulldown']:
				bar.SetButtonInfo(index,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12)
				index = index + 1
				# the return object is a components.ComboBox
				global ID_TOOLBAR_COMBO
				tbcb = self.createToolBarCombo(bar, index, ID_TOOLBAR_COMBO, TOOLBAR_COMBO_WIDTH, TOOLBAR_COMBO_HEIGHT, self.onToolbarCombo)
				ID_TOOLBAR_COMBO = ID_TOOLBAR_COMBO + 1
				index = index + 1
				self._toolbarCombo.append((tbcb, cb))
				for str in list:
					tbcb.addstring(str)
				tbcb.setcursel(list.index(init))

		self.ShowControlBar(bar,1,0)


	# Set the player toolbar
	def setPlayerToolbar(self):
		self._setToolbarFromTemplate(ToolbarTemplate.PLAYER_TEMPLATE)
		barid = usercmdui.class2ui[TOOLBAR_GENERAL].id
		self.ShowControlBar(self.__bars[barid],1,0)


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
			for tbcb, cb in self._toolbarCombo:
				if tbcb._id == id:
					cb(tbcb.getvalue())
					return

class GRiNSToolbar(window.Wnd):
	def __init__(self, parent):
		style = win32con.WS_CHILD |\
			win32con.WS_VISIBLE |\
			afxres.CBRS_TOP |\
			afxres.CBRS_TOOLTIPS|\
			afxres.CBRS_FLYBY|\
			afxres.CBRS_SIZE_DYNAMIC
		wndToolBar = win32ui.CreateToolBar(parent,style,afxres.AFX_IDW_TOOLBAR)
		wndToolBar.LoadToolBar(grinsRC.IDR_GRINSED)
		wndToolBar.EnableDocking(afxres.CBRS_ALIGN_ANY)
		wndToolBar.SetWindowText("General")
		wndToolBar.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
		window.Wnd.__init__(self,wndToolBar)

		# enable/dissable tools draging
		self._enableToolDrag = 1
		# shortcut for GRiNS private clipboard format
		self.CF_TOOL = Sdk.RegisterClipboardFormat('Tool')
		if self._enableToolDrag:
			self.hookMessages()
			self._dragging = None

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

