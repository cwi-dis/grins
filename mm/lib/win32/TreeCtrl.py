__version__ = "$Id$"

import win32ui

import win32con
import commctrl

from win32mu import Win32Msg

from pywin.mfc import window

debug = 0

class TreeCtrl(window.Wnd):
	def __init__ (self):
		window.Wnd.__init__(self, win32ui.CreateTreeCtrl())
		self._selections = []
		self._multiSelListeners = []

	def create(self, parent, rc, id):
		style = win32con.WS_VISIBLE | commctrl.TVS_HASBUTTONS |\
				commctrl.TVS_HASLINES | commctrl.TVS_SHOWSELALWAYS |\
				win32con.WS_BORDER | win32con.WS_TABSTOP\
				 | commctrl.TVS_LINESATROOT  
		self.CreateWindow(style, rc, parent, id)
		self.HookMessage(self.OnLButtonDown, win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.OnLButtonUp, win32con.WM_LBUTTONUP)
		parent.HookNotify(self.OnSelChanged, commctrl.TVN_SELCHANGED)
		self.HookMessage(self.OnDump, win32con.WM_USER+1)

	def createAsDlgItem(self, dlg, id):
		wnd = dlg.GetDlgItem(id)
		rc = wnd.GetWindowRect()
		wnd.DestroyWindow()
		rc = dlg.ScreenToClient(rc)
		self.create(dlg, rc, id)

	def OnLButtonDown(self, params):
		msg = Win32Msg(params)
		point = msg.pos()
		flags = msg._wParam
		self.SetFocus()

		hitflags, hititem = self.HitTest(point)
		if not (hitflags & commctrl.TVHT_ONITEM):
			if debug: self.scheduleDump()
			return 1

		if not (flags & win32con.MK_CONTROL):
			# remove multi-select mode
			nsel = len(self._selections)
			for item in self._selections:
				self.SetItemState(item, 0, commctrl.TVIS_SELECTED)
			self._selections = []
			self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
			if nsel: self.OnMultiSelChanged()

			# do a normal selection/deselection
			return 1
		
		# enter multi-select mode

		# selected item on entry
		try: 
			selitem = self.GetSelectedItem()
			if selitem:
				selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
		except: 
			selitem = None
		nsel = len(self._selections)

		# select/deselect normally hit item the same way base would do
		hitstate = self.GetItemState(hititem, commctrl.TVIS_SELECTED)
		if hitstate & commctrl.TVIS_SELECTED:
			self.SetItemState(hititem, 0, commctrl.TVIS_SELECTED)
			self.removeSelection(hititem)
		else:
			self.SelectItem(hititem)
			self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
			self.appendSelection(hititem)
		
		# restore selection of previously selected item once not the hit item
		if selitem and selitem!=hititem and (selstate & commctrl.TVIS_SELECTED):
			self.SetItemState(selitem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)	
			self.appendSelection(selitem)

		# keep always at least one selection
		if not self._selections:
			self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
			self.appendSelection(hititem)
		
		# motify listeners
		if nsel != len(self._selections):
			self.OnMultiSelChanged()

		# absorb event		
		return 0


	def OnLButtonUp(self, params):
		return 1

	def OnSelChanged(self, std, extra):
		if debug:
			print 'OnSelChanged'
			self.scheduleDump()

	def OnMultiSelChanged(self):
		for listener in self._multiSelListeners:
			listener.OnMultiSelChanged()
		if debug:
			print 'OnMultiSelChanged'
			self.scheduleDump()

	def addMultiSelListener(self, listener):
		if hasattr(listener, 'OnMultiSelChanged') and\
			listener not in self._multiSelListeners:
			self._multiSelListeners.append(listener)

	def removeMultiSelListener(self, listener):
		if listener in self._multiSelListeners:
			self._multiSelListeners.remove(listener)
		
	def OnDump(self, params):
		print self.getSelectedItems()

	def scheduleDump(self):
		self.PostMessage(win32con.WM_USER+1)

	def insertLabel(self, text, parent, after):
		return self.InsertItem(commctrl.TVIF_TEXT, text, 0, 0, 0, 0, None, parent, after)
	
	def appendSelection(self, item):
		if item not in self._selections:
			self._selections.append(item)

	def removeSelection(self, item):
		if item in self._selections:
			self._selections.remove(item)

	def getSelectedItems(self):
		if len(self._selections)>0:
			return self._selections
		try: selected = self.GetSelectedItem()
		except: return []
		return [selected,]

 