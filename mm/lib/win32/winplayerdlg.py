__version__ = "$Id$"

import win32con, win32ui, win32api

import afxres

import components

import grinsRC
import usercmd, usercmdui

from pywinlib.mfc import window

DEFAULT_PLAYER_ATTRIBUTES = [ ('option','Bitrate'),
	('option', 'Language'),
	('boolean', 'boolean attribute 1'),
	('boolean', 'boolean attribute 2'),]

class ResItem:
	classid = 0x0082
	style = win32con.WS_CHILD | win32con.WS_VISIBLE
	def __init__(self, name, width, height):
		self.name = name
		self.width = width
		self.height = height
		self.id = 0
	def getResourceList(self, x, y):
		return [self.classid, self.name, self.id, (x, y, self.width, self.height), self.style]
	
class Option(ResItem):
	classid = 0x0085
	style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.CBS_DROPDOWNLIST | win32con.CBS_SORT | win32con.WS_VSCROLL | win32con.WS_BORDER
	def __init__(self, name, width=80, height=12):
		ResItem.__init__(self, name, width, height)
	def getResourceList(self, x, y):
		return [self.classid, self.name, self.id, (x, y, self.width, 48), self.style]

class Boolean(ResItem):
	classid = 0x0080
	style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_AUTOCHECKBOX
	def __init__(self, name, width=80, height=12):
		ResItem.__init__(self, name, width, height)

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
		self._resitems = []
		self._ctrls = {}

	def createWindow(self, parent, attributes = DEFAULT_PLAYER_ATTRIBUTES):
		self._parent = parent
		self.createResourceItems(attributes)
		AFX_IDW_DIALOGBAR = 0xE805
		CBRS_GRIPPER = 0x00400000
		self.CreateWindowIndirect(parent, self.makeTemplate(), 
			afxres.CBRS_SIZE_DYNAMIC | CBRS_GRIPPER | afxres.CBRS_FLOAT_MULTI, AFX_IDW_DIALOGBAR)
		self.EnableDocking(afxres.CBRS_ALIGN_ANY);
		parent.EnableDocking(afxres.CBRS_ALIGN_ANY);
		l, t, r, b = parent.GetWindowRect()
		parent.FloatControlBar(self, (l+100, (t+b)/2) )
		self.setButtonIcons()
		self.createComponents()
		self.hookCommands()

	def createResourceItems(self, attributes):
		id = 1
		for attr in attributes:
			attrtype, name = attr
			resitem = None
			if attrtype == 'option':
				resitem = Option(name)
			elif attrtype == 'boolean':
				resitem = Boolean(name)
			if resitem:
				resitem.id = id
				self._resitems.append(resitem)
				id = id + 1
		
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

		maxWidth = 0
		for item in self._resitems:
			template.append(item.getResourceList(x, y))
			y = y + item.height + 4
			if item.width > maxWidth: maxWidth = item.width
					
		dlgStyle = win32con.DS_CONTROL | win32con.WS_CHILD | win32con.DS_SETFONT
		template. insert(0, ["Player control panel", (0, 0, maxWidth+16, y), dlgStyle, None, (8, "MS Sans Serif")])
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
		
	def createComponents(self):
		for item in self._resitems:
			if isinstance(item, Option):
				self._ctrls[item.name] = components.ComboBox(self, item.id)
			elif isinstance(item, Boolean):
				self._ctrls[item.name] = components.CheckButton(self, item.id)
		for ctrl in self._ctrls.values():
			ctrl.attach_to_parent()

	def hookCommands(self):
		for ctrl in self._ctrls.values():
			if isinstance(ctrl, components.ComboBox):
				self._parent.HookCommand(self.onCombo, ctrl.getId())
			elif isinstance(ctrl, components.CheckButton):
				self._parent.HookCommand(self.onCheck, ctrl.getId())

	def onCombo(self, id, code):
		if code == win32con.CBN_SELCHANGE:
			print 'onCombo', id	
				
	def onCheck(self, id, code):
		if code==win32con.BN_CLICKED:
			print 'onCheck', id		
