__version__ = "$Id$"

# @win32doc|TransitionView
# This module contains the ui implementation of the TransitionView.
# It is implemented as a Form view.
# The MFC CFormView is essentially a view that contains controls.
# These controls are laid out based on a dialog-template resource
# similar to a dialog box.
# Objects of this class are exported to Python through the win32ui pyd
# as objects of type PyCFormView.
# The _TransitionView extends the GenFormView which is an extension to PyCFormView.

# The _TransitionView is created using the resource dialog template with identifier IDD_USERGROUP.
# To edit this template, open it using the resource editor.
# Like all resources it can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.
# The resource project is cmif\win32\src\GRiNSRes\GRiNSRes.dsp which creates
# the run time GRiNSRes.dll

# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu, components, win32dialog

# std mfc windows stuf
from pywinlib.mfc import window,object,docview,dialog
import afxres,commctrl

# UserCmds
from usercmd import *
from usercmdui import *

# GRiNS resource ids
import grinsRC

from GenFormView import GenFormView

class _TransitionView(GenFormView):
    def __init__(self,doc,bgcolor=None):
        GenFormView.__init__(self,doc,grinsRC.IDD_USERGROUP)
        self['Groups']=components.ListBox(self,grinsRC.IDC_GROUPS)
        self['New']=components.Button(self,grinsRC.IDCMD_NEW_GROUP)
        self['Edit']=components.Button(self,grinsRC.IDCMD_EDIT_GROUP)
        self['Delete']=components.Button(self,grinsRC.IDCMD_DELETE_GROUP)

        self._init_ugroups=[]
        self._init_pos=None

    # Sets the acceptable commands.
    def set_cmddict(self,cmddict):
        self._cmddict=cmddict

    def OnInitialUpdate(self):
        GenFormView.OnInitialUpdate(self)
        self.EnableCmd('Groups',1)
        self.EnableCmd('New',1)
        if len(self._init_ugroups):
            self.setgroups(self._init_ugroups,self._init_pos)

    # Reponse to message WM_COMMAND
    def OnCmd(self,params):
        # crack message
        msg=win32mu.Win32Msg(params)
        id=msg.cmdid()
        nmsg=msg.getnmsg()

        # special response
        if id==self['Groups']._id:self.OnListCmd(id,nmsg)

        # std stuff
        for k in self.keys():
            if self[k]._id==id:
                if self._cmddict.has_key(k):
                    apply(apply,self._cmddict[k])
                return

    # Response to a selection change of the listbox
    # and selection dblclick
    def OnListCmd(self,id,code):
        if code==win32con.LBN_SELCHANGE:
            pos=self['Groups'].getcursel()
            if pos==None or pos<0:
                self.EnableCmd('Edit',0)
                self.EnableCmd('Delete',0)
            else:
                self.EnableCmd('Edit',1)
                self.EnableCmd('Delete',1)
        if code==win32con.LBN_DBLCLK:
            apply(apply,self._cmddict['Edit'])


    def getgroup(self):
        # Return name of currently selected user group.
        if self.is_oswindow():
            ix=self['Groups'].getcursel()
            if ix==None or ix<0: return None
            return self['Groups'].gettext(ix)
        else:
            if not self._init_pos: return None
            return self._init_ugroups[self._init_pos]

    def setgroups(self, ugroups, pos):
        # Set the list of user groups.

        # Arguments (no defaults):
        # ugroups -- list of strings giving the names of the user groups
        # pos -- None or index in ugroups list--the initially
        #       selected element in the list
        if self.is_oswindow():
            l=self['Groups']
            l.delalllistitems()
            l.addlistitems(ugroups, 0)
            l.selectitem(pos)
            self.OnListCmd(l._id,win32con.LBN_SELCHANGE)
        else:
            self._init_ugroups=ugroups
            self._init_pos=pos
