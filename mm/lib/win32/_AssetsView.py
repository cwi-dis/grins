__version__ = "$Id$"

import win32ui, win32con, afxres
import commctrl

import ListCtrl
import components
from win32mu import Win32Msg

import grinsRC

from pywinlib.mfc import docview
import GenView

class _AssetsView(GenView.GenView, docview.ListView):
	def __init__(self, doc, bgcolor=None):
		GenView.GenView.__init__(self, bgcolor)
		docview.ListView.__init__(self, doc)

		# view decor
		self._dlgBar = win32ui.CreateDialogBar()

		# add components 
		self._showAll = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_ALL)
		self._showUnused = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_UNUSED)
		
		self.listCtrl = None

	def OnCreate(self, cs):
		# create dialog bar
		AFX_IDW_DIALOGBAR = 0xE805
		self._dlgBar.CreateWindow(self.GetParent(), grinsRC.IDD_ASSETSBAR, afxres.CBRS_ALIGN_BOTTOM, AFX_IDW_DIALOGBAR)
		
		# attach components
		self._showAll.attach_to_parent()
		self._showUnused.attach_to_parent()

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		self.listCtrl = ListCtrl.ListCtrl(self, self.GetListCtrl())
		
		# redirect all command messages to self.OnCmd
		self.GetParent().HookMessage(self.OnCmd, win32con.WM_COMMAND)
		
		# build demo
		builder = ListCtrlBuilder(self.listCtrl)
		builder.buildDemo()

	def OnCmd(self, params):
		msg = Win32Msg(params)
		code = msg.HIWORD_wParam()
		id = msg.LOWORD_wParam()
		hctrl = msg._lParam
		if id == self._showAll._id and code == win32con.BN_CLICKED:
			self.showAll()
		elif id == self._showUnused._id and code == win32con.BN_CLICKED:
			self.showUnused()
		else:
			print 'OnCmd', id, code

	# temp for dev
	def OnClose(self):
		if 0 and self._closecmdid>0:
			self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND, self._closecmdid)
		else:
			self.GetParent().DestroyWindow()

	def showAll(self):
		print 'showAll'
	
	def showUnused(self):
		print 'showUnused'


class ListCtrlBuilder:
	def __init__(self, listCtrl):
		self.listCtrl = listCtrl

	def buildDemo(self):
		lc = self.listCtrl
		
		# set icons
		normalList = grinsRC.IDI_GRINS_INFO, grinsRC.IDI_GRINS_QUESTION, grinsRC.IDI_GRINS_STOP
		smallList = grinsRC.IDI_GRINS_INFO, grinsRC.IDI_GRINS_QUESTION, grinsRC.IDI_GRINS_STOP
		lc.setIconLists(normalList, smallList)

		# insert columns: (align, width, text) list
		columnsTemplate = [('left', 200, 'column 1'), ('left', 600, 'column 2')]
		lc.insertColumns(columnsTemplate)

		# insert item at row 0
		row, text, imageindex, iteminfo = 0, 'entry 1', 1, ('entry 1 info', )
		lc.inertItem(row, text, imageindex, iteminfo)

		# insert item at row 1
		row, text, imageindex, iteminfo = 1, 'entry 2', 0, ('entry 2 info', )
		lc.inertItem(row, text, imageindex, iteminfo)

		print lc.getItemCount(), 'items in list'


