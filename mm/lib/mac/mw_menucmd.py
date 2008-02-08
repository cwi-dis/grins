__version__ = "$Id$"

from Carbon import Menu
MenuMODULE=Menu  # Silly name clash with FrameWork.Menu
import MenuTemplate
import flags

#
# Stuff imported from other mw_ modules
#
import mw_globals

#
# Extra commands dictionary. This is a bit of a hack: this dict is filled
# by the CommandHandler init routine. It's a global variable because the popup
# menus also need it, and it is cheaper to generate it only once.
#
extra_command_dict = {}
#
# Our menus are pretty similar to FrameWork menus, but we handle
# dispatching a bit different. So, we inherit the FrameWork menus
# but override a few methods.
#

from FrameWork import Menu, PopupMenu, MenuItem, SubMenu

class MyMenuMixin:
    # We call our callbacks in a simpler way...
    def dispatch(self, id, item, window, event):
        title, shortcut, callback, type = self.items[item-1]
        if callback:
            apply(callback[0], callback[1])

    def addsubmenu(self, label, title=''):
        sub = MyMenu(self.bar, title, -1)
        item = self.additem(label, '\x1B', None, 'submenu')
        self.menu.SetItemMark(item, sub.id)
        sub._parent = self
        sub._parent_item = item
        return sub

class MyMenu(MyMenuMixin, Menu):
    pass

class MyPopupMenu(MyMenuMixin, PopupMenu):
    """This is either a cascading or button-triggered popup menu"""
    def __init__(self, bar):
        PopupMenu.__init__(self, bar)
        self._submenus = {}

    def delete(self):
        PopupMenu.delete(self)
        for m in self._submenus.values():
            m.delete()
        self._submenus = {}

    def adddependent(self, sub):
        self._submenus[sub.id] = sub

    def dispatch(self, id, item, window, event):
        if id == self.id:
            MyMenuMixin.dispatch(self, id, item, window, event)
        else:
            try:
                m = self._submenus[id]
            except KeyError:
                print "Warning: MenuEvent ID=%d received in Menu ID=%d"%(id, self.id)
            else:
                m.dispatch(id, item, window, event)

class FullPopupMenu:
    """This is a contextual (right-mouse) popup menu"""
    def __init__(self, list, title = None, accelerators=None):
        self._themenu = mw_globals.toplevel._addpopup()
        self._fill_menu(self._themenu, list, accelerators)

    def delete(self):
        self._themenu.delete()
        self._themenu = None

    def _fill_menu(self, menu, list, accelerators):
        self.toggle_values = []
        self.toggle_entries = []
        for item in list:
            if item is None:
                menu.addseparator()
            else:
                is_toggle_item = 0
                if len(item) > 3:
                    char, itemstring, callback, tp = \
                          item[:4]
                    if tp == 't':
                        is_toggle_item = 1
                        callback = (self.toggle_callback, (len(self.toggle_values), callback))
                        if len(item) > 4:
                            self.toggle_values.append(item[4])
                        else:
                            self.toggle_values.append(0)
                elif len(item) == 3:
                    char, itemstring, callback = item
                else:
                    itemstring, callback = item
                    char = ''
                if type(callback) == type([]):
                    # Submenu
                    m = menu.addsubmenu(itemstring)
                    self._fill_menu(m, callback, accelerators)
                else:
                    m = MenuItem(menu, itemstring, '',
                                 callback)
                    if char and not accelerators is None:
                        accelerators[char] = callback
                        # We abuse the mark position for the shortcut (sigh...)
                        # XXXX Can be done differently with Appearance
                        m.setmark(ord(char))
                    if is_toggle_item:
                        self.toggle_entries.append(m)
                        m.check(self.toggle_values[-1])

    def toggle_callback(self, index, (cbfunc, cbargs)):
        self.toggle_values[index] = not self.toggle_values[index]
        self.toggle_entries[index].check(self.toggle_values[index])
        apply(cbfunc, cbargs)

    def popup(self, x, y, event, window=None):
        self._themenu.popup(x, y, event, window=window)

