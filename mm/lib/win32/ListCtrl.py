__version__ = "$Id$"

import win32ui

import win32con
import commctrl

import win32mu

from pywinlib.mfc import window

class ListCtrl(window.Wnd):
	def __init__ (self, dlg=None, ctrl=None, resId=None):
		self.parent = dlg
		if not ctrl:
			if resId != None:
				ctrl = dlg.GetDlgItem(resId)
			else:
				ctrl = win32ui.CreateListCtrl()
		else:
			ctrl.SetWindowLong(win32con.GWL_STYLE, self.getStyle())
		window.Wnd.__init__(self, ctrl)
		self.hookMessages()
		self.popup = None
		self.selected = -1

	def getStyle(self):
		style = win32con.WS_VISIBLE | win32con.WS_CHILD\
				| commctrl.LVS_REPORT | commctrl.LVS_SHAREIMAGELISTS\
				| win32con.WS_BORDER | win32con.WS_TABSTOP
		return style

	# create a new ListCtrl instance
	def create(self, parent, rc, id):
		self.parent = parent
		self.CreateWindow(self.getStyle(), rc, parent, id)
		self.hookMessages()
		
	# create a new ListCtrl instance replacing a placeholder
	def createAsDlgItem(self, dlg, id):
		wnd = dlg.GetDlgItem(id)
		rc = wnd.GetWindowRect()
		wnd.DestroyWindow()
		rc = dlg.ScreenToClient(rc)
		self.create(dlg, rc, id)

	def hookMessages(self):
		self.HookMessage(self.OnLButtonDown, win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.OnLButtonUp, win32con.WM_LBUTTONUP)
		self.HookMessage(self.OnKeyDown, win32con.WM_KEYDOWN)

		# list notifications
		self.GetParent().HookNotify(self.OnItemChanged, commctrl.LVN_ITEMCHANGED)

		# popup menu
		self.HookMessage(self.OnRButtonDown, win32con.WM_RBUTTONDOWN)
		self.GetParent().HookMessage(self.OnCommand,win32con.WM_COMMAND)

	#
	# response to hooked windows messages
	#
	def OnLButtonDown(self, params):
		msg = win32mu.Win32Msg(params)
		point = msg.pos()
		flags = msg._wParam
		return 1

	def OnLButtonUp(self, params):
		return 1

	def OnRButtonDown(self, params):		
		msg = win32mu.Win32Msg(params)
		point = msg.pos()
		flags = msg._wParam
		point = self.ClientToScreen(point)
		flags = win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_LEFTBUTTON
		if self.popup:
			self.popup.TrackPopupMenu(point, flags, self.GetParent())

	# simulate dialog tab
	def OnKeyDown(self, params):
		key = params[2]
		if key == win32con.VK_TAB: 
			self.parent.SetFocus() 

	def OnDestroy(self, params):
		if self.popup:
			self.popup.DestroyMenu()

	def OnItemChanged(self, std, extra):
		nmsg = win32mu.Win32NotifyMsg( std, extra, 'list')
		if nmsg.state & commctrl.LVIS_SELECTED:
			self.selected = nmsg.row
			print 'selection: row', nmsg.row, `self.GetItemText(nmsg.row,0)`
		else:
			self.selected = -1
			print 'selection: None'

	#
	#  command responses
	#
	# delegate to what GRiNS thinks as the view
	def OnCommand(self, params):
		msg = win32mu.Win32Msg(params)
		self.getView().onUserCmd(msg.cmdid())

	#
	#  popup menu
	#
 	def setpopup(self, menutemplate):
		import win32menu, usercmdui
		popup = win32menu.Menu('popup')
		popup.create_popup_from_menubar_spec_list(menutemplate, usercmdui.usercmd2id)
		if self.popup:
			self.popup.DestroyMenu()
		self.popup = popup
	
	# return what GRiNS thinks as the view for command delegation
	def getView(self):
		return self.parent

	#
	#  ListCtrl management
	#
	def setStyle(self, stylelist, on=1):
		flag = 0
		for what in stylelist:
			if what == 'singlesel':
				flag = flag | commctrl.LVS_SINGLESEL
			elif what == 'editlabels':
				flag = flag | commctrl.LVS_EDITLABELS
			elif what == 'autoarrange':
				flag = flag | commctrl.LVS_AUTOARRANGE
			elif what == 'sortascending':
				flag = flag | commctrl.LVS_SORTASCENDING
			elif what == 'sortascending':
				flag = flag | commctrl.LVS_SORTASCENDING
			elif what == 'showselalways':
				flag = flag | commctrl.LVS_SHOWSELALWAYS
			elif what == 'nolabelwrap':
				flag = flag | commctrl.LVS_NOLABELWRAP
			elif what == 'nocolumnheader':
				flag = flag | commctrl.LVS_NOCOLUMNHEADER
			elif what == 'nosortheader':
				flag = flag | commctrl.LVS_NOSORTHEADER
			elif what == 'shareimagelists':
				flag = flag | commctrl.LVS_SHAREIMAGELISTS
			else:
				print 'uknown style', what
		if flag:
			style = self.GetWindowLong(win32con.GWL_STYLE)
			style = style & ~flag
			if on:
				style = style | flag
			self.SetWindowLong(win32con.GWL_STYLE, style)
			self.RedrawWindow()

	def setMode(self, what):
		if what == 'icon':
			flag = commctrl.LVS_ICON
		elif what == 'smallicon':
			flag = commctrl.LVS_SMALLICON
		elif what == 'report':
			flag = commctrl.LVS_REPORT
		else:
			flag = commctrl.LVS_LIST
		style = self.GetWindowLong(win32con.GWL_STYLE)
		style = style & ~commctrl.LVS_TYPEMASK
		style = style | flag
		self.SetWindowLong(win32con.GWL_STYLE, style)
		self.RedrawWindow()

	# normal = (grinsRC.IDI_N1, grinsRC.IDI_N2, )
	# small = (grinsRC.IDI_L1, grinsRC.IDI_S2, )
	def setIconLists(self, normalList, smallList):
		app = win32ui.GetApp()
		mask = 0

		# normal icons image list
		if normalList:
			initcount = len(normalList)
			growby = initcount
			normalImageList = win32ui.CreateImageList(32, 32, mask, initcount, growby)
			normalImageList.SetBkColor(win32mu.RGB((255,255,255)))
			# populate normal image list
			for id in normalList:
				normalImageList.Add(app.LoadIcon(id))
		
		# smal icons image list
		if smallList:
			initcount = len(smallList)
			growby = initcount
			smallImageList = win32ui.CreateImageList(16, 16, mask, initcount, growby)
			smallImageList.SetBkColor(win32mu.RGB((255,255,255)))
			# populate small image list
			for id in normalList:
				smallImageList.Add(app.LoadIcon(id))

		# finally set image list
		if normalList:
			self.SetImageList(normalImageList, commctrl.LVSIL_NORMAL)
		if smallList:
			self.SetImageList(smallImageList, commctrl.LVSIL_SMALL)

	def insertColumns(self, template):
		fmtflags = {'left':commctrl.LVCFMT_LEFT, 'center':commctrl.LVCFMT_CENTER, 'right':commctrl.LVCFMT_RIGHT}
		index = 0
		for align, width, text in template:
			fmtflag = fmtflags.get(align)
			if fmtflag is None: 
				fmtflag = LVCFMT_LEFT
			self.InsertColumn(index, (fmtflag, width, text, 0))
			index = index + 1

	def deleteAllColumns(self):
		# There must be a better way to do this, but we don't seem to
		# have GetHeaderCtrl() in Python
		try:
			while 1:
				self.DeleteColumn(0)
		except win32ui.error:
			pass

	def insertItem(self, row, text, imageindex, iteminfo):
		self.InsertItem(row, text, imageindex)
		subindex = 1
		for text in iteminfo:
			self.SetItemText(row, subindex, text)
			subindex = subindex + 1

	def removeAll(self):
		self.DeleteAllItems()
	
	def removeItem(self, row):
		self.DeleteItem(row)

	def getItemCount(self):
		return self.GetItemCount()

	def selectItem(self, row):
		self.SetItemState(row, commctrl.LVIS_SELECTED | commctrl.LVIS_FOCUSED, commctrl.LVIS_SELECTED | commctrl.LVIS_FOCUSED)
	
	def deselectItem(self, row):
		self.SetItemState(row, commctrl.LVIS_SELECTED | commctrl.LVIS_FOCUSED, 0)

	def isItemSelected(self, row):
		return self.GetItemState(row, commctrl.LVIS_SELECTED) & commctrl.LVIS_SELECTED

	def findSelected(self):
		n = self.GetItemCount()
		for row in range(n):
			if self.GetItemState(row, commctrl.LVIS_SELECTED) & commctrl.LVIS_SELECTED:
				return row
		return -1

	def getSelected(self):
		if self.selected < 0:
			return -1
		# assert
		if self.isItemSelected(self.selected):
			return self.selected
		return -1



