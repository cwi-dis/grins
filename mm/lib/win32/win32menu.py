
from types import *
import win32ui, win32con


# 1.a menu specification grammar:
# entry: <simple_entry> | <sep_entry> | <CASCADE_ENTRY>
# simple_entry: (ENTRY | TOGGLE, LABEL, SHORTCUT, ID)
# sep_enty: (SEP,)
# cascade_entry: (CASCADE,LABEL,menu_spec_list)
# menubar_entry: (LABEL,menu_spec_list)
# menu_spec_list: list of entry
# menubar_spec_list: list of menubar_entry
# menu_exec_list: (MENU,menu_spec_list)

# OR:
# cb_entry: (accelerator,LABEL,callback_tuple[,Type,Init]) | None
# callback_tuple: (callback,(arg,))
# callback_menu_spec_list: list of cb_entry

# 2. Menu functions available through the underline win32 object
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

class Menu:
	def __init__(self,type='menu'):
		if type=='menu':m=win32ui.CreateMenu()
		else: m=win32ui.CreatePopupMenu()
		self.__dict__['_obj_'] = m
		self._dynamic_cascade_dict={}	# dict holding dynamic menus, valid until next call
		self._toggles={}

	def __del__(self):
		del self._obj_
	def __getattr__(self, attr):	
		try:	
			if attr != '__dict__':
				o = self.__dict__['_obj_']
				if o:
					return getattr(o, attr)
		except KeyError:
			pass
		raise AttributeError, attr


	# create menu from a <menu_spec_list>
	def create_from_menu_spec_list(self,list,cb_obj2id=None):
		self._exec_list=[] # common list for algorithm
		self._cb_obj2id=cb_obj2id # callback for id transl
		self._toggles={}
		self._create_menu(self,list)
		while len(self._exec_list):
			proc_list=self._exec_list[:]
			self._exec_list=[]
			for submenu,spec_list in proc_list:
				self._create_menu(submenu,spec_list)
		del self._exec_list
		self._cb_obj2id=None

	# create menu from a <menubar_spec_list>
	def create_from_menubar_spec_list(self,list,cb_obj2id=None):
		self._exec_list=[] # common list for algorithm
		self._cb_obj2id=cb_obj2id # callback for id transl
		self._create_toplevel_menu(self,list)
		while len(self._exec_list):
			proc_list=self._exec_list[:]
			self._exec_list=[]
			for submenu,spec_list in proc_list:
				self._create_menu(submenu,spec_list)
		del self._exec_list
		self._cb_obj2id=None

	# create toplevel menubar from a <menubar_spec_list>
	# returns a <menu_exec_list>
	def _create_toplevel_menu(self,menu,list):
		flags=win32con.MF_STRING|win32con.MF_ENABLED|win32con.MF_POPUP
		for item in list:
			submenu=win32ui.CreatePopupMenu()
			menu.AppendMenu(flags,submenu.GetHandle(),item[0])
			self._exec_list.append((submenu,item[1]))

	# create menu from a <menu_spec_list>
	# appends remaining to self <menu_exec_list>
	def _create_menu(self,menu,list):
		[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)
		flags=win32con.MF_STRING|win32con.MF_ENABLED
		id=-1
		for item in list:
			if item[0]==ENTRY:
				if self._cb_obj2id:id=self._cb_obj2id(item[3])
				else: id=item[3]
				menu.AppendMenu(flags, id, item[1])
			elif item[0]==TOGGLE:
				if self._cb_obj2id:id=self._cb_obj2id(item[3])
				else: id=item[3]
				menu.AppendMenu(flags|win32con.MF_UNCHECKED, id, item[1])
				self._toggles[id]=1
			elif item[0]==SEP:
				menu.AppendMenu(win32con.MF_SEPARATOR)
			elif item[0]==CASCADE:
				submenu=win32ui.CreatePopupMenu()
				menu.AppendMenu(flags|win32con.MF_POPUP,submenu.GetHandle(),item[1])
				self._exec_list.append((submenu,item[2]))
			elif item[0]==DYNAMICCASCADE:
				submenu=Menu('popup') #win32ui.CreatePopupMenu()
				menu.AppendMenu(flags|win32con.MF_POPUP,submenu.GetHandle(),item[1])
				self._dynamic_cascade_dict[item[2]]=submenu

	# cascade menus management
	def get_cascade_menu(self,clid):
		if clid in self._dynamic_cascade_dict.keys():
			return self._dynamic_cascade_dict[clid]
		return None
	def clear_cascade(self,clid):
		sm=self.get_cascade_menu(clid)
		if not sm: return
		n=sm.GetMenuItemCount()
		for i in range(n):
			sm.DeleteMenu(0,win32con.MF_BYPOSITION) 
	def clear_cascade_menus(self):
		for cl in self._dynamic_cascade_dict.keys():
			self.clear_cascade(cl)

	def AppendPopup(self,submenu,str):
		nextpos = self.GetMenuItemCount()+1;
		breakpos = (nextpos-1) % 25;
		if breakpos==0 and nextpos!=1:
			self.AppendMenu(win32con.MF_POPUP|win32con.MF_MENUBARBREAK,submenu.GetHandle(),str)
		else:
			self.AppendMenu(win32con.MF_POPUP,submenu.GetHandle(),str)

	def FloatMenu(self,wnd,x,y):
		menu = self.GetSubMenu(0)
		pt=(x,y)
		pt=wnd.ClientToScreen(pt);
		res = menu.TrackPopupMenu(pt,win32con.TPM_RETURNCMD|win32con.TPM_RIGHTBUTTON|win32con.TPM_LEFTBUTTON,wnd);
		return res

