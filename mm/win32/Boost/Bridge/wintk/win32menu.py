__version__ = "$Id$"

from types import *
import winuser, win32con

# @win32doc|win32menu
# This module contains the definition of the Menu class
# that extends the PyCMenu. The PyCMenu class exports to
# Python the MFC class CMenu which is a wrapper class for
# win32 nenus.
# The purpose of this class is to facilitate the creation
# and manipulation of menus by offering functionality at
# a higher level.

# This class creates menus given a list of items
# in one of the following formats:

# # 1.a menu specification grammar:
# Contains the specification for player menu in the
# following Grammar:
# # entry: <simple_entry> | <sep_entry> | <dyn_cascade_entry> | <CASCADE_ENTRY>
# # simple_entry: (ENTRY | TOGGLE, LABEL, SHORTCUT, ID)
# # sep_enty: (SEP,)
# # dyn_cascade_entry: (DYNAMICCASCADE, LABEL, ID)
# # cascade_entry: (CASCADE,LABEL,menu_spec_list)
# # menubar_entry: (LABEL,menu_spec_list)
# # menu_spec_list: list of entry
# # menubar_spec_list: list of menubar_entry
# # menu_exec_list: (MENU,menu_spec_list)
# where ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE are type constants.
# LABEL and and SHORTCUT are strings
# ID is either an integer or an object that can be maped to an integer

# OR:
# cb_entry: (accelerator,LABEL,callback_tuple[,Type,Init]) | None
# callback_tuple: (callback,(arg,))
# callback_menu_spec_list: list of cb_entry

# The Menu class becomes indirectly an extension to PyCMenu
# by defining apropriately the __getattr__ method.

# 2. Menu functions available through the underline win32 object
#       AppendMenu|Appends a new item to the end of a menu. Python can specify the state of the menu item by setting values in nFlags.
#       DeleteMenu|Deletes the specified menu item.
#       EnableMenuItem|Enables, disables, or dims a menu item.
#       GetHandle|Returns the menu object's underlying hMenu.
#       GetMenuItemCount|Determines the number of items in a menu.
#       GetMenuItemID|Returns the item ID for the specified item in a pop-up menu.
#       GetMenuString|Returns the string for a specified menu item.
#       GetSubMenu|Returns a submenu.
#       InsertMenu|Inserts an item into a menu.
#       ModifyMenu|Modify an item in a menu.
#       TrackPopupMenu|Creates a popup menu anywhere on the screen.

import flags
import features

