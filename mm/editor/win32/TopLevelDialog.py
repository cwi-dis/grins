__version__ = "$Id$"

import windowinterface, Help
import win32api, win32con, cmifex2

class TopLevelDialog:
	def show(self):
		if self.window is not None:
			return
		self.window = w = windowinterface.Window(self.basename,
				deleteCallback = (self.close_callback, ()))
## 				deleteCallback = (self.close_callback, ()), havpar = 0)
		buttons = [('Play', (self.play_callback, ())),
			 # The numbers below correspond with the
			 # positions in the `self.views' list (see
			 # `makeviews' below).
			 ('Player', (self.view_callback, (0,)), 't'),
			 ('Hierarchy view', (self.view_callback, (1,)), 't'),
			 ('Channel view', (self.view_callback, (2,)), 't'),
			 ('Hyperlinks', (self.view_callback, (3,)), 't'),
			 None,
			 ('Save', (self.save_callback, ())),
##			 ('Save for Player', (self.save_player_callback, ())),
			 ('Save as...', (self.saveas_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Close', (self.close_callback, ()))]
		if Help.hashelp():
			buttons.append(None)
			buttons.append(('Help', (self.help_callback, ())))

		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'textwindow'):
			buttons.insert(5, ('View Source...', (self.source_callback, ())))

		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		width = constant2
		height = constant
		butw = 0
		max = 0
		length = 0
		for item in buttons:
			if type item is type(()):
				label = item[0]
				length = cmifex2.GetStringLength(w._hWnd, label)
				if length>max:
					max = length

		butw = max + 60
		width = width + butw
		height = height + (len(buttons)-1)*25



		self.buttons = self.window.ButtonRow(
			buttons,
			top = 0, bottom = height-constant, left = 0, right = butw,
			vertical = 1)

		cmifex2.ResizeWindow(w._hWnd, width, height)
		self.window._hWnd.HookKeyStroke(self.help_callback,104)
		self.window.show()

	def hide(self):
		if self.window is None:
			return
## 		CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
## 		dir = CMIFDIR+"\\Help\\Cmifed.hlp"
## 		win32api.WinHelp(self.window._hWnd.GetSafeHwnd(),dir,win32con.HELP_QUIT,0)
		self.window.close()
		self.window = None

	def setbuttonstate(self, i, showing):
		self.buttons.setbutton(i+1, showing)

	def showsource(self, source):
		if self.source is not None:
			if self.source.is_closed():
				self.source.show()
			return
		self.source = windowinterface.textwindow(source)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'

		reply = cmifex2.MesBox(prompt,"Warning !"," qc")

		if reply == win32con.IDCANCEL:
			cmifex2.SetFlag(1)
			return 2

		if reply == win32con.IDNO:
			self.reply = 1
			return 1

		return 0