class ContextualPopupMenu:
    """This is a contextual (right-mouse) popup menu that maps to usercmds"""
    def __init__(self, list, callbackfunc):
        self._cmd_to_item = {}
        self._themenu = mw_globals.toplevel._addpopup()
        self._fill_menu(self._themenu, list, callbackfunc)

    def delete(self):
        self._themenu.delete()
        self._themenu = None
        self._cmd_to_item = {}

    def _fill_menu(self, menu, list, callbackfunc):
        curflags = flags.curflags()
        for item in list:
            flag = item[0]
            if not (flag & curflags):
                continue
            if item[1] == MenuTemplate.SEP:
                menu.addseparator()
            elif item[1] == MenuTemplate.ENTRY:
                itemstring = item[2]
                cmd = item[4]
                callback = (callbackfunc, (cmd,))
                m = MenuItem(menu, itemstring, '',
                             callback)
                self._cmd_to_item[cmd] = m
                m.enable(0) #DBG
            elif item[1] == MenuTemplate.CASCADE:
                itemstring = item[2]
                list = item[3]
                m = menu.addsubmenu(itemstring)
                self._themenu.adddependent(m)
                self._fill_menu(m, list, callbackfunc)
            else:
                raise 'Only SEP, ENTRY or CASCADE in popup', list

    def update_menu_enabled(self, testfunc):
        for cmd, mentry in self._cmd_to_item.items():
            must_be_enabled = testfunc(cmd)
            mentry.enable(must_be_enabled)

    def popup(self, x, y, event, window=None):
        self._themenu.popup(x, y, event, window=window)

class SelectPopupMenu(PopupMenu):
    def __init__(self, list):
        PopupMenu.__init__(self, mw_globals.toplevel._menubar)
        self.additemlist(list)

    def additemlist(self, list):
        for item in list:
            if item is None:
                self.addseparator()
            else:
                self.additem(item)

    def getpopupinfo(self):
        return self.menu, self.id

class _DynamicMenu:
    """_DynamicMenu - Helper class for dynamic menus"""

    def __init__(self, menu, callbackfunc, args=()):
        self.items = []
        self.menus = []
        self.callback = callbackfunc
        self.args = args
        self.menu = menu
        self.menu.enable(0)

    def set(self, list):
        if list != self.items:
            # If the list isn't the same we have to modify it
            if list[:len(self.items)] != self.items:
                # And if the old list isn't a prefix we start from scratch
                self.menus.reverse()
                for m in self.menus:
                    m.delete()
                self.menus = []
                self.items = []
                self.cur = None
            list = list[len(self.items):]
            for item in list:
                name, value, rest = item[0], item[1], item[2:]
                arglist = self.args + (value,)
                self.menus.append(MenuItem(self.menu, name, None, (self.callback, arglist)))
                self.items.append(item)
                if len(rest) > 0 and rest[0] == 't':
                    if len(rest) > 1 and rest[1]:
                        self.menus[-1].check(1)
                    else:
                        self.menus[-1].check(0)
        anything_there = (not not self.items)
        self.menu.enable(anything_there)
        return anything_there

class _SpecialMenu(_DynamicMenu):
    """_SpecialMenu - Helper class for CommandHandler Window and Document menus"""

    def __init__(self, menu, callbackfunc):
        _DynamicMenu.__init__(self, menu, callbackfunc)
        self.cur = None

    def set(self, list, cur):
        dynlist = map(lambda x: (x,x), list)
        anything_there = _DynamicMenu.set(self, dynlist)
        if cur != self.cur:
            if self.cur != None:
                self.menus[self.cur].check(0)
            if cur != None:
                self.menus[cur].check(1)
            self.cur = cur
        return anything_there

