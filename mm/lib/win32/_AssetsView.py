__version__ = "$Id$"

import win32ui, win32con, afxres
import commctrl

Sdk = win32ui.GetWin32Sdk()


import ListCtrl
import components
from win32mu import Win32Msg
import longpath

import grinsRC

from pywinlib.mfc import docview
import GenView
import DropTarget
import string

import MMurl

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
	'animation': grinsRC.IDI_ANIMATION,
	'animate': grinsRC.IDI_ANIMATE,
	'brush': grinsRC.IDI_BRUSH,
}

class _AssetsView(GenView.GenView, docview.ListView, DropTarget.DropTargetListener):

	def __init__(self, doc, bgcolor=None):
		GenView.GenView.__init__(self, bgcolor)
		docview.ListView.__init__(self, doc)
		DropTarget.DropTargetListener.__init__(self)
		self._dropmap = {
			'FileName': (self.dragfile, self.dropfile),
			'URL': (self.dragurl, self.dropurl),
		##	'NodeUID': (self.dragnode, self.dropnode),
		}

		# view decor
		self._dlgBar = win32ui.CreateDialogBar()

		# add components 
		self._showAll = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_ALL)
		self._showTemplate = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_TEMPLATE)
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
		self._showTemplate.attach_to_parent()
		self._showClipboard.attach_to_parent()

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		self.listCtrl = ListCtrl.ListCtrl(self, self.GetListCtrl())
		
		# redirect all command messages to self.OnCmd
		self.GetParent().HookMessage(self.OnCmd, win32con.WM_COMMAND)
		
		self.rebuildList()
		self.registerDropTargetFor(self.listCtrl)
		# XXXX There is no cleanup method!

	def OnCmd(self, params):
		msg = Win32Msg(params)
		code = msg.HIWORD_wParam()
		id = msg.LOWORD_wParam()
		hctrl = msg._lParam
		if id == self._showAll._id and code == win32con.BN_CLICKED:
			self.showAll()
		elif id == self._showTemplate._id and code == win32con.BN_CLICKED:
			self.showTemplate()
		elif id == self._showClipboard._id and code == win32con.BN_CLICKED:
			self.showClipboard()
		else:
			print 'OnCmd', id, code

	def showAll(self):
		cb = self._cmddict['setview']
		cb('all')
	
	def showTemplate(self):
		cb = self._cmddict['setview']
		cb('template')

	def showClipboard(self):
		cb = self._cmddict['setview']
		cb('clipboard')

	def setView(self, which):
		self._showAll.setcheck(which == 'all')
		self._showTemplate.setcheck(which == 'template')
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
				print '_AssetsView: no icon for', imagename
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
		return cb(cursel)

	def doDragDrop(self, type, value):
		if type == 'URL':
			rv = self.listCtrl.DoDragDrop(DropTarget.CF_URL, value)
		elif type == 'node':
			value = string.join(value, ',')
			rv = self.listCtrl.DoDragDrop(DropTarget.CF_NODEUID, value)
		else:
			print 'Unknown assetview dragtype', type
			rv = None
		return rv

	#
	# drag/drop destination code
	#

	def dragfile(self,dataobj,kbdstate,x,y):
		cb = self._cmddict.get('dragurl')
		if not cb:
			return 0
		filename=dataobj.GetGlobalData(DropTarget.CF_FILE)
		filename=longpath.short2longpath(filename)
		if not filename:
			return 0
		url = MMurl.pathname2url(filename)
		rv = cb(x, y, url)
		rrv = self._string2drageffect(rv)
		return rrv

	def dropfile(self,dataobj,effect,x,y):
		cb = self._cmddict.get('dropurl')
		if not cb:
			return 0
		filename=dataobj.GetGlobalData(DropTarget.CF_FILE)
		filename=longpath.short2longpath(filename)
		if not filename:
			return 0
		url = MMurl.pathname2url(filename)
		rv = cb(x, y, url)
		return self._string2drageffect(rv)

	def dragurl(self,dataobj,kbdstate,x,y):
		cb = self._cmddict.get('dragurl')
		if not cb:
			return 0
		url = dataobj.GetGlobalData(DropTarget.CF_URL)
		if not url:
			return 0
		rv = cb(x, y, url)
		return self._string2drageffect(rv)

	def dropurl(self,dataobj,effect,x,y):
		cb = self._cmddict.get('dropurl')
		if not cb:
			return 0
		url = dataobj.GetGlobalData(DropTarget.CF_URL)
		if not url:
			return 0
		rv = cb(x, y, url)
		return self._string2drageffect(rv)

	def _string2drageffect(self, str):
		if str == 'move':
			return DropTarget.DROPEFFECT_MOVE
		elif str == 'copy':
			return DropTarget.DROPEFFECT_COPY
		elif str == 'link':
			return DropTarget.DROPEFFECT_LINK
		if str != None:
			print 'Unknown drageffect', str
		return 0