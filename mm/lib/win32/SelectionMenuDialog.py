__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2

class SelectionMenuDialog:
	def __init__(self, listprompt, selectionprompt, itemlist, default, parent=None):
		attrs = {'textString': default}
		if hasattr(self, 'NomatchCallback'):
			attrs['mustMatch'] = TRUE
		if listprompt:
			attrs['listLabelString'] = listprompt
		if selectionprompt:
			attrs['selectionLabelString'] = selectionprompt
		print attrs
	
		self._menuselection = None

		self._menuid = None;

		self._menus = {}

		if default:
			itemlist.append(default)

		menu, menuid = cmifex2.GetMenu(parent)
			
		if menu == 0:
			menu = cmifex2.CreateMenu()
			
		self._menus[menuid] = itemlist

		submenu = cmifex2.CreateMenu()
			
		for item in itemlist:
			cmifex2.AppendMenu(submenu, item, -1)
			
		if not listprompt:
			listprompt = "Selection"
			
		cmifex2.PopupAppendMenu(menu, submenu, listprompt)
		cmifex2.SetMenu(parent,menu)
		parent.HookMessage(self._menu2_callback, win32con.WM_INITMENUPOPUP)
		parent.HookMessage(self._menu_callback, win32con.WM_COMMAND)
		
	def _nomatch_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		ret = self.NomatchCallback(call_data.value)
		if ret and type(ret) is StringType:
			showmessage(ret, mtype = 'error')

		
	def _menu_callback(self, params):
		item = params[2]-1
		if self._menus.has_key(self._menuselection):
			l = self._menus[self._menuselection]
			str = l[item]
			try:
				func = self.OkCallback
			except AttributeError:
				pass
			else:
				ret = func(str)
				if ret:
					if type(ret) is StringType:
						win32ui.MessageBox(ret, "Error !", win32con.MB_OK)
					return
			


	def _menu2_callback(self, params):
		self._menuselection = params[3]