class CommandHandler:
    def __init__(self, menubartemplate):
        import settings
        import features
        self.curflags = flags.curflags()
        self.cmd_to_menu = {}
        self.cmd_enabled = {}
##         self.must_update_window_menu = 1
##         self.must_update_document_menu = 1
        self.all_cmd_groups = [None, None, None]
        self.menubartraversal = []
        for menutemplate in menubartemplate:
            flag, entrytype, title, content = menutemplate
            if flag & self.curflags:
                menu = mw_globals.toplevel._addmenu(title)
                rv = self.fillmenu(menu, entrytype, content)
                self.menubartraversal.append(rv)
##         # Create special menus
##         menu = mw_globals.toplevel._addmenu('Documents')
##         self.document_menu = _SpecialMenu(menu,
##             mw_globals.toplevel._pop_group)
##         menu = mw_globals.toplevel._addmenu('Windows')
##         self.window_menu = _SpecialMenu(menu,
##             mw_globals.toplevel._pop_window)

    def install_cmd(self, number, group):
        if self.all_cmd_groups[number] == group:
            return 0
        self.all_cmd_groups[number] = group
##         if number == 0:
##             self.must_update_window_menu = 1
##         else:
##             self.must_update_document_menu = 1
        # Don't update, we do that in the event loop by calling
        # update_menus_enabled
        return 1

    def uninstall_cmd(self, number, group):
        if self.all_cmd_groups[number] == group:
            self.install_cmd(number, None)
            return 1
        if __debug__:
            if group in self.all_cmd_groups:
                raise 'Oops, group in wrong position!'
        return 0

    def makemenu(self, menu, content):
        itemlist = []
        for entry in content:
            flags = entry[0]
            if not (flags & self.curflags):
                continue
            entry_type = entry[1]
            if entry_type in (MenuTemplate.ENTRY,
                              MenuTemplate.TOGGLE):
                d1, d2, name, shortcut, cmd = entry
                mw_globals._all_commands[cmd] = 1
                if self.cmd_to_menu.has_key(cmd):
                    raise 'Duplicate menu command', \
                          (name, cmd)
                if entry_type == MenuTemplate.ENTRY:
                    cbfunc = self.normal_callback
                else:
                    cbfunc = self.toggle_callback
                if type(name) == type(''):
                    mname = name
                else:
                    mname = name[0]
                mentry = MenuItem(menu, mname, shortcut,
                                  (cbfunc, (cmd,)))
                self.cmd_to_menu[cmd] = mentry
                self.cmd_enabled[cmd] = 1
                itemlist.append((entry_type, cmd, name))
            elif entry_type == MenuTemplate.SEP:
                menu.addseparator()
            elif entry_type in (MenuTemplate.CASCADE, MenuTemplate.DYNAMICCASCADE,
                            MenuTemplate.SPECIAL):
                d1, d2, name, subcontent = entry
                submenu = SubMenu(menu, name, name)
                rv = self.fillmenu(submenu, entry_type, subcontent)
                itemlist.append(rv)
            else:
                raise 'Unknown menu entry type', entry_type
        return itemlist

    def fillmenu(self, submenu, entrytype, subcontent):
        if entrytype == MenuTemplate.CASCADE:
            subitemlist = self.makemenu(submenu, subcontent)
            return (entrytype, submenu, subitemlist)
        elif entrytype == MenuTemplate.DYNAMICCASCADE:
            cmd = subcontent
            dynamicmenu = _DynamicMenu(submenu, self.dynamic_callback, (cmd,))
            mw_globals._all_commands[cmd] = 1
            self.cmd_to_menu[cmd] = dynamicmenu
            self.cmd_enabled[cmd] = 1
            return (entrytype, cmd, dynamicmenu)
        elif entrytype == MenuTemplate.SPECIAL:
            if subcontent == 'documents':
                callback = mw_globals.toplevel._pop_group
                filler = self.update_document_menu
            elif subcontent == 'windows':
                callback = mw_globals.toplevel._pop_window
                filler = self.update_window_menu
            specialmenu = _SpecialMenu(submenu, callback)
            return (entrytype, specialmenu, filler)
        else:
            raise 'Unknown menu type', entry_type

    def toggle_callback(self, cmd):
        mentry = self.cmd_to_menu[cmd]
        group = self.find_toggle_group(cmd)
        if group:
            group.toggle_toggle(cmd) # Force a menubar redraw later
        else:
            print 'HUH? No group for toggle cmd', cmd
        self.normal_callback(cmd)

    def normal_callback(self, cmd):
        callback = self.find_command(cmd, mustfind=1)
        if callback:
            func, arglist = callback
            apply(func, arglist)
        else: # debug
            print 'CommandHandler: unknown command', cmd #debug

    def dynamic_callback(self, cmd, arg):
        callbackfunc = self.find_command(cmd, mustfind=1)
        if callbackfunc:
            apply(callbackfunc, arg)
        else:
            print 'CommandHandler: unknown dynamic command', cmd

    def find_command(self, cmd, mustfind=0):
        for group in self.all_cmd_groups:
            if group:
                callback = group.get_command_callback(cmd)
                if callback:
