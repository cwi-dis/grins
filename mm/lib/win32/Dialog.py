__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2

from AppForms import Window


class Dialog:
	def __init__(self, list, title = '', prompt = None, grab = 1,
		     vertical = 1, del_Callback = None, parent = None):
		if not title:
			title = ''
		
		if del_Callback == None :
			del_Callback = (self.close, ())

		self.window = w = Window(title,
				deleteCallback = del_Callback, havpar = 0)
		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = constant2
		self._h = constant
		butw = 0
		max = 0
		ls = []
		for item in list :
			if item is None:
				continue
			else :
				ls.append(item[0])
		
		length = 0
		for item in ls:
			label = item
			if label:
				length = cmifex2.GetStringLength(w._hWnd, label)
				if length>max:
					max = length

		butw = max + 60
		self._w = self._w + butw
		self._h = self._h + len(ls)*25+10	

		buttons = list
		
		self._buttons = self.window.ButtonRow(
			buttons,
			top = 0, bottom = self._h-constant, left = 0, right = butw,
			vertical = 1)

		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.window.show()
		self._widget = w
		self._menu = None

	# destruction
	def _destroy(self, widget, client_data, call_data):
		self._widget = None
		self._menu = None
		self._buttons = []

	def close(self):
		w = self._widget
		w.close()
		self._widget = None

	# pop up menu
	def destroy_menu(self):
		if self._menu:
			cmifex2.DestroyMenu(self._menu)
		self._menu = None

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._widget.CreatePopupMenu('dialogMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			list = [title, None] + list
		_create_menu(menu, list, toplevel._default_visual,
			     toplevel._default_colormap)
		self._menu = menu
		self._widget.AddEventHandler(X.ButtonPressMask, FALSE,
					     self._post_menu, None)

	def _post_menu(self, widget, client_data, call_data):
		if not self._menu:
			return
		if call_data.button == X.Button3:
			self._menu.MenuPosition(call_data)
			self._menu.ManageChild()

	# buttons
	def _callback(self, widget, callback, call_data):
		if callback:
			apply(callback[0], callback[1])

	def getbutton(self, button):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		return self._buttons[button].set

	def setbutton(self, button, onoff = 1):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		self._buttons[button].set = onoff


class MainDialog(Dialog):
	print "MainDialog"
	pass
