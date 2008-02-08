__version__ = "$Id$"

# @win32doc|_ErrorsView
# This module contains the ui implementation of the ErrorsView.
# It is implemented as a Form view.
# The MFC CFormView is essentially a view that contains controls.
# These controls are laid out based on a dialog-template resource
# similar to a dialog box.
# Objects of this class are exported to Python through the win32ui pyd
# as objects of type PyCFormView.

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

from GenView import GenView

class _ErrorsView(GenView, docview.ListView):
    def __init__(self,doc,bgcolor=None):
        GenView.__init__(self, bgcolor)

        # XXX don't use the document from mainframe. It crashes ???
        doc=docview.Document(docview.DocTemplate())
        docview.ListView.__init__(self, doc)
        self._listener = None
        self._selected = None

    def setListener(self, listener):
        self._listener = listener

    def removeListener(self):
        self._listener = None

    # Sets the acceptable commands.
    def set_cmddict(self,cmddict):
        self._cmddict=cmddict

    # change the list style.
    # look at MFC reference for more details
    def __setStyle(self):
        flag = commctrl.LVS_LIST|commctrl.LVS_SINGLESEL
        style = self.GetWindowLong(win32con.GWL_STYLE)
        style = style & ~commctrl.LVS_TYPEMASK
        style = style | flag
        self.SetWindowLong(win32con.GWL_STYLE, style)
        self.RedrawWindow()

    def OnCreate(self, cs):
        # change the default style
        self.__setStyle()

    def OnInitialUpdate(self):
        # redirect all command messages to self.OnCmd
        self.GetParent().HookMessage(self.OnCmd, win32con.WM_COMMAND)

        # enable selection notifications
        self.GetParent().HookNotify(self.onItemChanged, commctrl.LVN_ITEMCHANGED)

        # enable double click notification
        self.GetParent().HookNotify(self.onDoubleClick, commctrl.NM_DBLCLK)

    def setErrorList(self, errorList):
        # delete all previous items
        self.DeleteAllItems()

        pos = 0
        for message, line in errorList:
            self.InsertItem(pos, message)
            pos = pos+1

        # select the first item
        self.SetItemState(0, commctrl.LVIS_SELECTED | commctrl.LVIS_FOCUSED, commctrl.LVIS_SELECTED | commctrl.LVIS_FOCUSED)

    def onItemChanged(self, std, extra):
        nmsg = win32mu.Win32NotifyMsg( std, extra, 'list')
        if nmsg.state & commctrl.LVIS_SELECTED:
            if self._listener:
                # nofify the listener
                self._listener.onItemSelected(nmsg.row)
                self._selected = nmsg.row

    def onDoubleClick(self, std, extra):
        if self._listener and self._selected != None:
            # nofify the listener, and pop it
            self._listener.onItemSelected(self._selected, 1)
#
    # Reponse to message WM_COMMAND
    def OnCmd(self,params):
        pass