##                     if mustfind and self.cmd_enabled.has_key(cmd) and not self.cmd_enabled[cmd]: # debug
##                         print 'CommandHandler: disabled command selected:', cmd # debug
                    return callback
        return None

    def find_command_dynamic_list(self, cmd):
        for group in self.all_cmd_groups:
            if group:
                dynamiclist = group.get_command_dynamic_list(cmd)
                if not dynamiclist is None:
                    return dynamiclist
        return []

    def find_toggle_group(self, cmd):
        for group in self.all_cmd_groups:
            if group and group.has_command(cmd):
                return group
        return None

    def _update_one(self, items):
        any_active = 0
        for item in items:
            itemtype = item[0]
            if itemtype == MenuTemplate.CASCADE:
                itemtype, submenu, subitems = item
                must_be_enabled = self._update_one(subitems)
                submenu.enable(must_be_enabled)
            elif itemtype == MenuTemplate.DYNAMICCASCADE:
                itemtype, cmd, dynamicmenu = item
                dynamiclist = self.find_command_dynamic_list(cmd)
                must_be_enabled = dynamicmenu.set(dynamiclist)
            elif itemtype == MenuTemplate.SPECIAL:
                itemtype, specialmenu, fillerfunc = item
                must_be_enabled = fillerfunc(specialmenu)
            else:
                itemtype, cmd, names = item
                must_be_enabled = (not not self.find_command(cmd))
                if must_be_enabled != self.cmd_enabled[cmd]:
                    mentry = self.cmd_to_menu[cmd]
                    mentry.enable(must_be_enabled)
                    self.cmd_enabled[cmd] = must_be_enabled
                if must_be_enabled and \
                                itemtype == MenuTemplate.TOGGLE:
                    mentry = self.cmd_to_menu[cmd]
                    group = self.find_toggle_group(cmd)
                    if group:
                        togglestate = group.get_toggle(cmd)
                        if type(names) == type(''):
                            mentry.check(togglestate)
                        else:
                            mentry.settext(names[togglestate])
            if must_be_enabled:
                any_active = 1
        return any_active

    def update_menus(self):
        self._update_one(self.menubartraversal)
##         if self.must_update_window_menu:
##             self.update_window_menu()
##             self.must_update_window_menu = 0
##         if self.must_update_document_menu:
##             self.update_document_menu()
##             self.must_update_document_menu = 0

    def update_window_menu(self, menu):
        list, cur = mw_globals.toplevel._get_window_names()
        return menu.set(list, cur)

    def update_document_menu(self, menu):
        list, cur = mw_globals.toplevel._get_group_names()
        return menu.set(list, cur)
