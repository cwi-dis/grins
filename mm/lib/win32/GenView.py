__version__ = "$Id$"

import win32con

# Common interface of MFC Views in GRiNS context

class GenView:
    def __init__(self, bgcolor=None):
        self._closecmdid=-1
        self._commandlist = []
        self._cmd_state = {}
        self._is_active = 0

    #
    # Creation attributes
    #
    def isResizeable(self):
        return 1

    # Creates the actual OS window
    def createWindow(self, parent):
        self._parent = parent
        self.CreateWindow(parent)

    # Sets the acceptable command list by delegating to its parent keeping a copy.
    def set_commandlist(self, list):
        self._commandlist = list
        if self._is_active:
            self.activate()

    # Toggles menu entries by delegating to its parent
    def set_toggle(self, command, onoff):
        self._cmd_state[command] = onoff
        if self._is_active:
            self._parent.getMDIFrame().set_toggle(command, onoff)

    def set_menu_state(self):
        for command in self._cmd_state.keys():
            onoff=self._cmd_state[command]
            self._parent.getMDIFrame().set_toggle(command,onoff)

    def enableDlgBarCmd(self, id, f):
        frame = self.GetParent()
        if f:
            frame.HookCommandUpdate(frame.OnUpdateCmdEnable, id)
        else:
            frame.HookCommandUpdate(frame.OnUpdateCmdDissable, id)

    def enableDlgBarComponent(self, component, f):
        frame = self.GetParent()
        if f:
            frame.HookCommandUpdate(frame.OnUpdateCmdEnable, component._id)
        else:
            frame.HookCommandUpdate(frame.OnUpdateCmdDissable, component._id)

    # Called when the view is deactivated
    def activate(self):
        self._is_active=1
        self._parent.getMDIFrame().set_commandlist(self._commandlist,self._strid)
        self.set_menu_state()

    # Called when the view is deactivated
    def deactivate(self):
        self._is_active=0
        self._parent.getMDIFrame().set_commandlist(None, self._strid)

    def setclosecmd(self, cmdid):
        self._closecmdid = cmdid

    # Called by the frame work before closing this View
    def OnClose(self):
        if self._closecmdid>0:
            self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND,self._closecmdid)
        else:
            self.GetParent().DestroyWindow()

    # Returns true if the OS window exists
    def is_oswindow(self):
        return (hasattr(self,'GetSafeHwnd') and self.GetSafeHwnd())

    # Helper function that given the string id of the control calls the callback
    def call(self,strcmd):
        if self._cbdict.has_key(strcmd):
            apply(apply,self._cbdict[strcmd])

    # Return 1 if self is an os window
    def is_showing(self):
        if not hasattr(self,'GetSafeHwnd'):
            return 0
        return self.GetSafeHwnd()and self.IsWindowVisible()

    # Called by the core system to show this view
    def show(self):
        if hasattr(self,'GetSafeHwnd'):
            if self.GetSafeHwnd():
                self.GetParent().ShowWindow(win32con.SW_SHOW)
                self.GetParent().getMDIFrame().MDIActivate(self.GetParent())

    # Called by the core system to hide this view
    def hide(self):
        self.close()

    def close(self):
        if hasattr(self,'_obj_') and self._obj_:
            self.GetParent().DestroyWindow()

    # Bring window in front of peers
    def pop(self):
        if not hasattr(self,'GetParent'):return
        childframe=self.GetParent()
        childframe.ShowWindow(win32con.SW_SHOW)
        frame=childframe.GetMDIFrame()
        frame.MDIActivate(childframe)

    def getgeometry(self, units = None):
        # Ignore units.
        placement = self.GetParent().GetWindowPlacement()
        outerrect = placement[4]
        out_l, out_t, out_r, out_b = outerrect
        out_w = out_r - out_l
        out_h = out_b - out_t
        in_w = out_w - 16
        in_h = out_h - 35
        return (out_l, out_t, in_w, in_h)
