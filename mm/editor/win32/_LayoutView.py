__version__ = "$Id$"

# @win32doc|_LayoutView
# This module contains the ui implementation of LayoutView.
# It view is implemented as a Form view (MFC term).
# The MFC CFormView is essentially a view that contains controls.
# These controls are laid out based on a dialog-template resource
# similar to a dialog box.
# Objects of this class are exported to Python through the win32ui pyd
# as objects of type PyCFormView.
# The _LayoutView extends the GenFormView which is an extension to PyCFormView.

# The _LayoutView is created using the resource dialog template with identifier IDD_LAYOUT1.
# To edit this template, open it using the resource editor.
# Like all resources it can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.
# The resource project is cmif\win32\src\GRiNSRes\GRiNSRes.dsp which creates
# the run time GRiNSRes.dll

# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywinlib.mfc import window,object,docview,dialog
import afxres,commctrl

# UserCmds
from usercmd import *
from usercmdui import *

# GRiNS resource ids
import grinsRC

from GenFormView import GenFormView

class _LayoutView(GenFormView):
    def __init__(self,doc,bgcolor=None):
        GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT)
        self._lnames=l=('LayoutList','ChannelList','OtherList')
        self[l[0]]=components.ListBox(self,grinsRC.IDC_LAYOUTS)
        self[l[1]]=components.ListBox(self,grinsRC.IDC_LAYOUT_CHANNELS)
        self[l[2]]=components.ListBox(self,grinsRC.IDC_OTHER_CHANNELS)

        self[NEW_LAYOUT]=components.Button(self,grinsRC.IDCMD_NEW_LAYOUT)
        self[RENAME]=components.Button(self,grinsRC.IDCMD_RENAME)
        self[DELETE]=components.Button(self,grinsRC.IDCMD_DELETE)
        self[NEW_REGION]=components.Button(self,grinsRC.IDCMD_NEW_CHANNEL)
        self[REMOVE_REGION]=components.Button(self,grinsRC.IDCMD_REMOVE_CHANNEL)
        self[ATTRIBUTES]=components.Button(self,grinsRC.IDCMD_ATTRIBUTES)
        self[ADD_REGION]=components.Button(self,grinsRC.IDCMD_ADD_CHANNEL)

        self._activecmds={}

    def OnInitialUpdate(self):
        GenFormView.OnInitialUpdate(self)
        # enable all lists
        for name in self._lnames:
            self.EnableCmd(name,1)

    # Sets the acceptable commands.
    def set_commandlist(self,commandlist):
        frame=self.GetParent()
        contextcmds=self._activecmds
        for cl in self.keys():
            if type(cl)!=type(''):
                self.EnableCmd(cl,0)
        contextcmds.clear()
        if not commandlist: return
        for cmd in commandlist:
            if cmd.__class__== CLOSE_WINDOW:continue
            id=self[cmd.__class__]._id
            self.EnableCmd(cmd.__class__,1)
            contextcmds[id]=cmd

    # Reponse to message WM_COMMAND
    def OnCmd(self,params):
        # crack message
        msg=win32mu.Win32Msg(params)
        id=msg.cmdid()
        nmsg=msg.getnmsg()

        # delegate list notifications
        for name in self._lnames:
            if id==self[name]._id:
                self.OnListCmd(id,nmsg)
                return

        # process rest
        cmd=None
        contextcmds=self._activecmds
        if contextcmds.has_key(id):
            cmd=contextcmds[id]
        if cmd is not None and cmd.callback is not None:
            apply(apply,cmd.callback)

    # Response to a selection change of the listbox
    def OnListCmd(self,id,code):
        if code==win32con.LBN_SELCHANGE:
            for s in self._lnames:
                if self[s]._id==id:
                    self[s].callcb()
                    break
        if code==win32con.LBN_DBLCLK and id==self['ChannelList']._id:
            self.PostMessage(win32con.WM_COMMAND,self[ATTRIBUTES]._id)
