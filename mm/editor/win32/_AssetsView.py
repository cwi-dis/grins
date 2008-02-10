__version__ = "$Id$"

import win32ui, win32con, afxres

Sdk = win32ui.GetWin32Sdk()


import ListCtrl
import components
from win32mu import Win32Msg
import longpath

import grinsRC

from pywinlib.mfc import docview
import GenView
import DropTarget
import IconMixin
import string

import MMurl

class _AssetsView(GenView.GenView,
                                docview.ListView,
                                DropTarget.DropTargetListener,
                                IconMixin.ViewMixin):

    def __init__(self, doc, bgcolor=None):
        GenView.GenView.__init__(self, bgcolor)
        docview.ListView.__init__(self, doc)
        DropTarget.DropTargetListener.__init__(self)
        self._dropmap = {
                'FileName': (self.dragitem, self.dropitem),
                'URL': (self.dragitem, self.dropitem),
                'NodeUID': (self.dragitem, self.dropitem),
                'Region': (self.dragitem, self.dropitem),
        }

        # view decor
        self._dlgBar = win32ui.CreateDialogBar()

        # add components
        self._showAll = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_ALL)
        self._showTemplate = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_TEMPLATE)
        self._showClipboard = components.RadioButton(self._dlgBar, grinsRC.IDC_RADIO_CLIPBOARD)

        self.listCtrl = None
        self.initicons()
        self.columnsTemplate = []
        self.items = []

        self._ignoredragdrop = 0

    # Sets the acceptable commands.
    def set_cmddict(self,cmddict):
        self._cmddict=cmddict

    def OnCreate(self, cs):
        # create dialog bar
        AFX_IDW_DIALOGBAR = 0xE805
        self._dlgBar.CreateWindow(self.GetParent(), grinsRC.IDD_ASSETSBAR, afxres.CBRS_ALIGN_BOTTOM, AFX_IDW_DIALOGBAR)

        # attach components
        self._showAll.attach_to_parent()
        self._showTemplate.attach_to_parent()
        self._showClipboard.attach_to_parent()

    # Called by the framework after the OS window has been created
    def OnInitialUpdate(self):
        self.listCtrl = ListCtrl.ListCtrl(self, self.GetListCtrl())

        # redirect all command messages to self.OnCmd
        self.GetParent().HookMessage(self.OnCmd, win32con.WM_COMMAND)

        self.rebuildList()
        self.registerDropTargetFor(self.listCtrl)
        self.listCtrl.addSelListener(self)
        # XXXX There is no cleanup method!

    def OnCmd(self, params):
        msg = Win32Msg(params)
        code = msg.HIWORD_wParam()
        id = msg.LOWORD_wParam()
        hctrl = msg._lParam
        if id == self._showAll._id and code == win32con.BN_CLICKED:
            self.showAll()
        elif id == self._showTemplate._id and code == win32con.BN_CLICKED:
            self.showTemplate()
        elif id == self._showClipboard._id and code == win32con.BN_CLICKED:
            self.showClipboard()
        else:
            print 'OnCmd', id, code

    def showAll(self):
        cb = self._cmddict['setview']
        cb('all')

    def showTemplate(self):
        cb = self._cmddict['setview']
        cb('template')

    def showClipboard(self):
        cb = self._cmddict['setview']
        cb('clipboard')

    def setView(self, which):
        self._showAll.setcheck(which == 'all')
        self._showTemplate.setcheck(which == 'template')
        self._showClipboard.setcheck(which == 'clipboard')

    def rebuildList(self):
        lc = self.listCtrl
        if not lc: return

        # set icons
        self.seticonlist(lc)

        # insert columns: (align, width, text) list
        lc.deleteAllColumns()
        lc.insertColumns(self.columnsTemplate)

        lc.removeAll()

        row = 0
        for item in self.items:
            imagename = item[0]
            imageindex = self.geticonid(imagename)
            if imageindex is None:
                imageindex = -1 # XXXX
                print '_AssetsView: no icon for', imagename
            text = item[1]
            iteminfo = item[2:]
            lc.insertItem(row, text, imageindex, iteminfo)
            row = row + 1

    def setColumns(self, columnlist):
        self.columnsTemplate = columnlist

    def setItems(self, items):
        self.items = items

    def getSelected(self):
        if not self.listCtrl:
            return -1
        return self.listCtrl.getSelected()

    def OnSelChanged(self):
        cursel = self.listCtrl.getSelected()
        cb = self._cmddict.get('select')
        if cb:
            cb(cursel)

    # Called by the listCtrl code when it wants to start
    # a drag. If the current focus is draggable start the
    # drag and return 1.
    def startDrag(self):
        cursel = self.listCtrl.getSelected()
        if cursel < 0:
            return 0
        cb = self._cmddict.get('startdrag')
        if not cb:
            return 0
        return cb(cursel)

    def doDragDrop(self, flavor, value, ignoreself=0, effects=None):
        if ignoreself:
            self._ignoredragdrop = 1
        flavorid, str = DropTarget.EncodeDragData(flavor, value)
        if effects is None:
            rv = self.listCtrl.DoDragDrop(flavorid, str)
        else:
            rv = self.listCtrl.DoDragDrop(flavorid, str, effects)
        self._ignoredragdrop = 0
        return rv

    #
    # drag/drop destination code
    #

    def dragitem(self,dataobj,kbdstate,x,y):
        if self._ignoredragdrop:
            return 0
        cb = self._cmddict.get('dragitem')
        if not cb:
            return 0
        flavor, object = DropTarget.DecodeDragData(dataobj)
        if not flavor:
            return 0
        rv = cb(x, y, flavor, object)
        return DropTarget.Name2DragEffect(rv)

    def dropitem(self,dataobj,effect,x,y):
        if self._ignoredragdrop:
            return 0
        cb = self._cmddict.get('dropitem')
        if not cb:
            return 0
        flavor, object = DropTarget.DecodeDragData(dataobj)
        rv = cb(x, y, flavor, object)
        return DropTarget.Name2DragEffect(rv)
