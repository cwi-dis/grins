__version__ = "$Id$"

import string
import win32ui, win32con, win32api
from win32modules import cmifex2
from appcon import TRUE,FALSE

from AppForms import Window
import AppMenu

class _Dialog:
	def __init__(self, list, title = '', prompt = None, grab = 1,
		     vertical = 1, del_Callback = None):
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
				length = cmifex2.GetStringLength(w._wnd, label)
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

		cmifex2.ResizeWindow(w._wnd, self._w, self._h)
		self.window.show()
		self._wnd=w._wnd

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
			DestroyMenu(self._menu)
		self._menu = None

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._widget.CreatePopupMenu('dialogMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			list = [title, None] + list
		AppMenu._create_menu(menu, list, toplevel._default_visual,
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



class MainDialog(_Dialog):
	pass

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1, canclose=TRUE):
	w = Window(title, grab = grab, havpar=0)
	options = {'top': None, 'left': None, 'right': None, 'bottom':None}

	constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+ 20
	constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+10
	_w = constant2
	_h = constant
	vbw = 0
	vbh = 0
	hbw = 0
	lbh = 25
	max = 0

	ls = list

	if vertical == 1:
		length = 0
		for item in ls:
			if item:
				label = item[0]
				if label:
					length = cmifex2.GetStringLength(w._wnd,label)
				if length>vbw:
					vbw = length
		vbw = vbw + 30
		max = vbw
		_h = _h + len(ls)*20 + (len(ls)-1)*5
	else:
		length = 0
		for item in ls:
			if item:
				label = item[0]
				if label:
					length = cmifex2.GetStringLength(w._wnd,label)
					hbw = hbw + length + 15
			else:
				hbw = hbw + 15
		max = hbw
		_h = _h + 30

	if prompt:
		ls = string.splitfields(prompt ,'\n')
		maxline = 0;
		for line in ls:
			if (line==None or line==''):
				line=' '
			length = cmifex2.GetStringLength(w._wnd,line)
			if length>maxline:
				maxline = length
		lbh = (len(ls)+1)*15
		_h = _h + lbh
		if max<maxline + 10:
			max = maxline + 10

	_w = _w + max

#	if prompt:
#		l = apply(w.Label, (prompt,), options)
#		options['top'] = l

	options['left'] = 0
	options['top'] = 0
	options['right'] = max
	options['bottom'] = lbh

	if prompt:
		l = apply(w.Label, (prompt,), options)


	options['left'] = 0
	options['top'] = lbh
	options['right'] = max
	options['bottom'] = _h - lbh - constant

	options['vertical'] = vertical
	if grab:
		if canclose:
			options['callback'] = (lambda w: w.close(), (w,))
	b = apply(w.ButtonRow, (list,), options)
	w.buttons = b
	cmifex2.ResizeWindow(w._wnd, _w, _h)
	w.show()
	return w
