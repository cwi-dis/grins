
from types import *
import win32ui, win32con


# PyCMenu members
#	AppendMenu|Appends a new item to the end of a menu. Python can specify the state of the menu item by setting values in nFlags.
#	DeleteMenu|Deletes the specified menu item.
#	EnableMenuItem|Enables, disables, or dims a menu item.
#	GetHandle|Returns the menu object's underlying hMenu.
#	GetMenuItemCount|Determines the number of items in a menu.
#	GetMenuItemID|Returns the item ID for the specified item in a pop-up menu.
#	GetMenuString|Returns the string for a specified menu item.
#	GetSubMenu|Returns a submenu.
#	InsertMenu|Inserts an item into a menu.
#	ModifyMenu|Modify an item in a menu.
#	TrackPopupMenu|Creates a popup menu anywhere on the screen.


#####################################
# replacement of cmifex2 menu related utilities plus more


def CreateMenu():
	return win32ui.CreateMenu()

def GetMenu(wnd):
	menu = wnd.GetMenu()
	if menu: count=GetMenuItemCount()
	else: count = 0
	wnd.SetMenu(menu)
	wnd.DrawMenuBar()
	return menu,count

def SetMenu(wnd,menu):
	wnd.SetMenu(menu)
	wnd.DrawMenuBar()

def FloatMenu(wnd,menu,x,y):
	menu = menu.GetSubMenu(0)
	pt=(x,y)
	pt=wnd.ClientToScreen(pt);
	res = menu.TrackPopupMenu(pt,win32con.TPM_RETURNCMD|win32con.TPM_RIGHTBUTTON|win32con.TPM_LEFTBUTTON,wnd);
	return res

def CheckMenuItem(menu,pos,check):
	flags = win32con.MF_BYPOSITION
	if check==0:
		flags = flags | win32con.MF_UNCHECKED
	else:
		flags = flags | win32con.MF_CHECKED
	menu.CheckMenuItem(pos,flags)


# positions are used as the cmd ids
def AppendMenu(menu,str,pos):
	if len(str)==0: 
		menu.AppendMenu(win32con.MF_SEPARATOR,0)
		return
	nextpos=menu.GetMenuItemCount()+1
	breakpos = (nextpos-1) % 25
	if breakpos==0 and nextpos!=1:
		if pos!=-1:
			menu.AppendMenu(win32con.MF_STRING|win32con.MF_MENUBARBREAK,pos,str)
		else:
			menu.AppendMenu(win32con.MF_STRING|win32con.MF_MENUBARBREAK,nextpos,str)
	else:
		if pos!=-1:
			menu.AppendMenu(win32con.MF_STRING,pos,str);
		else:
			menu.AppendMenu(win32con.MF_STRING,nextpos,str)


def PopupAppendMenu(menu,submenu,str):
	nextpos = menu.GetMenuItemCount()+1;
	breakpos = (nextpos-1) % 25;
	if breakpos==0 and nextpos!=1:
		menu.AppendMenu(win32con.MF_POPUP|win32con.MF_MENUBARBREAK,submenu.GetHandle(),str)
	else:
		menu.AppendMenu(win32con.MF_POPUP,submenu.GetHandle(),str)

def InsertMenu(menu,pos,str):
	if len(str)==0: 
		menu.InsertMenu(pos,win32con.MF_SEPARATOR|win32con.MF_BYPOSITION)
	else:
		nextpos=menu.GetMenuItemCount()+1
		menu.InsertMenu(pos,win32con.MF_STRING|win32con.MF_BYPOSITION,nextpos,str)

def PopupInsertMenu(menu,submenu,pos,str):
	menu.InsertMenu(pos,win32con.MF_POPUP|win32con.MF_BYPOSITION,submenu,str)

def DestroyMenu(menu):
	del menu

def DeleteMenu(menu,pos):
	menu.DeleteMenu(pos,win32con.MF_BYPOSITION)


def _create_menu(menu, list, menuid, cbdict, acc = None):
	accelerator = None
	length = 0
	i = 0
	id = menuid
	dict  = cbdict
	buts = []
	while i < len(list):
		entry = list[i]
		i = i + 1
		if entry is None:
			AppendMenu(menu, '', 0)
			continue
		length = length + 1
		if type(entry) is StringType:
			AppendMenu(menu, entry, id)
			id = id + 1
			buts.append((entry,None))
			continue
		btype = 'p'		# default is pushbutton
		initial = 0
		if acc is None:
			labelString, callback = entry[:2]
			if len(entry) > 2:
				btype = entry[2]
				if len(entry) > 3:
					initial = entry[3]
		else:
			if len(entry)==2:
				accelerator = None
				labelString, callback = entry
			else:
				accelerator, labelString, callback = entry[:3]
			if len(entry) > 3:
				btype = entry[3]
				if len(entry) > 4:
					initial = entry[4]

		if type(callback) is ListType:
			submenu = CreateMenu()
			temp = _create_menu(submenu, callback, id, dict, acc)			
			if temp:
				id = temp[0]
				dict2 = temp[1]
				dkeys = dict2.keys()
				for k in dkeys:
					if not dict.has_key(k):
						dict[k] = dict2[k]
			buts.append((labelString, temp[2]))
			PopupAppendMenu(menu, submenu, labelString)
		else:
			buts.append((labelString, None))
			if type(callback) is not TupleType:
				callback = (callback, (labelString,))
			attrs = {'labelString': labelString}
			if accelerator:
				if type(accelerator) is not StringType or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
				attrs['acceleratorText'] = accelerator
				labelString = labelString + '\t' + accelerator
			AppendMenu(menu, labelString, id)
			dict[id] = callback
			if btype == 't':
				CheckMenuItem(menu,id,initial)
			id = id + 1
		
	t = (id, dict, buts)
	return t
