__version__ = "$Id$"

import win32ui, win32con, afxres
import commctrl

Sdk = win32ui.GetWin32Sdk()


import ListCtrl
import components
from win32mu import Win32Msg

import grinsRC

from pywinlib.mfc import docview
import GenView

ICONNAME_TO_RESID={
	None: grinsRC.IDI_ICON_ASSET_BLANK,
	'ref': grinsRC.IDI_ICON_ASSET_BLANK,
	'text': grinsRC.IDI_ICON_ASSET_TEXT,
	'image': grinsRC.IDI_ICON_ASSET_IMAGE,
	'video': grinsRC.IDI_ICON_ASSET_VIDEO,
	'audio': grinsRC.IDI_ICON_ASSET_AUDIO,
	'html': grinsRC.IDI_ICON_ASSET_TEXT,
##	'node': grinsRC.IDI_ICON_NODE,
	'imm': grinsRC.IDI_ICON_NODE,
	'ext': grinsRC.IDI_ICON_NODE,
	'par': grinsRC.IDI_ICON_PAROPEN,
	'seq': grinsRC.IDI_ICON_SEQOPEN,
	'excl': grinsRC.IDI_ICON_EXCLOPEN,
	'switch': grinsRC.IDI_ICON_SWITCHOPEN,
	'prio': grinsRC.IDI_ICON_PRIOOPEN,
	'properties': grinsRC.IDI_PROPERTIES,
	'viewport': grinsRC.IDI_VIEWPORT,
	'region': grinsRC.IDI_REGION,
}

class _AssetsView(GenView.GenView, docview.ListView):
	CF_URL = Sdk.RegisterClipboardFormat('URL')

	def __init__(self, doc, bgcolor=None):
		GenView.GenView.__init__(self, bgcolor)
		docview.ListView.__init__(self, doc)

		# view decor
		self._dlgBar = win32ui.CreateDialogBar()

		# add components 
		self._showAll = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_ALL)
		self._showUnused = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_UNUSED)
		self._showClipboard = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_CLIPBOARD)
		
		self.listCtrl = None
		self.initicons()
		self.columnsTemplate = []
		self.items = []

	def initicons(self):
		self.iconlist_small = []
		self.iconname_to_index = {}
		for k, v in ICONNAME_TO_RESID.items():
			if v is None:
				self.iconname_to_index[k] = None
				continue
			if not v in self.iconlist_small:
				self.iconlist_small.append(v)
			self.iconname_to_index[k] = self.iconlist_small.index(v)

	# Sets the acceptable commands. 
	def set_cmddict(self,cmddict):
		self._cmddict=cmddict

	def OnCreate(self, cs):
		# create dialog bar
		AFX_IDW_DIALOGBAR = 0xE805
		self._dlgBar.CreateWindow(self.GetParent(), grinsRC.IDD_ASSETSBAR, afxres.CBRS_ALIGN_BOTTOM, AFX_IDW_DIALOGBAR)
		
		# attach components
		self._showAll.attach_to_parent()
		self._showUnused.attach_to_parent()
		self._showClipboard.attach_to_parent()

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		self.listCtrl = ListCtrl.ListCtrl(self, self.GetListCtrl())
		
		# redirect all command messages to self.OnCmd
		self.GetParent().HookMessage(self.OnCmd, win32con.WM_COMMAND)
		
		self.rebuildList()

	def OnCmd(self, params):
		msg = Win32Msg(params)
		code = msg.HIWORD_wParam()
		id = msg.LOWORD_wParam()
		hctrl = msg._lParam
		if id == self._showAll._id and code == win32con.BN_CLICKED:
			self.showAll()
		elif id == self._showUnused._id and code == win32con.BN_CLICKED:
			self.showUnused()
		elif id == self._showClipboard._id and code == win32con.BN_CLICKED:
			self.showClipboard()
		else:
			print 'OnCmd', id, code

	def showAll(self):
		cb = self._cmddict['setview']
		cb('all')
	
	def showUnused(self):
		cb = self._cmddict['setview']
		cb('unused')

	def showClipboard(self):
		cb = self._cmddict['setview']
		cb('clipboard')

	def setView(self, which):
		self._showAll.setcheck(which == 'all')
		self._showUnused.setcheck(which == 'unused')
		self._showClipboard.setcheck(which == 'clipboard')

	def rebuildList(self):
		lc = self.listCtrl
		if not lc: return
		
		# set icons
		lc.setIconLists(self.iconlist_small, self.iconlist_small)

		# insert columns: (align, width, text) list
		lc.deleteAllColumns()
		lc.insertColumns(self.columnsTemplate)

		lc.removeAll()

		row = 0
		for item in self.items:
			imagename = item[0]
			imageindex = self.iconname_to_index.get(imagename)
			if imageindex is None:
				imageindex = -1 # XXXX
			text = item[1]
			iteminfo = item[2:]
			lc.insertItem(row, text, imageindex, iteminfo)
			row = row + 1

	def setColumns(self, columnlist):
		self.columnsTemplate = columnlist

	def setItems(self, items):
		self.items = items

	def getSelected(self):
		if not self.listCtrl:
			return -1
		return self.listCtrl.getSelected()

	# Called by the listCtrl code when it wants to start
	# a drag. If the current focus is draggable start the
	# drag and return 1.
	def startDrag(self):
		cursel = self.listCtrl.getSelected()
		if cursel < 0:
			return 0
		cb = self._cmddict.get('startdrag')
		if not cb:
			return 0
		type, value = cb(cursel)
		if not type:
			return 0
		if type == 'URL':
			self.listCtrl.DoDragDrop(self.CF_URL, value)
			return 1
		print 'Unknown assetview dragtype', type
		return 0
