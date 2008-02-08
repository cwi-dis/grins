__version__ = "$Id$"

# app constants
from appcon import *

class DocumentFrame:
    def __init__(self):
        self._activecmds={'app':{},'document':{},'pview_':{}}
        self._dyncmds = {}

    def set_commandlist(self, commandlist, context):
        self._activecmds[context] = {}
        if commandlist:
            for cmd in      commandlist:
                self._activecmds[context][cmd.__class__] = cmd
        #print 'DocumentFrame.set_commandlist', commandlist, context

    def setcoords(self,coords, units=UNIT_MM):
        print 'DocumentFrame.setcoords', coords, units

    def set_dynamiclist(self, command, list):
        print 'DocumentFrame.set_dynamiclist', command, list

    def set_toggle(self, cmdcl, onoff):
        print 'DocumentFrame.set_toggle',  cmdcl, onoff

    def setplayerstate(self, state):
        print 'DocumentFrame.setplayerstate', state

    def execute_cmd(self, cmdclass):
        for ctx in ('pview_', 'document', 'app'):
            dict = self._activecmds[ctx]
            if dict:
                cmd = dict.get(cmdclass)
                if cmd is not None and cmd.callback:
                    apply(apply, cmd.callback)
                    return

    def get_cmd_instance(self, cmdclass):
        for ctx in ('pview_', 'document', 'app'):
            dict = self._activecmds[ctx]
            if dict:
                cmd = dict.get(cmdclass)
                if cmd is not None and cmd.callback:
                    return cmd

## #######################
import wingeneric

import winstruct

import win32con

import usercmd, wndusercmd, usercmdui
import win32menu, MenuTemplate

class MainWnd(wingeneric.Wnd, DocumentFrame):
    def __init__(self):
        wingeneric.Wnd.__init__(self)
        DocumentFrame.__init__(self)
        self._title = 'GRiNS Player'

    def create(self):
        wingeneric.Wnd.create(self)
        self.setMenu()
        self.SetTimer(1, 100)
        self.HookMessage(self.OnTimer, win32con.WM_TIMER)
        self.HookMessage(self.OnCommand, win32con.WM_COMMAND)

    def OnTimer(self, params):
        self.get_toplevel().serve_events(params)

    def OnCommand(self, params):
        cmdid = winstruct.Win32Msg(params).id()
        import usercmdui
        cmd = usercmdui.id2usercmd(cmdid)
        if cmd:
            self.execute_cmd(cmd)
            return
        for cbd in self._dyncmds.values():
            if cbd.has_key(cmdid):
                apply(apply, cbd[cmdid])
                return

    # we want to reuse this
    def close(self):
        pass

    def setMenu(self):
        mainmenu = win32menu.Menu()
        template = MenuTemplate.MENUBAR
        mainmenu.create_from_menubar_spec_list(template,  usercmdui.usercmd2id)
        self.SetMenu(mainmenu._obj_)
        self.DrawMenuBar()
        self._mainmenu = mainmenu

    def set_toggle(self, cmdcl, onoff):
        id = usercmdui.usercmd2id(cmdcl)
        flags = win32con.MF_BYCOMMAND
        if onoff==0:
            flags = flags | win32con.MF_UNCHECKED
        else:
            flags = flags | win32con.MF_CHECKED
        self.GetMenu().CheckMenuItem(id, flags)

    def updateUI(self):
        pass

    def get_toplevel(self):
        import __main__
        return __main__.toplevel

    def set_commandlist(self, commandlist, context):
        menu = self.GetMenu()

        # disable previous if any
        prev_commandlist_dict = self._activecmds.get(context)
        if prev_commandlist_dict:
            prev_commandlist = prev_commandlist_dict.values()
            flags = win32con.MF_BYCOMMAND | win32con.MF_GRAYED
            for cmdinst in prev_commandlist:
                cmd = cmdinst.__class__
                id = usercmdui.usercmd2id(cmd)
                menu.EnableMenuItem(id, flags)

        # enable new
        self._activecmds[context] = {}
        if commandlist:
            flags = win32con.MF_BYCOMMAND | win32con.MF_ENABLED
            for cmdinst in commandlist:
                cmd = cmdinst.__class__
                self._activecmds[context][cmd] = cmdinst
                id = usercmdui.usercmd2id(cmd)
                menu.EnableMenuItem(id, flags)

        # exception
        if context == 'app':
            cmd = wndusercmd.ABOUT_GRINS
            id = usercmdui.usercmd2id(cmd)
            menu.EnableMenuItem(id, flags)

    def set_dynamiclist(self, command, list):
        submenu = self._mainmenu.get_cascade_menu(command)
        if not submenu:
            return
        cmd_instance = self.get_cmd_instance(command)
        if cmd_instance is None:
            return
        idstart = usercmdui.usercmd2id(command) + 1
        menuspec = []
        callback = cmd_instance.callback
        self._dyncmds[command] = {}
        for entry in list:
            entry = (entry[0], (callback, entry[1])) + entry[2:]
            menuspec.append(entry)
        self._mainmenu.clear_cascade(command)
        win32menu._create_menu(submenu, menuspec, idstart, self._dyncmds[command])