class Menu:
    def __init__(self,type='menu'):
        if type=='menu':m = winuser.CreateMenu()
        else: m=winuser.CreatePopupMenu()
        self.__dict__['_obj_'] = m
        self._dynamic_cascade_dict={}   # dict holding dynamic menus, valid until next call
        self._toggles={}
        self._optional_flags = flags.curflags()

    # Delete the underlying win32 object
    def __del__(self):
        del self._obj_
    # make this object as an extension of the underline win32 object
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
        self._submenus_dict={} # dictionary for 1st level submenus
        self._create_toplevel_menu(self,list)
        while len(self._exec_list):
            proc_list=self._exec_list[:]
            self._exec_list=[]
            for submenu,spec_list in proc_list:
                self._create_menu(submenu,spec_list)
        del self._exec_list
        self._cb_obj2id=None

    # create popup from a <menubar_spec_list>
    def create_popup_from_menubar_spec_list(self,list,cb_obj2id=None):
        self._exec_list=[] # common list for algorithm
        self._cb_obj2id=cb_obj2id # callback for id transl
        self._submenus_dict={} # dictionary for 1st level submenus
        self._create_menu(self,list)
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
            submenu=Menu('popup') #winuser.CreatePopupMenu()
            menu.AppendMenu(flags,submenu.GetHandle(),item[0])
            self._exec_list.append((submenu,item[1]))
            self._submenus_dict[item[0]]=submenu

    # create menu from a <menu_spec_list>
    # appends remaining to self <menu_exec_list>
    def _create_menu(self,menu,list):
        from MenuTemplate import ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE
        flags=win32con.MF_STRING|win32con.MF_ENABLED
        id=-1
        for item in list:
            if type(item[0]) is type(()) or type(item[0]) is type([]):
                for flag in item[0]:
                    if flag in features.feature_set:
                        # ok
                        break
                else:
                    # no matching feature
                    # special case for empty list
                    # in that case, accept entry
                    if item[0]:
                        # list not empty, reject entry
                        continue
            elif (item[0] & self._optional_flags) == 0:
                # old product-based flag
                continue
            if item[1]==ENTRY:
                if self._cb_obj2id:id=self._cb_obj2id(item[4])
                else: id=item[4]
                entry_flags = win32con.MF_STRING|win32con.MF_GRAYED
                menu.AppendMenu(entry_flags, id, item[2])
            elif item[1]==TOGGLE:
                if self._cb_obj2id:id=self._cb_obj2id(item[4])
                else: id=item[4]
                menu.AppendMenu(flags|win32con.MF_UNCHECKED, id, item[2])
                self._toggles[id]=1
            elif item[1]==SEP:
                menu.AppendMenu(win32con.MF_SEPARATOR)
            elif item[1]==CASCADE:
                submenu=winuser.CreatePopupMenu()
                menu.AppendMenu(flags|win32con.MF_POPUP,submenu.GetHandle(),item[2])
                self._exec_list.append((submenu,item[3]))
            elif item[1]==DYNAMICCASCADE:
                submenu=Menu('popup') #winuser.CreatePopupMenu()
                menu.AppendMenu(flags|win32con.MF_POPUP,submenu.GetHandle(),item[2])
                self._dynamic_cascade_dict[item[3]]=submenu

    # cascade menus management
    def get_cascade_menu(self,clid):
        return self._dynamic_cascade_dict.get(clid)
    def clear_cascade(self,clid):
        sm=self.get_cascade_menu(clid)
        if not sm: return
        n=sm.GetMenuItemCount()
        for i in range(n):
            sm.DeleteMenu(0,win32con.MF_BYPOSITION)
    def clear_cascade_menus(self,exceptions=[]):
        for cl in self._dynamic_cascade_dict.keys():
            if cl not in exceptions:
                self.clear_cascade(cl)

    def AppendPopup(self,submenu,str):
        nextpos = self.GetMenuItemCount()+1;
        breakpos = (nextpos-1) % 25;
        if breakpos==0 and nextpos!=1:
            self.AppendMenu(win32con.MF_POPUP|win32con.MF_MENUBARBREAK,submenu.GetHandle(),str)
        else:
            self.AppendMenu(win32con.MF_POPUP,submenu.GetHandle(),str)

    # Appends a menu item and checks for a breaks
    def AppendMenuEx(self,str,pos):
        if len(str)==0:
            self.AppendMenu(win32con.MF_SEPARATOR,0)
            return
        nextpos=self.GetMenuItemCount()+1
        breakpos = (nextpos-1) % 25
        if breakpos==0 and nextpos!=1:
            if pos!=-1:
                self.AppendMenu(win32con.MF_STRING|win32con.MF_MENUBARBREAK,pos,str)
            else:
                self.AppendMenu(win32con.MF_STRING|win32con.MF_MENUBARBREAK,nextpos,str)
        else:
            if pos!=-1:
                self.AppendMenu(win32con.MF_STRING,pos,str);
            else:
                self.AppendMenu(win32con.MF_STRING,nextpos,str)
    # Dispaly popup menu
    def FloatMenu(self,wnd,x,y):
        menu = self.GetSubMenu(0)
        pt=(x,y)
        pt=wnd.ClientToScreen(pt);
        res = menu.TrackPopupMenu(pt,win32con.TPM_RETURNCMD|win32con.TPM_RIGHTBUTTON|win32con.TPM_LEFTBUTTON,wnd);
        return res

# EXAMPLE:
# menu for: <_SubWindow instance at 165ac80>
#       ('', 'raise', (<method ChannelWindow.popup of TextChannel instance at 161c440>, ()))
#       ('', 'lower', (<method ChannelWindow.popdown of TextChannel instance at 161c440>, ()))
#       None
#       ('', 'push focus', (<method ChannelWindow.focuscall of TextChannel instance at 161c440>, ()))
#       None
#       ('', 'highlight', (<method ChannelWindow.highlight of TextChannel instance at 161c440>, ()))
#       ('', 'unhighlight', (<method ChannelWindow.unhighlight of TextChannel instance at 161c440>, ()))
#       None
#       ('', 'resize', (<method ChannelWindow.resize_window of TextChannel instance at 161c440>,
#       (<LayoutChannel instance, name=  Flashing regions  >,)))

# create menu from a callback_menu_spec_list
# Member of menu but for convenience (and history) defined outside the class
def _create_menu(self, list, menuid, cbdict, acc = None):
    self._toggles={}
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
            self.AppendMenuEx('', 0)
            continue
        length = length + 1
        if type(entry) is StringType:
            self.AppendMenuEx(entry, id)
            id = id + 1
            buts.append((entry,None))
            continue
        btype = 'p'             # default is pushbutton
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
            submenu = Menu() #winuser.CreateMenu()
            temp = _create_menu(submenu, callback, id, dict, acc)
            if temp:
                id = temp[0]
                dict2 = temp[1]
                dkeys = dict2.keys()
                for k in dkeys:
                    if not dict.has_key(k):
                        dict[k] = dict2[k]
            buts.append((labelString, temp[2]))
            self.AppendPopup(submenu, labelString)

        else:
            if type(callback) is not TupleType:
                callback = (callback, (labelString,))
            if accelerator:
                if type(accelerator) is not StringType or \
                   len(accelerator) != 1:
                    raise error, 'menu accelerator must be single character'
                acc[accelerator] = callback
                labelString = labelString + '\t' + accelerator
            self.AppendMenuEx(labelString, id)
            dict[id] = callback
            if btype == 't':
                self._toggles[id]=1
                if initial:
                    self.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_CHECKED)
                else:
                    self.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)
            id = id + 1
    t = (id, dict, buts)
    return t
