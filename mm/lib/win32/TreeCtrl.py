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

	def create(self, parent, rc, id):
		style = win32con.WS_VISIBLE | commctrl.TVS_HASBUTTONS |\
				commctrl.TVS_HASLINES | commctrl.TVS_SHOWSELALWAYS |\
				win32con.WS_BORDER | win32con.WS_TABSTOP\
				# | commctrl.TVS_LINESATROOT  
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

		# what base tree considers as selected
		try: selected = self.GetSelectedItem()
		except: selected = None

		hitflags, hititem = self.HitTest(point)
		if not (hitflags & commctrl.TVHT_ONITEM):
			if debug: self.scheduleDump()
			return 1

		if not (flags & win32con.MK_CONTROL):
			# deselect all
			for item in self._selections:
				self.SetItemState(item, 0, commctrl.TVIS_SELECTED)
			self._selections = []
			# do a normal selection/deselection
			if debug: self.scheduleDump()
			return 1

		# enter multi-select mode
		if self._selections:
			self.SelectItem(0)
			
		if selected and selected not in self._selections:
			self._selections.append(selected)
		
		state = self.GetItemState(hititem, commctrl.TVIS_SELECTED)
		if not (state & commctrl.TVIS_SELECTED):
			# not selected, so do select it
			self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
			if hititem not in self._selections:
				self._selections.append(hititem)
		else:
			# its selected, so deselect it
			self.SetItemState(hititem, 0, commctrl.TVIS_SELECTED)
			if hititem in self._selections:
				self._selections.remove(hititem)
		if debug: self.scheduleDump()
		return 0

	def OnLButtonUp(self, params):
		return 1

	def OnSelChanged(self, std, extra):
		if debug:
			print 'OnSelChanged'
			self.scheduleDump()

	def OnDump(self, params):
		print self.GetSelectedItems()

	def scheduleDump(self):
		self.PostMessage(win32con.WM_USER+1)

	def insertLabel(self, text, parent, after):
		return self.InsertItem(commctrl.TVIF_TEXT, text, 0, 0, 0, 0, None, parent, after)
		
	def GetSelectedItems(self):
		if len(self._selections)>0:
			return self._selections
		try: selected = self.GetSelectedItem()
		except: return []
		return [selected,]

