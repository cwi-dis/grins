__version__ = "$Id$"

import win32con, win32ui, win32api

import afxres

import components

import grinsRC
import usercmd, usercmdui

from pywinlib.mfc import window

class PlayerDlgBar(window.Wnd):
	iconplay = win32ui.GetApp().LoadIcon(grinsRC.IDI_PLAY)
	iconpause = win32ui.GetApp().LoadIcon(grinsRC.IDI_PAUSE)
	iconstop = win32ui.GetApp().LoadIcon(grinsRC.IDI_STOP)
	BUTTON = 0x0080
	EDIT = 0x0081
	STATIC = 0x0082
	LISTBOX	= 0x0083
	SCROLLBAR = 0x0084
	COMBOBOX = 0x0085
	def __init__(self):
		window.Wnd.__init__(self, win32ui.CreateDialogBar())
		self._parent = None

	def createWindow(self, parent):
		self._parent = parent
		AFX_IDW_DIALOGBAR = 0xE805
		CBRS_GRIPPER = 0x00400000
		self.CreateWindowIndirect(parent, self.makeTemplate(), 
			afxres.CBRS_SIZE_DYNAMIC | CBRS_GRIPPER | afxres.CBRS_FLOAT_MULTI, AFX_IDW_DIALOGBAR)
		self.EnableDocking(afxres.CBRS_ALIGN_ANY);
		parent.EnableDocking(afxres.CBRS_ALIGN_ANY);
		l, t, r, b = parent.GetWindowRect()
		parent.FloatControlBar(self, (l+100, (t+b)/2) )
		self.setButtonIcons()

	# item -> wndClass, text, id, rect, style, exstyle, extraData
	# dialog -> caption, rect, style, exstyle, font, menu, wndClass		
	def makeTemplate(self):
		template = []
		cs = win32con.WS_CHILD | win32con.WS_VISIBLE
		x = 8
		y = 4
		cmdid = usercmdui.usercmd2id

		# row 1
		template.append([self.BUTTON, "Play", cmdid(usercmd.PLAY), (x, y, 12, 12), cs | win32con.BS_ICON])
		template.append([self.BUTTON, "Pause", cmdid(usercmd.PAUSE), (x+16, y, 12, 12), cs | win32con.BS_ICON])
		template.append([self.BUTTON, "Stop", cmdid(usercmd.STOP), (x+32, y, 12, 12), cs | win32con.BS_ICON])
		y = y + 12 + 4

		# row 2
		template.append([self.COMBOBOX, "Bitrate", 101, (x, y, 80, 4*12), cs | win32con.CBS_DROPDOWNLIST | win32con.CBS_SORT | win32con.WS_VSCROLL | win32con.WS_BORDER])
		y = y + 12 + 4

		# row 3
		template.append([self.COMBOBOX, "Language", 102, (x, y, 80, 4*12), cs | win32con.CBS_DROPDOWNLIST | win32con.CBS_SORT | win32con.WS_VSCROLL |win32con.WS_BORDER])
		y = y + 12 + 4

		# row 4
		template.append([self.BUTTON, "Boolean attribute", 111, (x, y, 80, 12), cs | win32con.BS_AUTOCHECKBOX])
		y = y + 12 + 4

		# row 5
		template.append([self.BUTTON, "Boolean attribute", 112, (x, y, 80, 12), cs | win32con.BS_AUTOCHECKBOX])
		y = y + 12 + 4

		dlgStyle = win32con.DS_CONTROL | win32con.WS_CHILD | win32con.DS_SETFONT
		template. insert(0, ["Player controls", (0, 0, 96, y), dlgStyle, None, (8, "MS Sans Serif")])
		return template		


	def setButtonIcons(self):
		cmdid = usercmdui.usercmd2id
		self._bplay = components.Button(self,cmdid(usercmd.PLAY))
		self._bpause = components.Button(self,cmdid(usercmd.PAUSE))
		self._bstop = components.Button(self,cmdid(usercmd.STOP))
		self._bplay.attach_to_parent()
		self._bpause.attach_to_parent()
		self._bstop.attach_to_parent()
		self._bplay.seticon(self.iconplay)
		self._bpause.seticon(self.iconpause)
		self._bstop.seticon(self.iconstop)
		