"""
EXAMPLE:
menu for: <_SubWindow instance at 165ac80>
	('', 'raise', (<method ChannelWindow.popup of TextChannel instance at 161c440>, ()))
	('', 'lower', (<method ChannelWindow.popdown of TextChannel instance at 161c440>, ()))
	None
	('', 'push focus', (<method ChannelWindow.focuscall of TextChannel instance at 161c440>, ()))
	None
	('', 'highlight', (<method ChannelWindow.highlight of TextChannel instance at 161c440>, ()))
	('', 'unhighlight', (<method ChannelWindow.unhighlight of TextChannel instance at 161c440>, ()))
	None
	('', 'resize', (<method ChannelWindow.resize_window of TextChannel instance at 161c440>, 
	(<LayoutChannel instance, name=  Flashing regions  >,)))

"""

# create menu from a callback_menu_spec_list

def _create_menu(menu, list, menuid, cbdict, acc = None):
	menu._toggles={}
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
			submenu = win32ui.CreateMenu()
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
				menu._toggles[id]=1
				if initial:
					menu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_CHECKED)	
				else:
					menu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)			
			id = id + 1
	t = (id, dict, buts)
	return t

def _create_menu_X(menu, list, visual, colormap, acc = None, widgets = None):
	if widgets is None:
		widgets = {}
	if len(list) > 30:
		menu.numColumns = (len(list) + 29) / 30
		menu.packing = Xmd.PACK_COLUMN
	if _def_useGadget:
		separator = Xm.SeparatorGadget
		label = Xm.LabelGadget
		cascade = Xm.CascadeButtonGadget
		toggle = Xm.ToggleButtonGadget
		pushbutton = Xm.PushButtonGadget
	else:
		separator = Xm.Separator
		label = Xm.Label
		cascade = Xm.CascadeButton
		toggle = Xm.ToggleButton
		pushbutton = Xm.PushButton
	accelerator = None
	for entry in list:
		if entry is None:
			dummy = menu.CreateManagedWidget('separator',
							 separator, {})
			continue
		if type(entry) is StringType:
			dummy = menu.CreateManagedWidget(
				'menuLabel', label,
				{'labelString': entry})
			widgets[entry] = dummy, None
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
			accelerator, labelString, callback = entry[:3]
			if len(entry) > 3:
				btype = entry[3]
				if len(entry) > 4:
					initial = entry[4]
		if type(callback) is ListType:
			submenu = menu.CreatePulldownMenu('submenu',
				{'colormap': colormap,
				 'visual': visual,
				 'depth': visual.depth,
				 'orientation': Xmd.VERTICAL,
				 'tearOffModel': Xmd.TEAR_OFF_ENABLED})
			button = menu.CreateManagedWidget(
				'submenuLabel', cascade,
				{'labelString': labelString, 'subMenuId': submenu})
			subwidgets = {}
			widgets[labelString] = button, subwidgets
			_create_menu(submenu, callback, visual, colormap, acc,
				     subwidgets)
		else:
			if type(callback) is not TupleType:
				callback = (callback, (labelString,))
			attrs = {'labelString': labelString}
			if accelerator:
				if type(accelerator) is not StringType or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
				attrs['acceleratorText'] = accelerator
			if btype == 't':
				attrs['set'] = initial
				button = menu.CreateManagedWidget('menuToggle',
						toggle, attrs)
				cbfunc = 'valueChangedCallback'
			else:
				button = menu.CreateManagedWidget('menuLabel',
						pushbutton, attrs)
				cbfunc = 'activateCallback'
			button.AddCallback(cbfunc, _generic_callback, callback)
			widgets[labelString] = button, None

def ClearSubmenu(sm):
	n=sm.GetMenuItemCount()
	for i in range(n):
		sm.DeleteMenu(0,win32con.MF_BYPOSITION) 
	return sm



##############################################
# JUST REMINDERS FUNCTIONS

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


def CheckMenuItem(menu,pos,check):
	flags = win32con.MF_BYPOSITION
	if check==0:
		flags = flags | win32con.MF_UNCHECKED
	else:
		flags = flags | win32con.MF_CHECKED
	menu.CheckMenuItem(pos,flags)

def CheckMenuItemByCmd(menu,id,check):
	flags = win32con.MF_BYCOMMAND
	if check==0:
		flags = flags | win32con.MF_UNCHECKED
	else:
		flags = flags | win32con.MF_CHECKED
	menu.CheckMenuItem(id,flags)

def ClearSubmenu(sm):
	n=sm.GetMenuItemCount()
	for i in range(n):
		sm.DeleteMenu(0,win32con.MF_BYPOSITION) 
	return sm

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



